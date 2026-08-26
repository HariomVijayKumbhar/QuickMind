import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Depends, File, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from schemas import (
    SummarizeRequest,
    AskRequest,
    GenerateRequest,
    AnalyzeRequest,
    SuggestRequest,
    ApiResponse,
)
from ai_provider import generate
from security import get_current_user
from utils import limiter, get_client_ip
from auth_routes import router as auth_router
from file_parser import extract_text


app = FastAPI(title="Quickmind API")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
cors_origins = [origin.strip().rstrip("/") for origin in FRONTEND_URL.split(",") if origin.strip()]
for default_origin in ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]:
    if default_origin not in cors_origins:
        cors_origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/summarize", response_model=ApiResponse)
def summarize(
    req: SummarizeRequest,
    request: Request,
    user=Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        system = (
            "You are an expert analytical assistant. Your task is to produce a comprehensive, detailed, "
            "and well-structured summary based EXCLUSIVELY and STRICTLY on the provided text. "
            "Do NOT hallucinate, extrapolate, or introduce any outside facts or assumptions. "
            "Every section must be directly supported by the text. "
            "Structure your summary clearly with:\n"
            "- Executive Overview\n"
            "- Detailed Key Points & Core Findings\n"
            "- Important Specifics, Data & Nuances\n"
            "- Main Conclusions / Takeaways"
        )
        prompt = f"Please provide a thorough, detailed summary of the following document based STRICTLY on its contents:\n\n---\nDOCUMENT TEXT:\n{req.text}\n---"
        result = generate(prompt, system)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@app.post("/api/ask", response_model=ApiResponse)
def ask(
    req: AskRequest,
    request: Request,
    user=Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        if req.context and req.context.strip():
            system = (
                "You are an expert document assistant. You answer questions with thorough detail, "
                "basing your answer EXCLUSIVELY and STRICTLY on the provided document context. "
                "Do NOT use external knowledge, unstated assumptions, or extrapolate beyond the text. "
                "If the answer is not mentioned in or cannot be directly proven from the provided document, you MUST say: "
                "'This information is not found in the provided document.' "
                "When answering from the document, provide a comprehensive, clear explanation citing relevant details from the text."
            )
            prompt = f"DOCUMENT CONTEXT:\n{req.context}\n\nQUESTION:\n{req.question}\n\nAnswer the question in detail based STRICTLY and ONLY on the document context above:"
        else:
            system = "You are a helpful assistant. Provide detailed, accurate answers to user questions."
            prompt = req.question
        result = generate(prompt, system)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@app.post("/api/generate", response_model=ApiResponse)
def generate_content(
    req: GenerateRequest,
    request: Request,
    user=Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        if req.context and req.context.strip():
            system = (
                "You are an expert content creator. Generate high-quality, detailed content "
                "based EXCLUSIVELY and STRICTLY on the facts and information in the provided document context. "
                "Do NOT introduce outside facts, hallucinations, or speculations not found in the document."
            )
            prompt = f"DOCUMENT CONTEXT:\n{req.context}\n\nPROMPT / INSTRUCTIONS:\n{req.prompt}\n\nGenerate the requested content in detail based ONLY on the document context above:"
        else:
            system = "You are a helpful assistant that generates high-quality, detailed written content based on user prompts."
            prompt = req.prompt
        result = generate(prompt, system)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@app.post("/api/analyze", response_model=ApiResponse)
def analyze(
    req: AnalyzeRequest,
    request: Request,
    user=Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        system = (
            "You are an expert document analyst. Provide a thorough, in-depth, and detailed analysis "
            "based EXCLUSIVELY on the provided document text. Do NOT use outside assumptions or invent information. "
            "Provide structured, detailed sections covering:\n"
            "1. Executive Overview & Core Message\n"
            "2. Detailed Key Points & Findings (with specific evidence from the text)\n"
            "3. Tone, Audience, & Communication Style\n"
            "4. Structure, Strengths & Notable Insights\n"
            "5. Summary Assessment"
        )
        prompt = f"Perform a comprehensive, detailed analysis of the following document. Base all observations strictly on the text provided:\n\n---\nDOCUMENT TEXT:\n{req.text}\n---"
        result = generate(prompt, system)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@app.post("/api/suggest", response_model=ApiResponse)
def suggest(
    req: SuggestRequest,
    request: Request,
    user=Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        if req.context and req.context.strip():
            system = (
                "You are an expert strategic advisor and productivity coach. Provide detailed, actionable suggestions, "
                "next steps, and recommendations based EXCLUSIVELY and STRICTLY on the provided document context. "
                "Ensure every recommendation is directly grounded in the facts and scope of the document without fabricating outside facts."
            )
            prompt = f"DOCUMENT CONTEXT:\n{req.context}\n\nTASK / GOAL:\n{req.task}\n\nProvide detailed, actionable suggestions and next steps derived strictly from the document content:"
        else:
            system = "You are a productivity coach. Provide actionable, specific, and detailed suggestions."
            prompt = f"Given the following task/goal, suggest intelligent next steps or improvements:\n\n{req.task}"
        result = generate(prompt, system)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@app.post("/api/upload", response_model=ApiResponse)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    client_ip = get_client_ip(request)
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    try:
        content = file.file.read()
        text = extract_text(file.filename, content, mime=file.content_type or "")
        return ApiResponse(success=True, data=text)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error="Failed to process file.")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Invalid input: " + str(exc.errors()[0]["msg"])},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

