from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.services.document_service import document_service
from app.services.auth_service import get_current_user
from app.database import get_db
from app.models import User, HistoryEntry

router = APIRouter(prefix="/api", tags=["Question Answering"])

@router.post("/ask")
async def ask_endpoint(
    request: Request,
    question: Optional[str] = Form(None),
    reference_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_question = ""
        context_text = ""

        content_type = request.headers.get("content-type", "")

        # 1. Handle JSON request body
        if "application/json" in content_type:
            try:
                body = await request.json()
                user_question = body.get("question", "")
                context_text = body.get("reference_text", "") or ""
            except Exception:
                pass

        # 2. Handle file upload if provided
        if not context_text and file is not None and file.filename:
            file_bytes = await file.read()
            context_text = document_service.extract_text(file_bytes, file.filename)
            if not user_question and question:
                user_question = question.strip()

        # 3. Handle Form data
        if not user_question and question and question.strip():
            user_question = question.strip()
            if not context_text and reference_text and reference_text.strip():
                context_text = reference_text.strip()

        if not user_question or not user_question.strip():
            return {"success": False, "error": "Please provide a question to ask."}

        if context_text and context_text.strip():
            document_service.validate_text_length(context_text)

        res = ai_service.ask(question=user_question, reference_text=context_text)

        # Save to history
        db.add(HistoryEntry(
            user_id=current_user.id,
            operation_type="ask",
            input_summary=user_question[:200],
            result=res.get("result", ""),
        ))
        db.commit()

        return {"success": True, "data": res}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        return {"success": False, "error": f"An error occurred while answering your question: {str(e)}"}
