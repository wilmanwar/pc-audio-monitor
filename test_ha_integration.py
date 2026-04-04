#!/usr/bin/env python
"""Test script for Home Assistant integration."""

import logging
import os
from dotenv import load_dotenv
from ha_notifier import HomeAssistantNotifier

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("Home Assistant Integration Test")
    logger.info("=" * 70)
    
    # Initialize notifier from environment
    notifier = HomeAssistantNotifier.from_env()
    
    if not notifier:
        logger.error("Failed to initialize notifier. Check HA_HOST and HA_TOKEN in .env")
        return 1
    
    logger.info(f"Notifier configured:")
    logger.info(f"  Host: {notifier.host}:{notifier.port}")
    logger.info(f"  Service: {notifier.notify_service}")
    logger.info(f"  Protocol: {notifier.protocol}")
    
    logger.info("\nSending test alert...")
    success = notifier.send_alert(
        title="PC Audio Monitor Test",
        message="This is a test message from the PC Audio Monitor app"
    )
    
    if success:
        logger.info("SUCCESS: Alert sent to Home Assistant!")
        return 0
    else:
        logger.error("FAILED: Could not send alert. Check Home Assistant configuration.")
        return 1


if __name__ == '__main__':
    exit(main())
