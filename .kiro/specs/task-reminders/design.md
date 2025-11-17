# Design Document - Task Reminders

## Overview

Система напоминаний использует APScheduler для фоновой проверки задач и отправки уведомлений через Telegram. Поддерживает напоминания перед дедлайном, в момент дедлайна и ежедневную утреннюю сводку.

## Architecture

### Components

```
APScheduler (Background)
    ↓
ReminderService.check_reminders() [every 5 min]
    ↓
TaskRepository.get_tasks_needing_reminders()
    ↓
For each task:
    ↓
TelegramNotifier.send_reminder()
    ↓
Telegram Bot API
    ↓
User receives notification
```

### Daily Summary

```
APScheduler (9:00 AM daily)
    ↓
ReminderService.send_daily_summary()
    ↓
For each user:
    ↓
Get today's tasks + overdue
    ↓
Format summary message
    ↓
TelegramNotifier.send_summary()
```

## Implementation

### 1. ReminderService

**Файл:** `backend/app/services/reminder_service.py`

```python
class ReminderService:
    def __init__(self):
        self.task_repo = get_task_repository()
        self.user_repo = get_user_repository()
    
    async def check_reminders(self):
        """Check and send reminders for tasks."""
        # Get tasks needing reminders
        tasks = await self._get_tasks_needing_reminders()
        
        for task in tasks:
            await self._send_task_reminder(task)
    
    async def send_daily_summary(self):
        """Send daily summary to all users."""
        users = await self.user_repo.get_all_with_telegram()
        
        for user in users:
            await self._send_user_summary(user)
```

### 2. Task Reminder Logic

**Когда отправлять:**
- За 1 час до дедлайна
- В момент дедлайна
- Не отправлять если уже отправляли

**Tracking:**
Добавить поле в tasks:
```sql
last_reminder_sent_at TIMESTAMPTZ
```

### 3. Scheduler Setup

**Файл:** `backend/app/bot/scheduler.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

def setup_scheduler():
    # Check reminders every 5 minutes
    scheduler.add_job(
        check_and_send_reminders,
        trigger=IntervalTrigger(minutes=5),
        id='check_reminders'
    )
    
    # Daily summary at 9:00 AM
    scheduler.add_job(
        send_daily_summaries,
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_summary'
    )
    
    scheduler.start()
```

### 4. Telegram Notifier

**Файл:** `backend/app/bot/notifier.py`

```python
class TelegramNotifier:
    def __init__(self, bot):
        self.bot = bot
    
    async def send_reminder(
        self,
        telegram_id: int,
        task: dict,
        reminder_type: str  # "before" or "deadline"
    ):
        """Send task reminder to user."""
        message = self._format_reminder(task, reminder_type)
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
```

## Database Changes

### Add to tasks table

```sql
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_tasks_deadline 
ON tasks(deadline) WHERE status != 'completed';
```

### Add user_settings table

```sql
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    reminders_enabled BOOLEAN DEFAULT true,
    daily_summary_time TIME DEFAULT '09:00',
    reminder_minutes_before INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Message Formats

### Task Reminder

```
⏰ Напоминание о задаче!

🟡 Позвонить партнеру
📅 Дедлайн: сегодня в 15:00 (через 1 час)

[Выполнено] [Отложить на час] [Отменить]
```

### Daily Summary

```
☀️ Доброе утро! Ваши задачи на сегодня:

📋 Задачи на сегодня (3):
🟡 Позвонить партнеру (15:00)
🟢 Купить молоко
🔴 Встреча с клиентом (18:00)

⚠️ Просроченные (1):
🔴 Оплатить интернет (вчера)

✅ Вчера выполнено: 2 задачи

Хорошего дня! 💪
```

## Error Handling

### Scenarios

1. **User blocked bot**
   - Catch TelegramError
   - Mark user as inactive
   - Stop sending reminders

2. **Task deleted**
   - Check task exists before sending
   - Skip if not found

3. **Scheduler crash**
   - Auto-restart on error
   - Log all errors
   - Alert admin

4. **Database unavailable**
   - Retry after 1 minute
   - Log error
   - Continue with next check

## Performance

### Optimization

- Batch load tasks (100 at a time)
- Parallel notification sending
- Cache user settings
- Index on deadline column

### Monitoring

- Log reminder count per check
- Track send success rate
- Monitor scheduler health
- Alert on failures

## Testing

### Unit Tests

1. Test reminder time calculation
2. Test message formatting
3. Test user settings
4. Test error handling

### Integration Tests

1. Test full reminder flow
2. Test daily summary
3. Test with real scheduler
4. Test Telegram sending

### Manual Testing

1. Create task with deadline in 1 hour
2. Wait and verify reminder received
3. Test daily summary at 9 AM
4. Test settings changes
5. Test with completed tasks

## Future Enhancements

1. Custom reminder times per task
2. Recurring reminders
3. Snooze functionality
4. Reminder history
5. Smart reminders based on user patterns
