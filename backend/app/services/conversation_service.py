"""Conversation service for managing chat history and context."""

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import DatabaseError
from app.shared.supabase import get_supabase_client, supabase_available

logger = logging.getLogger(__name__)

# Configuration
CONVERSATION_BUFFER_LIMIT = 6  # Keep last 6 messages in memory
MAX_STORED_MESSAGES = 200  # Maximum messages to store per user
SUMMARY_TRIGGER_MESSAGES = 12  # Generate summary after this many messages


class ConversationService:
    """Service for managing conversation history and context.
    
    This service replaces the global dictionaries in handlers.py with
    a proper service that can be tested and scaled.
    """
    
    def __init__(self):
        """Initialize conversation service."""
        # In-memory buffers (for quick access)
        self._buffers: dict[str, deque] = {}
        self._message_counts: dict[str, int] = {}
        self._summary_cache: dict[str, Optional[str]] = {}
    
    def _get_buffer(self, user_id: str) -> deque:
        """Get or create conversation buffer for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Conversation buffer
        """
        if user_id not in self._buffers:
            self._buffers[user_id] = deque(maxlen=CONVERSATION_BUFFER_LIMIT)
        return self._buffers[user_id]
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        telegram_id: Optional[int] = None,
    ) -> None:
        """Add message to conversation history.
        
        Args:
            user_id: User ID
            role: Message role (user or assistant)
            content: Message content
            telegram_id: Optional Telegram user ID
        """
        # Add to in-memory buffer
        buffer = self._get_buffer(user_id)
        buffer.append({
            "role": role,
            "text": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Increment message count
        self._message_counts[user_id] = self._message_counts.get(user_id, 0) + 1
        
        # Store in database
        if supabase_available():
            try:
                supabase = get_supabase_client()
                supabase.table("assistant_messages").insert({
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "telegram_id": telegram_id,
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to store message in database: {e}")
        
        # Check if we should generate summary
        if self._message_counts[user_id] >= SUMMARY_TRIGGER_MESSAGES:
            await self._generate_and_store_summary(user_id, telegram_id)
    
    async def get_recent_messages(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """Get recent messages for user.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        if not supabase_available():
            # Return from in-memory buffer
            buffer = self._get_buffer(user_id)
            return list(buffer)
        
        try:
            supabase = get_supabase_client()
            result = (
                supabase.table("assistant_messages")
                .select("role, content, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            if not result.data:
                return []
            
            # Convert to expected format and reverse to chronological order
            messages = [
                {
                    "role": msg["role"],
                    "text": msg["content"],
                    "timestamp": msg["created_at"],
                }
                for msg in reversed(result.data)
            ]
            
            return messages
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return list(self._get_buffer(user_id))
    
    async def get_conversation_context(self, user_id: str) -> str:
        """Get conversation context for AI.
        
        This includes recent messages and any stored summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Context string
        """
        # Get summary if available
        summary = await self._get_latest_summary(user_id)
        
        # Get recent messages
        messages = await self.get_recent_messages(user_id, limit=6)
        
        # Build context
        context_parts = []
        
        if summary:
            context_parts.append(f"Previous conversation summary: {summary}")
        
        if messages:
            context_parts.append("Recent messages:")
            for msg in messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_parts.append(f"{role}: {msg['text']}")
        
        return "\n".join(context_parts)
    
    async def _get_latest_summary(self, user_id: str) -> Optional[str]:
        """Get latest conversation summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Summary text or None
        """
        # Check cache first
        if user_id in self._summary_cache:
            return self._summary_cache[user_id]
        
        if not supabase_available():
            return None
        
        try:
            supabase = get_supabase_client()
            result = (
                supabase.table("assistant_conversation_summaries")
                .select("summary")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                summary = result.data[0]["summary"]
                self._summary_cache[user_id] = summary
                return summary
        except Exception as e:
            logger.warning(f"Failed to get summary: {e}")
        
        return None
    
    async def _generate_and_store_summary(
        self,
        user_id: str,
        telegram_id: Optional[int] = None,
    ) -> None:
        """Generate and store conversation summary.
        
        Args:
            user_id: User ID
            telegram_id: Optional Telegram user ID
        """
        # TODO: Implement AI-based summary generation
        # For now, just reset the counter
        
        logger.info(f"Summary generation triggered for user {user_id}")
        
        # Reset message count
        self._message_counts[user_id] = 0
        
        # Prune old messages
        await self._prune_old_messages(user_id)
    
    async def _prune_old_messages(self, user_id: str) -> None:
        """Prune old messages to keep database size manageable.
        
        Args:
            user_id: User ID
        """
        if not supabase_available():
            return
        
        try:
            supabase = get_supabase_client()
            
            # Get messages beyond the limit
            result = (
                supabase.table("assistant_messages")
                .select("id")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(MAX_STORED_MESSAGES, MAX_STORED_MESSAGES + 200)
                .execute()
            )
            
            if result.data:
                ids_to_delete = [row["id"] for row in result.data]
                supabase.table("assistant_messages").delete().in_("id", ids_to_delete).execute()
                logger.info(f"Pruned {len(ids_to_delete)} old messages for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to prune messages: {e}")
    
    async def clear_conversation(self, user_id: str) -> None:
        """Clear conversation history for user.
        
        Args:
            user_id: User ID
        """
        # Clear in-memory data
        if user_id in self._buffers:
            self._buffers[user_id].clear()
        if user_id in self._message_counts:
            del self._message_counts[user_id]
        if user_id in self._summary_cache:
            del self._summary_cache[user_id]
        
        # Clear database
        if supabase_available():
            try:
                supabase = get_supabase_client()
                supabase.table("assistant_messages").delete().eq("user_id", user_id).execute()
                logger.info(f"Cleared conversation for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to clear conversation: {e}")


def get_conversation_service() -> ConversationService:
    """Get conversation service instance."""
    return ConversationService()
