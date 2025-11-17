# Implementation Plan: Bot Critical Diagnosis and Fix

## Phase 1: Diagnostic Tools

- [x] 1. Create diagnostic script
  - Create `backend/diagnose.py` with SystemDiagnostics class
  - Implement environment variables check
  - Implement database connection test
  - Implement database schema validation
  - Implement bot initialization test
  - Implement handlers registration check
  - Implement AI service availability test
  - Generate markdown diagnostic report
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 2. Create database validation utilities
  - Create `backend/app/core/database_validator.py`
  - Implement check_connection() method
  - Implement check_tables_exist() method
  - Implement check_schema_integrity() method
  - Add detailed error messages for each check
  - _Requirements: 2.1, 2.5, 9.5_

- [ ] 3. Create bot validation utilities
  - Create `backend/app/bot/validator.py` with BotValidator class
  - Implement validate_environment() method
  - Implement validate_handlers() method
  - Implement validate_database() method
  - Implement validate_full_startup() method
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

## Phase 2: Database Fixes

- [ ] 4. Create unified migration script
  - Create `backend/apply_all_migrations.py`
  - Implement MigrationManager class
  - Add check_existing_tables() method
  - Add apply_migration() method with error handling
  - Add verify_schema() method
  - Add rollback capability for failed migrations
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 5. Verify and fix database schema
  - Run diagnostic to identify missing tables
  - Apply 001_complete_schema.sql migration
  - Apply 002_add_missing_columns.sql migration
  - Apply 004_add_mood_entries.sql migration
  - Apply 005_add_reminders.sql migration
  - Apply 006_add_indexes.sql migration
  - Verify all tables exist with correct columns
  - Create test data for validation
  - _Requirements: 2.1, 2.2, 9.1, 9.2, 9.3_

- [ ] 6. Test database CRUD operations
  - Test user creation and retrieval
  - Test task creation and retrieval
  - Test finance record creation
  - Test note creation
  - Test mood entry creation
  - Test message history storage
  - Verify foreign key constraints work
  - _Requirements: 2.1, 2.2, 2.3_

## Phase 3: Bot Initialization Fixes

- [x] 7. Fix bot initialization in __init__.py
  - Review current _create_application() function
  - Add validation before handler registration
  - Add detailed logging for each step
  - Add error handling with graceful degradation
  - Verify all handlers are registered
  - Log registered handlers list on startup
  - _Requirements: 7.1, 7.2, 7.4, 10.1_

- [ ] 8. Add startup validation
  - Import BotValidator in bot/__init__.py
  - Run validation before starting bot
  - Log validation results
  - Fail fast if critical components missing
  - Add retry logic for transient failures
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 9. Enhance bot run.py
  - Add pre-flight checks before starting
  - Add better error messages for common issues
  - Add health check loop with logging
  - Add graceful shutdown handling
  - Test both polling and webhook modes
  - _Requirements: 7.1, 7.4, 7.5, 10.5_

## Phase 4: Command Handlers Fixes

- [ ] 10. Test and fix /start command
  - Run /start command manually
  - Verify user is created in database
  - Verify welcome message is sent
  - Add error handling for database failures
  - Add logging for user registration
  - _Requirements: 3.1, 10.2_

- [ ] 11. Test and fix /help command
  - Run /help command manually
  - Verify help message is sent
  - Update help text if needed
  - Add logging
  - _Requirements: 3.2, 10.2_

- [ ] 12. Test and fix /tasks command
  - Run /tasks command manually
  - Verify tasks are retrieved from database
  - Verify empty state message works
  - Fix any database query issues
  - Add pagination if needed
  - Add logging
  - _Requirements: 3.3, 2.2, 10.2_

- [ ] 13. Test and fix /finances command
  - Run /finances command manually
  - Verify finance records are retrieved
  - Verify calculations are correct
  - Fix category grouping if broken
  - Add logging
  - _Requirements: 3.4, 2.2, 10.2_

- [ ] 14. Test and fix /mood command
  - Run /mood command manually
  - Verify mood entries are retrieved
  - Verify trends calculation works
  - Fix emoji mapping if needed
  - Add logging
  - _Requirements: 3.5, 2.2, 10.2_

- [ ] 15. Test and fix /profile command
  - Run /profile command manually
  - Verify user data is retrieved
  - Update profile display format
  - Add logging
  - _Requirements: 3.6, 10.2_

- [ ] 16. Test and fix /reminders command
  - Run /reminders command manually
  - Verify settings are retrieved
  - Verify inline keyboard is displayed
  - Fix any button issues
  - Add logging
  - _Requirements: 3.7, 4.2, 10.2_

## Phase 5: Callback Handlers Fixes

- [ ] 17. Test and fix reminder callbacks
  - Test "toggle reminders" button
  - Test "change time" buttons
  - Test "change summary time" button
  - Verify database updates work
  - Verify message updates work
  - Add error handling
  - Add logging
  - _Requirements: 4.2, 4.3, 4.4, 4.5, 10.2_

- [ ] 18. Add sleep tracking buttons (if needed)
  - Review sleep.py handlers
  - Add inline keyboard to /sleep command
  - Implement callback handlers for sleep actions
  - Test button interactions
  - Add logging
  - _Requirements: 4.1, 4.2, 4.3_

## Phase 6: Memory and Context Fixes

- [ ] 19. Test message history storage
  - Send test message to bot
  - Verify message is saved to assistant_messages table
  - Verify user_id and telegram_id are correct
  - Verify timestamp is correct
  - Check for any database errors
  - _Requirements: 5.1, 2.1, 10.2_

- [ ] 20. Test conversation context retrieval
  - Send multiple messages to bot
  - Verify last 6 messages are retrieved
  - Verify context is passed to AI
  - Test context-aware responses
  - _Requirements: 5.2, 5.3, 10.2_

- [ ] 21. Test context limits and cleanup
  - Send more than 6 messages
  - Verify only last 6 are used
  - Test with new user (empty history)
  - Verify old messages are kept in DB
  - _Requirements: 5.4, 5.5_

## Phase 7: Enhanced Logging

- [ ] 22. Add detailed logging to all handlers
  - Add entry/exit logs to each handler
  - Log user_id and message_id
  - Log input parameters
  - Log execution time
  - Log errors with stack traces
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 23. Add structured logging
  - Update logging configuration
  - Add request_id to all logs
  - Add user_id to all logs
  - Add component name to all logs
  - Format logs as JSON for production
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 24. Add heartbeat logging
  - Add periodic health check log
  - Log active connections
  - Log memory usage
  - Log error counts
  - Run every 60 seconds
  - _Requirements: 10.5_

## Phase 8: Web Application Check

- [ ] 25. Test web app loading
  - Open https://misix.netlify.app
  - Check for console errors
  - Verify assets load correctly
  - Check network requests
  - _Requirements: 6.1, 6.5_

- [ ] 26. Test API connectivity
  - Test /health endpoint
  - Test /api/v2/auth/login endpoint
  - Check CORS headers
  - Verify error messages
  - _Requirements: 6.2, 6.3, 6.5_

- [ ] 27. Fix CORS if needed
  - Check FRONTEND_ALLOWED_ORIGINS in .env
  - Update CORS middleware if needed
  - Test from web app
  - Verify preflight requests work
  - _Requirements: 6.5_

- [ ] 28. Test authentication flow
  - Try to register new user
  - Try to login
  - Verify JWT token is returned
  - Test token refresh
  - Test protected endpoints
  - _Requirements: 6.4_

## Phase 9: End-to-End Testing

- [ ] 29. Create automated test script
  - Create `backend/test_bot_commands.py`
  - Implement BotCommandTester class
  - Add test_command() method
  - Add test_all_commands() method
  - Add test_callback_handlers() method
  - Generate test report
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 30. Run manual testing checklist
  - Test /start command
  - Test /help command
  - Test natural language message
  - Test task creation
  - Test /tasks command
  - Test finance tracking
  - Test /finances command
  - Test mood tracking
  - Test /mood command
  - Test reminder buttons
  - Test voice message
  - Test web app login
  - Document any issues found
  - _Requirements: All_

## Phase 10: Documentation and Deployment

- [ ] 31. Create diagnostic report
  - Run full diagnostic script
  - Generate markdown report
  - Document all issues found
  - Document all fixes applied
  - Add recommendations for future
  - _Requirements: 8.5_

- [ ] 32. Update deployment documentation
  - Update DEPLOYMENT.md with new steps
  - Add troubleshooting section
  - Add diagnostic script usage
  - Add common issues and solutions
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 33. Create monitoring dashboard
  - Set up health check endpoint
  - Add metrics collection
  - Create simple status page
  - Add alerting rules
  - Document monitoring setup
  - _Requirements: 10.5_

- [ ] 34. Deploy fixes to production
  - Apply database migrations on production
  - Deploy updated bot code
  - Verify bot starts successfully
  - Monitor logs for errors
  - Test all commands in production
  - _Requirements: All_

## Phase 11: Validation and Monitoring

- [ ] 35. Monitor bot for 24 hours
  - Check logs every 2 hours
  - Verify no errors
  - Check user interactions
  - Verify data is being saved
  - Check memory usage
  - _Requirements: 10.5_

- [ ] 36. Collect user feedback
  - Ask users to test bot
  - Document any issues reported
  - Fix critical issues immediately
  - Plan fixes for minor issues
  - _Requirements: All_

- [ ] 37. Create post-mortem document
  - Document root causes found
  - Document fixes applied
  - Document lessons learned
  - Add preventive measures
  - Share with team
  - _Requirements: All_
