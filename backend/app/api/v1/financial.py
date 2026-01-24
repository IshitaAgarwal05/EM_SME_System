"""
Payments and financial API endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, check_organization_access
from app.services.payment_service import PaymentService
from app.schemas.financial import (
    PaymentCreate, 
    PaymentUpdate, 
    PaymentResponse,
    ContractorCreate,
    ContractorUpdate,
    ContractorResponse,
    TransactionResponse,
    TransactionUpdate,
    CategorizeRequest
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.models.financial import Payment, Contractor, Transaction
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/financial", tags=["Financial"])

# --- Contractors ---

@router.post("/contractors", response_model=ContractorResponse, status_code=status.HTTP_201_CREATED)
async def create_contractor(
    data: ContractorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = PaymentService(db)
    return await service.create_contractor(data, current_user)

@router.get("/contractors", response_model=PaginatedResponse[ContractorResponse])
async def list_contractors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
):
    query = select(Contractor).where(Contractor.organization_id == current_user.organization_id)
    
    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Pagination
    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse.create(
        items=[ContractorResponse.model_validate(c) for c in items],
        total=total,
        page=pagination.page,
        limit=pagination.limit
    )

@router.get("/contractors/{contractor_id}", response_model=ContractorResponse)
async def get_contractor(
    contractor_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = PaymentService(db)
    try:
        contractor = await service.get_contractor(contractor_id)
        check_organization_access(contractor.organization_id, current_user)
        return contractor
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Contractor not found")

@router.patch("/contractors/{contractor_id}", response_model=ContractorResponse)
async def update_contractor(
    contractor_id: UUID,
    data: ContractorUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = PaymentService(db)
    try:
        return await service.update_contractor(contractor_id, data, current_user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Contractor not found")

@router.get("/contractors/{contractor_id}/details")
async def get_contractor_details(
    contractor_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = PaymentService(db)
    try:
        return await service.get_contractor_details(contractor_id, current_user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Contractor not found")

# --- Payments ---

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = PaymentService(db)
    try:
        return await service.create_payment(data, current_user)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payments", response_model=PaginatedResponse[PaymentResponse])
async def list_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    status: str | None = Query(None),
    contractor_id: UUID | None = Query(None),
):
    service = PaymentService(db) # For future use if loading complex relationships
    
    query = select(Payment).where(Payment.organization_id == current_user.organization_id)
    
    if status:
        query = query.where(Payment.status == status)
    if contractor_id:
        query = query.where(Payment.contractor_id == contractor_id)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Pagination
    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    payments = result.scalars().all()
    
    # Fetch relationships one by one for schema (optimize later)
    # Using service.get_payment logic basically but manual here to keep it simple or bulk load
    # For now returning as is, but relationship 'contractor' might be missing if lazy loaded.
    # Ideally use selectinload in query above.
    return PaginatedResponse.create(
        items=[PaymentResponse.model_validate(p) for p in payments], 
        total=total, 
        page=pagination.page, 
        limit=pagination.limit
    )

@router.post("/payments/{payment_id}/reconcile/{transaction_id}", response_model=PaymentResponse)
async def reconcile_payment(
    payment_id: UUID,
    transaction_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = PaymentService(db)
    try:
        return await service.reconcile_payment(payment_id, transaction_id, current_user)
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Transactions ---

@router.get("/transactions", response_model=PaginatedResponse[TransactionResponse])
async def list_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    reconciled: bool | None = Query(None),
):
    query = select(Transaction).where(Transaction.organization_id == current_user.organization_id)
    
    if reconciled is not None:
        query = query.where(Transaction.is_reconciled == reconciled)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset(pagination.offset).limit(pagination.limit).order_by(Transaction.transaction_date.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse.create(
        items=[TransactionResponse.model_validate(i) for i in items],
        total=total,
        page=pagination.page,
        limit=pagination.limit
    )
@router.post("/transactions/categorize-all")
async def categorize_all_transactions(
    request: CategorizeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Trigger AI/Rule-based categorization for all uncategorized transactions."""
    from app.services.analytics_service import AnalyticsService
    service = AnalyticsService(db, current_user.organization_id)
    return await service.categorize_transactions(request.categories)


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Update a financial transaction (e.g. manually change category)."""
    query = select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(transaction, key, value)
        
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.get("/statements/pl")
async def get_pl_statement(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int = Query(None),
):
    """Get Profit & Loss statement data."""
    if not year:
        from datetime import date
        year = date.today().year
    from app.services.analytics_service import AnalyticsService
    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_pl_statement(year)


@router.get("/statements/bs")
async def get_bs_statement(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int = Query(None),
):
    """Get Balance Sheet statement data (Schedule III format, current + previous year)."""
    if not year:
        from datetime import date
        year = date.today().year
    from app.services.analytics_service import AnalyticsService
    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_bs_statement(year)


@router.get("/statements/cf")
async def get_cashflow_statement(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int = Query(None),
):
    """Get Cash Flow Statement data."""
    if not year:
        from datetime import date
        year = date.today().year
    from app.services.analytics_service import AnalyticsService
    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_cashflow_statement(year)


@router.get("/statements/export")
async def export_financial_statements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Export transactions to Excel."""
    from fastapi.responses import StreamingResponse
    import pandas as pd
    import io
    
    query = select(Transaction).where(Transaction.organization_id == current_user.organization_id)
    result = await db.execute(query)
    txns = result.scalars().all()
    
    df = pd.DataFrame([{
        "Date": t.transaction_date,
        "Description": t.description,
        "Category": t.category or "Uncategorized",
        "Type": t.transaction_type,
        "Amount": float(t.amount),
        "Reconciled": t.is_reconciled
    } for t in txns])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=financial_statement.xlsx"}
    )
