from typing import Optional
from fastapi import APIRouter, Form
from pydantic import BaseModel, Field
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api", tags=["Content Generation"])

class GenerateRequest(BaseModel):
    type: str = Field("Email", alias="content_type", description="Content type (Email, LinkedIn post, Report, Message)")
    topic: str = Field(..., description="Main topic or instruction")
    tone: str = Field("Professional", description="Desired tone (Professional, Casual, Persuasive, Concise)")
    key_points: Optional[str] = Field(None, description="Optional key points to include")

@router.post("/generate")
async def generate_endpoint(
    request_data: Optional[GenerateRequest] = None,
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

        if topic and topic.strip():
            c_topic = topic.strip()
            c_type = content_type or "Email"
            c_tone = tone or "Professional"
            c_points = key_points
        elif request_data and request_data.topic and request_data.topic.strip():
            c_topic = request_data.topic.strip()
            c_type = request_data.type or "Email"
            c_tone = request_data.tone or "Professional"
            c_points = request_data.key_points
        else:
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
