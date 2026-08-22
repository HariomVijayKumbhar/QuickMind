from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.services.document_service import document_service
from app.services.auth_service import get_current_user
from app.services.rate_limit_service import api_rate_limiter
from app.database import get_db
from app.models import User, HistoryEntry

router = APIRouter(prefix="/api", tags=["Summarize"])


class SummarizeRequest(BaseModel):
    text: Optional[str] = Field(None, max_length=100000)
    length: Optional[str] = Field("short", pattern="^(short|detailed)$")


@router.post("/summarize")
async def summarize_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    length: Optional[str] = Form("short"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not api_rate_limiter.check_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 20 requests per minute."
        )
    try:
        content_to_summarize = ""
        summary_length = "short"

        content_type = request.headers.get("content-type", "")

        is_file_upload = False

        # 1. Handle JSON request body
        if "application/json" in content_type:
            try:
                body = await request.json()
                content_to_summarize = body.get("text", "")
                summary_length = body.get("length", "short")
            except Exception:
                pass

        # 2. Handle file upload if provided
        if not content_to_summarize and file is not None and file.filename:
            file_bytes = await file.read()
            document_service.validate_file(file.filename, len(file_bytes))
            content_to_summarize = document_service.extract_text(file_bytes, file.filename)
            summary_length = length or "short"
            is_file_upload = True

        # 3. Handle Form text input
        if not content_to_summarize and text and text.strip():
            content_to_summarize = text.strip()
            summary_length = length or "short"

        if not content_to_summarize or not content_to_summarize.strip():
            return {
                "success": False,
                "error": "Please provide either pasted text or upload a document file (.pdf, .docx, .txt) to summarize."
            }

        if not is_file_upload:
            document_service.validate_text_length(content_to_summarize)

        res = ai_service.summarize(content_to_summarize, length=summary_length)

        # Save to history (preview only — never full content)
        db.add(HistoryEntry(
            user_id=current_user.id,
            operation_type="summarize",
            input_summary=content_to_summarize[:200],
            result=res.get("result", ""),
        ))
        db.commit()

        return {"success": True, "data": res}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        return {"success": False, "error": f"An error occurred while generating summary: {str(e)}"}
