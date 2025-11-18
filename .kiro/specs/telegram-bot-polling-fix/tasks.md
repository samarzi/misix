# Implementation Plan

- [x] 1. Create PollingManager class
  - Create `backend/app/bot/polling.py` with PollingManager class
  - Implement `__init__`, `start_polling`, `stop_polling`, and `_poll_updates` methods
  - Add proper error handling and logging
  - Track polling state (is_running, last_update_id, etc.)
  - _Requirements: 1.1, 1.4, 3.3_

- [x] 2. Implement polling loop logic
  - Implement `_poll_updates` method with infinite loop
  - Use `bot.get_updates()` with 30-second timeout
  - Track offset to avoid duplicate updates
  - Process updates through `application.process_update()`
  - Add error recovery with 5-second retry delay
  - _Requirements: 1.2, 1.3, 1.4, 3.5_

- [x] 3. Add configuration detection
  - Create `should_use_polling()` function in polling.py
  - Check if webhook URL is configured and valid
  - Return True if polling should be used, False otherwise
  - _Requirements: 3.1, 3.2_

- [x] 4. Integrate polling into bot initialization
  - Update `backend/app/bot/__init__.py`
  - Add `get_polling_manager()` function
  - Store polling manager as module-level variable
  - Export polling manager functions
  - _Requirements: 1.1, 3.2_

- [x] 5. Update application lifecycle
  - Modify `backend/app/web/main.py` lifespan function
  - Import polling manager
  - Start polling after `application.start()` if webhook not configured
  - Stop polling before `application.stop()` during shutdown
  - Add proper error handling and logging
  - _Requirements: 1.1, 1.5, 3.2, 3.4_

- [x] 6. Add comprehensive logging
  - Log polling start with configuration details
  - Log number of updates received in each batch
  - Log errors with full context and traceback
  - Log polling stop during shutdown
  - Log update processing (update_id, user_id, type)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 7. Test polling locally
  - Start the application locally
  - Send test message to bot via Telegram
  - Verify message is received and processed
  - Check logs for polling activity
  - Test error recovery by simulating network issues
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 8. Deploy and verify in production
  - Deploy updated code to Render
  - Monitor logs for polling start message
  - Send test message to production bot
  - Verify message is received and response sent
  - Monitor for any errors or issues
  - _Requirements: 3.4, 3.5_
