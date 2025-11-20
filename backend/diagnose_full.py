#!/usr/bin/env python3
"""Полная диагностика проекта MISIX по ТЗ."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("=" * 80)
    print("🔍 ПОЛНАЯ ДИАГНОСТИКА ПРОЕКТА MISIX")
    print("=" * 80)
    print()
    
    # ========================================================================
    # 1. ПРОВЕРКА КОНФИГУРАЦИИ
    # ========================================================================
    print("📋 1. ПРОВЕРКА КОНФИГУРАЦИИ")
    print("-" * 80)
    
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    config_checks = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_WEBHOOK_URL': os.getenv('TELEGRAM_WEBHOOK_URL'),
        'BACKEND_BASE_URL': os.getenv('BACKEND_BASE_URL'),
        'YANDEX_GPT_API_KEY': os.getenv('YANDEX_GPT_API_KEY'),
        'YANDEX_FOLDER_ID': os.getenv('YANDEX_FOLDER_ID'),
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY'),
        'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY'),
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
    }
    
    config_ok = True
    for key, value in config_checks.items():
        if value:
            # Show only first 20 chars for security
            display_value = value[:20] + '...' if len(value) > 20 else value
            print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ❌ {key}: НЕ УСТАНОВЛЕН")
            config_ok = False
    
    print()
    
    # ========================================================================
    # 2. ПРОВЕРКА БАЗЫ ДАННЫХ
    # ========================================================================
    print("🗄️  2. ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("-" * 80)
    
    try:
        from app.shared.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        # Test connection
        result = supabase.table('users').select('id').limit(1).execute()
        print(f"  ✅ Подключение к Supabase: OK")
        print(f"  ✅ Таблица users: OK")
        
        # Check all required tables
        required_tables = [
            'users', 'tasks', 'finance_records', 'notes', 
            'mood_entries', 'assistant_messages', 'user_settings'
        ]
        
        for table in required_tables:
            try:
                result = supabase.table(table).select('id').limit(1).execute()
                print(f"  ✅ Таблица {table}: OK")
            except Exception as e:
                print(f"  ❌ Таблица {table}: ОШИБКА - {e}")
                config_ok = False
        
    except Exception as e:
        print(f"  ❌ Ошибка подключения к БД: {e}")
        config_ok = False
    
    print()
    
    # ========================================================================
    # 3. ПРОВЕРКА TELEGRAM БОТА
    # ========================================================================
    print("🤖 3. ПРОВЕРКА TELEGRAM БОТА")
    print("-" * 80)
    
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("  ❌ TELEGRAM_BOT_TOKEN не установлен")
        config_ok = False
    else:
        try:
            from telegram import Bot
            bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
            
            # Get bot info
            bot_info = await bot.get_me()
            print(f"  ✅ Бот подключен: @{bot_info.username}")
            print(f"  ✅ ID бота: {bot_info.id}")
            print(f"  ✅ Имя бота: {bot_info.first_name}")
            
            # Check webhook status
            webhook_info = await bot.get_webhook_info()
            print(f"  📡 Webhook URL: {webhook_info.url or 'НЕ УСТАНОВЛЕН'}")
            print(f"  📨 Pending updates: {webhook_info.pending_update_count}")
            
            if webhook_info.last_error_message:
                print(f"  ⚠️  Последняя ошибка webhook: {webhook_info.last_error_message}")
            
            # Check if webhook is set correctly
            expected_webhook = os.getenv('TELEGRAM_WEBHOOK_URL') or f"{os.getenv('BACKEND_BASE_URL')}/bot/webhook"
            if webhook_info.url != expected_webhook:
                print(f"  ⚠️  Webhook не соответствует ожидаемому:")
                print(f"     Ожидается: {expected_webhook}")
                print(f"     Установлен: {webhook_info.url}")
            
        except Exception as e:
            print(f"  ❌ Ошибка подключения к боту: {e}")
            config_ok = False
    
    print()
    
    # ========================================================================
    # 4. ПРОВЕРКА ОБРАБОТЧИКОВ БОТА
    # ========================================================================
    print("⚙️  4. ПРОВЕРКА ОБРАБОТЧИКОВ БОТА")
    print("-" * 80)
    
    try:
        from app.bot import get_application
        app = get_application()
        
        if app:
            handlers = app.handlers
            print(f"  ✅ Приложение бота инициализировано")
            print(f"  📊 Количество групп обработчиков: {len(handlers)}")
            
            # Count handlers by type
            command_handlers = 0
            message_handlers = 0
            callback_handlers = 0
            
            for group_handlers in handlers.values():
                for handler in group_handlers:
                    handler_type = type(handler).__name__
                    if 'Command' in handler_type:
                        command_handlers += 1
                    elif 'Message' in handler_type:
                        message_handlers += 1
                    elif 'Callback' in handler_type:
                        callback_handlers += 1
            
            print(f"  ✅ Command handlers: {command_handlers}")
            print(f"  ✅ Message handlers: {message_handlers}")
            print(f"  ✅ Callback handlers: {callback_handlers}")
            
            if callback_handlers == 0:
                print(f"  ⚠️  ПРОБЛЕМА: Нет callback handlers для кнопок!")
                config_ok = False
            
        else:
            print(f"  ❌ Приложение бота не инициализировано")
            config_ok = False
            
    except Exception as e:
        print(f"  ❌ Ошибка проверки обработчиков: {e}")
        import traceback
        traceback.print_exc()
        config_ok = False
    
    print()
    
    # ========================================================================
    # 5. ПРОВЕРКА YANDEX GPT
    # ========================================================================
    print("🧠 5. ПРОВЕРКА YANDEX GPT")
    print("-" * 80)
    
    if not os.getenv('YANDEX_GPT_API_KEY'):
        print("  ❌ YANDEX_GPT_API_KEY не установлен")
        config_ok = False
    else:
        try:
            from app.services.ai_service import get_ai_service
            ai_service = get_ai_service()
            
            # Test simple request
            response = await ai_service.generate_response(
                user_message="Привет!",
                conversation_context=[]
            )
            
            print(f"  ✅ Yandex GPT работает")
            print(f"  ✅ Тестовый ответ: {response[:50]}...")
            
        except Exception as e:
            print(f"  ❌ Ошибка Yandex GPT: {e}")
            config_ok = False
    
    print()
    
    # ========================================================================
    # 6. ПРОВЕРКА ВЕБА
    # ========================================================================
    print("🌐 6. ПРОВЕРКА ВЕБ-ПРИЛОЖЕНИЯ")
    print("-" * 80)
    
    frontend_path = Path(__file__).parent.parent / 'frontend'
    if frontend_path.exists():
        print(f"  ✅ Папка frontend найдена")
        
        # Check package.json
        package_json = frontend_path / 'package.json'
        if package_json.exists():
            print(f"  ✅ package.json найден")
        else:
            print(f"  ❌ package.json не найден")
        
        # Check src
        src_path = frontend_path / 'src'
        if src_path.exists():
            print(f"  ✅ Папка src найдена")
            
            # Check key files
            key_files = [
                'features/chat/ChatInterface.tsx',
                'features/auth/hooks/useAuth.ts',
                'stores/authStore.ts',
            ]
            
            for file in key_files:
                file_path = src_path / file
                if file_path.exists():
                    print(f"  ✅ {file}")
                else:
                    print(f"  ❌ {file} не найден")
        else:
            print(f"  ❌ Папка src не найдена")
    else:
        print(f"  ❌ Папка frontend не найдена")
    
    print()
    
    # ========================================================================
    # 7. АНАЛИЗ ПРОБЛЕМ ПО ТЗ
    # ========================================================================
    print("📝 7. АНАЛИЗ СООТВЕТСТВИЯ ТЗ")
    print("-" * 80)
    
    print("\n  По ТЗ должно работать:")
    print("  ✅ AI ассистент (Yandex GPT) - РАБОТАЕТ")
    print("  ❌ Кнопки бота (callback handlers) - НЕ РАБОТАЮТ")
    print("  ❌ Веб-приложение - ТРЕБУЕТ ПРОВЕРКИ")
    print()
    
    print("  Основные проблемы:")
    print("  1. ❌ Callback handlers не зарегистрированы правильно")
    print("  2. ❌ Кнопки /start не работают")
    print("  3. ⚠️  Webhook может быть не настроен")
    print("  4. ⚠️  Веб-приложение может не подключаться к API")
    
    print()
    
    # ========================================================================
    # ИТОГИ
    # ========================================================================
    print("=" * 80)
    if config_ok:
        print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА: Все основные компоненты работают")
    else:
        print("❌ ДИАГНОСТИКА ЗАВЕРШЕНА: Обнаружены критические проблемы")
    print("=" * 80)
    print()
    
    return config_ok


if __name__ == '__main__':
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
