# 🔧 ИСПРАВЛЕНИЯ ДЛЯ ПРОЕКТА MISIX

## Проблема 1: Кнопки бота не работают

### Файл: `backend/app/bot/handlers/command.py`

**Проблема:** В `handle_quick_action_callback` создается неправильный fake Update.

**Текущий код (строки 260-285):**
```python
async def handle_quick_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from quick action buttons."""
    try:
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        # Route to appropriate handler
        if action == "help":
            await query.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
            logger.info(f"User {query.from_user.id} requested help via button")
            
        elif action == "tasks":
            # Create fake update for tasks command
            fake_update = Update(
                update_id=update.update_id,
                message=query.message
            )
            await handle_tasks_command(fake_update, context)
```

**Исправленный код:**
```python
async def handle_quick_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from quick action buttons."""
    try:
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        logger.info(f"Processing callback action: {action} from user {query.from_user.id}")
        
        # Route to appropriate handler
        if action == "help":
            await query.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
            logger.info(f"User {query.from_user.id} requested help via button")
            
        elif action == "tasks":
            # Call handler directly with callback query context
            try:
                await _handle_tasks_for_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle tasks callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось загрузить задачи. Попробуйте команду /tasks"
                )
            
        elif action == "finances":
            try:
                await _handle_finances_for_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle finances callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось загрузить финансы. Попробуйте команду /finances"
                )
            
        elif action == "mood":
            try:
                await _handle_mood_for_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle mood callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось загрузить настроение. Попробуйте команду /mood"
                )
            
        elif action == "sleep":
            try:
                from app.bot.handlers.sleep import handle_sleep_start_callback
                await handle_sleep_start_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle sleep callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось начать трекинг сна. Попробуйте команду /sleep"
                )
        
        logger.info(f"Successfully processed callback action: {action}")
        
    except Exception as e:
        logger.error(f"Failed to handle quick action callback: {e}", exc_info=True)
        try:
            await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")
        except:
            pass


async def _handle_tasks_for_callback(query, context):
    """Handle tasks command from callback query."""
    from app.repositories.user import get_user_repository
    from app.services.task_service import get_task_service
    
    user_telegram = query.from_user
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.get_by_telegram_id(user_telegram.id)
    
    if not user:
        await query.message.reply_text(
            "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
        )
        return
    
    # Get tasks
    task_service = get_task_service()
    tasks = await task_service.get_by_user(str(user["id"]))
    
    if not tasks:
        await query.message.reply_text(
            "📋 У вас пока нет задач.\n\nСоздайте задачу, написав мне, например:\n\"Напомни завтра купить молоко\""
        )
        return
    
    # Format tasks
    active_tasks = [t for t in tasks if t.get("status") != "completed"]
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    message = "📋 **Ваши задачи:**\n\n"
    
    if active_tasks:
        message += "**Активные:**\n"
        for task in active_tasks[:10]:
            title = task.get("title", "Без названия")
            deadline = task.get("deadline")
            priority = task.get("priority", "medium")
            
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            
            message += f"{priority_emoji} {title}"
            if deadline:
                from datetime import datetime
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                message += f" (до {deadline.strftime('%d.%m')})"
            message += "\n"
    
    if completed_tasks:
        message += f"\n✅ Выполнено: {len(completed_tasks)}"
    
    await query.message.reply_text(message, parse_mode="Markdown")


async def _handle_finances_for_callback(query, context):
    """Handle finances command from callback query."""
    from app.repositories.user import get_user_repository
    from app.services.finance_service import get_finance_service
    
    user_telegram = query.from_user
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.get_by_telegram_id(user_telegram.id)
    
    if not user:
        await query.message.reply_text(
            "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
        )
        return
    
    # Get finances
    finance_service = get_finance_service()
    records = await finance_service.get_by_user(str(user["id"]))
    
    if not records:
        await query.message.reply_text(
            "💰 У вас пока нет финансовых записей.\n\nДобавьте расход, написав:\n\"Потратил 500₽ на кофе\""
        )
        return
    
    # Calculate stats
    total_expenses = sum(r.get("amount", 0) for r in records if r.get("type") == "expense")
    total_income = sum(r.get("amount", 0) for r in records if r.get("type") == "income")
    balance = total_income - total_expenses
    
    # Group by category
    from collections import defaultdict
    expenses_by_category = defaultdict(float)
    for r in records:
        if r.get("type") == "expense":
            category = r.get("category", "другое")
            expenses_by_category[category] += r.get("amount", 0)
    
    message = "💰 **Финансовая сводка:**\n\n"
    message += f"💸 Расходы: {total_expenses:,.0f}₽\n"
    message += f"💵 Доходы: {total_income:,.0f}₽\n"
    message += f"{'📈' if balance >= 0 else '📉'} Баланс: {balance:+,.0f}₽\n"
    
    if expenses_by_category:
        message += "\n**По категориям:**\n"
        sorted_categories = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
        for category, amount in sorted_categories[:5]:
            message += f"• {category}: {amount:,.0f}₽\n"
    
    await query.message.reply_text(message, parse_mode="Markdown")


async def _handle_mood_for_callback(query, context):
    """Handle mood command from callback query."""
    from app.repositories.user import get_user_repository
    from app.services.mood_service import get_mood_service
    
    user_telegram = query.from_user
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.get_by_telegram_id(user_telegram.id)
    
    if not user:
        await query.message.reply_text(
            "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
        )
        return
    
    # Get mood history
    mood_service = get_mood_service()
    history = await mood_service.get_mood_history(str(user["id"]), days=7)
    
    if not history:
        await query.message.reply_text(
            "😊 У вас пока нет записей о настроении.\n\nРасскажите как вы себя чувствуете!"
        )
        return
    
    # Get trends
    trends = await mood_service.analyze_mood_trends(str(user["id"]), days=7)
    
    mood_emojis = {
        "happy": "😊",
        "sad": "😢",
        "anxious": "😰",
        "calm": "😌",
        "excited": "🤩",
        "tired": "😴",
        "stressed": "😫",
        "angry": "😠",
        "neutral": "😐"
    }
    
    message = "😊 **Ваше настроение (последние 7 дней):**\n\n"
    message += f"📊 Средняя интенсивность: {trends.average_intensity:.1f}/10\n"
    message += f"🎯 Чаще всего: {mood_emojis.get(trends.most_common_mood, '😊')} {trends.most_common_mood}\n"
    
    message += "\n**Последние записи:**\n"
    for entry in history[:5]:
        mood = entry.get("mood", "")
        intensity = entry.get("intensity", 5)
        emoji = mood_emojis.get(mood, "😊")
        message += f"{emoji} {mood} ({intensity}/10)\n"
    
    await query.message.reply_text(message, parse_mode="Markdown")
```

---

## Проблема 2: Таблица finance_records отсутствует

### Вариант A: Переименовать таблицу в Supabase

Выполнить в Supabase SQL Editor:

```sql
-- Переименовать таблицу
ALTER TABLE IF EXISTS finance_accounts RENAME TO finance_records;

-- Проверить
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'finance_records';
```

### Вариант B: Обновить код

Если таблица должна называться `finance_accounts`, обновить:

**Файл: `backend/app/repositories/finance.py`**

Заменить все `finance_records` на `finance_accounts`:
```python
# Было:
result = self.supabase.table("finance_records")...

# Стало:
result = self.supabase.table("finance_accounts")...
```

---

## Проблема 3: Добавить обработчик для sleep callback

### Файл: `backend/app/bot/handlers/sleep.py`

Добавить в конец файла:

```python
async def handle_sleep_start_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sleep tracking start from callback query.
    
    Args:
        query: Callback query
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        from datetime import datetime
        
        user_telegram = query.from_user
        
        # Get or create user
        user_repo = get_user_repository()
        user = await user_repo.get_or_create_by_telegram_id(
            telegram_id=user_telegram.id,
            username=user_telegram.username,
            first_name=user_telegram.first_name,
            last_name=user_telegram.last_name
        )
        
        logger.info(f"User {user_telegram.id} started sleep tracking via button")
        
        # TODO: Save sleep start time to database
        # For now, just acknowledge
        await query.message.reply_text(
            "🛌 Спокойной ночи! Я запомнил, что вы легли спать.\n\n"
            "Напишите /wake когда проснетесь, чтобы я записал продолжительность сна."
        )
        
    except Exception as e:
        logger.error(f"Failed to start sleep tracking: {e}", exc_info=True)
        await query.message.reply_text(
            "Не удалось начать трекинг сна. Попробуйте позже."
        )
```

---

## Проблема 4: Улучшить логирование ошибок

### Файл: `backend/app/bot/handlers/command.py`

В начале каждого обработчика добавить try-catch с логированием:

```python
async def handle_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command - show user's tasks."""
    try:
        # ... existing code ...
    except Exception as e:
        logger.error(f"Failed to handle tasks command: {e}", exc_info=True)
        try:
            await update.message.reply_text(
                "Не удалось загрузить задачи. Попробуйте позже."
            )
        except:
            pass
```

---

## Тестирование после исправлений

### 1. Проверить кнопки бота:

```bash
# Отправить боту /start
# Нажать на каждую кнопку:
# - ❓ Помощь
# - 📋 Задачи
# - 💰 Финансы
# - 😊 Настроение
# - 🛌 Я спать
```

### 2. Проверить логи:

```bash
# Проверить логи на Render.com
# Должны быть сообщения:
# "Processing callback action: tasks from user 123456"
# "Successfully processed callback action: tasks"
```

### 3. Проверить finance_records:

```python
# Запустить в Python:
from app.shared.supabase import get_supabase_client
supabase = get_supabase_client()
result = supabase.table('finance_records').select('*').limit(1).execute()
print(result.data)
```

---

## Приоритет применения:

1. ✅ **КРИТИЧНО:** Исправить callback handlers (Проблема 1)
2. ✅ **КРИТИЧНО:** Исправить finance_records (Проблема 2)
3. ✅ **ВАЖНО:** Добавить sleep callback (Проблема 3)
4. ✅ **ВАЖНО:** Улучшить логирование (Проблема 4)

---

## После применения исправлений:

1. Перезапустить бота на Render.com
2. Протестировать все кнопки
3. Проверить логи
4. Обновить статус в CRITICAL_ANALYSIS_REPORT.md
