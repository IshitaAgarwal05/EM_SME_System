"""
Financial and payment Pydantic schemas.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.schemas.common import TimestampSchema


class ContractorBase(BaseModel):
    """Base contractor schema."""

    name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, max_length=255)
    payment_terms: str | None = Field(default=None, max_length=100)
    default_rate: Decimal | None = Field(default=None, ge=0)
    rate_type: str | None = Field(default=None, pattern="^(hourly|daily|fixed|monthly)$")
    bank_account_number: str | None = Field(default=None, max_length=50)
    ifsc_code: str | None = Field(default=None, max_length=20)
    upi_id: str | None = Field(default=None, max_length=100)
    service_type: str | None = Field(default=None, max_length=100)
    payment_mode: str | None = Field(default=None, max_length=50)
    contract_start_date: date | None = None
    contract_end_date: date | None = None
    notes: str | None = None


class ContractorCreate(ContractorBase):
    """Schema for creating a contractor."""
    pass


class ContractorUpdate(BaseModel):
    """Schema for updating a contractor."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, max_length=255)
    payment_terms: str | None = None
    default_rate: Decimal | None = Field(default=None, ge=0)
    rate_type: str | None = Field(default=None, pattern="^(hourly|daily|fixed|monthly)$")
    bank_account_number: str | None = None
    ifsc_code: str | None = None
    upi_id: str | None = None
    service_type: str | None = None
    payment_mode: str | None = None
    contract_start_date: date | None = None
    contract_end_date: date | None = None
    is_active: bool | None = None
    notes: str | None = None


class ContractorResponse(ContractorBase, TimestampSchema):
    """Schema for contractor response."""

    id: UUID
    organization_id: UUID
    is_active: bool

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    """Base payment schema."""

    amount: Decimal = Field(gt=0)
    currency: str = Field(default="INR", max_length=3)
    payment_type: str = Field(pattern="^(contractor|vendor|client|other)$")
    due_date: date | None = None
    payment_date: date | None = None
    invoice_number: str | None = Field(default=None, max_length=100)
    description: str | None = None
    notes: str | None = None


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""

    contractor_id: UUID | None = None
    transaction_id: UUID | None = None
    task_ids: list[UUID] = Field(default_factory=list, description="List of task IDs to link")


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""

    amount: Decimal | None = Field(default=None, gt=0)
    status: str | None = Field(
        default=None,
        pattern="^(pending|processing|completed|failed|cancelled)$",
    )
    due_date: date | None = None
    payment_date: date | None = None
    invoice_number: str | None = None
    description: str | None = None
    notes: str | None = None


class PaymentResponse(PaymentBase, TimestampSchema):
    """Schema for payment response."""

    id: UUID
    organization_id: UUID
    status: str
    contractor_id: UUID | None
    paid_by: UUID | None
    transaction_id: UUID | None
    contractor: ContractorResponse | None = None

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    """Base transaction schema."""
    transaction_date: date
    description: str
    amount: Decimal
    transaction_type: str = Field(pattern="^(credit|debit)$")
    category: str | None = None
    reference_no: str | None = None
    counterparty: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    
    
class TransactionCreate(TransactionBase):
    bank_account_id: UUID | None = None


class TransactionUpdate(BaseModel):
    category: str | None = None
    notes: str | None = None
    tags: list[str] | None = None

class CategorizeRequest(BaseModel):
    categories: list[str] | None = None

class TransactionResponse(TransactionBase, TimestampSchema):
    id: UUID
    organization_id: UUID
    bank_account_id: UUID | None
    is_reconciled: bool
    source: str
    
    class Config:
        from_attributes = True
