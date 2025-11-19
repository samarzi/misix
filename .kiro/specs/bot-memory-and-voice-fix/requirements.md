# Requirements Document: Bot Memory and Voice Message Fix

## Introduction

Исправление критических проблем бота: отсутствие памяти (user_id теряется), ошибка с full_name при создании пользователя, и ошибка обработки голосовых сообщений.

## Glossary

- **Bot**: Telegram бот MISIX
- **User Repository**: Репозиторий для работы с пользователями в БД
- **Message Handler**: Обработчик сообщений от пользователей
- **Voice Handler**: Обработчик голосовых сообщений
- **Conversation Service**: Сервис для работы с историей диалогов
- **full_name**: Обязательное поле в таблице users (first_name + last_name)

## Requirements

### Requirement 1: Fix User Creation with full_name

**User Story:** Как пользователь бота, я хочу, чтобы бот создавал мой профиль без ошибок, чтобы я мог начать работу с ботом.

#### Acceptance Criteria

1. WHEN the User Repository creates a new user THEN the System SHALL generate full_name from first_name and last_name
2. WHEN first_name is provided THEN the System SHALL use it in full_name
3. WHEN last_name is provided THEN the System SHALL append it to full_name
4. WHEN both first_name and last_name are null THEN the System SHALL use username as full_name
5. WHEN username is also null THEN the System SHALL use "Telegram User" as full_name

### Requirement 2: Fix User ID Persistence

**User Story:** Как пользователь бота, я хочу, чтобы бот помнил наш разговор, чтобы я мог продолжать диалог с контекстом.

#### Acceptance Criteria

1. WHEN the Message Handler creates or retrieves a user THEN the System SHALL store the user_id as UUID string
2. WHEN the Message Handler passes user_id to Conversation Service THEN the System SHALL pass valid UUID string
3. WHEN user creation fails THEN the System SHALL NOT pass None as user_id to database queries
4. WHEN in fallback mode THEN the System SHALL skip database operations that require user_id
5. WHEN user_id is None THEN the System SHALL NOT call conversation history methods

### Requirement 3: Fix Voice Message Processing

**User Story:** Как пользователь бота, я хочу отправлять голосовые сообщения, чтобы бот их распознавал и обрабатывал как текст.

#### Acceptance Criteria

1. WHEN the Voice Handler transcribes audio THEN the System SHALL create a proper text message for processing
2. WHEN creating mock update THEN the System SHALL NOT modify immutable Telegram Message objects
3. WHEN processing transcribed text THEN the System SHALL pass it through normal text message flow
4. WHEN voice processing fails THEN the System SHALL send clear error message to user
5. WHEN transcription succeeds THEN the System SHALL show recognized text to user before processing

## Technical Notes

### Problem 1: full_name constraint violation
```
'null value in column "full_name" of relation "users" violates not-null constraint'
```
Решение: генерировать full_name из first_name + last_name или использовать username/fallback

### Problem 2: user_id = None в запросах
```
'invalid input syntax for type uuid: "None"'
```
Решение: не передавать None в БД запросы, пропускать операции с БД в fallback режиме

### Problem 3: Voice message error
```
"Failed to process transcribed message: Attribute `text` of class `Message` can't be set!"
```
Решение: не модифицировать immutable объекты Telegram, создавать новый Update правильно
