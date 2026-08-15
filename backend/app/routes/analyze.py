from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field
from app.services.ai_service import ai_service
from app.services.document_service import document_service

router = APIRouter(prefix="/api", tags=["Document Analysis"])

class AnalyzeRequest(BaseModel):
    text: Optional[str] = Field(None, description="Pasted document or text to analyze")

@router.post("/analyze")
async def analyze_endpoint(
    request_data: Optional[AnalyzeRequest] = None,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        content_to_analyze = ""
        
        if file is not None and file.filename:
            file_bytes = await file.read()
            content_to_analyze = document_service.extract_text(file_bytes, file.filename)
        elif text and text.strip():
            document_service.validate_text_length(text)
            content_to_analyze = text.strip()
        elif request_data and request_data.text and request_data.text.strip():
            document_service.validate_text_length(request_data.text)
            content_to_analyze = request_data.text.strip()
        else:
            return {
                "success": False,
                "error": "Please provide either pasted text or upload a document file (.pdf, .docx, .txt) to analyze."
            }

        res = ai_service.analyze(content_to_analyze)
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
            "error": f"An error occurred while analyzing the document: {str(e)}"
        }
