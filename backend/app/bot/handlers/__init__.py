"""Bot handlers module.

This module contains refactored bot handlers split by domain.
The original handlers.py is kept for backward compatibility but should
be gradually migrated to use these new modular handlers.
"""

# Re-export commonly used functions for backward compatibility
from .message import handle_text_message
from .command import handle_start_command, handle_help_command

__all__ = [
    "handle_text_message",
    "handle_start_command", 
    "handle_help_command",
]
