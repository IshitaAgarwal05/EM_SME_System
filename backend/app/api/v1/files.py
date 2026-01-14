"""
File upload and processing API endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.dependencies import CurrentUser, check_organization_access
from app.services.excel_parser import ExcelParserService
from app.models.system import FileUpload
from app.models.financial import BankAccount
from app.schemas.system import FileUploadResponse

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("", response_model=list[FileUploadResponse])
async def list_files(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """
    List uploaded files for the current organization.
    """
    query = select(FileUpload).where(
        FileUpload.organization_id == current_user.organization_id
    ).order_by(FileUpload.created_at.desc())
    
    result = await db.execute(query)
    files = result.scalars().all()
    return files

@router.post("/upload")
async def upload_file(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """
    Simple file upload endpoint (alias for preview/import staging).
    """
    # Just return the preview for now as that's likely what they want
    return await preview_upload(db, current_user, file)


@router.post("/upload/preview")
async def preview_upload(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """
    Upload a file and get a preview of parsed transactions.
    Does NOT save to DB yet.
    """
    print(f"DEBUG UPLOAD: filename={file.filename}, content_type={file.content_type}")
    if not file.filename.lower().endswith(('.xls', '.xlsx', '.csv')):
        print(f"DEBUG: Invalid extension for {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    contents = await file.read()
    print(f"DEBUG: Read {len(contents)} bytes")
    
    parser = ExcelParserService(db, current_user.organization_id)
    result = await parser.parse_and_preview(contents, file.filename)
    
    return result


@router.post("/import")
async def import_file(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    file: UploadFile = File(...),
    bank_account_id: UUID | None = Form(None),
):
    """
    Upload and import transactions directly.
    """
    # 1. Save file upload record
    file_upload = FileUpload(
        organization_id=current_user.organization_id,
        uploaded_by=current_user.id,
        filename=file.filename,
        storage_path="metrics_only_mock_path", # In real app, upload to GCS/S3
        processing_status="processing"
    )
    db.add(file_upload)
    await db.flush()
    
    # 2. Parse
    contents = await file.read()
    parser = ExcelParserService(db, current_user.organization_id)
    preview = await parser.parse_and_preview(contents, file.filename)
    
    # 3. Import
    try:
        count = await parser.confirm_import(
            file_upload_id=file_upload.id, 
            preview_data=preview['all_rows'], 
            bank_account_id=bank_account_id
        )
        
        file_upload.processing_status = "completed"
        file_upload.rows_imported = count
        await db.commit()
        
        return {"message": "Import successful", "count": count}
        
    except Exception as e:
        file_upload.processing_status = "failed"
        file_upload.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """
    Delete an uploaded file and all associated transactions.
    """
    # 1. Check if file exists and belongs to organization
    query = select(FileUpload).where(
        FileUpload.id == file_id,
        FileUpload.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    file_upload = result.scalar_one_or_none()
    
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 2. Delete associated transactions
    from app.models.financial import Transaction
    from sqlalchemy import delete
    
    delete_txns_query = delete(Transaction).where(
        Transaction.source_file_id == file_id,
        Transaction.organization_id == current_user.organization_id
    )
    await db.execute(delete_txns_query)
    
    # 3. Delete the file record
    await db.delete(file_upload)
    await db.commit()
    
    return None
