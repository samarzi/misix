"""Finance request and response models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Models
# ============================================================================

class CreateTransactionRequest(BaseModel):
    """Request model for creating a financial transaction.
    
    Example:
        {
            "amount": 1500.50,
            "currency": "RUB",
            "type": "expense",
            "category_id": "123e4567-e89b-12d3-a456-426614174000",
            "account_id": "123e4567-e89b-12d3-a456-426614174001",
            "description": "Grocery shopping",
            "merchant": "Supermarket",
            "transaction_date": "2025-01-17T14:30:00Z"
        }
    """
    
    amount: Decimal = Field(
        ...,
        decimal_places=2,
        description="Transaction amount (positive for income, negative for expense)",
        examples=[1500.50],
    )
    currency: str = Field(
        default="RUB",
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217)",
        examples=["RUB", "USD", "EUR"],
    )
    type: str = Field(
        ...,
        description="Transaction type (income or expense)",
        examples=["expense"],
    )
    category_id: Optional[UUID] = Field(
        default=None,
        description="Category ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    account_id: Optional[UUID] = Field(
        default=None,
        description="Account ID",
        examples=["123e4567-e89b-12d3-a456-426614174001"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Transaction description",
        examples=["Grocery shopping"],
    )
    merchant: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Merchant name",
        examples=["Supermarket"],
    )
    transaction_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Transaction date",
        examples=["2025-01-17T14:30:00Z"],
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional notes",
    )
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate transaction type."""
        allowed = {"income", "expense"}
        if v not in allowed:
            raise ValueError(f"Type must be one of: {allowed}")
        return v
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate and normalize currency code."""
        return v.upper()
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is not zero."""
        if v == 0:
            raise ValueError("Amount cannot be zero")
        return v


class UpdateTransactionRequest(BaseModel):
    """Request model for updating a transaction."""
    
    amount: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        description="Transaction amount",
    )
    currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Currency code",
    )
    type: Optional[str] = Field(
        default=None,
        description="Transaction type",
    )
    category_id: Optional[UUID] = Field(
        default=None,
        description="Category ID",
    )
    account_id: Optional[UUID] = Field(
        default=None,
        description="Account ID",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Description",
    )
    merchant: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Merchant",
    )
    transaction_date: Optional[datetime] = Field(
        default=None,
        description="Transaction date",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes",
    )
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate transaction type."""
        if v is None:
            return v
        allowed = {"income", "expense"}
        if v not in allowed:
            raise ValueError(f"Type must be one of: {allowed}")
        return v
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency code."""
        if v is None:
            return v
        return v.upper()


class CreateCategoryRequest(BaseModel):
    """Request model for creating a finance category.
    
    Example:
        {
            "name": "Groceries",
            "type": "expense",
            "budget": 15000.00,
            "color": "#FF5733",
            "icon": "🛒"
        }
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name",
        examples=["Groceries"],
    )
    type: str = Field(
        ...,
        description="Category type (income or expense)",
        examples=["expense"],
    )
    budget: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        ge=0,
        description="Monthly budget for this category",
        examples=[15000.00],
    )
    color: Optional[str] = Field(
        default=None,
        max_length=7,
        description="Color code (hex)",
        examples=["#FF5733"],
    )
    icon: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Icon emoji",
        examples=["🛒"],
    )
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate category type."""
        allowed = {"income", "expense"}
        if v not in allowed:
            raise ValueError(f"Type must be one of: {allowed}")
        return v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name."""
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class UpdateCategoryRequest(BaseModel):
    """Request model for updating a category."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Category name",
    )
    budget: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        ge=0,
        description="Monthly budget",
    )
    color: Optional[str] = Field(
        default=None,
        max_length=7,
        description="Color code",
    )
    icon: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Icon emoji",
    )


class CreateAccountRequest(BaseModel):
    """Request model for creating a finance account.
    
    Example:
        {
            "name": "Main Checking Account",
            "balance": 50000.00,
            "currency": "RUB",
            "institution": "Sberbank"
        }
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Account name",
        examples=["Main Checking Account"],
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        decimal_places=2,
        description="Current balance",
        examples=[50000.00],
    )
    currency: str = Field(
        default="RUB",
        min_length=3,
        max_length=3,
        description="Currency code",
        examples=["RUB"],
    )
    institution: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Financial institution name",
        examples=["Sberbank"],
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name."""
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        return v.upper()


class UpdateAccountRequest(BaseModel):
    """Request model for updating an account."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Account name",
    )
    balance: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        description="Balance",
    )
    currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Currency",
    )
    institution: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Institution",
    )


# ============================================================================
# Response Models
# ============================================================================

class TransactionResponse(BaseModel):
    """Response model for transaction data."""
    
    id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    type: str
    category_id: Optional[UUID]
    account_id: Optional[UUID]
    description: Optional[str]
    merchant: Optional[str]
    transaction_date: datetime
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Response model for category data."""
    
    id: UUID
    user_id: UUID
    name: str
    type: str
    budget: Optional[Decimal]
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AccountResponse(BaseModel):
    """Response model for account data."""
    
    id: UUID
    user_id: UUID
    name: str
    balance: Decimal
    currency: str
    institution: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
