"""Background scheduler for task reminders."""

import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot

from app.services.reminder_service import get_reminder_service
from app.bot.notifier import get_telegram_notifier

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


async def check_and_send_reminders(bot: Bot):
    """Check for tasks needing reminders and send them.
    
    Args:
        bot: Telegram Bot instance
    """
    try:
        logger.info("Starting reminder check...")
        
        reminder_service = get_reminder_service()
        notifier = get_telegram_notifier(bot)
        
        # Get reminders to send
        reminders = await reminder_service.check_reminders()
        
        if not reminders:
            logger.info("No reminders to send")
            return
        
        # Send reminders
        sent_count = 0
        failed_count = 0
        
        for reminder in reminders:
            success = await notifier.send_reminder(
                telegram_id=reminder["user"]["telegram_id"],
                task=reminder["task"],
                reminder_type=reminder["reminder_type"]
            )
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
                # Retry after 1 minute
                asyncio.create_task(
                    retry_send_reminder(bot, reminder, delay=60)
                )
        
        logger.info(f"Reminders sent: {sent_count}, failed: {failed_count}")
        
    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {e}", exc_info=True)


async def retry_send_reminder(bot: Bot, reminder: dict, delay: int = 60):
    """Retry sending a failed reminder after delay.
    
    Args:
        bot: Telegram Bot instance
        reminder: Reminder dict
        delay: Delay in seconds before retry
    """
    try:
        await asyncio.sleep(delay)
        
        logger.info(f"Retrying reminder for task {reminder['task']['id']}")
        
        notifier = get_telegram_notifier(bot)
        await notifier.send_reminder(
            telegram_id=reminder["user"]["telegram_id"],
            task=reminder["task"],
            reminder_type=reminder["reminder_type"]
        )
        
    except Exception as e:
        logger.error(f"Retry failed for reminder: {e}")


async def send_daily_summaries(bot: Bot):
    """Send daily summaries to all users.
    
    Args:
        bot: Telegram Bot instance
    """
    try:
        logger.info("Starting daily summary send...")
        
        reminder_service = get_reminder_service()
        notifier = get_telegram_notifier(bot)
        
        # Get all users
        users = await reminder_service.get_all_users_for_summary()
        
        sent_count = 0
        skipped_count = 0
        
        for user in users:
            # Get summary data
            summary_data = await reminder_service.get_daily_summary_data(user["id"])
            
            if not summary_data:
                skipped_count += 1
                continue
            
            # Send summary
            success = await notifier.send_daily_summary(
                telegram_id=user["telegram_id"],
                summary_data=summary_data
            )
            
            if success:
                sent_count += 1
        
        logger.info(f"Daily summaries sent: {sent_count}, skipped: {skipped_count}")
        
    except Exception as e:
        logger.error(f"Error in send_daily_summaries: {e}", exc_info=True)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Set up and start the scheduler.
    
    Args:
        bot: Telegram Bot instance
        
    Returns:
        Configured AsyncIOScheduler
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already exists, returning existing instance")
        return scheduler
    
    logger.info("Setting up scheduler...")
    
    scheduler = AsyncIOScheduler()
    
    # Check reminders every 5 minutes
    scheduler.add_job(
        check_and_send_reminders,
        trigger=IntervalTrigger(minutes=5),
        args=[bot],
        id='check_reminders',
        name='Check and send task reminders',
        replace_existing=True,
        max_instances=1
    )
    
    # Daily summary at 9:00 AM
    scheduler.add_job(
        send_daily_summaries,
        trigger=CronTrigger(hour=9, minute=0),
        args=[bot],
        id='daily_summary',
        name='Send daily task summaries',
        replace_existing=True,
        max_instances=1
    )
    
    logger.info("Scheduler configured with jobs:")
    logger.info("  - check_reminders: every 5 minutes")
    logger.info("  - daily_summary: daily at 9:00 AM")
    
    return scheduler


def start_scheduler():
    """Start the scheduler."""
    global scheduler
    
    if scheduler is None:
        logger.error("Scheduler not set up, call setup_scheduler first")
        return
    
    if scheduler.running:
        logger.warning("Scheduler already running")
        return
    
    try:
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler not initialized")
        return
    
    if not scheduler.running:
        logger.warning("Scheduler not running")
        return
    
    try:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance.
    
    Returns:
        AsyncIOScheduler instance or None
    """
    return scheduler
