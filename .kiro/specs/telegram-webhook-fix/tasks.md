# Implementation Plan

- [x] 1. Create WebhookManager component
  - Create new file `backend/app/bot/webhook.py` with WebhookManager class
  - Implement `set_webhook()` method to register webhook in Telegram API
  - Implement `delete_webhook()` method to remove webhook from Telegram API
  - Implement `get_webhook_info()` method to check current webhook status
  - Implement `process_pending_updates()` method to handle queued messages
  - Add comprehensive logging for all webhook operations
  - Add error handling with retry logic for network errors
  - _Requirements: 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3_

- [x] 1.1 Write property test for webhook setup
  - **Property 1: Webhook установка в production**
  - **Validates: Requirements 1.1, 3.1, 3.5**

- [x] 1.2 Write property test for error resilience
  - **Property 4: Устойчивость к ошибкам обработки**
  - **Validates: Requirements 4.3**

- [-] 2. Add webhook configuration helpers
  - Add `get_webhook_url()` function to determine webhook URL from environment
  - Add `get_webhook_manager()` function to bot/__init__.py
  - Update `should_use_polling()` to check webhook validity more thoroughly
  - Add URL validation logic (HTTPS, not localhost, not example.com)
  - Export new functions from bot/__init__.py
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 2.1 Write property test for polling fallback
  - **Property 2: Fallback на polling при невалидном webhook**
  - **Validates: Requirements 1.3, 3.3, 3.4**

- [ ] 2.2 Write unit tests for URL validation
  - Test valid HTTPS URLs are accepted
  - Test localhost URLs trigger polling
  - Test HTTP URLs trigger polling
  - Test example.com URLs trigger polling
  - _Requirements: 3.3, 3.4_

- [-] 3. Update application lifecycle in web/main.py
  - Modify lifespan() function to integrate WebhookManager
  - Add webhook setup logic in Phase 3 (after bot initialization)
  - Check current webhook status before setting new webhook
  - Process pending updates after webhook setup
  - Add proper webhook cleanup in shutdown phase
  - Add detailed logging for webhook lifecycle events
  - Handle transition between polling and webhook modes
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.1, 2.5, 4.5_

- [ ] 3.1 Write property test for pending updates processing
  - **Property 3: Обработка накопившихся обновлений**
  - **Validates: Requirements 4.1, 4.2**

- [ ] 3.2 Write property test for mode transitions
  - **Property 7: Корректный переход между режимами**
  - **Validates: Requirements 4.5**

- [ ] 3.3 Write integration test for webhook endpoint
  - Send mock Telegram update to /bot/webhook
  - Verify update is processed correctly
  - Verify response is sent to user
  - _Requirements: 1.2_

- [x] 4. Update configuration files
  - Add TELEGRAM_WEBHOOK_URL to render.yaml env vars
  - Update backend/.env.example with TELEGRAM_WEBHOOK_URL
  - Add documentation comments explaining webhook vs polling
  - _Requirements: 3.1, 3.2_

- [ ] 5. Checkpoint - Verify webhook setup locally
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Deploy and configure webhook
  - Add TELEGRAM_WEBHOOK_URL=https://misix.onrender.com/bot/webhook to Render environment
  - Trigger redeploy on Render
  - Monitor logs for successful webhook setup
  - Verify webhook is registered in Telegram API
  - Test bot by sending message
  - Verify pending updates are processed
  - _Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 4.1, 4.2_

- [ ] 6.1 Write property test for webhook logging
  - **Property 6: Полное логирование webhook операций**
  - **Validates: Requirements 1.5, 2.1, 2.2, 2.3, 2.4, 2.5**

- [ ] 7. Final checkpoint - Verify bot is responding
  - Send test messages to bot
  - Verify responses are received
  - Check logs for any errors
  - Verify all 6 pending updates were processed
  - Ensure all tests pass, ask the user if questions arise.
