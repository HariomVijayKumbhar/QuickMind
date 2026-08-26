from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=30000)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: str = Field(default="", max_length=30000)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    context: str = Field(default="", max_length=30000)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=30000)


class SuggestRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=2000)
    context: str = Field(default="", max_length=30000)


class ApiResponse(BaseModel):
    success: bool
    data: str | None = None
    error: str | None = None
