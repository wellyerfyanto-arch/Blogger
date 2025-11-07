#!/usr/bin/env python3
"""
Dedicated worker untuk scheduler - run sebagai separate service di Render
"""

import os
import time
import schedule
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduler-worker')

# Import app components
import sys
sys.path.append('/opt/render/project/src')

from app import auto_poster

def run_scheduled_posts():
    """Run scheduled posts check"""
    try:
        logger.info("🕒 Running scheduled posts check...")
        auto_poster.process_scheduled_posts()
        logger.info("✅ Scheduled posts check completed")
    except Exception as e:
        logger.error(f"❌ Scheduled posts check failed: {str(e)}")

def main():
    """Main worker loop"""
    logger.info("🚀 Starting Crypto Auto Poster Scheduler Worker")
    
    # Setup schedules
    config = auto_poster.posting_config['posting_schedule']
    
    if config['frequency'] == 'daily':
        schedule.every().day.at(config['time']).do(run_scheduled_posts)
        logger.info(f"✅ Daily scheduler set for {config['time']}")
    elif config['frequency'] == 'weekly':
        for day in config['days']:
            getattr(schedule.every(), day).at(config['time']).do(run_scheduled_posts)
        logger.info(f"✅ Weekly scheduler set for {config['days']} at {config['time']}")
    elif config['frequency'] == 'hourly':
        schedule.every().hour.do(run_scheduled_posts)
        logger.info("✅ Hourly scheduler set")
    
    # Initial run
    logger.info("🔍 Running initial check...")
    run_scheduled_posts()
    
    logger.info("✅ Scheduler worker started successfully")
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Log heartbeat every 30 minutes
            if int(time.time()) % 1800 == 0:
                logger.info("💓 Worker heartbeat - running normally")
                
        except Exception as e:
            logger.error(f"💥 Worker loop error: {str(e)}")
            time.sleep(60)

if __name__ == '__main__':
    main()