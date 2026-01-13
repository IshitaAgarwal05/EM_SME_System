"""
Payment service for handling contractor payments, invoices, and reconciliation.
"""

from datetime import date, datetime
from typing import Sequence
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.models.financial import Payment, Contractor, TaskPaymentLink, Transaction
from app.models.task import Task
from app.models.user import User
from app.schemas.financial import PaymentCreate, PaymentUpdate, ContractorCreate, ContractorUpdate

logger = structlog.get_logger()


class PaymentService:
    """Service for payment and financial operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_contractor(self, data: ContractorCreate, user: User) -> Contractor:
        """Create a new contractor."""
        contractor = Contractor(
            organization_id=user.organization_id,
            **data.model_dump()
        )
        self.db.add(contractor)
        await self.db.commit()
        await self.db.refresh(contractor)
        return contractor

    async def get_contractor_details(self, contractor_id: UUID, user: User) -> dict:
        """Get contractor with associated payments and tasks."""
        contractor = await self.get_contractor(contractor_id)
        if contractor.organization_id != user.organization_id:
             raise AuthorizationError("Access denied")

        # Get payments
        from sqlalchemy import select
        payments_query = select(Payment).where(Payment.contractor_id == contractor_id).order_by(Payment.created_at.desc())
        payments_result = await self.db.execute(payments_query)
        payments = payments_result.scalars().all()

        # Get tasks
        from app.models.task import Task
        tasks_query = select(Task).where(Task.contractor_id == contractor_id).order_by(Task.due_date.desc())
        tasks_result = await self.db.execute(tasks_query)
        tasks = tasks_result.scalars().all()

        return {
            "contractor": contractor,
            "payments": payments,
            "tasks": tasks
        }

    async def get_contractor(self, contractor_id: UUID) -> Contractor:
        result = await self.db.execute(select(Contractor).where(Contractor.id == contractor_id))
        contractor = result.scalar_one_or_none()
        if not contractor:
            raise NotFoundError("Contractor", str(contractor_id))
        return contractor

    async def update_contractor(self, contractor_id: UUID, data: ContractorUpdate, user: User) -> Contractor:
        contractor = await self.get_contractor(contractor_id)
        if contractor.organization_id != user.organization_id:
             raise AuthorizationError("Access denied")
             
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(contractor, key, value)
            
        await self.db.commit()
        await self.db.refresh(contractor)
        return contractor

    async def create_payment(self, data: PaymentCreate, user: User) -> Payment:
        """Create a payment record and link to tasks."""
        
        # Validate contractor if provided
        if data.contractor_id:
            contractor = await self.db.get(Contractor, data.contractor_id)
            if not contractor or contractor.organization_id != user.organization_id:
                raise ValidationError("Invalid contractor ID")

        # Create payment
        payment_data = data.model_dump(exclude={'task_ids'})
        payment = Payment(
            organization_id=user.organization_id,
            paid_by=user.id,
            status="pending",
            **payment_data
        )
        self.db.add(payment)
        await self.db.flush()

        # Link tasks
        if data.task_ids:
            for task_id in data.task_ids:
                task = await self.db.get(Task, task_id)
                if not task or task.organization_id != user.organization_id:
                     logger.warning("invalid_task_link", task_id=str(task_id))
                     continue
                
                link = TaskPaymentLink(
                    task_id=task_id,
                    payment_id=payment.id,
                    amount_allocated=None # Could allocate proportionally in future
                )
                self.db.add(link)

        await self.db.commit()
        await self.db.refresh(payment)
        
        # Load relationships
        query = select(Payment).options(selectinload(Payment.contractor)).where(Payment.id == payment.id)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_payment(self, payment_id: UUID) -> Payment:
        query = select(Payment).options(selectinload(Payment.contractor)).where(Payment.id == payment_id)
        result = await self.db.execute(query)
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError("Payment", str(payment_id))
        return payment

    async def update_payment(self, payment_id: UUID, data: PaymentUpdate, user: User) -> Payment:
        payment = await self.get_payment(payment_id)
        if payment.organization_id != user.organization_id:
             raise AuthorizationError("Access denied")

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(payment, key, value)
            
        # If status changes to completed and no payment date, set it
        if data.status == "completed" and not payment.payment_date:
            payment.payment_date = date.today()

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def reconcile_payment(self, payment_id: UUID, transaction_id: UUID, user: User) -> Payment:
        """Link a payment request to a bank transaction."""
        payment = await self.get_payment(payment_id)
        if payment.organization_id != user.organization_id:
             raise AuthorizationError("Access denied")
             
        transaction = await self.db.get(Transaction, transaction_id)
        if not transaction or transaction.organization_id != user.organization_id:
            raise NotFoundError("Transaction", str(transaction_id))

        if transaction.is_reconciled:
             raise ValidationError("Transaction already reconciled")

        # Update Payment
        payment.transaction_id = transaction.id
        payment.status = "completed"
        payment.payment_date = transaction.transaction_date

        # Update Transaction
        transaction.is_reconciled = True
        transaction.reconciled_by = user.id
        from datetime import timezone
        transaction.reconciled_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(payment)
        return payment
