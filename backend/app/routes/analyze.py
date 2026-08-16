from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.services.document_service import document_service
from app.services.auth_service import get_current_user
from app.database import get_db
from app.models import User, HistoryEntry

router = APIRouter(prefix="/api", tags=["Document Analysis"])

@router.post("/analyze")
async def analyze_endpoint(
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        content_to_analyze = ""

        req_content_type = request.headers.get("content-type", "")

        # 1. Handle JSON request body
        if "application/json" in req_content_type:
            try:
                body = await request.json()
                content_to_analyze = body.get("text", "")
            except Exception:
                pass

        # 2. Handle file upload if provided
        if not content_to_analyze and file is not None and file.filename:
            file_bytes = await file.read()
            content_to_analyze = document_service.extract_text(file_bytes, file.filename)

        # 3. Handle Form text input
        if not content_to_analyze and text and text.strip():
            content_to_analyze = text.strip()

        if not content_to_analyze or not content_to_analyze.strip():
            return {
                "success": False,
                "error": "Please provide either pasted text or upload a document file (.pdf, .docx, .txt) to analyze."
            }

        document_service.validate_text_length(content_to_analyze)
        res = ai_service.analyze(content_to_analyze)

        # Save to history
        db.add(HistoryEntry(
            user_id=current_user.id,
            operation_type="analyze",
            input_summary=content_to_analyze[:200],
            result=str(res.get("main_topic", "")),
        ))
        db.commit()

        return {"success": True, "data": res}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        return {"success": False, "error": f"An error occurred while analyzing the document: {str(e)}"}
