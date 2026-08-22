from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.services.auth_service import get_current_user
from app.services.rate_limit_service import api_rate_limiter
from app.database import get_db
from app.models import User, HistoryEntry

router = APIRouter(prefix="/api", tags=["Content Generation"])


class GenerateRequest(BaseModel):
    content_type: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., min_length=1, max_length=500)
    tone: Optional[str] = Field(None, max_length=100)
    key_points: Optional[str] = Field(None, max_length=2000)


@router.post("/generate")
async def generate_endpoint(
    request: Request,
    content_type: Optional[str] = Form("Email"),
    topic: Optional[str] = Form(None),
    tone: Optional[str] = Form("Professional"),
    key_points: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not api_rate_limiter.check_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 20 requests per minute."
        )
    try:
        c_type = "Email"
        c_topic = ""
        c_tone = "Professional"
        c_points = None

        req_content_type = request.headers.get("content-type", "")

        # 1. Handle JSON request body
        if "application/json" in req_content_type:
            try:
                body = await request.json()
                c_topic = body.get("topic", "")
                c_type = body.get("content_type", body.get("type", "Email"))
                c_tone = body.get("tone", "Professional")
                c_points = body.get("key_points", None)
            except Exception:
                pass

        # 2. Handle Form data fallback
        if not c_topic and topic and topic.strip():
            c_topic = topic.strip()
            c_type = content_type or "Email"
            c_tone = tone or "Professional"
            c_points = key_points

        if not c_topic or not c_topic.strip():
            return {"success": False, "error": "Please provide a topic or prompt for content generation."}

        res = ai_service.generate_content(
            content_type=c_type,
            topic=c_topic,
            tone=c_tone,
            key_points=c_points
        )

        # Save to history
        db.add(HistoryEntry(
            user_id=current_user.id,
            operation_type="generate",
            input_summary=f"[{c_type}] {c_topic[:180]}",
            result=res.get("result", ""),
        ))
        db.commit()

        return {"success": True, "data": res}
    except ValueError as ve:
        return {"success": False, "error": str(ve)}
    except Exception as e:
        return {"success": False, "error": f"An error occurred during content generation: {str(e)}"}
