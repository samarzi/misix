from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from app.shared.supabase import get_supabase_client
from app.web.auth import get_current_user_id

router = APIRouter()

# Pydantic models
class FinanceCategoryBase(BaseModel):
    name: str
    type: str  # 'income' or 'expense'
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None

class FinanceCategory(FinanceCategoryBase):
    id: str
    user_id: str
    is_default: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

class FinanceTransactionBase(BaseModel):
    category_id: Optional[str] = None
    amount: float
    currency: str = "RUB"
    type: str  # 'income' or 'expense'
    description: Optional[str] = None
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    tags: Optional[List[str]] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None

class FinanceTransaction(FinanceTransactionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class PersonalDataCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_confidential: bool = False

class PersonalDataCategory(PersonalDataCategoryBase):
    id: str
    user_id: str
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

class PersonalDataEntryBase(BaseModel):
    category_id: Optional[str] = None
    title: str
    data_type: str  # 'login', 'contact', 'document', 'other'
    login_username: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    document_number: Optional[str] = None
    document_expiry: Optional[date] = None
    custom_fields: Optional[dict] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    is_favorite: bool = False

class PersonalDataEntry(PersonalDataEntryBase):
    id: str
    user_id: str
    is_confidential: bool = False
    last_accessed: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class MoodEntryBase(BaseModel):
    mood_level: int  # 1-10
    mood_description: Optional[str] = None
    energy_level: Optional[int] = None
    stress_level: Optional[int] = None
    sleep_hours: Optional[float] = None
    notes: Optional[str] = None
    factors: Optional[List[str]] = None
    entry_date: Optional[date] = None

class MoodEntry(MoodEntryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class DiaryEntryBase(BaseModel):
    title: Optional[str] = None
    content: str
    entry_type: str = "general"  # 'general', 'gratitude', 'reflection', 'dream', 'goal', 'achievement'
    mood_level: Optional[int] = None
    tags: Optional[List[str]] = None
    is_private: bool = False
    entry_date: Optional[date] = None

class DiaryEntry(DiaryEntryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class FinanceDebtBase(BaseModel):
    counterparty: str
    amount: float
    currency: str = "RUB"
    direction: str  # 'owed_by_me' или 'owed_to_me'
    status: str = "pending"
    due_date: Optional[date] = None
    notes: Optional[str] = None
    category_id: Optional[str] = None


class FinanceDebt(FinanceDebtBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class ReminderBase(BaseModel):
    title: str
    reminder_time: datetime
    timezone: str = "Europe/Moscow"
    status: str = "scheduled"
    recurrence_rule: Optional[str] = None
    payload: Optional[dict] = None


class Reminder(ReminderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class AssistantPersona(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    tone: str = "neutral"
    language_style: str = "neutral"
    empathy_level: str = "medium"
    motivation_level: str = "medium"
    is_active: bool = True

class UserAssistantSettings(BaseModel):
    id: str
    user_id: str
    current_persona_id: Optional[str] = None
    voice_enabled: bool = False
    notifications_enabled: bool = True
    language: str = "ru"
    timezone: str = "Europe/Moscow"
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"

# API endpoints will be implemented below
# (continuing in the next part...)

# =============================================
# FINANCE CATEGORIES
# =============================================

@router.get("/categories", response_model=List[FinanceCategory])
async def get_finance_categories(
    type_filter: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's finance categories."""
    supabase = get_supabase_client()

    query = supabase.table("finance_categories").select("*").eq("user_id", user_id)
    if type_filter:
        query = query.eq("type", type_filter)

    response = query.order("sort_order").execute()

    return response.data

@router.post("/categories", response_model=FinanceCategory)
async def create_finance_category(
    category: FinanceCategoryBase,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new finance category."""
    supabase = get_supabase_client()

    category_data = {
        "user_id": user_id,
        "name": category.name,
        "type": category.type,
        "color": category.color,
        "icon": category.icon,
        "parent_id": category.parent_id
    }

    response = supabase.table("finance_categories").insert(category_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create category")

    return response.data[0]

@router.put("/categories/{category_id}", response_model=FinanceCategory)
async def update_finance_category(
    category_id: str,
    category: FinanceCategoryBase,
    user_id: str = Depends(get_current_user_id)
):
    """Update a finance category."""
    supabase = get_supabase_client()

    update_data = {
        "name": category.name,
        "type": category.type,
        "color": category.color,
        "icon": category.icon,
        "parent_id": category.parent_id
    }

    response = supabase.table("finance_categories").update(update_data).eq("id", category_id).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Category not found")

    return response.data[0]

@router.delete("/categories/{category_id}")
async def delete_finance_category(
    category_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a finance category."""
    supabase = get_supabase_client()

    response = supabase.table("finance_categories").delete().eq("id", category_id).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Category not found")

    return {"message": "Category deleted successfully"}

# =============================================
# FINANCE TRANSACTIONS
# =============================================

@router.get("/transactions", response_model=List[FinanceTransaction])
async def get_finance_transactions(
    skip: int = 0,
    limit: int = 50,
    type_filter: Optional[str] = None,
    category_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's finance transactions with filtering."""
    supabase = get_supabase_client()

    query = supabase.table("finance_transactions").select("*").eq("user_id", user_id)

    if type_filter:
        query = query.eq("type", type_filter)
    if category_id:
        query = query.eq("category_id", category_id)
    if start_date:
        query = query.gte("transaction_date", start_date.isoformat())
    if end_date:
        query = query.lte("transaction_date", end_date.isoformat())

    response = query.order("transaction_date", desc=True).range(skip, skip + limit - 1).execute()

    return response.data

@router.post("/transactions", response_model=FinanceTransaction)
async def create_finance_transaction(
    transaction: FinanceTransactionBase,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new finance transaction."""
    supabase = get_supabase_client()

    transaction_data = {
        "user_id": user_id,
        "category_id": transaction.category_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "type": transaction.type,
        "description": transaction.description,
        "merchant": transaction.merchant,
        "payment_method": transaction.payment_method,
        "tags": transaction.tags,
        "transaction_date": transaction.transaction_date or datetime.utcnow(),
        "notes": transaction.notes
    }

    response = supabase.table("finance_transactions").insert(transaction_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create transaction")

    return response.data[0]

@router.put("/transactions/{transaction_id}", response_model=FinanceTransaction)
async def update_finance_transaction(
    transaction_id: str,
    transaction: FinanceTransactionBase,
    user_id: str = Depends(get_current_user_id)
):
    """Update a finance transaction."""
    supabase = get_supabase_client()

    update_data = {
        "category_id": transaction.category_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "type": transaction.type,
        "description": transaction.description,
        "merchant": transaction.merchant,
        "payment_method": transaction.payment_method,
        "tags": transaction.tags,
        "transaction_date": transaction.transaction_date,
        "notes": transaction.notes
    }

    response = supabase.table("finance_transactions").update(update_data).eq("id", transaction_id).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return response.data[0]

@router.delete("/transactions/{transaction_id}")
async def delete_finance_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a finance transaction."""
    supabase = get_supabase_client()

    response = supabase.table("finance_transactions").delete().eq("id", transaction_id).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {"message": "Transaction deleted successfully"}

@router.get("/stats")
async def get_finance_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get finance statistics."""
    supabase = get_supabase_client()

    # Get date range (default to current month)
    if not start_date:
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.utcnow()

    # Get transactions in date range
    response = supabase.table("finance_transactions").select("*").eq("user_id", user_id)\
        .gte("transaction_date", start_date.isoformat())\
        .lte("transaction_date", end_date.isoformat()).execute()

    transactions = response.data

    # Calculate stats
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expenses

    # Group by categories
    expenses_by_category = {}
    income_by_category = {}

    for transaction in transactions:
        category_id = transaction.get("category_id")
        if not category_id:
            continue

        if transaction["type"] == "expense":
            expenses_by_category[category_id] = expenses_by_category.get(category_id, 0) + transaction["amount"]
        else:
            income_by_category[category_id] = income_by_category.get(category_id, 0) + transaction["amount"]

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance
        },
        "expenses_by_category": expenses_by_category,
        "income_by_category": income_by_category,
        "transaction_count": len(transactions)
    }


# =============================================
# FINANCE DEBTS
# =============================================

@router.get("/debts", response_model=List[FinanceDebt])
async def get_finance_debts(
    status: Optional[str] = None,
    direction: Optional[str] = None,
    include_overdue: bool = False,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    query = supabase.table("finance_debts").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    if direction:
        query = query.eq("direction", direction)
    if not include_overdue:
        query = query.neq("status", "overdue")

    response = query.order("due_date", desc=False).execute()
    return response.data or []


@router.post("/debts", response_model=FinanceDebt)
async def create_finance_debt(
    debt: FinanceDebtBase,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    debt_data = {
        "user_id": user_id,
        "counterparty": debt.counterparty,
        "amount": debt.amount,
        "currency": debt.currency,
        "direction": debt.direction,
        "status": debt.status,
        "due_date": debt.due_date,
        "notes": debt.notes,
        "category_id": debt.category_id,
    }

    response = supabase.table("finance_debts").insert(debt_data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create debt entry")
    return response.data[0]


@router.put("/debts/{debt_id}", response_model=FinanceDebt)
async def update_finance_debt(
    debt_id: str,
    debt_update: FinanceDebtBase,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    update_data = {
        "counterparty": debt_update.counterparty,
        "amount": debt_update.amount,
        "currency": debt_update.currency,
        "direction": debt_update.direction,
        "status": debt_update.status,
        "due_date": debt_update.due_date,
        "notes": debt_update.notes,
        "category_id": debt_update.category_id,
        "updated_at": datetime.utcnow().isoformat()
    }

    response = supabase.table("finance_debts").update(update_data).eq("id", debt_id).eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Debt not found")
    return response.data[0]


@router.post("/debts/{debt_id}/settle")
async def settle_finance_debt(
    debt_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    response = supabase.table("finance_debts").update({
        "status": "paid",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", debt_id).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Debt not found")

    return {"message": "Debt settled", "status": "paid"}


# =============================================
# REMINDERS
# =============================================

@router.get("/reminders", response_model=List[Reminder])
async def get_reminders(
    status: Optional[str] = None,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    query = supabase.table("reminders").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    if from_time:
        query = query.gte("reminder_time", from_time.isoformat())
    if to_time:
        query = query.lte("reminder_time", to_time.isoformat())

    response = query.order("reminder_time", desc=False).execute()
    return response.data or []


@router.post("/reminders", response_model=Reminder)
async def create_reminder(
    reminder: ReminderBase,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    reminder_data = {
        "user_id": user_id,
        "title": reminder.title,
        "reminder_time": reminder.reminder_time,
        "timezone": reminder.timezone,
        "status": reminder.status,
        "recurrence_rule": reminder.recurrence_rule,
        "payload": reminder.payload,
    }

    response = supabase.table("reminders").insert(reminder_data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create reminder")
    return response.data[0]


@router.put("/reminders/{reminder_id}", response_model=Reminder)
async def update_reminder(
    reminder_id: str,
    reminder_update: ReminderBase,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    update_data = {
        "title": reminder_update.title,
        "reminder_time": reminder_update.reminder_time,
        "timezone": reminder_update.timezone,
        "status": reminder_update.status,
        "recurrence_rule": reminder_update.recurrence_rule,
        "payload": reminder_update.payload,
        "updated_at": datetime.utcnow().isoformat()
    }

    response = supabase.table("reminders").update(update_data).eq("id", reminder_id).eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return response.data[0]


@router.post("/reminders/{reminder_id}/cancel")
async def cancel_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()

    response = supabase.table("reminders").update({
        "status": "cancelled",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", reminder_id).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return {"message": "Reminder cancelled", "status": "cancelled"}
