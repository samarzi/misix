# Design Document - Voice Messages Support

## Overview

Интеграция Yandex SpeechKit для распознавания голосовых сообщений. Голосовые сообщения транскрибируются в текст и обрабатываются через существующий MessageHandler, что позволяет использовать весь функционал (задачи, финансы, заметки, настроение) голосом.

## Architecture

### Flow

```
Voice Message (Telegram)
    ↓
VoiceHandler
    ↓
Download Audio File
    ↓
YandexSpeechKit.transcribe()
    ↓
Transcribed Text
    ↓
Process as Text Message
    ↓
[Existing MessageHandler Flow]
    ↓
AI Response
    ↓
Send Reply
```

## Components

### 1. Enhanced handle_voice_message

**Файл:** `backend/app/bot/handlers/message.py`

**Текущая реализация:**
```python
async def handle_voice_message(...):
    # TODO: Implement voice transcription
    await update.message.reply_text("Голосовые сообщения будут поддерживаться...")
```

**Новая реализация:**
```python
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages with transcription."""
    try:
        user = update.effective_user
        voice = update.message.voice
        
        # 1. Send "typing" indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # 2. Download voice file
        voice_file = await context.bot.get_file(voice.file_id)
        audio_bytes = await voice_file.download_as_bytearray()
        
        # 3. Transcribe with Yandex SpeechKit
        speech_kit = get_yandex_speech_kit()
        transcription = await speech_kit.transcribe_audio(bytes(audio_bytes))
        
        if not transcription:
            await update.message.reply_text(
                "Не удалось распознать речь. Попробуйте еще раз."
            )
            return
        
        # 4. Show transcription to user
        await update.message.reply_text(
            f"🎤 Распознано: \"{transcription}\"\n\nОбрабатываю..."
        )
        
        # 5. Create mock text message and process
        mock_update = create_mock_text_update(update, transcription)
        await handle_text_message(mock_update, context)
        
    except Exception as e:
        logger.error(f"Voice message processing failed: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке голосового сообщения."
        )
```

### 2. Mock Update Helper

**Новая функция:**
```python
def create_mock_text_update(voice_update: Update, text: str) -> Update:
    """Create mock text update from voice update."""
    # Copy voice update but replace message with text
    mock_update = copy.deepcopy(voice_update)
    mock_update.message.text = text
    mock_update.message.voice = None
    return mock_update
```

### 3. YandexSpeechKit Integration

**Файл:** `backend/app/bot/yandex_speech.py` (уже существует)

**Проверим существующую реализацию:**
- Метод `transcribe_audio(audio_data: bytes) -> Optional[str]`
- Поддержка OGG формата
- Retry logic
- Error handling

**Если нужны улучшения:**
```python
async def transcribe_audio(
    self,
    audio_data: bytes,
    language_code: str = "ru-RU"
) -> Optional[str]:
    """Transcribe audio using Yandex SpeechKit."""
    try:
        # Existing implementation
        # Add timeout and better error handling
        ...
    except TimeoutError:
        logger.error("Transcription timeout")
        return None
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return None
```

## Data Flow

### 1. Voice Message Reception

```python
# Telegram sends voice message
voice_message = {
    "file_id": "...",
    "file_unique_id": "...",
    "duration": 5,  # seconds
    "mime_type": "audio/ogg"
}
```

### 2. Audio Download

```python
# Download from Telegram servers
voice_file = await bot.get_file(voice.file_id)
audio_bytes = await voice_file.download_as_bytearray()

# audio_bytes: bytes (OGG format)
```

### 3. Transcription

```python
# Send to Yandex SpeechKit
transcription = await speech_kit.transcribe_audio(audio_bytes)

# transcription: "потратил 500 рублей на кофе"
```

### 4. Processing

```python
# Process as text message
# Same flow as handle_text_message:
# - Get/create user
# - Get context
# - Classify intents
# - Extract data
# - Generate response
```

## Error Handling

### Scenarios

1. **Download Failed**
   ```python
   try:
       audio_bytes = await voice_file.download_as_bytearray()
   except Exception as e:
       await update.message.reply_text(
           "Не удалось скачать голосовое сообщение."
       )
   ```

2. **Transcription Failed**
   ```python
   if not transcription:
       await update.message.reply_text(
           "Не удалось распознать речь. Говорите четче или попробуйте текстом."
       )
   ```

3. **Yandex API Unavailable**
   ```python
   except YandexSpeechKitError:
       await update.message.reply_text(
           "Сервис распознавания речи временно недоступен."
       )
   ```

4. **Processing Error**
   ```python
   except Exception as e:
       logger.error(f"Voice processing failed: {e}")
       await update.message.reply_text(
           "Произошла ошибка. Попробуйте позже."
       )
   ```

## Performance Considerations

### Timeouts

- Download: 10 seconds
- Transcription: 30 seconds
- Total processing: 45 seconds

### File Size Limits

- Max duration: 60 seconds
- Max file size: 20 MB (Telegram limit)

### Cleanup

```python
# Delete temporary files
try:
    if temp_file_path:
        os.remove(temp_file_path)
except:
    pass
```

## User Experience

### Feedback Flow

```
User sends voice → "🎤 Обрабатываю..."
                ↓
Transcription done → "🎤 Распознано: 'потратил 500₽ на кофе'"
                ↓
Processing → "Обрабатываю..."
                ↓
Response → "💸 Записал расход: 500₽ (еда и напитки)"
```

### Example Interactions

**Scenario 1: Create Task**
```
User: 🎤 "напомни завтра позвонить маме"
Bot: 🎤 Распознано: "напомни завтра позвонить маме"
     
     ✅ Создал задачу: позвонить маме (до 18.11.2025)
     Хорошо, напомню завтра!
```

**Scenario 2: Track Expense**
```
User: 🎤 "потратил триста рублей на обед"
Bot: 🎤 Распознано: "потратил триста рублей на обед"
     
     💸 Записал расход: 300₽ (еда и напитки)
     Записал!
```

**Scenario 3: Multiple Intents**
```
User: 🎤 "потратил двести на такси и напомни купить молоко"
Bot: 🎤 Распознано: "потратил двести на такси и напомни купить молоко"
     
     💸 Записал расход: 200₽ (транспорт)
     ✅ Создал задачу: купить молоко
     Готово!
```

## Testing Strategy

### Unit Tests

1. Test voice file download
2. Test transcription with mock audio
3. Test error handling
4. Test mock update creation

### Integration Tests

1. End-to-end voice message processing
2. Test with real Yandex SpeechKit
3. Test various audio qualities
4. Test different accents and speeds

### Manual Testing

1. Send clear voice message
2. Send noisy voice message
3. Send very short message (< 1 sec)
4. Send long message (> 30 sec)
5. Test multiple intents in voice
6. Test with background noise

## Configuration

### Environment Variables

```bash
YANDEX_SPEECHKIT_API_KEY=your_key_here
YANDEX_FOLDER_ID=your_folder_id
```

### Yandex SpeechKit Settings

```python
{
    "language_code": "ru-RU",
    "format": "oggopus",
    "sample_rate_hertz": 48000
}
```

## Limitations

1. **Language:** Only Russian supported initially
2. **Duration:** Max 60 seconds
3. **Quality:** Depends on audio quality and background noise
4. **Latency:** 3-5 seconds for transcription
5. **Cost:** Yandex SpeechKit API charges per request

## Future Enhancements

1. **Multi-language support** - detect language automatically
2. **Voice responses** - reply with voice using TTS
3. **Streaming transcription** - real-time processing
4. **Audio quality enhancement** - noise reduction
5. **Speaker identification** - multiple users in one audio
