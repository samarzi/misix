import logging
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.shared.security import decrypt_safely, encrypt_text, is_encryption_available
from app.shared.supabase import get_supabase_client
from app.web.auth import get_current_user_id

router = APIRouter()

logger = logging.getLogger(__name__)

# Pydantic models for Personal Data
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
    login_password: Optional[str] = None
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

# Pydantic models for Diary
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

# Pydantic models for Assistant Personalization
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

class UserAssistantSettingsBase(BaseModel):
    current_persona_id: Optional[str] = None
    voice_enabled: bool = False
    notifications_enabled: bool = True
    language: str = "ru"
    timezone: str = "Europe/Moscow"
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"

class UserAssistantSettings(UserAssistantSettingsBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

# =============================================
# PERSONAL DATA CATEGORIES
# =============================================

@router.get("/personal/categories", response_model=List[PersonalDataCategory])
async def get_personal_data_categories(user_id: str = Depends(get_current_user_id)):
    """Get user's personal data categories."""
    supabase = get_supabase_client()

    response = supabase.table("personal_data_categories").select("*").eq("user_id", user_id).order("sort_order").execute()

    return response.data

@router.post("/personal/categories", response_model=PersonalDataCategory)
async def create_personal_data_category(
    category: PersonalDataCategoryBase,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new personal data category."""
    supabase = get_supabase_client()

    category_data = {
        "user_id": user_id,
        "name": category.name,
        "description": category.description,
        "color": category.color,
        "icon": category.icon,
        "is_confidential": category.is_confidential
    }

    response = supabase.table("personal_data_categories").insert(category_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create category")

    return response.data[0]

# =============================================
# PERSONAL DATA ENTRIES
# =============================================

@router.get("/personal/entries", response_model=List[PersonalDataEntry])
async def get_personal_data_entries(
    category_id: Optional[str] = None,
    data_type: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's personal data entries with filtering."""
    supabase = get_supabase_client()

    query = supabase.table("personal_data_entries").select("*").eq("user_id", user_id)

    if category_id:
        query = query.eq("category_id", category_id)
    if data_type:
        query = query.eq("data_type", data_type)
    if is_favorite is not None:
        query = query.eq("is_favorite", is_favorite)

    response = query.order("created_at", desc=True).execute()

    entries = response.data or []

    if not entries:
        return entries

    decrypted_entries = []
    encryption_ready = is_encryption_available()

    for item in entries:
        decrypted_item = dict(item)

        if encryption_ready:
            for field in ("login_username", "login_password", "contact_phone", "contact_email", "document_number"):
                decrypted_item[field] = decrypt_safely(decrypted_item.get(field))

        decrypted_entries.append(decrypted_item)

    return decrypted_entries

@router.post("/personal/entries", response_model=PersonalDataEntry)
async def create_personal_data_entry(
    entry: PersonalDataEntryBase,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new personal data entry."""
    supabase = get_supabase_client()

    encryption_ready = is_encryption_available()

    entry_data = {
        "user_id": user_id,
        "category_id": entry.category_id,
        "title": entry.title,
        "data_type": entry.data_type,
        "login_username": encrypt_text(entry.login_username) if encryption_ready else entry.login_username,
        "login_password": encrypt_text(entry.login_password) if encryption_ready else entry.login_password,
        "contact_name": entry.contact_name,
        "contact_phone": encrypt_text(entry.contact_phone) if encryption_ready else entry.contact_phone,
        "contact_email": encrypt_text(entry.contact_email) if encryption_ready else entry.contact_email,
        "document_number": encrypt_text(entry.document_number) if encryption_ready else entry.document_number,
        "document_expiry": entry.document_expiry,
        "custom_fields": entry.custom_fields,
        "tags": entry.tags,
        "notes": entry.notes,
        "is_favorite": entry.is_favorite,
        "is_confidential": entry.data_type in ['login'] or bool(entry.login_password)
    }

    if entry_data["is_confidential"] and not encryption_ready:
        logger.warning(
            "Attempting to store confidential personal data without encryption key configured."
        )

    response = supabase.table("personal_data_entries").insert(entry_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create entry")

    return response.data[0]

# =============================================
# MOOD TRACKING
# =============================================

@router.get("/diary/mood", response_model=List[MoodEntry])
async def get_mood_entries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's mood entries."""
    supabase = get_supabase_client()

    query = supabase.table("mood_entries").select("*").eq("user_id", user_id)

    if start_date:
        query = query.gte("entry_date", start_date.isoformat())
    if end_date:
        query = query.lte("entry_date", end_date.isoformat())

    response = query.order("entry_date", desc=True).execute()

    return response.data

@router.post("/diary/mood", response_model=MoodEntry)
async def create_mood_entry(
    mood: MoodEntryBase,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new mood entry."""
    supabase = get_supabase_client()

    mood_data = {
        "user_id": user_id,
        "mood_level": mood.mood_level,
        "mood_description": mood.mood_description,
        "energy_level": mood.energy_level,
        "stress_level": mood.stress_level,
        "sleep_hours": mood.sleep_hours,
        "notes": mood.notes,
        "factors": mood.factors,
        "entry_date": mood.entry_date or date.today()
    }

    response = supabase.table("mood_entries").insert(mood_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create mood entry")

    return response.data[0]

@router.get("/diary/mood/today")
async def get_today_mood(user_id: str = Depends(get_current_user_id)):
    """Get today's mood entry."""
    supabase = get_supabase_client()

    today = date.today()
    response = supabase.table("mood_entries").select("*").eq("user_id", user_id).eq("entry_date", today.isoformat()).execute()

    return response.data[0] if response.data else None

# =============================================
# DIARY ENTRIES
# =============================================

@router.get("/diary/entries", response_model=List[DiaryEntry])
async def get_diary_entries(
    entry_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's diary entries."""
    supabase = get_supabase_client()

    query = supabase.table("diary_entries").select("*").eq("user_id", user_id)

    if entry_type:
        query = query.eq("entry_type", entry_type)
    if start_date:
        query = query.gte("entry_date", start_date.isoformat())
    if end_date:
        query = query.lte("entry_date", end_date.isoformat())

    response = query.order("entry_date", desc=True).execute()

    return response.data

@router.post("/diary/entries", response_model=DiaryEntry)
async def create_diary_entry(
    entry: DiaryEntryBase,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new diary entry."""
    supabase = get_supabase_client()

    entry_data = {
        "user_id": user_id,
        "title": entry.title,
        "content": entry.content,
        "entry_type": entry.entry_type,
        "mood_level": entry.mood_level,
        "tags": entry.tags,
        "is_private": entry.is_private,
        "entry_date": entry.entry_date or date.today()
    }

    response = supabase.table("diary_entries").insert(entry_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create diary entry")

    return response.data[0]

# =============================================
# ASSISTANT PERSONALIZATION
# =============================================

@router.get("/assistant/personas", response_model=List[AssistantPersona])
async def get_assistant_personas():
    """Get all available assistant personas."""
    supabase = get_supabase_client()

    response = supabase.table("assistant_personas").select("*").eq("is_active", True).execute()

    return response.data

@router.get("/assistant/settings", response_model=UserAssistantSettings)
async def get_user_assistant_settings(user_id: str = Depends(get_current_user_id)):
    """Get user's assistant settings."""
    supabase = get_supabase_client()

    response = supabase.table("user_assistant_settings").select("*").eq("user_id", user_id).execute()

    if not response.data:
        # Create default settings
        default_settings = {
            "user_id": user_id,
            "current_persona_id": None,
            "voice_enabled": False,
            "notifications_enabled": True,
            "language": "ru",
            "timezone": "Europe/Moscow",
            "working_hours_start": "09:00",
            "working_hours_end": "18:00"
        }
        response = supabase.table("user_assistant_settings").insert(default_settings).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create default settings")

    return response.data[0]

@router.put("/assistant/settings", response_model=UserAssistantSettings)
async def update_user_assistant_settings(
    settings: UserAssistantSettingsBase,
    user_id: str = Depends(get_current_user_id)
):
    """Update user's assistant settings."""
    supabase = get_supabase_client()

    update_data = {
        "current_persona_id": settings.current_persona_id,
        "voice_enabled": settings.voice_enabled,
        "notifications_enabled": settings.notifications_enabled,
        "language": settings.language,
        "timezone": settings.timezone,
        "working_hours_start": settings.working_hours_start,
        "working_hours_end": settings.working_hours_end
    }

    response = supabase.table("user_assistant_settings").update(update_data).eq("user_id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Settings not found")

    return response.data[0]

# =============================================
# USER PROFILE DATA
# =============================================

@router.get("/profile/data")
async def get_user_profile_data(
    category: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's profile data."""
    supabase = get_supabase_client()

    query = supabase.table("user_profile_data").select("*").eq("user_id", user_id)

    if category:
        query = query.eq("category", category)

    response = query.order("created_at").execute()

    # Convert to dict format
    profile_data = {}
    for item in response.data:
        profile_data[item["data_key"]] = {
            "value": item["data_value"],
            "type": item["data_type"],
            "category": item["category"],
            "is_private": item["is_private"]
        }

    return profile_data

@router.put("/profile/data/{key}")
async def update_user_profile_data(
    key: str,
    value: str,
    category: str = "personal",
    is_private: bool = False,
    user_id: str = Depends(get_current_user_id)
):
    """Update or create user profile data."""
    supabase = get_supabase_client()

    # Try to update existing
    update_data = {
        "data_value": value,
        "category": category,
        "is_private": is_private
    }

    response = supabase.table("user_profile_data").update(update_data).eq("user_id", user_id).eq("data_key", key).execute()

    if not response.data:
        # Create new entry
        insert_data = {
            "user_id": user_id,
            "data_key": key,
            "data_value": value,
            "data_type": "text",
            "category": category,
            "is_private": is_private
        }
        response = supabase.table("user_profile_data").insert(insert_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update profile data")

    return {"message": "Profile data updated successfully"}
