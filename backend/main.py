import os

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
CORS_ORIGINS = [FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
        prompt = f"Summarize the following text concisely:\n\n{req.text}"
        system = "You are a helpful assistant that produces clear, concise summaries."
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
        prompt = req.question
        if req.context:
            prompt = f"Context:\n{req.context}\n\nQuestion: {req.question}"
        system = "You are a helpful assistant. Answer the question accurately based on the provided context if given."
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
        prompt = req.prompt
        system = "You are a helpful assistant that generates high-quality written content based on user prompts."
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
        prompt = f"Analyze the following document. Provide key points, tone, and structure feedback:\n\n{req.text}"
        system = "You are an expert document analyst. Provide clear, structured analysis."
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
        prompt = f"Given the following task/goal, suggest intelligent next steps or improvements:\n\n{req.task}"
        system = "You are a productivity coach. Provide actionable, specific suggestions."
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
        text = extract_text(file.filename, content)
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
