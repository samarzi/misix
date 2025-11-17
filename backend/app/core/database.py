"""Database validation and connection testing for MISIX application.

This module provides utilities to test database connectivity, verify schema,
and provide diagnostic information for troubleshooting database issues.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

from app.shared.supabase import get_supabase_client, supabase_available

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConnectionInfo:
    """Anonymized database connection information for logging."""
    
    host: str
    port: int
    database: str
    user: str
    ssl_enabled: bool
    connection_pool_size: Optional[int] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "ssl_enabled": self.ssl_enabled,
            "connection_pool_size": self.connection_pool_size
        }


@dataclass
class SchemaValidationResult:
    """Result of database schema validation."""
    
    all_tables_exist: bool
    required_tables: list[str] = field(default_factory=list)
    existing_tables: list[str] = field(default_factory=list)
    missing_tables: list[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get human-readable summary.
        
        Returns:
            Summary string with emoji
        """
        if self.all_tables_exist:
            return f"✅ All {len(self.required_tables)} required tables exist"
        return f"❌ Missing {len(self.missing_tables)} tables: {', '.join(self.missing_tables)}"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "all_tables_exist": self.all_tables_exist,
            "required_count": len(self.required_tables),
            "existing_count": len(self.existing_tables),
            "missing_count": len(self.missing_tables),
            "missing_tables": self.missing_tables
        }


class DatabaseValidator:
    """Validates database connection and schema."""
    
    # Required tables for MISIX application
    REQUIRED_TABLES = [
        "users",
        "notes",
        "tasks",
        "finance_transactions",
        "mood_entries",
        "reminders",
        "assistant_sessions",
        "assistant_messages",
    ]
    
    def __init__(self):
        """Initialize database validator."""
        self.client = None
    
    async def test_connection(self) -> bool:
        """Test basic database connectivity.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check if Supabase is configured
            if not supabase_available():
                logger.error("Supabase not configured - missing URL or service key")
                return False
            
            # Get Supabase client
            self.client = get_supabase_client()
            
            # Test connection with a simple query
            # Query the users table (should exist)
            result = self.client.table("users").select("id").limit(1).execute()
            
            logger.info("✅ Database connection successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}", exc_info=True)
            return False
    
    async def verify_schema(self) -> SchemaValidationResult:
        """Verify all required tables exist.
        
        Returns:
            SchemaValidationResult with details about existing and missing tables
        """
        existing_tables = []
        missing_tables = []
        
        try:
            if not self.client:
                if not supabase_available():
                    logger.error("Cannot verify schema - Supabase not configured")
                    return SchemaValidationResult(
                        all_tables_exist=False,
                        required_tables=self.REQUIRED_TABLES,
                        existing_tables=[],
                        missing_tables=self.REQUIRED_TABLES
                    )
                self.client = get_supabase_client()
            
            # Check each required table
            for table_name in self.REQUIRED_TABLES:
                try:
                    # Try to query the table (limit 0 for minimal overhead)
                    self.client.table(table_name).select("*").limit(0).execute()
                    existing_tables.append(table_name)
                    logger.debug(f"✅ Table '{table_name}' exists")
                except Exception as e:
                    missing_tables.append(table_name)
                    logger.warning(f"❌ Table '{table_name}' missing or inaccessible: {e}")
            
            all_exist = len(missing_tables) == 0
            
            result = SchemaValidationResult(
                all_tables_exist=all_exist,
                required_tables=self.REQUIRED_TABLES,
                existing_tables=existing_tables,
                missing_tables=missing_tables
            )
            
            if all_exist:
                logger.info(f"✅ Schema validation passed - all {len(self.REQUIRED_TABLES)} tables exist")
            else:
                logger.error(
                    f"❌ Schema validation failed - {len(missing_tables)} tables missing: "
                    f"{', '.join(missing_tables)}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Schema validation error: {e}", exc_info=True)
            return SchemaValidationResult(
                all_tables_exist=False,
                required_tables=self.REQUIRED_TABLES,
                existing_tables=existing_tables,
                missing_tables=missing_tables or self.REQUIRED_TABLES
            )
    
    async def get_connection_info(self) -> Optional[DatabaseConnectionInfo]:
        """Get anonymized connection information for logging.
        
        Returns:
            DatabaseConnectionInfo with sanitized connection details, or None if unavailable
        """
        try:
            from app.core.config import settings
            
            # Parse Supabase URL to extract connection info
            if not settings.supabase_url:
                return None
            
            parsed = urlparse(settings.supabase_url)
            
            # Extract host and port
            host = parsed.hostname or "unknown"
            port = parsed.port or 443  # Supabase uses HTTPS (443)
            
            # Supabase uses PostgreSQL on port 5432 for direct connections
            # But the REST API uses HTTPS
            # For display purposes, show the API endpoint info
            
            info = DatabaseConnectionInfo(
                host=host,
                port=port,
                database="postgres",  # Supabase default database name
                user="supabase_admin",  # Generic user name (not actual)
                ssl_enabled=parsed.scheme == "https",
                connection_pool_size=None  # Not applicable for Supabase REST API
            )
            
            logger.debug(f"Database connection info: {info.to_dict()}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return None
    
    async def test_write_operation(self) -> bool:
        """Test if database write operations work.
        
        This creates a test user record and immediately deletes it to verify
        that data persistence is working correctly.
        
        Returns:
            True if write operation successful, False otherwise
        """
        try:
            if not self.client:
                if not supabase_available():
                    logger.error("Cannot test write operation - Supabase not configured")
                    return False
                self.client = get_supabase_client()
            
            # Create a test user with a unique telegram_id
            test_telegram_id = 999999999  # Use a high number unlikely to conflict
            test_data = {
                "telegram_id": test_telegram_id,
                "username": "_test_user_",
                "full_name": "Test User",
                "language_code": "en"
            }
            
            # Insert test record
            insert_result = self.client.table("users").upsert(
                test_data,
                on_conflict="telegram_id"
            ).execute()
            
            if not insert_result.data:
                logger.error("❌ Write test failed - no data returned from insert")
                return False
            
            # Verify the record was created
            select_result = self.client.table("users").select("*").eq(
                "telegram_id", test_telegram_id
            ).execute()
            
            if not select_result.data:
                logger.error("❌ Write test failed - record not found after insert")
                return False
            
            # Clean up - delete test record
            self.client.table("users").delete().eq(
                "telegram_id", test_telegram_id
            ).execute()
            
            logger.info("✅ Database write operation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database write operation test failed: {e}", exc_info=True)
            return False
