# Telegram Webhook Fix - Deployment Instructions

## Проблема
Бот не отвечает на сообщения, потому что webhook не установлен в Telegram API.

## Решение
Добавлен WebhookManager для автоматической установки webhook при старте приложения.

## Что было сделано

### 1. Код
- ✅ Создан `backend/app/bot/webhook.py` - WebhookManager для управления webhook
- ✅ Обновлен `backend/app/bot/__init__.py` - добавлены функции get_webhook_manager() и get_webhook_url()
- ✅ Обновлен `backend/app/web/main.py` - интегрирован WebhookManager в lifecycle
- ✅ Обновлен `render.yaml` - добавлена переменная TELEGRAM_WEBHOOK_URL
- ✅ Обновлен `backend/.env.example` - добавлена документация
- ✅ Написаны property-based тесты (100 итераций каждый)

### 2. Тесты
- ✅ 12 тестов написано
- ✅ Все тесты прошли успешно
- ✅ Property-based тесты с hypothesis

## Инструкции по деплою

### Шаг 1: Добавить переменную окружения в Render

1. Зайди в Render Dashboard: https://dashboard.render.com
2. Выбери сервис `misix-backend`
3. Перейди в **Environment**
4. Добавь новую переменную:
   ```
   Key: TELEGRAM_WEBHOOK_URL
   Value: https://misix.onrender.com/bot/webhook
   ```
5. Нажми **Save Changes**

### Шаг 2: Задеплой изменения

Render автоматически задеплоит после сохранения переменной окружения.

Или можно вручную:
```bash
git add .
git commit -m "fix: add webhook manager for telegram bot"
git push origin main
```

### Шаг 3: Проверь логи

После деплоя проверь логи в Render:

Ищи эти сообщения:
```
✅ Webhook set successfully: https://misix.onrender.com/bot/webhook
📨 Processed 6 pending updates
```

### Шаг 4: Проверь webhook в Telegram

Выполни команду:
```bash
curl "https://api.telegram.org/bot8434194677:AAFsWYG1BKJlj1ujALNs4M6yniW1_GeHQcQ/getWebhookInfo"
```

Должен вернуться:
```json
{
  "ok": true,
  "result": {
    "url": "https://misix.onrender.com/bot/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### Шаг 5: Протестируй бота

1. Открой Telegram
2. Найди бота @misix_bot (или как он называется)
3. Отправь сообщение: "Привет"
4. Бот должен ответить!

## Что происходит при старте

1. Приложение запускается
2. Проверяется конфигурация (webhook или polling)
3. Если webhook mode:
   - Получается webhook URL из TELEGRAM_WEBHOOK_URL или BACKEND_BASE_URL
   - Проверяется текущий статус webhook в Telegram
   - Устанавливается новый webhook
   - Обрабатываются все накопившиеся сообщения (6 штук)
4. Если polling mode:
   - Удаляется webhook (если был)
   - Запускается polling

## Логи для мониторинга

Успешная установка webhook:
```
🌐 Webhook mode detected, setting up webhook...
📡 Current webhook: none (pending: 6)
🔧 Setting webhook to: https://misix.onrender.com/bot/webhook
✅ Webhook set successfully in 1.23s
📡 Webhook URL: https://misix.onrender.com/bot/webhook
📨 Pending updates: 6
🔄 Processing 6 pending updates...
✅ Processed 6 pending updates
✅ Phase 3 complete: Telegram bot initialized
```

Ошибка установки webhook:
```
❌ Failed to set webhook: <error message>
⚠️  Bot will not receive messages via webhook
```

## Откат (Rollback)

Если что-то пошло не так:

1. Удали переменную `TELEGRAM_WEBHOOK_URL` из Render
2. Приложение автоматически переключится на polling mode
3. Бот продолжит работать через polling

## Troubleshooting

### Webhook не устанавливается
- Проверь, что URL начинается с `https://`
- Проверь, что URL доступен извне
- Проверь логи на ошибки

### Бот не отвечает после установки webhook
- Проверь, что webhook endpoint `/bot/webhook` доступен
- Проверь логи на ошибки обработки обновлений
- Проверь, что TELEGRAM_BOT_TOKEN правильный

### Накопившиеся сообщения не обработались
- Проверь логи на ошибки в `process_pending_updates`
- Сообщения могли быть слишком старыми (Telegram хранит 24 часа)

## Дополнительная информация

- Спецификация: `.kiro/specs/telegram-webhook-fix/`
- Тесты: `backend/tests/unit/test_webhook_manager.py`
- WebhookManager: `backend/app/bot/webhook.py`
