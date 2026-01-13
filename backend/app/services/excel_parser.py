"""
Excel parser service for ingesting bank statements and matching transactions.
"""

from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import UUID

import pandas as pd
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import FileProcessingError
from app.models.financial import Transaction
from app.models.system import FileUpload

logger = structlog.get_logger()


class ExcelParserService:
    """Service for parsing Excel/CSV files and detecting transactions."""

    def __init__(self, db: AsyncSession, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id

    async def parse_and_preview(self, file_content: bytes, filename: str) -> dict[str, Any]:
        """
        Parse file content and return preview data.

        Args:
            file_content: Raw bytes of the uploaded file
            filename: Name of the file

        Returns:
            Dictionary with parsed transactions and metadata
        """
        try:
            # 1. Smart Header Detection
            # Some statements have metadata in first few rows. We need to find the real header.
            header_row_idx = 0
            if filename.endswith(('.xls', '.xlsx')):
                # Read first 20 rows without header to inspect
                df_scan = pd.read_excel(BytesIO(file_content), header=None, nrows=20)
                
                # Keywords to identify a header row
                key_terms = ["date", "particulars", "description", "narration", "debit", "credit", "withdrawal", "deposit", "amount", "balance", "val", "chq", "ref"]
                
                best_score = 0
                for idx, row in df_scan.iterrows():
                    row_str = " ".join([str(x).lower() for x in row.values if pd.notna(x)])
                    score = sum(1 for term in key_terms if term in row_str)
                    
                    # Robust check: A header usually has 'date' and something regarding 'amount' or 'debit/credit'
                    has_date = "date" in row_str
                    has_money = any(t in row_str for t in ["amount", "debit", "credit", "withdrawal", "deposit"])
                    
                    if has_date and has_money and score > best_score:
                        best_score = score
                        header_row_idx = idx
            
            print(f"DEBUG: Detected header at row index {header_row_idx}")

            # 2. Read DataFrame with correct header
            if filename.endswith(".csv"):
                 df = pd.read_csv(BytesIO(file_content))
            else:
                 df = pd.read_excel(BytesIO(file_content), header=header_row_idx)
            
            print(f"DEBUG: Columns found: {df.columns.tolist()}")

            # Basic clean up
            df = df.dropna(how="all")
            
            # Normalize headers
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Map columns
            column_map = self._detect_columns(df.columns)
            
            # Validation: Need Date AND (Amount OR (Debit AND/OR Credit))
            has_amount = column_map.get("amount")
            has_split = column_map.get("debit") or column_map.get("credit") or column_map.get("withdrawal") or column_map.get("deposit")
            
            if not column_map.get("date") or (not has_amount and not has_split):
                logger.error("missing_cols", map=column_map, columns=df.columns.tolist())
                raise FileProcessingError(f"Could not detect critical columns. Found: {list(column_map.keys())}")

            preview_data = []
            for idx, row in df.iterrows():
                try:
                    # Clean date
                    date_val = None
                    raw_date = row[column_map["date"]]
                    try:
                        date_val = pd.to_datetime(raw_date, dayfirst=True) # Common in India/UK
                    except:
                         date_val = pd.to_datetime(raw_date)

                    # Description
                    raw_desc = str(row[column_map["description"]])
                    counterparty, ref_no = self._extract_metadata(raw_desc)

                    # Amount Logic
                    amount_val = 0.0
                    txn_type = "debit"
                    
                    if column_map.get("amount"):
                        # Single column logic
                        raw_amt = row[column_map["amount"]]
                        if pd.isna(raw_amt) or raw_amt == "":
                             continue
                        if isinstance(raw_amt, str):
                             raw_amt = raw_amt.replace(",", "").replace(" ", "")
                        try:
                            amount_val = float(raw_amt)
                        except:
                            continue
                        txn_type = "credit" if amount_val > 0 else "debit"
                        amount_val = abs(amount_val)
                    else:
                        # Split column logic
                        debit = 0.0
                        credit = 0.0
                        
                        # Check Debit / Withdrawal
                        d_col = column_map.get("debit") or column_map.get("withdrawal")
                        if d_col:
                            val = row[d_col]
                            if pd.notna(val) and val != "" and str(val).strip() != "":
                                try:
                                    if isinstance(val, str): val = val.replace(",", "")
                                    debit = float(val)
                                except: pass
                        
                        # Check Credit / Deposit
                        c_col = column_map.get("credit") or column_map.get("deposit")
                        if c_col:
                             val = row[c_col]
                             if pd.notna(val) and val != "" and str(val).strip() != "":
                                 try:
                                     if isinstance(val, str): val = val.replace(",", "")
                                     credit = float(val)
                                 except: pass
                                 
                        if credit > 0:
                            amount_val = credit
                            txn_type = "credit"
                        elif debit > 0:
                            amount_val = debit
                            txn_type = "debit"
                        else:
                            continue # Skip row with no amount

                    preview_data.append({
                        "row": idx + 1 + header_row_idx, 
                        "date": date_val.isoformat(),
                        "description": raw_desc,
                        "counterparty": counterparty,
                        "reference_no": ref_no,
                        "amount": amount_val,
                        "type": txn_type,
                        "status": "valid"
                    })
                    
                except Exception as e:
                    # logger.warning("parse_row_error", row=idx, error=str(e))
                    continue # Skip empty/malformed rows gracefully

            return {
                "total_rows": len(df),
                "parsed_rows": len(preview_data),
                "preview": preview_data[:50],
                "all_rows": preview_data,
                "columns_mapped": column_map
            }

        except Exception as e:
            logger.error("file_parsing_failed", filename=filename, error=str(e))
            raise FileProcessingError(f"Failed to parse file: {str(e)}")

    def _extract_metadata(self, description: str) -> tuple[str | None, str | None]:
        """Extract counterparty and reference number from description using regex."""
        import re
        desc = description.upper()
        
        counterparty = None
        ref_no = None
        
        # 1. Try to find Ref/UTR numbers (usually alphanumeric 10-16 chars)
        ref_patterns = [
            r"REF[:\-\s]+([A-Z0-9]{8,18})",
            r"UTR[:\-\s]*([A-Z0-9]{12,16})",
            r"CHQ NO[:\-\s]*(\d{6})",
            r"/([A-Z0-9]{10,16})/"
        ]
        for pattern in ref_patterns:
            match = re.search(pattern, desc)
            if match:
                ref_no = match.group(1)
                break
                
        # 2. Heuristic for Counterparty (First few words or after common prefixes)
        # UPI Transfer: UPI/NAME/REF/...
        if "UPI/" in desc:
            parts = desc.split("/")
            if len(parts) > 1:
                counterparty = parts[1]
        
        # NEFT/RTGS
        elif "NEFT-" in desc or "RTGS-" in desc:
            match = re.search(r"(?:NEFT|RTGS)-([A-Z\s]+)-", desc)
            if match:
                counterparty = match.group(1).strip()
        
        # Pos/Card
        elif "POS/" in desc:
            match = re.search(r"POS/([^/]+)/", desc)
            if match:
                 counterparty = match.group(1).strip()
                 
        if not counterparty:
             # Just take first two words if no specific pattern matched
             words = desc.split()
             if len(words) >= 2:
                  counterparty = f"{words[0]} {words[1]}"
             elif len(words) == 1:
                  counterparty = words[0]
                  
        return counterparty, ref_no

    def _detect_columns(self, columns: list[str]) -> dict[str, str]:
        """Heuristic to map standard columns."""
        mapping = {}
        
        # Extended Key Terms
        date_terms = ["date", "txn date", "transaction date", "value date", "tran date"]
        desc_terms = ["description", "narration", "particulars", "remarks", "details", "transaction remarks"]
        
        # Single Amount Column
        amount_terms = ["amount", "txn amount", "transaction amount", "amount(rs.)", "amount (rs.)"]
        
        # Split Columns
        debit_terms = ["debit", "withdrawal", "dr", "withdrawal (dr)", "debit amount"]
        credit_terms = ["credit", "deposit", "cr", "deposit (cr)", "credit amount"]
        
        for col in columns:
            col_lower = str(col).lower()
            
            if not mapping.get("date") and any(t in col_lower for t in date_terms):
                mapping["date"] = col
            
            elif not mapping.get("description") and any(t in col_lower for t in desc_terms):
                mapping["description"] = col
                
            elif not mapping.get("amount") and (col_lower in amount_terms or any(t == col_lower for t in amount_terms)):
                 mapping["amount"] = col
                 
            # Split checks
            elif not mapping.get("debit") and any(t in col_lower for t in debit_terms):
                 mapping["debit"] = col
            elif not mapping.get("credit") and any(t in col_lower for t in credit_terms):
                 mapping["credit"] = col
                 
        return mapping

    async def confirm_import(
        self, 
        file_upload_id: UUID, 
        preview_data: list[dict],
        bank_account_id: UUID | None = None
    ) -> int:
        """
        Import confirmed transactions into database.
        """
        imported_count = 0
        
        for item in preview_data:
            if item.get("status") != "valid":
                continue
                
            txn = Transaction(
                organization_id=self.organization_id,
                bank_account_id=bank_account_id,
                transaction_date=datetime.fromisoformat(item["date"]).date(),
                description=item["description"],
                counterparty=item.get("counterparty"),
                reference_no=item.get("reference_no"),
                amount=item["amount"],
                transaction_type=item["type"],
                source="excel_import",
                source_file_id=file_upload_id,
                source_row_number=item["row"],
                is_reconciled=False
            )
            self.db.add(txn)
            imported_count += 1
            
        await self.db.commit()
        return imported_count
