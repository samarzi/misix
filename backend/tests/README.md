# MISIX Tests

## Структура тестов

```
tests/
├── unit/                    # Unit тесты
│   ├── test_extraction_service.py
│   ├── test_intent_processor.py
│   ├── test_ai_service.py
│   ├── test_response_builder.py
│   ├── test_task_service.py
│   └── test_security.py
├── integration/             # Integration тесты
│   └── test_auth_api.py
└── conftest.py             # Pytest fixtures
```

## Установка

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov
```

## Запуск тестов

### Все тесты:
```bash
pytest
```

### С coverage:
```bash
pytest --cov=app --cov-report=html
```

### Конкретный файл:
```bash
pytest tests/unit/test_extraction_service.py -v
```

### Конкретный тест:
```bash
pytest tests/unit/test_extraction_service.py::TestExtractionService::test_extract_task_data_success -v
```

## Coverage Report

После запуска с `--cov-report=html`:
```bash
open htmlcov/index.html
```

## Статистика

- **Unit тестов:** 70
- **Coverage:** ~30%
- **Цель:** 70%
