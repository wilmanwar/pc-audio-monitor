"""Main entry point for PC Audio Monitor."""

import logging
import os
import time
import signal
from dotenv import load_dotenv
from audio_capture import AudioCapture
from audio_monitor import AudioMonitor
from alert_schedule import AlertSchedule
from ha_notifier import HomeAssistantNotifier

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

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle shutdown signal."""
    global running
    logger.info("\nShutdown signal received. Stopping monitor...")
    running = False


def main():
    """Main entry point."""
    global running
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 70)
    logger.info("PC Audio Monitor - Home Assistant Integration")
    logger.info("=" * 70)
    
    try:
        # Initialize Home Assistant notifier
        logger.info("Initializing Home Assistant notifier...")
        ha_notifier = HomeAssistantNotifier.from_env()
        if not ha_notifier:
            logger.warning("Home Assistant configuration incomplete. Alerts will not be sent.")
            logger.warning("Set HA_HOST and HA_TOKEN environment variables in .env file")
            ha_notify = lambda: None
        else:
            ha_notify = ha_notifier.send_alert
        
        # Initialize audio capture
        threshold_db = float(os.getenv('AUDIO_THRESHOLD_DB', '-40'))
        chunk_duration = float(os.getenv('AUDIO_CHUNK_DURATION_SECONDS', '2.0'))
        monitor_interval = float(os.getenv('MONITOR_INTERVAL_SECONDS', '60'))
        cooldown = int(os.getenv('ALERT_COOLDOWN_SECONDS', '60'))
        
        logger.info(f"Audio settings: threshold={threshold_db}dB, chunk={chunk_duration}s, cooldown={cooldown}s")
        logger.info(f"Monitor interval: {monitor_interval} seconds")
        
        # Initialize alert schedule (when alerts are enabled)
        alert_schedule = AlertSchedule.from_env()
        logger.info(f"Alert schedule: {alert_schedule.get_status()}")
        
        audio_capture = AudioCapture(threshold_db=threshold_db, duration=chunk_duration)
        audio_monitor = AudioMonitor(
            on_sound_stopped=ha_notify,
            cooldown_seconds=cooldown,
            alert_schedule=alert_schedule
        )
        
        logger.info("Monitor ready. Waiting for audio status changes...")
        logger.info("Press Ctrl+C to stop.\n")
        
        # Main monitoring loop
        check_count = 0
        while running:
            try:
                check_count += 1
                logger.debug(f"[Check #{check_count}] Analyzing audio...")
                
                has_audio, rms_db = audio_capture.has_audio()
                audio_monitor.update(has_audio)
                
                schedule_status = audio_monitor.alert_schedule.get_status()
                logger.info(f"RMS: {rms_db:7.2f} dB | State: {audio_monitor.current_state.value:8s} | {schedule_status}")
                
                # Wait before next check
                for _ in range(int(monitor_interval)):
                    if not running:
                        break
                    time.sleep(1)
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retry
        
        logger.info("Monitor stopped.")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())

