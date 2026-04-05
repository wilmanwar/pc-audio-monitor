"""Main entry point for PC Audio Monitor."""

import logging
import os
import time
import signal
import numpy as np
from dotenv import load_dotenv

from audio_capture import AudioCapture
from audio_monitor import AudioMonitor
from alert_schedule import AlertSchedule
from music_classifier import MusicClassifier
from notifier import MultiNotifier

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('LOG_FILE', 'pc_audio_monitor.log')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

running = True


def signal_handler(sig, frame):
    global running
    logger.info("\nShutdown signal received. Stopping monitor...")
    running = False


def main():
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 70)
    logger.info("PC Audio Monitor — Music Interruption Detector")
    logger.info("=" * 70)

    try:
        # --- Notification channels (HA + Pushover) ---
        notifier = MultiNotifier()

        # --- Settings ---
        threshold_db      = float(os.getenv('AUDIO_THRESHOLD_DB', '-50'))
        silence_threshold = float(os.getenv('SILENCE_THRESHOLD_DB', '-75'))
        chunk_duration    = float(os.getenv('AUDIO_CHUNK_DURATION_SECONDS', '3.0'))
        monitor_interval  = float(os.getenv('MONITOR_INTERVAL_SECONDS', '5'))
        cooldown          = int(os.getenv('ALERT_COOLDOWN_SECONDS', '300'))
        auto_detect       = os.getenv('AUTO_DETECT_AUDIO', 'true').lower() in ('true', '1', 'yes')
        alert_after       = int(os.getenv('ALERT_AFTER_SECONDS', '180'))   # 3 minutes
        genre_window      = int(os.getenv('GENRE_WINDOW', '12'))           # checks to average genre over

        logger.info(
            f"Settings: silence_threshold={silence_threshold}dB  low_volume={threshold_db}dB  "
            f"chunk={chunk_duration}s  interval={monitor_interval}s  "
            f"cooldown={cooldown}s  alert_after={alert_after}s  genre_window={genre_window}"
        )

        # --- Alert schedule ---
        alert_schedule = AlertSchedule.from_env()
        logger.info(f"Alert schedule: {alert_schedule.get_status()}")

        # --- Core components ---
        audio_capture  = AudioCapture(
            threshold_db=threshold_db,
            silence_threshold_db=silence_threshold,
            duration=chunk_duration,
            auto_detect=auto_detect,
        )
        classifier     = MusicClassifier(samplerate=int(os.getenv('AUDIO_SAMPLE_RATE', '44100')))
        audio_monitor  = AudioMonitor(
            on_music_interrupted=notifier.send_alert,
            cooldown_seconds=cooldown,
            alert_after_seconds=alert_after,
            genre_window=genre_window,
            alert_schedule=alert_schedule,
        )

        logger.info("Monitor ready. Listening for music…")
        logger.info("Press Ctrl+C to stop.\n")

        check_count = 0
        while running:
            try:
                check_count += 1

                # 1. Capture once — reuse for both RMS check and classification
                has_audio, is_low_volume, rms_db, raw_audio = audio_capture.capture_and_analyze()

                # 2. Classify
                if has_audio and len(raw_audio) > 0:
                    result = classifier.classify_audio(raw_audio)
                    is_music   = result['is_music']
                    music_conf = result['music_confidence']
                    genre      = result['genre']
                    genre_conf = result['genre_confidence']
                    if is_low_volume:
                        logger.debug(
                            f"Low volume ({rms_db:.1f}dB) but classifying anyway: "
                            f"{'music' if is_music else 'not music'} ({genre})"
                        )
                else:
                    is_music   = False
                    music_conf = 0.0
                    genre      = 'Silence'
                    genre_conf = 1.0

                # 3. Update state machine
                audio_monitor.update(
                    has_audio=has_audio,
                    is_music=is_music,
                    music_confidence=music_conf,
                    genre=genre,
                    genre_confidence=genre_conf,
                )

                # 4. Send live status to HA on every poll (no window gating)
                interruption_secs = None
                if audio_monitor._interruption_since is not None:
                    from datetime import datetime
                    interruption_secs = (datetime.now() - audio_monitor._interruption_since).total_seconds()

                stable_genre, stable_conf = audio_monitor._stable_genre()
                notifier.update_status(
                    state=audio_monitor.current_state.value,
                    genre=stable_genre,
                    genre_confidence=stable_conf,
                    music_confidence=music_conf,
                    rms_db=rms_db,
                    interruption_seconds=interruption_secs,
                    alert_after_seconds=alert_after,
                    raw_genre=genre,
                    raw_genre_confidence=genre_conf,
                )

                # 5. Log summary
                state_label = audio_monitor.current_state.value.upper()
                schedule_status = audio_monitor.alert_schedule.get_status()
                logger.info(
                    f"[#{check_count:4d}] RMS={rms_db:7.2f}dB | "
                    f"State={state_label:9s} | "
                    f"Raw={genre:12s} ({genre_conf:.0%}) | "
                    f"Stable={stable_genre:12s} ({stable_conf:.0%}) | "
                    f"MusicConf={music_conf:.2f} | {schedule_status}"
                )

                # 6. Wait for next check
                for _ in range(int(monitor_interval)):
                    if not running:
                        break
                    time.sleep(1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(5)

        logger.info("Monitor stopped.")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())