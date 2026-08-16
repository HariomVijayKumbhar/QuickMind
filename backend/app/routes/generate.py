from typing import Optional
from fastapi import APIRouter, Request, Form
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api", tags=["Content Generation"])

@router.post("/generate")
async def generate_endpoint(
    request: Request,
    content_type: Optional[str] = Form("Email"),
    topic: Optional[str] = Form(None),
    tone: Optional[str] = Form("Professional"),
    key_points: Optional[str] = Form(None)
):
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
            return {
                "success": False,
                "error": "Please provide a topic or prompt for content generation."
            }

        res = ai_service.generate_content(
            content_type=c_type,
            topic=c_topic,
            tone=c_tone,
            key_points=c_points
        )
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
            "error": f"An error occurred during content generation: {str(e)}"
        }
