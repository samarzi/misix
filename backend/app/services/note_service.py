"""Note service for business logic."""

import logging
from typing import Optional

from app.core.exceptions import NotFoundError, AuthorizationError
from app.models.common import PaginationParams
from app.models.note import CreateNoteRequest, UpdateNoteRequest, NoteFilters
from app.repositories.note import NoteRepository, get_note_repository

logger = logging.getLogger(__name__)


class NoteService:
    """Service for note management business logic."""
    
    def __init__(self, note_repo: Optional[NoteRepository] = None):
        """Initialize note service.
        
        Args:
            note_repo: Note repository (injected for testing)
        """
        self.note_repo = note_repo or get_note_repository()
    
    async def create_note(
        self,
        user_id: str,
        note_data: CreateNoteRequest,
    ) -> dict:
        """Create a new note.
        
        Args:
            user_id: User ID creating the note
            note_data: Note data
            
        Returns:
            Created note
        """
        data = {
            "user_id": user_id,
            **note_data.model_dump(exclude_none=True),
        }
        
        note = await self.note_repo.create(data)
        logger.info(f"Note created: {note['id']} by user {user_id}")
        
        return note
    
    async def get_note(self, note_id: str, user_id: str) -> dict:
        """Get note by ID.
        
        Args:
            note_id: Note ID
            user_id: User ID requesting the note
            
        Returns:
            Note data
            
        Raises:
            NotFoundError: If note not found
            AuthorizationError: If user doesn't own the note
        """
        note = await self.note_repo.get_by_id(note_id)
        
        if not note:
            raise NotFoundError("Note", note_id)
        
        # Verify ownership
        if note["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to access this note")
        
        return note
    
    async def get_user_notes(
        self,
        user_id: str,
        filters: Optional[NoteFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[dict], int]:
        """Get user's notes with filtering and pagination.
        
        Args:
            user_id: User ID
            filters: Optional filters
            pagination: Optional pagination params
            
        Returns:
            Tuple of (notes, total_count)
        """
        pagination = pagination or PaginationParams()
        
        # Get notes with filters
        notes = await self.note_repo.get_by_user_id_with_filters(
            user_id=user_id,
            filters=filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        
        # Get total count
        total = await self.note_repo.count_by_user_id_with_filters(
            user_id=user_id,
            filters=filters,
        )
        
        return notes, total
    
    async def update_note(
        self,
        note_id: str,
        user_id: str,
        note_data: UpdateNoteRequest,
    ) -> dict:
        """Update a note.
        
        Args:
            note_id: Note ID
            user_id: User ID updating the note
            note_data: Updated note data
            
        Returns:
            Updated note
            
        Raises:
            NotFoundError: If note not found
            AuthorizationError: If user doesn't own the note
        """
        # Verify ownership
        await self.get_note(note_id, user_id)
        
        # Prepare update data
        data = note_data.model_dump(exclude_none=True)
        
        note = await self.note_repo.update(note_id, data)
        logger.info(f"Note updated: {note_id} by user {user_id}")
        
        return note
    
    async def delete_note(self, note_id: str, user_id: str) -> bool:
        """Delete a note.
        
        Args:
            note_id: Note ID
            user_id: User ID deleting the note
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If note not found
            AuthorizationError: If user doesn't own the note
        """
        # Verify ownership
        await self.get_note(note_id, user_id)
        
        result = await self.note_repo.delete(note_id)
        logger.info(f"Note deleted: {note_id} by user {user_id}")
        
        return result
    
    async def toggle_favorite(self, note_id: str, user_id: str) -> dict:
        """Toggle note favorite status.
        
        Args:
            note_id: Note ID
            user_id: User ID
            
        Returns:
            Updated note
        """
        note = await self.get_note(note_id, user_id)
        is_favorite = note.get("is_favorite", False)
        
        return await self.update_note(
            note_id,
            user_id,
            UpdateNoteRequest(is_favorite=not is_favorite),
        )
    
    async def archive_note(self, note_id: str, user_id: str) -> dict:
        """Archive a note.
        
        Args:
            note_id: Note ID
            user_id: User ID
            
        Returns:
            Updated note
        """
        return await self.update_note(
            note_id,
            user_id,
            UpdateNoteRequest(is_archived=True),
        )
    
    async def unarchive_note(self, note_id: str, user_id: str) -> dict:
        """Unarchive a note.
        
        Args:
            note_id: Note ID
            user_id: User ID
            
        Returns:
            Updated note
        """
        return await self.update_note(
            note_id,
            user_id,
            UpdateNoteRequest(is_archived=False),
        )
    
    async def search_notes(
        self,
        user_id: str,
        query: str,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[dict], int]:
        """Search notes by content.
        
        Args:
            user_id: User ID
            query: Search query
            pagination: Optional pagination params
            
        Returns:
            Tuple of (notes, total_count)
        """
        filters = NoteFilters(search=query)
        return await self.get_user_notes(user_id, filters, pagination)


def get_note_service() -> NoteService:
    """Get note service instance."""
    return NoteService()
