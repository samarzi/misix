"""Legacy configuration module - DEPRECATED.

This module is kept for backward compatibility only.
New code should use app.core.config instead.
"""

import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env.local")

# Import new configuration
from app.core.config import settings as new_settings

warnings.warn(
    "app.shared.config is deprecated. Use app.core.config instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Expose settings for backward compatibility
settings = new_settings
