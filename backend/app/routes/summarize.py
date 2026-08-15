from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field
from app.services.ai_service import ai_service
from app.services.document_service import document_service

router = APIRouter(prefix="/api", tags=["Summarize"])

class SummarizeRequest(BaseModel):
    text: Optional[str] = Field(None, description="Pasted text to summarize")
    length: str = Field("short", description="Summary length: 'short' or 'detailed'")

@router.post("/summarize")
async def summarize_endpoint(
    request_data: Optional[SummarizeRequest] = None,
    length: Optional[str] = Form("short"),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        content_to_summarize = ""
        summary_length = "short"
        
        # 1. Handle file upload if provided
        if file is not None and file.filename:
            file_bytes = await file.read()
            content_to_summarize = document_service.extract_text(file_bytes, file.filename)
            summary_length = length or "short"
        # 2. Handle Form text input
        elif text and text.strip():
            document_service.validate_text_length(text)
            content_to_summarize = text.strip()
            summary_length = length or "short"
        # 3. Handle JSON payload
        elif request_data and request_data.text and request_data.text.strip():
            document_service.validate_text_length(request_data.text)
            content_to_summarize = request_data.text.strip()
            summary_length = request_data.length or "short"
        else:
            return {
                "success": False,
                "error": "Please provide either pasted text or upload a document file (.pdf, .docx, .txt) to summarize."
            }

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
