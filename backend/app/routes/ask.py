from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field
from app.services.ai_service import ai_service
from app.services.document_service import document_service

router = APIRouter(prefix="/api", tags=["Question Answering"])

class AskRequest(BaseModel):
    question: str = Field(..., description="The user question")
    reference_text: Optional[str] = Field(None, description="Optional reference context or pasted document text")

@router.post("/ask")
async def ask_endpoint(
    request_data: Optional[AskRequest] = None,
    question: Optional[str] = Form(None),
    reference_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        user_question = ""
        context_text = ""
        
        # Determine question and reference_text sources
        if file is not None and file.filename:
            file_bytes = await file.read()
            context_text = document_service.extract_text(file_bytes, file.filename)
            user_question = question or ""
        elif question and question.strip():
            user_question = question.strip()
            if reference_text and reference_text.strip():
                document_service.validate_text_length(reference_text)
                context_text = reference_text.strip()
        elif request_data and request_data.question and request_data.question.strip():
            user_question = request_data.question.strip()
            if request_data.reference_text and request_data.reference_text.strip():
                document_service.validate_text_length(request_data.reference_text)
                context_text = request_data.reference_text.strip()
        else:
            return {
                "success": False,
                "error": "Please provide a question to ask."
            }

        if not user_question:
            return {
                "success": False,
                "error": "Question field cannot be blank."
            }

        res = ai_service.ask(question=user_question, reference_text=context_text)
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
            "error": f"An error occurred while answering your question: {str(e)}"
        }
