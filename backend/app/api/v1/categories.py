"""
Category management API endpoints.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, ManagerUser
from app.models.event import Category
from app.schemas.event import CategoryBulkCreate, CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])
logger = structlog.get_logger()


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """List all categories for the organization."""
    query = select(Category).where(
        Category.organization_id == current_user.organization_id
    ).order_by(Category.name)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    return categories


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Create a new category (manager only)."""
    # Check if category with same name already exists
    existing = await db.execute(
        select(Category).where(
            Category.organization_id == current_user.organization_id,
            Category.name == category_data.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists"
        )
    
    category = Category(
        organization_id=current_user.organization_id,
        **category_data.model_dump()
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.post("/bulk-create", response_model=list[CategoryResponse])
async def bulk_create_categories(
    bulk_data: CategoryBulkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Create multiple categories at once (manager only)."""
    # Get existing category names
    existing_query = select(Category.name).where(
        Category.organization_id == current_user.organization_id
    )
    existing_result = await db.execute(existing_query)
    existing_names = {row[0] for row in existing_result.all()}
    
    # Filter out duplicates
    new_categories = []
    for cat_data in bulk_data.categories:
        if cat_data.name not in existing_names:
            category = Category(
                organization_id=current_user.organization_id,
                **cat_data.model_dump()
            )
            new_categories.append(category)
            existing_names.add(cat_data.name)
    
    db.add_all(new_categories)
    await db.commit()
    
    for cat in new_categories:
        await db.refresh(cat)
    
    return new_categories


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Update category (manager only)."""
    query = select(Category).where(
        Category.id == category_id,
        Category.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    for field, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Delete category (manager only)."""
    query = select(Category).where(
        Category.id == category_id,
        Category.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    if category.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default category"
        )
    
    await db.delete(category)
    await db.commit()
