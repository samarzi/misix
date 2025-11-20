"""Finance service for business logic."""

import logging
from decimal import Decimal
from typing import Optional

from app.core.exceptions import NotFoundError, AuthorizationError
from app.models.common import PaginationParams
from app.models.finance import (
    CreateTransactionRequest,
    UpdateTransactionRequest,
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CreateAccountRequest,
    UpdateAccountRequest,
)
from app.repositories.finance import (
    FinanceTransactionRepository,
    get_transaction_repository,
    get_category_repository,
    get_account_repository
)

logger = logging.getLogger(__name__)


class FinanceService:
    """Service for finance management business logic."""
    
    def __init__(
        self,
        transaction_repo: Optional[FinanceTransactionRepository] = None,
        category_repo: Optional[object] = None,
        account_repo: Optional[object] = None
    ):
        """Initialize finance service.
        
        Args:
            transaction_repo: Transaction repository (injected for testing)
            category_repo: Category repository (injected for testing)
            account_repo: Account repository (injected for testing)
        """
        self.transaction_repo = transaction_repo or get_transaction_repository()
        self.category_repo = category_repo or get_category_repository()
        self.account_repo = account_repo or get_account_repository()
        # Alias for backward compatibility
        self.finance_repo = self.transaction_repo
    
    # ========================================================================
    # Transaction Operations
    # ========================================================================
    
    async def create_transaction(
        self,
        user_id: str,
        transaction_data: CreateTransactionRequest,
    ) -> dict:
        """Create a new transaction.
        
        Args:
            user_id: User ID creating the transaction
            transaction_data: Transaction data
            
        Returns:
            Created transaction
        """
        data = {
            "user_id": user_id,
            **transaction_data.model_dump(exclude_none=True),
        }
        
        # Convert Decimal to float for database
        if "amount" in data:
            data["amount"] = float(data["amount"])
        
        # Convert datetime to ISO string
        if "transaction_date" in data and data["transaction_date"]:
            data["transaction_date"] = data["transaction_date"].isoformat()
        
        transaction = await self.transaction_repo.create(data)
        logger.info(f"Transaction created: {transaction['id']} by user {user_id}")
        
        return transaction
    
    async def get_transaction(self, transaction_id: str, user_id: str) -> dict:
        """Get transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            user_id: User ID requesting the transaction
            
        Returns:
            Transaction data
            
        Raises:
            NotFoundError: If transaction not found
            AuthorizationError: If user doesn't own the transaction
        """
        transaction = await self.finance_repo.get_transaction_by_id(transaction_id)
        
        if not transaction:
            raise NotFoundError("Transaction", transaction_id)
        
        # Verify ownership
        if transaction["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to access this transaction")
        
        return transaction
    
    async def get_user_transactions(
        self,
        user_id: str,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[dict], int]:
        """Get user's transactions with pagination.
        
        Args:
            user_id: User ID
            pagination: Optional pagination params
            
        Returns:
            Tuple of (transactions, total_count)
        """
        pagination = pagination or PaginationParams()
        
        transactions = await self.finance_repo.get_transactions_by_user_id(
            user_id=user_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        
        total = await self.finance_repo.count_transactions_by_user_id(user_id)
        
        return transactions, total
    
    async def update_transaction(
        self,
        transaction_id: str,
        user_id: str,
        transaction_data: UpdateTransactionRequest,
    ) -> dict:
        """Update a transaction.
        
        Args:
            transaction_id: Transaction ID
            user_id: User ID updating the transaction
            transaction_data: Updated transaction data
            
        Returns:
            Updated transaction
        """
        # Verify ownership
        await self.get_transaction(transaction_id, user_id)
        
        data = transaction_data.model_dump(exclude_none=True)
        
        # Convert Decimal to float
        if "amount" in data:
            data["amount"] = float(data["amount"])
        
        # Convert datetime to ISO string
        if "transaction_date" in data and data["transaction_date"]:
            data["transaction_date"] = data["transaction_date"].isoformat()
        
        transaction = await self.finance_repo.update_transaction(transaction_id, data)
        logger.info(f"Transaction updated: {transaction_id} by user {user_id}")
        
        return transaction
    
    async def delete_transaction(self, transaction_id: str, user_id: str) -> bool:
        """Delete a transaction.
        
        Args:
            transaction_id: Transaction ID
            user_id: User ID deleting the transaction
            
        Returns:
            True if deleted
        """
        # Verify ownership
        await self.get_transaction(transaction_id, user_id)
        
        result = await self.finance_repo.delete_transaction(transaction_id)
        logger.info(f"Transaction deleted: {transaction_id} by user {user_id}")
        
        return result
    
    # ========================================================================
    # Category Operations
    # ========================================================================
    
    async def create_category(
        self,
        user_id: str,
        category_data: CreateCategoryRequest,
    ) -> dict:
        """Create a new category.
        
        Args:
            user_id: User ID creating the category
            category_data: Category data
            
        Returns:
            Created category
        """
        data = {
            "user_id": user_id,
            **category_data.model_dump(exclude_none=True),
        }
        
        # Convert Decimal to float
        if "budget" in data and data["budget"]:
            data["budget"] = float(data["budget"])
        
        category = await self.finance_repo.create_category(data)
        logger.info(f"Category created: {category['id']} by user {user_id}")
        
        return category
    
    async def get_user_categories(self, user_id: str) -> list[dict]:
        """Get user's categories.
        
        Args:
            user_id: User ID
            
        Returns:
            List of categories
        """
        return await self.finance_repo.get_categories_by_user_id(user_id)
    
    async def update_category(
        self,
        category_id: str,
        user_id: str,
        category_data: UpdateCategoryRequest,
    ) -> dict:
        """Update a category.
        
        Args:
            category_id: Category ID
            user_id: User ID updating the category
            category_data: Updated category data
            
        Returns:
            Updated category
        """
        # Verify ownership
        category = await self.finance_repo.get_category_by_id(category_id)
        if not category or category["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to update this category")
        
        data = category_data.model_dump(exclude_none=True)
        
        # Convert Decimal to float
        if "budget" in data and data["budget"]:
            data["budget"] = float(data["budget"])
        
        category = await self.finance_repo.update_category(category_id, data)
        logger.info(f"Category updated: {category_id} by user {user_id}")
        
        return category
    
    async def delete_category(self, category_id: str, user_id: str) -> bool:
        """Delete a category.
        
        Args:
            category_id: Category ID
            user_id: User ID deleting the category
            
        Returns:
            True if deleted
        """
        # Verify ownership
        category = await self.finance_repo.get_category_by_id(category_id)
        if not category or category["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to delete this category")
        
        result = await self.finance_repo.delete_category(category_id)
        logger.info(f"Category deleted: {category_id} by user {user_id}")
        
        return result
    
    # ========================================================================
    # Account Operations
    # ========================================================================
    
    async def create_account(
        self,
        user_id: str,
        account_data: CreateAccountRequest,
    ) -> dict:
        """Create a new account.
        
        Args:
            user_id: User ID creating the account
            account_data: Account data
            
        Returns:
            Created account
        """
        data = {
            "user_id": user_id,
            **account_data.model_dump(exclude_none=True),
        }
        
        # Convert Decimal to float
        if "balance" in data:
            data["balance"] = float(data["balance"])
        
        account = await self.finance_repo.create_account(data)
        logger.info(f"Account created: {account['id']} by user {user_id}")
        
        return account
    
    async def get_user_accounts(self, user_id: str) -> list[dict]:
        """Get user's accounts.
        
        Args:
            user_id: User ID
            
        Returns:
            List of accounts
        """
        return await self.finance_repo.get_accounts_by_user_id(user_id)
    
    async def update_account(
        self,
        account_id: str,
        user_id: str,
        account_data: UpdateAccountRequest,
    ) -> dict:
        """Update an account.
        
        Args:
            account_id: Account ID
            user_id: User ID updating the account
            account_data: Updated account data
            
        Returns:
            Updated account
        """
        # Verify ownership
        account = await self.finance_repo.get_account_by_id(account_id)
        if not account or account["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to update this account")
        
        data = account_data.model_dump(exclude_none=True)
        
        # Convert Decimal to float
        if "balance" in data:
            data["balance"] = float(data["balance"])
        
        account = await self.finance_repo.update_account(account_id, data)
        logger.info(f"Account updated: {account_id} by user {user_id}")
        
        return account
    
    async def delete_account(self, account_id: str, user_id: str) -> bool:
        """Delete an account.
        
        Args:
            account_id: Account ID
            user_id: User ID deleting the account
            
        Returns:
            True if deleted
        """
        # Verify ownership
        account = await self.finance_repo.get_account_by_id(account_id)
        if not account or account["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to delete this account")
        
        result = await self.finance_repo.delete_account(account_id)
        logger.info(f"Account deleted: {account_id} by user {user_id}")
        
        return result
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    async def get_finance_summary(self, user_id: str) -> dict:
        """Get finance summary for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Summary dictionary with income, expense, balance
        """
        transactions = await self.finance_repo.get_transactions_by_user_id(user_id)
        
        income = sum(
            float(t["amount"]) for t in transactions
            if t["type"] == "income"
        )
        expense = sum(
            abs(float(t["amount"])) for t in transactions
            if t["type"] == "expense"
        )
        balance = income - expense
        
        return {
            "income": income,
            "expense": expense,
            "balance": balance,
            "transaction_count": len(transactions),
        }


def get_finance_service() -> FinanceService:
    """Get finance service instance."""
    return FinanceService()
