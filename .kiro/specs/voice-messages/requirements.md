# Requirements Document - Voice Messages Support

## Introduction

Реализация поддержки голосовых сообщений в Telegram боте MISIX. Пользователи смогут отправлять голосовые сообщения, которые будут автоматически транскрибироваться через Yandex SpeechKit и обрабатываться как текстовые сообщения.

## Glossary

- **VoiceHandler**: Обработчик голосовых сообщений
- **YandexSpeechKit**: Сервис Yandex для распознавания речи
- **Transcription**: Текстовая расшифровка голосового сообщения
- **MessageHandler**: Существующий обработчик текстовых сообщений

## Requirements

### Requirement 1: Прием голосовых сообщений

**User Story:** Как пользователь, я хочу отправлять голосовые сообщения боту, чтобы быстро взаимодействовать без набора текста

#### Acceptance Criteria

1. WHEN пользователь отправляет голосовое сообщение, THE VoiceHandler SHALL получить файл из Telegram
2. WHEN файл получен, THE VoiceHandler SHALL скачать аудио файл
3. THE VoiceHandler SHALL поддерживать форматы OGG и MP3
4. THE VoiceHandler SHALL логировать получение голосового сообщения
5. IF скачивание не удалось, THEN THE VoiceHandler SHALL отправить сообщение об ошибке

### Requirement 2: Транскрибация через Yandex SpeechKit

**User Story:** Как пользователь, я хочу чтобы мои голосовые сообщения распознавались точно, чтобы бот правильно понимал мои команды

#### Acceptance Criteria

1. WHEN аудио файл скачан, THE VoiceHandler SHALL отправить его в YandexSpeechKit
2. THE YandexSpeechKit SHALL распознать речь на русском языке
3. WHEN транскрипция получена, THE VoiceHandler SHALL залогировать результат
4. IF транскрипция пустая, THEN THE VoiceHandler SHALL сообщить что не удалось распознать
5. THE VoiceHandler SHALL обрабатывать ошибки API Yandex

### Requirement 3: Обработка как текстового сообщения

**User Story:** Как пользователь, я хочу чтобы голосовые сообщения обрабатывались так же как текстовые, чтобы создавать задачи и записи голосом

#### Acceptance Criteria

1. WHEN транскрипция получена, THE VoiceHandler SHALL передать текст в существующий MessageHandler
2. THE System SHALL классифицировать намерения из транскрибированного текста
3. THE System SHALL извлекать данные (задачи, финансы, заметки, настроение)
4. THE System SHALL генерировать AI ответ
5. THE System SHALL отправить текстовый ответ пользователю

### Requirement 4: Обратная связь пользователю

**User Story:** Как пользователь, я хочу видеть что бот обрабатывает мое голосовое сообщение, чтобы понимать что происходит

#### Acceptance Criteria

1. WHEN голосовое сообщение получено, THE VoiceHandler SHALL отправить индикатор "печатает"
2. WHEN транскрипция завершена, THE VoiceHandler SHALL показать распознанный текст
3. THE VoiceHandler SHALL отправить ответ в течение 10 секунд
4. IF обработка занимает больше времени, THEN THE VoiceHandler SHALL уведомить пользователя
5. THE VoiceHandler SHALL отправлять понятные сообщения об ошибках

### Requirement 5: Производительность и надежность

**User Story:** Как пользователь, я хочу чтобы голосовые сообщения обрабатывались быстро и надежно

#### Acceptance Criteria

1. THE VoiceHandler SHALL обрабатывать голосовые сообщения до 60 секунд
2. THE System SHALL завершать транскрипцию в течение 5 секунд для 10-секундного аудио
3. IF Yandex SpeechKit недоступен, THEN THE VoiceHandler SHALL сообщить об ошибке
4. THE VoiceHandler SHALL удалять временные аудио файлы после обработки
5. THE System SHALL логировать время обработки для мониторинга
