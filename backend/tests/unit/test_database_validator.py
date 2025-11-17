"""Unit tests for database validator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.database import (
    DatabaseValidator,
    DatabaseConnectionInfo,
    SchemaValidationResult
)


class TestDatabaseConnectionInfo:
    """Test DatabaseConnectionInfo data model."""
    
    def test_connection_info_creation(self):
        """Test creating connection info."""
        info = DatabaseConnectionInfo(
            host="db.example.com",
            port=5432,
            database="postgres",
            user="admin",
            ssl_enabled=True,
            connection_pool_size=10
        )
        
        assert info.host == "db.example.com"
        assert info.port == 5432
        assert info.database == "postgres"
        assert info.user == "admin"
        assert info.ssl_enabled is True
        assert info.connection_pool_size == 10
    
    def test_connection_info_to_dict(self):
        """Test converting connection info to dictionary."""
        info = DatabaseConnectionInfo(
            host="db.example.com",
            port=5432,
            database="postgres",
            user="admin",
            ssl_enabled=True
        )
        
        info_dict = info.to_dict()
        
        assert isinstance(info_dict, dict)
        assert info_dict["host"] == "db.example.com"
        assert info_dict["port"] == 5432
        assert info_dict["database"] == "postgres"
        assert info_dict["user"] == "admin"
        assert info_dict["ssl_enabled"] is True
        
        # Should not contain sensitive information
        assert "password" not in info_dict
        assert "secret" not in info_dict


class TestSchemaValidationResult:
    """Test SchemaValidationResult data model."""
    
    def test_schema_result_all_exist(self):
        """Test schema result when all tables exist."""
        result = SchemaValidationResult(
            all_tables_exist=True,
            required_tables=["users", "tasks", "notes"],
            existing_tables=["users", "tasks", "notes"],
            missing_tables=[]
        )
        
        assert result.all_tables_exist is True
        assert len(result.missing_tables) == 0
        
        summary = result.get_summary()
        assert "✅" in summary
        assert "3" in summary
    
    def test_schema_result_missing_tables(self):
        """Test schema result with missing tables."""
        result = SchemaValidationResult(
            all_tables_exist=False,
            required_tables=["users", "tasks", "notes"],
            existing_tables=["users"],
            missing_tables=["tasks", "notes"]
        )
        
        assert result.all_tables_exist is False
        assert len(result.missing_tables) == 2
        
        summary = result.get_summary()
        assert "❌" in summary
        assert "tasks" in summary
        assert "notes" in summary
    
    def test_schema_result_to_dict(self):
        """Test converting schema result to dictionary."""
        result = SchemaValidationResult(
            all_tables_exist=False,
            required_tables=["users", "tasks"],
            existing_tables=["users"],
            missing_tables=["tasks"]
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["all_tables_exist"] is False
        assert result_dict["required_count"] == 2
        assert result_dict["existing_count"] == 1
        assert result_dict["missing_count"] == 1
        assert result_dict["missing_tables"] == ["tasks"]


class TestDatabaseValidator:
    """Test DatabaseValidator with mocked database."""
    
    @pytest.mark.asyncio
    async def test_connection_success(self):
        """Test successful database connection."""
        validator = DatabaseValidator()
        
        # Mock Supabase client
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}]
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_result
        
        with patch('app.core.database.supabase_available', return_value=True):
            with patch('app.core.database.get_supabase_client', return_value=mock_client):
                connected = await validator.test_connection()
                
                assert connected is True
                assert validator.client is not None
    
    @pytest.mark.asyncio
    async def test_connection_failure_not_configured(self):
        """Test connection failure when Supabase not configured."""
        validator = DatabaseValidator()
        
        with patch('app.core.database.supabase_available', return_value=False):
            connected = await validator.test_connection()
            
            assert connected is False
    
    @pytest.mark.asyncio
    async def test_connection_failure_exception(self):
        """Test connection failure with exception."""
        validator = DatabaseValidator()
        
        with patch('app.core.database.supabase_available', return_value=True):
            with patch('app.core.database.get_supabase_client', side_effect=Exception("Connection error")):
                connected = await validator.test_connection()
                
                assert connected is False
    
    @pytest.mark.asyncio
    async def test_verify_schema_all_tables_exist(self):
        """Test schema verification when all tables exist."""
        validator = DatabaseValidator()
        
        # Mock Supabase client that returns success for all tables
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_result
        
        validator.client = mock_client
        
        with patch('app.core.database.supabase_available', return_value=True):
            result = await validator.verify_schema()
            
            assert result.all_tables_exist is True
            assert len(result.missing_tables) == 0
            assert len(result.existing_tables) == len(DatabaseValidator.REQUIRED_TABLES)
    
    @pytest.mark.asyncio
    async def test_verify_schema_missing_tables(self):
        """Test schema verification with missing tables."""
        validator = DatabaseValidator()
        
        # Mock Supabase client that fails for some tables
        mock_client = MagicMock()
        
        def mock_table_query(table_name):
            """Mock table query that fails for specific tables."""
            mock_chain = MagicMock()
            if table_name in ["tasks", "notes"]:
                # Simulate missing table
                mock_chain.select.return_value.limit.return_value.execute.side_effect = Exception("Table not found")
            else:
                # Simulate existing table
                mock_result = MagicMock()
                mock_result.data = []
                mock_chain.select.return_value.limit.return_value.execute.return_value = mock_result
            return mock_chain
        
        mock_client.table.side_effect = mock_table_query
        validator.client = mock_client
        
        with patch('app.core.database.supabase_available', return_value=True):
            result = await validator.verify_schema()
            
            assert result.all_tables_exist is False
            assert "tasks" in result.missing_tables
            assert "notes" in result.missing_tables
    
    @pytest.mark.asyncio
    async def test_verify_schema_not_configured(self):
        """Test schema verification when database not configured."""
        validator = DatabaseValidator()
        
        with patch('app.core.database.supabase_available', return_value=False):
            result = await validator.verify_schema()
            
            assert result.all_tables_exist is False
            assert len(result.missing_tables) == len(DatabaseValidator.REQUIRED_TABLES)
    
    @pytest.mark.asyncio
    async def test_get_connection_info(self):
        """Test getting connection info."""
        validator = DatabaseValidator()
        
        with patch('app.core.database.settings') as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            
            info = await validator.get_connection_info()
            
            assert info is not None
            assert info.host == "test.supabase.co"
            assert info.port == 443
            assert info.ssl_enabled is True
    
    @pytest.mark.asyncio
    async def test_get_connection_info_no_url(self):
        """Test getting connection info when URL not set."""
        validator = DatabaseValidator()
        
        with patch('app.core.database.settings') as mock_settings:
            mock_settings.supabase_url = None
            
            info = await validator.get_connection_info()
            
            assert info is None
    
    @pytest.mark.asyncio
    async def test_write_operation_success(self):
        """Test successful write operation."""
        validator = DatabaseValidator()
        
        # Mock Supabase client
        mock_client = MagicMock()
        
        # Mock insert operation
        mock_insert_result = MagicMock()
        mock_insert_result.data = [{"telegram_id": 999999999}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_insert_result
        
        # Mock select operation
        mock_select_result = MagicMock()
        mock_select_result.data = [{"telegram_id": 999999999}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_select_result
        
        # Mock delete operation
        mock_delete_result = MagicMock()
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_delete_result
        
        validator.client = mock_client
        
        with patch('app.core.database.supabase_available', return_value=True):
            write_ok = await validator.test_write_operation()
            
            assert write_ok is True
    
    @pytest.mark.asyncio
    async def test_write_operation_failure(self):
        """Test write operation failure."""
        validator = DatabaseValidator()
        
        # Mock Supabase client that fails on insert
        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception("Write failed")
        
        validator.client = mock_client
        
        with patch('app.core.database.supabase_available', return_value=True):
            write_ok = await validator.test_write_operation()
            
            assert write_ok is False
    
    @pytest.mark.asyncio
    async def test_write_operation_not_configured(self):
        """Test write operation when database not configured."""
        validator = DatabaseValidator()
        
        with patch('app.core.database.supabase_available', return_value=False):
            write_ok = await validator.test_write_operation()
            
            assert write_ok is False
