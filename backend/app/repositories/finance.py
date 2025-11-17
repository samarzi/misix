"""Finance repository for database operations."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FinanceTransactionRepository(BaseRepository):
    """Repository for finance transaction data access."""
    
    def __init__(self):
        super().__init__("finance_transactions")
    
    async def get_by_date_range(
        self,
        user_id: str | UUID,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get transactions within date range.
        
        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            limit: Maximum number of transactions
            
        Returns:
            List of transactions
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .gte("transaction_date", start_date.isoformat())
                .lte("transaction_date", end_date.isoformat())
                .order("transaction_date", desc=True)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get by date range failed: {e}")
            return []
    
    async def get_by_category(
        self,
        user_id: str | UUID,
        category_id: str | UUID,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get transactions by category.
        
        Args:
            user_id: User ID
            category_id: Category ID
            limit: Maximum number of transactions
            
        Returns:
            List of transactions
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .eq("category_id", str(category_id))
                .order("transaction_date", desc=True)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get by category failed: {e}")
            return []


class FinanceCategoryRepository(BaseRepository):
    """Repository for finance category data access."""
    
    def __init__(self):
        super().__init__("finance_categories")
    
    async def get_by_type(
        self,
        user_id: str | UUID,
        category_type: str,
    ) -> list[dict]:
        """Get categories by type (income/expense).
        
        Args:
            user_id: User ID
            category_type: Category type
            
        Returns:
            List of categories
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .eq("type", category_type)
                .order("name")
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get by type failed: {e}")
            return []


class FinanceAccountRepository(BaseRepository):
    """Repository for finance account data access."""
    
    def __init__(self):
        super().__init__("finance_accounts")
    
    async def update_balance(
        self,
        account_id: str | UUID,
        new_balance: float,
    ) -> dict:
        """Update account balance.
        
        Args:
            account_id: Account ID
            new_balance: New balance
            
        Returns:
            Updated account data
        """
        return await self.update(account_id, {"balance": new_balance})


def get_transaction_repository() -> FinanceTransactionRepository:
    """Get transaction repository instance."""
    return FinanceTransactionRepository()


def get_category_repository() -> FinanceCategoryRepository:
    """Get category repository instance."""
    return FinanceCategoryRepository()


def get_account_repository() -> FinanceAccountRepository:
    """Get account repository instance."""
    return FinanceAccountRepository()
