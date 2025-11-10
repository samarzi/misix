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
