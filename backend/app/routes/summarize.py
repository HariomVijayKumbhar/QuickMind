from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form
from app.services.ai_service import ai_service
from app.services.document_service import document_service

router = APIRouter(prefix="/api", tags=["Summarize"])

@router.post("/summarize")
async def summarize_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    length: Optional[str] = Form("short")
):
    try:
        content_to_summarize = ""
        summary_length = "short"
        
        content_type = request.headers.get("content-type", "")

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
            content_to_summarize = document_service.extract_text(file_bytes, file.filename)
            summary_length = length or "short"

        # 3. Handle Form text input
        if not content_to_summarize and text and text.strip():
            content_to_summarize = text.strip()
            summary_length = length or "short"

        if not content_to_summarize or not content_to_summarize.strip():
            return {
                "success": False,
                "error": "Please provide either pasted text or upload a document file (.pdf, .docx, .txt) to summarize."
            }

        document_service.validate_text_length(content_to_summarize)
        res = ai_service.summarize(content_to_summarize, length=summary_length)
        return {
            "success": True,
            "data": res
        }
    except ValueError as ve:
        return {
            "success": False,
            "error": str(ve)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"An error occurred while generating summary: {str(e)}"
        }
