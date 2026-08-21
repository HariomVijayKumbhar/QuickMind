from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.services.document_service import document_service
from app.services.auth_service import get_current_user
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api", tags=["Document"])


@router.post("/document/extract")
async def document_extract_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Extract raw text from an uploaded file with no AI processing.
    Returns the full extracted text so the frontend can use it as
    the active document context for all downstream AI operations.

    Accepts: .pdf, .docx, .txt, .jpg, .jpeg, .png (same rules as /api/analyze).
    Returns: { "success": true, "data": { "text": "...", "is_ocr": true/false } }
    """
    try:
        if not file or not file.filename:
            return {"success": False, "error": "No file provided."}

        file_bytes = await file.read()
        is_ocr = document_service.is_ocr_path(file.filename)

        # extract_text internally calls validate_file for extension + size checks
        text = document_service.extract_text(file_bytes, file.filename)

        return {
            "success": True,
            "data": {
                "text": text,
                "is_ocr": is_ocr,
            },
        }
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        return {
            "success": False,
            "error": f"An error occurred while extracting document text: {str(e)}",
        }
