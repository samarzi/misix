"""Telegram notification service for reminders."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Service for sending Telegram notifications."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_reminder(
        self,
        telegram_id: int,
        task: Dict,
        reminder_type: str
    ) -> bool:
        """Send task reminder to user.
        
        Args:
            telegram_id: User's Telegram ID
            task: Task dict
            reminder_type: "before" or "deadline"
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = self._format_reminder(task, reminder_type)
            keyboard = self._create_reminder_keyboard(task["id"])
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"Sent {reminder_type} reminder to user {telegram_id} for task {task['id']}")
            return True
            
        except TelegramError as e:
            if "bot was blocked" in str(e).lower():
                logger.warning(f"User {telegram_id} blocked the bot")
            else:
                logger.error(f"Failed to send reminder to {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending reminder: {e}", exc_info=True)
            return False
    
    def _format_reminder(self, task: Dict, reminder_type: str) -> str:
        """Format reminder message.
        
        Args:
            task: Task dict
            reminder_type: "before" or "deadline"
            
        Returns:
            Formatted message string
        """
        # Priority emoji
        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }.get(task.get("priority", "medium"), "🟡")
        
        # Format deadline
        deadline = task.get("deadline")
        if deadline:
            deadline_str = deadline.strftime("%H:%M")
            if deadline.date() == datetime.utcnow().date():
                deadline_display = f"сегодня в {deadline_str}"
            else:
                deadline_display = deadline.strftime("%d.%m в %H:%M")
        else:
            deadline_display = "не указан"
        
        # Build message based on type
        if reminder_type == "before":
            header = "⏰ Напоминание о задаче!"
            time_info = f"📅 Дедлайн: {deadline_display} (скоро!)"
        else:  # deadline
            header = "🔔 Дедлайн задачи наступил!"
            time_info = f"📅 Дедлайн: {deadline_display}"
        
        title = task.get("title", "Без названия")
        
        message = f"""{header}

{priority_emoji} {title}
{time_info}"""
        
        return message
    
    def _create_reminder_keyboard(self, task_id: str) -> InlineKeyboardMarkup:
        """Create inline keyboard for reminder.
        
        Args:
            task_id: Task UUID as string
            
        Returns:
            InlineKeyboardMarkup with action buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Выполнено", callback_data=f"task_complete:{task_id}"),
                InlineKeyboardButton("⏰ Отложить", callback_data=f"task_snooze:{task_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_daily_summary(
        self,
        telegram_id: int,
        summary_data: Dict
    ) -> bool:
        """Send daily summary to user.
        
        Args:
            telegram_id: User's Telegram ID
            summary_data: Dict with today_tasks, overdue_tasks, completed_yesterday
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = self._format_daily_summary(summary_data)
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Sent daily summary to user {telegram_id}")
            return True
            
        except TelegramError as e:
            if "bot was blocked" in str(e).lower():
                logger.warning(f"User {telegram_id} blocked the bot")
            else:
                logger.error(f"Failed to send summary to {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending summary: {e}", exc_info=True)
            return False
    
    def _format_daily_summary(self, data: Dict) -> str:
        """Format daily summary message.
        
        Args:
            data: Dict with today_tasks, overdue_tasks, completed_yesterday
            
        Returns:
            Formatted message string
        """
        today_tasks = data.get("today_tasks", [])
        overdue_tasks = data.get("overdue_tasks", [])
        completed_yesterday = data.get("completed_yesterday", 0)
        
        message = "☀️ Доброе утро! Ваши задачи на сегодня:\n\n"
        
        # Today's tasks
        if today_tasks:
            message += f"📋 Задачи на сегодня ({len(today_tasks)}):\n"
            for task in today_tasks[:5]:  # Limit to 5
                priority_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(task.get("priority", "medium"), "🟡")
                
                title = task.get("title", "Без названия")
                deadline = task.get("deadline")
                time_str = f" ({deadline.strftime('%H:%M')})" if deadline else ""
                
                message += f"{priority_emoji} {title}{time_str}\n"
            
            if len(today_tasks) > 5:
                message += f"... и еще {len(today_tasks) - 5}\n"
            message += "\n"
        
        # Overdue tasks
        if overdue_tasks:
            message += f"⚠️ Просроченные ({len(overdue_tasks)}):\n"
            for task in overdue_tasks[:3]:  # Limit to 3
                priority_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(task.get("priority", "medium"), "🔴")
                
                title = task.get("title", "Без названия")
                deadline = task.get("deadline")
                
                if deadline:
                    days_overdue = (datetime.utcnow().date() - deadline.date()).days
                    if days_overdue == 1:
                        time_str = " (вчера)"
                    else:
                        time_str = f" ({days_overdue} дн. назад)"
                else:
                    time_str = ""
                
                message += f"{priority_emoji} {title}{time_str}\n"
            
            if len(overdue_tasks) > 3:
                message += f"... и еще {len(overdue_tasks) - 3}\n"
            message += "\n"
        
        # Yesterday's stats
        if completed_yesterday > 0:
            message += f"✅ Вчера выполнено: {completed_yesterday} задач\n\n"
        
        message += "Хорошего дня! 💪"
        
        return message


# Singleton instance
_notifier = None


def get_telegram_notifier(bot: Bot) -> TelegramNotifier:
    """Get or create TelegramNotifier singleton."""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier(bot)
    return _notifier
