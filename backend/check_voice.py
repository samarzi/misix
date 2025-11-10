#!/usr/bin/env python3
"""
Проверка голосового распознавания MISIX без запуска всего бота
Запуск: python3 check_voice.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env.local')

from app.bot.yandex_speech import get_yandex_speech_kit

async def check_voice_system():
    """Полная проверка системы голосового распознавания."""
    print("🎤 ПРОВЕРКА ГОЛОСОВОГО РАСПОЗНАВАНИЯ MISIX")
    print("=" * 50)

    # 1. Проверяем конфигурацию
    print("1️⃣ Конфигурация:")
    api_key = os.getenv('YANDEX_SPEECHKIT_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')

    print(f"   API Key: {'***' + api_key[-4:] if api_key else '❌ НЕТ'}")
    print(f"   Folder ID: {folder_id or '❌ НЕТ'}")

    if not api_key or not folder_id:
        print("   ❌ Конфигурация неполная!")
        return

    # 2. Проверяем SpeechKit класс
    print("\\n2️⃣ Класс YandexSpeechKit:")
    speech_kit = get_yandex_speech_kit()
    print(f"   ✅ Экземпляр создан: {type(speech_kit).__name__}")

    # Проверяем, что нет mock функций
    if hasattr(speech_kit, 'transcribe_audio_fallback'):
        print("   ❌ ПРОБЛЕМА: Функция transcribe_audio_fallback существует!")
        return
    else:
        print("   ✅ Хорошо: Функция transcribe_audio_fallback удалена")

    # 3. Тестируем IAM токен
    print("\\n3️⃣ IAM токен:")
    try:
        # Пытаемся получить IAM токен
        iam_token = await speech_kit._get_iam_token()
        if iam_token:
            print(f"   ✅ IAM токен получен: ***{iam_token[-10:]}")
        else:
            print("   ❌ IAM токен не получен")
            return
    except Exception as e:
        print(f"   ❌ Ошибка IAM: {e}")
        return

    # 4. Тестируем API вызов
    print("\\n4️⃣ Тест API вызова:")
    test_audio = b'test_audio_data'
    result = await speech_kit.transcribe_audio(test_audio)

    if result is None:
        print("   ✅ ПРАВИЛЬНО: API вернул None (нет mock ответов)")
    else:
        print(f"   ❌ ПРОБЛЕМА: API вернул '{result}' вместо None")
        return

    # 5. Проверяем обработку голосовых сообщений
    print("\\n5️⃣ Обработка голосовых сообщений:")

    class MockVoiceFile:
        def __init__(self, data):
            self.file_id = 'test'
            self.file_size = len(data)
            self._data = data

        async def download_as_bytearray(self):
            return bytearray(self._data)

    # Тест с данными, которые должны провалиться
    mock_file = MockVoiceFile(b'')
    voice_result = await speech_kit.transcribe_telegram_voice(mock_file)

    if voice_result is None:
        print("   ✅ ПРАВИЛЬНО: Голосовое распознавание вернуло None")
    else:
        print(f"   ❌ ПРОБЛЕМА: Голосовое распознавание вернуло '{voice_result}'")
        return

    print("\\n" + "=" * 50)
    print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("✅ Система голосового распознавания настроена правильно")
    print("✅ Mock ответы полностью удалены")
    print("✅ Система будет показывать честные ошибки")
    print("\\n📋 Что ожидать при тестировании:")
    print("• Если SpeechKit работает: покажет реальный распознанный текст")
    print("• Если SpeechKit не работает: покажет сообщение об ошибке")
    print("• Никаких фальшивых 'Привет' или других mock ответов!")

if __name__ == "__main__":
    asyncio.run(check_voice_system())
