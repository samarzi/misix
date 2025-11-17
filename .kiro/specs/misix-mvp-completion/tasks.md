# Implementation Plan: MISIX MVP Completion

## Overview

Этот план описывает пошаговую реализацию всех компонентов для завершения MVP проекта MISIX. Задачи организованы в логическом порядке с учетом зависимостей между компонентами.

---

## Phase 1: Core Message Processing Integration

### 1. Implement Extraction Service

- [ ] 1.1 Create ExtractionService class with Yandex GPT integration
  - Implement `extract_task_data()` method with optimized Russian prompts
  - Implement `extract_finance_data()` method with category detection
  - Implement `extract_note_data()` method with title generation
  - Implement `extract_mood_data()` method with intensity detection
  - Add error handling and logging for all methods
  - _Requirements: 1.1, 2.1_

- [ ] 1.2 Add JSON parsing and validation for extracted data
  - Parse Yandex GPT JSON responses safely
  - Validate extracted data against Pydantic models
  - Handle malformed JSON responses gracefully
  - _Requirements: 1.1, 8.1_

- [ ]* 1.3 Write unit tests for ExtractionService
  - Test each extraction method with sample messages
  - Test error handling for invalid responses
  - Test edge cases (empty messages, special characters)
  - _Requirements: 12.3_

### 2. Enhance Intent Processor

- [ ] 2.1 Complete IntentProcessor implementation
  - Fix indentation issues in `intent_processor.py`
  - Move handler methods inside the class
  - Add proper error handling for each intent type
  - _Requirements: 1.2, 4.1_

- [ ] 2.2 Integrate ExtractionService with IntentProcessor
  - Call extraction service for each intent type
  - Pass extracted data to corresponding service
  - Handle extraction failures gracefully
  - _Requirements: 1.1, 4.2_

- [ ] 2.3 Add support for multiple intents in one message
  - Process all intents with confidence > 0.7
  - Collect all created entities
  - Build combined response for multiple actions
  - _Requirements: 1.5, 2.3_

- [ ]* 2.4 Write unit tests for IntentProcessor
  - Test single intent processing
  - Test multiple intents processing
  - Test low confidence filtering
  - _Requirements: 12.3_

### 3. Create Response Builder

- [ ] 3.1 Implement ResponseBuilder class
  - Create `build_task_created()` with emoji and formatting
  - Create `build_finance_created()` with amount formatting
  - Create `build_note_created()` with title display
  - Create `build_mood_saved()` with mood emoji
  - Create `build_multiple_entities()` for combined responses
  - _Requirements: 1.1, 1.5_

- [ ] 3.2 Add contextual hints and suggestions
  - Add tips for first-time users
  - Suggest related actions
  - Include command shortcuts
  - _Requirements: 5.2_

- [ ]* 3.3 Write unit tests for ResponseBuilder
  - Test each response type
  - Test emoji rendering
  - Test multiple entities formatting
  - _Requirements: 12.1_

### 4. Integrate Message Handler with Intent Classification

- [ ] 4.1 Update message handler to use intent classification
  - Call `AIService.classify_intent()` for each message
  - Log classified intents with confidence scores
  - Handle AI service unavailability
  - _Requirements: 2.1, 2.5_

- [ ] 4.2 Route intents to IntentProcessor
  - Pass intents, message, and user_id to processor
  - Collect created entities from processor
  - Handle processing errors
  - _Requirements: 1.2, 4.1_

- [ ] 4.3 Build and send response to user
  - Use ResponseBuilder to format reply
  - Include all created entities in response
  - Add conversation context
  - Send reply via Telegram
  - _Requirements: 1.1, 4.5_

- [ ] 4.4 Save conversation messages
  - Save user message to conversation history
  - Save assistant response to conversation history
  - Maintain context for next messages
  - _Requirements: 7.1, 7.2_

- [ ]* 4.5 Write integration tests for message flow
  - Test end-to-end message processing
  - Test multiple intent handling
  - Test error scenarios
  - _Requirements: 12.2_

---

## Phase 2: Voice Messages and Commands

### 5. Implement Voice Message Processing

- [ ] 5.1 Complete voice message handler
  - Download voice file from Telegram with 10s timeout
  - Convert to format supported by Yandex SpeechKit
  - Log download time and file size
  - _Requirements: 3.1_

- [ ] 5.2 Integrate Yandex SpeechKit transcription
  - Call `YandexSpeechKit.transcribe_audio()` with 30s timeout
  - Handle transcription errors gracefully
  - Log transcription time and result
  - _Requirements: 3.2_

- [ ] 5.3 Process transcribed text as regular message
  - Show transcribed text to user
  - Pass text to message handler
  - Process intents and create entities
  - _Requirements: 3.3, 3.5_

- [ ] 5.4 Add error handling for voice processing
  - Handle download timeout
  - Handle transcription failures
  - Suggest text message alternative
  - _Requirements: 3.4, 8.4_

- [ ]* 5.5 Write integration tests for voice processing
  - Test successful transcription flow
  - Test timeout scenarios
  - Test error handling
  - _Requirements: 12.2_

### 6. Migrate and Enhance Bot Commands

- [ ] 6.1 Implement /start command
  - Welcome new users
  - Create user profile if doesn't exist
  - Show quick start guide
  - _Requirements: 5.1_

- [ ] 6.2 Implement /help command
  - List all available commands
  - Show usage examples
  - Include natural language examples
  - _Requirements: 5.2_

- [ ] 6.3 Implement /tasks command
  - Fetch user tasks from TaskService
  - Group by status (active, completed)
  - Add inline buttons for task actions (complete, delete)
  - Show task count and statistics
  - _Requirements: 5.3_

- [ ] 6.4 Implement /finances command
  - Fetch finance summary for current month
  - Show total income and expenses
  - Show breakdown by categories
  - Add inline buttons for period selection
  - _Requirements: 5.4_

- [ ] 6.5 Implement /mood command
  - Fetch mood history for last 7 days
  - Show mood trend (improving/declining)
  - Display average intensity
  - Add visualization with emoji
  - _Requirements: 5.5_

- [ ] 6.6 Implement /settings command
  - Show current user settings
  - Add inline buttons for changing settings
  - Include reminder preferences
  - _Requirements: 5.6_

- [ ]* 6.7 Write unit tests for all commands
  - Test each command handler
  - Test inline button callbacks
  - Test error scenarios
  - _Requirements: 12.1_

### 7. Remove Legacy Code

- [ ] 7.1 Backup old handlers.py
  - Copy to `handlers.py.backup`
  - Document what was removed
  - _Requirements: Design - Migration Plan_

- [ ] 7.2 Remove old imports from main.py
  - Remove imports of old handler functions
  - Clean up unused code
  - _Requirements: Design - Migration Plan_

- [ ] 7.3 Test all functionality with new handlers
  - Verify all commands work
  - Verify message processing works
  - Verify voice messages work
  - _Requirements: Design - Migration Plan_

- [ ] 7.4 Delete old handlers.py after 1 week
  - Confirm no issues in production
  - Delete backup file
  - _Requirements: Design - Migration Plan_

---

## Phase 3: Reminders and Testing

### 8. Implement Reminder System

- [ ] 8.1 Enhance ReminderService
  - Implement `check_upcoming_tasks()` to find tasks with deadlines
  - Implement `send_task_reminder()` with retry logic
  - Implement `send_daily_summary()` for morning digest
  - Add logging for all reminder actions
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 8.2 Integrate with APScheduler
  - Add job to check tasks every 5 minutes
  - Add job for daily summary at 9:00 AM
  - Handle scheduler errors gracefully
  - _Requirements: 6.5_

- [ ] 8.3 Implement /reminders command
  - Show current reminder settings
  - Add inline buttons to enable/disable reminders
  - Allow changing daily summary time
  - Allow changing reminder advance time (1 hour default)
  - _Requirements: 6.4_

- [ ] 8.4 Add reminder notifications with inline buttons
  - Add "Mark as done" button
  - Add "Snooze 1 hour" button
  - Add "View details" button
  - _Requirements: 6.1, 6.2_

- [ ]* 8.5 Write unit tests for ReminderService
  - Test task deadline detection
  - Test reminder sending logic
  - Test daily summary generation
  - _Requirements: 12.1_

### 9. Comprehensive Testing

- [ ] 9.1 Write unit tests for AIService
  - Test intent classification with sample messages
  - Test data extraction for all types
  - Test fallback responses
  - Test error handling
  - _Requirements: 12.1, 12.3_

- [ ] 9.2 Write unit tests for all Services
  - TaskService CRUD operations
  - FinanceService CRUD operations
  - NoteService CRUD operations
  - MoodService CRUD operations
  - ConversationService context management
  - _Requirements: 12.1_

- [ ] 9.3 Write unit tests for Repositories
  - BaseRepository CRUD operations
  - Task-specific queries
  - Finance-specific queries
  - Pagination functionality
  - _Requirements: 12.1_

- [ ] 9.4 Write integration tests for API endpoints
  - Tasks API CRUD
  - Finances API CRUD
  - Notes API CRUD
  - Dashboard summary API
  - _Requirements: 12.2_

- [ ] 9.5 Write integration tests for bot
  - End-to-end message processing
  - Voice message processing
  - Command execution
  - Multiple intents handling
  - _Requirements: 12.2_

- [ ] 9.6 Achieve 70% test coverage
  - Run coverage report
  - Identify untested code
  - Add missing tests
  - _Requirements: 12.1, 12.5_

### 10. Performance Optimization

- [ ] 10.1 Add caching for user settings
  - Cache user settings in Redis
  - Set TTL to 1 hour
  - Invalidate on settings update
  - _Requirements: 9.4_

- [ ] 10.2 Add caching for conversation context
  - Cache last 10 messages per user
  - Set TTL to 24 hours
  - Optimize context retrieval
  - _Requirements: 7.4, 9.4_

- [ ] 10.3 Optimize database queries
  - Use eager loading for related data
  - Add pagination to all list endpoints
  - Verify all indexes are used
  - _Requirements: 9.3_

- [ ] 10.4 Monitor and optimize response times
  - Add timing logs for each processing step
  - Identify bottlenecks
  - Optimize slow operations
  - _Requirements: 9.1, 9.2_

---

## Phase 4: Web Dashboard Enhancement

### 11. Improve Dashboard UI

- [ ] 11.1 Create dashboard summary component
  - Show cards for each module (tasks, finances, notes, mood)
  - Display key metrics (count, totals, trends)
  - Add loading states
  - _Requirements: 11.1_

- [ ] 11.2 Add charts for finances
  - Income vs expenses chart (bar chart)
  - Category breakdown (pie chart)
  - Monthly trend (line chart)
  - Use Chart.js or Recharts
  - _Requirements: 11.4_

- [ ] 11.3 Add mood visualization
  - Mood history chart (line chart with emoji)
  - Average intensity display
  - Trend indicator (improving/declining)
  - _Requirements: 11.4_

- [ ] 11.4 Implement real-time sync
  - Use WebSocket or polling for updates
  - Update dashboard when data changes in bot
  - Show notification for new data
  - _Requirements: 11.3_

- [ ] 11.5 Add data management features
  - Edit tasks, finances, notes inline
  - Delete items with confirmation
  - Create new items via forms
  - _Requirements: 11.2, 11.5_

- [ ] 11.6 Improve mobile responsiveness
  - Test on mobile devices
  - Optimize layout for small screens
  - Add touch-friendly controls
  - _Requirements: 11.1_

### 12. Final Testing and Documentation

- [ ] 12.1 End-to-end testing
  - Test complete user journey (bot + web)
  - Test all features work together
  - Test error scenarios
  - _Requirements: 12.5_

- [ ] 12.2 Performance testing
  - Load test with 100 concurrent users
  - Verify response times meet targets
  - Check database performance
  - _Requirements: 9.5_

- [ ] 12.3 Security audit
  - Review all input validation
  - Check authentication flows
  - Verify rate limiting works
  - Test CORS configuration
  - _Requirements: 10.1, 10.3, 10.4, 10.5_

- [ ] 12.4 Update documentation
  - Update README with new features
  - Document all commands
  - Add usage examples
  - Update API documentation
  - _Requirements: 5.2_

- [ ] 12.5 Create deployment checklist
  - Environment variables
  - Database migrations
  - Monitoring setup
  - Backup strategy
  - _Requirements: Design - Deployment Strategy_

---

## Phase 5: Production Deployment

### 13. Pre-deployment Preparation

- [ ] 13.1 Run all tests
  - Unit tests pass
  - Integration tests pass
  - Coverage > 70%
  - _Requirements: 12.5_

- [ ] 13.2 Review and apply database migrations
  - Backup production database
  - Apply migrations in staging
  - Verify data integrity
  - _Requirements: Design - Database Migrations_

- [ ] 13.3 Configure monitoring
  - Set up error tracking (Sentry)
  - Configure performance monitoring
  - Set up alerts for critical errors
  - _Requirements: Design - Monitoring and Metrics_

- [ ] 13.4 Prepare rollback plan
  - Document rollback steps
  - Test rollback in staging
  - Prepare backup deployment
  - _Requirements: Design - Deployment Strategy_

### 14. Deploy to Production

- [ ] 14.1 Deploy backend to Render
  - Push code to production branch
  - Verify deployment successful
  - Check health endpoint
  - _Requirements: Design - Deployment Strategy_

- [ ] 14.2 Deploy frontend to Netlify
  - Build production bundle
  - Deploy to Netlify
  - Verify site loads correctly
  - _Requirements: Design - Deployment Strategy_

- [ ] 14.3 Verify Telegram bot works
  - Test message processing
  - Test voice messages
  - Test all commands
  - _Requirements: Design - Deployment Strategy_

- [ ] 14.4 Monitor for issues
  - Watch error logs
  - Monitor response times
  - Check user feedback
  - _Requirements: Design - Monitoring and Metrics_

### 15. Post-deployment

- [ ] 15.1 Announce new features
  - Send message to all users
  - Update documentation
  - Post on social media
  - _Requirements: Design - Deployment Strategy_

- [ ] 15.2 Collect user feedback
  - Monitor user messages
  - Track feature usage
  - Identify pain points
  - _Requirements: Design - Monitoring and Metrics_

- [ ] 15.3 Plan next iteration
  - Review feedback
  - Prioritize improvements
  - Plan future features
  - _Requirements: Design - Future Enhancements_

---

## Summary

**Total Tasks:** 75 tasks (60 required + 15 optional tests)

**Estimated Timeline:**
- Phase 1: Core Integration - 1 week
- Phase 2: Voice & Commands - 1 week  
- Phase 3: Reminders & Testing - 1 week
- Phase 4: Web Dashboard - 1 week
- Phase 5: Deployment - 3 days

**Total: ~4.5 weeks**

**Key Milestones:**
1. ✅ Intent classification working in production
2. ✅ All modules integrated with bot
3. ✅ Voice messages fully functional
4. ✅ All commands migrated
5. ✅ Reminders system operational
6. ✅ Test coverage > 70%
7. ✅ Web dashboard enhanced
8. ✅ Production deployment complete

**Success Criteria:**
- Users can create tasks/finances/notes naturally
- Voice messages work reliably
- Reminders sent on time
- Web dashboard shows all data
- Test coverage > 70%
- Response time < 3 seconds
- Zero critical bugs in production
