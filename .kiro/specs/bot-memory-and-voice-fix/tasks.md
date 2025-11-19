# Implementation Plan: Bot Memory and Voice Message Fix

## Task List

- [x] 1. Fix User Repository - full_name generation
  - [x] 1.1 Add _generate_full_name helper method to UserRepository
    - Create static method that takes first_name, last_name, username
    - Implement priority logic: names → username → "Telegram User"
    - Return non-null string in all cases
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 1.2 Write property test for full_name generation
    - **Property 1: full_name generation from names**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Generate random first_name, last_name combinations
    - Verify full_name contains provided names in correct order
    - Test with hypothesis library, 100+ iterations
  
  - [ ]* 1.3 Write property test for username fallback
    - **Property 2: Username fallback for full_name**
    - **Validates: Requirements 1.4**
    - Generate cases with null names but valid username
    - Verify full_name equals username
  
  - [x] 1.4 Update get_or_create_by_telegram_id to use _generate_full_name
    - Call _generate_full_name before creating user
    - Add full_name to user_data dict
    - Ensure full_name is never null
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Fix Message Handler - user_id persistence
  - [x] 2.1 Update handle_text_message to handle None user_id
    - Check if user_id is None after user creation
    - Skip conversation context retrieval if None
    - Skip add_message calls if None
    - Continue with AI response generation
    - _Requirements: 2.3, 2.4, 2.5_
  
  - [ ]* 2.2 Write property test for user_id format
    - **Property 3: user_id is valid UUID string**
    - **Validates: Requirements 2.1, 2.2**
    - Generate random user data
    - Verify returned user_id is valid UUID string format
    - Test UUID parsing doesn't raise exception
  
  - [ ]* 2.3 Write property test for no None in DB queries
    - **Property 4: No None in database queries**
    - **Validates: Requirements 2.3, 2.4, 2.5**
    - Mock database operations
    - Simulate user_id = None scenario
    - Verify no DB methods called with None parameter
  
  - [x] 2.4 Add logging for fallback mode
    - Log when entering fallback mode (user_id = None)
    - Log when skipping DB operations
    - Keep existing error logging
    - _Requirements: 2.3, 2.4, 2.5_

- [x] 3. Fix Conversation Service - handle None user_id
  - [x] 3.1 Update get_conversation_context to handle None
    - Add check at start of method
    - Return empty list if user_id is None
    - Add warning log for fallback mode
    - _Requirements: 2.4, 2.5_
  
  - [x] 3.2 Update add_message to handle None
    - Add check at start of method
    - Return early if user_id is None
    - Add warning log for skipped save
    - _Requirements: 2.4, 2.5_
  
  - [x] 3.3 Update _get_latest_summary to handle None
    - Add check at start of method
    - Return None if user_id is None
    - Prevent UUID parsing error
    - _Requirements: 2.4, 2.5_

- [x] 4. Fix Voice Handler - immutable object handling
  - [x] 4.1 Rewrite create_mock_text_update function
    - Import telegram.Message class
    - Create new Message object with text parameter
    - Copy necessary fields from original message
    - Don't modify original objects
    - Return new Update with new Message
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 4.2 Write property test for voice update creation
    - **Property 5: Voice message creates valid text update**
    - **Validates: Requirements 3.1, 3.3**
    - Generate random transcription text
    - Create mock voice update
    - Verify resulting update has valid text message
    - Verify can be processed by text handler
  
  - [ ]* 4.3 Write property test for object immutability
    - **Property 6: Original Telegram objects unchanged**
    - **Validates: Requirements 3.2**
    - Create voice update
    - Call create_mock_text_update
    - Verify original update unchanged
    - Verify original message unchanged
  
  - [x] 4.4 Update handle_voice_message to show transcription
    - Send message with transcribed text before processing
    - Use format: "🎤 Распознано: {text}\n\nОбрабатываю..."
    - Keep existing error handling
    - _Requirements: 3.5_
  
  - [ ]* 4.5 Write property test for transcription display
    - **Property 7: Transcription shown to user**
    - **Validates: Requirements 3.5**
    - Mock bot.send_message
    - Process voice message
    - Verify message sent with transcribed text

- [x] 5. Checkpoint - Verify all fixes work together
  - Ensure all tests pass, ask the user if questions arise
  - Test with real Telegram messages
  - Verify no NULL full_name errors in logs
  - Verify no "invalid input syntax for type uuid" errors
  - Verify voice messages work end-to-end
  - Verify bot remembers conversation context

- [ ]* 6. Add integration tests
  - [ ]* 6.1 Test full message flow with memory
    - Create user, send multiple messages
    - Verify conversation context persists
    - Verify responses use previous context
  
  - [ ]* 6.2 Test voice message end-to-end
    - Send voice message
    - Verify transcription shown
    - Verify processed as text
    - Verify response generated
  
  - [ ]* 6.3 Test fallback mode behavior
    - Simulate DB failure
    - Verify bot continues working
    - Verify no crashes
    - Verify user gets responses

- [x] 7. Deploy and monitor
  - [ ] 7.1 Deploy code changes to production
    - Push changes to repository
    - Trigger deployment on Render
    - Wait for deployment to complete
  
  - [ ] 7.2 Monitor logs for errors
    - Check for NULL full_name errors (should be gone)
    - Check for UUID parsing errors (should be gone)
    - Check for voice message errors (should be gone)
    - Monitor for 10-15 minutes
  
  - [ ] 7.3 Test with real users
    - Send test messages from Telegram
    - Test text messages with memory
    - Test voice messages
    - Verify all features working
