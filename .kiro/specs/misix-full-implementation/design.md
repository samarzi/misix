# Design Document - MISIX Full Implementation

## Overview

Система автоматического извлечения структурированных данных из естественного разговора. Пользователь общается с ботом естественным языком, а система автоматически определяет намерения и извлекает данные для сохранения в соответствующие модули.

## Architecture

### High-Level Flow

```
User Message
    ↓
MessageHandler
    ↓
ConversationService (save user message)
    ↓
IntentClassifier (AI)
    ↓
┌─────────────┬──────────────┬──────────────┬──────────────┐
│ Task Intent │ Finance      │ Note Intent  │ Mood Intent  │
│             │ Intent       │              │              │
└──────┬──────┴──────┬───────┴──────┬───────┴──────┬───────┘
       ↓             ↓              ↓              ↓
   DataExtractor DataExtractor DataExtractor  MoodAnalyzer
       ↓             ↓              ↓              ↓
   TaskService  FinanceService NoteService   MoodService
       ↓             ↓              ↓              ↓
       └─────────────┴──────────────┴──────────────┘
                         ↓
                  Response Builder
                         ↓
                   AI Response
                         ↓
            ConversationService (save)
                         ↓
                  Telegram Reply
```

## Components and Interfaces

### 1. Enhanced MessageHandler

**Файл:** `backend/app/bot/handlers/message.py`

**Новая логика:**
```python
async def handle_text_message(update, context):
    # 1. Existing: Extract data, get/create user
    # 2. Existing: Get conversation context
    # 3. Existing: Save user message
    
    # 4. NEW: Classify intent
    intent_result = await ai_service.classify_intent(message_text)
    
    # 5. NEW: Process intents
    extracted_entities = []
    if intent_result['confidence'] > 0.7:
        entities = await process_intent(
            intent_result['intent'],
            message_text,
            user_id
        )
        extracted_entities.extend(entities)
    
    # 6. NEW: Build response with confirmations
    response = await ai_service.generate_response(
        user_message=message_text,
        conversation_context=conversation_context,
        extracted_entities=extracted_entities
    )
    
    # 7. Existing: Save response and send
```

### 2. Intent Classification

**Метод:** `AIService.classify_intent()`

**Улучшенный промпт:**
```python
prompt = """
Analyze this message and classify ALL intents present:
"{message}"

Possible intents:
- create_task: wants to create task/reminder
- add_expense: reporting expense
- add_income: reporting income  
- save_note: wants to save information
- track_mood: expressing mood/emotion
- general_chat: just talking

Respond with JSON:
{{
    "intents": [
        {{"type": "create_task", "confidence": 0.95}},
        {{"type": "add_expense", "confidence": 0.85}}
    ]
}}
"""
```

### 3. Data Extraction Service

**Новый файл:** `backend/app/services/extraction_service.py`

**Класс:** `ExtractionService`

**Методы:**
- `extract_task_data(message: str) -> Optional[TaskData]`
- `extract_finance_data(message: str) -> Optional[FinanceData]`
- `extract_note_data(message: str) -> Optional[NoteData]`
- `extract_mood_data(message: str) -> Optional[MoodData]`

**Пример для задач:**
```python
async def extract_task_data(self, message: str) -> Optional[dict]:
    prompt = f"""
Extract task information from: "{message}"

Return JSON:
{{
    "title": "task description",
    "deadline": "YYYY-MM-DD HH:MM or null",
    "priority": "low/medium/high",
    "confidence": 0.0-1.0
}}

Examples:
"напомни завтра позвонить" -> {{"title": "позвонить", "deadline": "tomorrow 09:00", "priority": "medium"}}
"срочно купить молоко" -> {{"title": "купить молоко", "deadline": null, "priority": "high"}}
"""
    
    response = await self.ai_service.gpt_client.chat(...)
    data = json.loads(response)
    
    if data['confidence'] < 0.7:
        return None
    
    # Parse relative dates
    if data['deadline']:
        data['deadline'] = self._parse_deadline(data['deadline'])
    
    return data
```

### 4. Mood Service

**Новый файл:** `backend/app/services/mood_service.py`

**Класс:** `MoodService`

**Методы:**
```python
async def save_mood(
    user_id: str,
    mood: str,  # happy, sad, anxious, calm, etc.
    intensity: int,  # 1-10
    note: Optional[str] = None
) -> dict

async def get_mood_history(
    user_id: str,
    days: int = 7
) -> List[dict]

async def analyze_mood_trends(
    user_id: str
) -> dict
```

### 5. Mood Model

**Новый файл:** `backend/app/models/mood.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MoodEntry(BaseModel):
    id: Optional[str] = None
    user_id: str
    mood: str  # happy, sad, anxious, calm, excited, tired, etc.
    intensity: int = Field(ge=1, le=10)
    note: Optional[str] = None
    created_at: Optional[datetime] = None
```

### 6. Mood Repository

**Новый файл:** `backend/app/repositories/mood.py`

```python
class MoodRepository(BaseRepository):
    def __init__(self):
        super().__init__("mood_entries")
    
    async def get_by_user_and_period(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]
```

## Data Models

### Task Data (Enhanced)

```python
{
    "title": str,
    "description": Optional[str],
    "deadline": Optional[datetime],
    "priority": str,  # low, medium, high
    "status": str,  # new, in_progress, completed
    "user_id": str,
    "source": str  # "telegram_auto", "telegram_manual", "web"
}
```

### Finance Data (Enhanced)

```python
{
    "amount": float,
    "type": str,  # expense, income
    "category": str,  # auto-detected
    "description": Optional[str],
    "date": datetime,
    "user_id": str,
    "source": str
}
```

### Mood Data (New)

```python
{
    "mood": str,
    "intensity": int,  # 1-10
    "note": Optional[str],
    "user_id": str,
    "created_at": datetime
}
```

## Database Schema Updates

### New Table: mood_entries

```sql
CREATE TABLE mood_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood TEXT NOT NULL,
    intensity INTEGER NOT NULL CHECK (intensity >= 1 AND intensity <= 10),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mood_entries_user ON mood_entries(user_id);
CREATE INDEX idx_mood_entries_created ON mood_entries(created_at);
```

## Error Handling

### Extraction Failures

1. **Low Confidence** (< 0.7)
   - Skip extraction
   - Continue normal conversation
   - Log for improvement

2. **Incomplete Data**
   - Save what we have
   - Ask for clarification in response
   - Store in "pending" state

3. **Multiple Intents**
   - Process each independently
   - Combine confirmations in response
   - Log all actions

## Response Building

### Confirmation Messages

```python
def build_confirmation(entities: List[dict]) -> str:
    confirmations = []
    
    for entity in entities:
        if entity['type'] == 'task':
            confirmations.append(
                f"✅ Создал задачу: {entity['title']}"
            )
        elif entity['type'] == 'expense':
            confirmations.append(
                f"💰 Записал расход: {entity['amount']}₽ ({entity['category']})"
            )
        elif entity['type'] == 'note':
            confirmations.append(
                f"📝 Сохранил заметку"
            )
        elif entity['type'] == 'mood':
            confirmations.append(
                f"😊 Отметил настроение: {entity['mood']}"
            )
    
    return "\n".join(confirmations)
```

### AI Response Integration

```python
# Add confirmations to AI context
system_prompt = f"""
You just performed these actions:
{confirmations}

Respond naturally, acknowledging what was done.
"""

response = await ai_service.generate_response(
    user_message=message,
    conversation_context=context,
    system_prompt=system_prompt
)
```

## Testing Strategy

### Unit Tests

1. Intent classification accuracy
2. Data extraction correctness
3. Service integration
4. Error handling

### Integration Tests

1. End-to-end message processing
2. Multiple intents in one message
3. Context-aware extraction
4. Database persistence

### Manual Testing Scenarios

```
User: "потратил 500 рублей на кофе"
Expected: Expense created, category="еда и напитки"

User: "напомни завтра в 9 позвонить партнеру"
Expected: Task created with deadline

User: "запомни что встреча в офисе на Ленина 5"
Expected: Note created

User: "сегодня отличное настроение!"
Expected: Mood entry created (happy, high intensity)

User: "потратил 200₽ на такси и напомни купить молоко"
Expected: Both expense and task created
```

## Performance Considerations

1. **Caching** - cache intent classification results for similar messages
2. **Batch Processing** - process multiple intents in parallel
3. **Async Operations** - all DB operations async
4. **Timeout** - 5 second timeout for AI operations

## Future Enhancements

1. **Learning** - improve extraction based on user corrections
2. **Proactive Suggestions** - "хочешь создать задачу?"
3. **Smart Categories** - learn user's category preferences
4. **Recurring Tasks** - detect and create recurring tasks
5. **Budget Tracking** - alert when spending exceeds limits
