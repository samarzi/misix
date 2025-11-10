from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.shared.config import settings
from app.shared.supabase import get_supabase_client
from app.web.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

class NoteBase(BaseModel):
    title: Optional[str] = None
    content: str
    content_format: str = "markdown"

class NoteCreate(NoteBase):
    folder_id: Optional[str] = None


class NoteCreatePublic(NoteBase):
    user_id: str

class Note(NoteBase):
    id: str
    user_id: str
    folder_id: Optional[str] = None
    is_favorite: bool = False
    is_archived: bool = False
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_format: Optional[str] = None
    folder_id: Optional[str] = None

@router.get("/notes", response_model=List[Note])
async def get_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    folder_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's notes with optional search and pagination."""
    try:
        supabase = get_supabase_client()

        query = supabase.table("notes").select("*").eq("user_id", user_id).eq("is_archived", False)

        if folder_id:
            query = query.eq("folder_id", folder_id)
        if search:
            query = query.ilike("content", f"%{search}%")

        query = query.order("updated_at", desc=True).range(skip, skip + limit - 1)

        response = query.execute()

        return [Note(**note) for note in response.data]
    except Exception as e:
        logger.error(f"Error fetching notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notes")

def _insert_note(payload: dict) -> Note:
    supabase = get_supabase_client()
    response = supabase.table("notes").insert(payload).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create note")

    return Note(**response.data[0])


@router.post("/notes", response_model=Note)
async def create_note(
    note: NoteCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new note."""
    try:
        payload = {
            "user_id": user_id,
            "title": note.title,
            "content": note.content,
            "content_format": note.content_format or "markdown",
        }
        if note.folder_id:
            payload["folder_id"] = note.folder_id

        return _insert_note(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")


@router.post("/notes/public", response_model=Note)
async def create_note_public(note: NoteCreatePublic):
    """Create a note when only user_id is available (no auth token)."""
    try:
        payload = {
            "user_id": note.user_id,
            "title": note.title,
            "content": note.content,
            "content_format": note.content_format or "markdown",
        }
        return _insert_note(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating public note: {e}")
        raise HTTPException(status_code=500, detail="Failed to create note")

@router.get("/notes/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific note by ID."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("notes").select("*").eq("id", note_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")

        return Note(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch note")

@router.put("/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: str,
    note_update: NoteUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update a note."""
    try:
        supabase = get_supabase_client()

        update_data = {}
        if note_update.title is not None:
            update_data["title"] = note_update.title
        if note_update.content is not None:
            update_data["content"] = note_update.content
        if note_update.content_format is not None:
            update_data["content_format"] = note_update.content_format
        if note_update.folder_id is not None:
            update_data["folder_id"] = note_update.folder_id

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = supabase.table("notes").update(update_data).eq("id", note_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")

        return Note(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update note")

@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a note."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("notes").delete().eq("id", note_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")

        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete note")

@router.patch("/notes/{note_id}/favorite")
async def toggle_note_favorite(
    note_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Toggle favorite status of a note."""
    try:
        supabase = get_supabase_client()

        # Get current favorite status
        response = supabase.table("notes").select("is_favorite").eq("id", note_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")

        current_favorite = response.data[0]["is_favorite"]
        new_favorite = not current_favorite

        # Update favorite status
        update_response = supabase.table("notes").update({
            "is_favorite": new_favorite,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", note_id).eq("user_id", user_id).execute()

        return {"is_favorite": new_favorite}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle favorite")

@router.patch("/notes/{note_id}/archive")
async def toggle_note_archive(
    note_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Toggle archive status of a note."""
    try:
        supabase = get_supabase_client()

        # Get current archive status
        response = supabase.table("notes").select("is_archived").eq("id", note_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")

        current_archived = response.data[0]["is_archived"]
        new_archived = not current_archived

        # Update archive status
        response = supabase.table("notes").update({
            "is_archived": new_archived,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", note_id).eq("user_id", user_id).execute()

        return {"is_archived": new_archived}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling archive for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle archive")
