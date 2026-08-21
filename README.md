# ⚡ QuickMind — AI Productivity Assistant

> An all-in-one AI-powered productivity application for text summarization, grounded Q&A, professional content generation, document analysis, and intelligent next-step recommendations.

---

## 📌 Problem Statement
Modern students, interns, and professionals waste significant time copying text between disparate AI prompts, summarizing long documents manually, drafting routine emails, and trying to extract key takeaways. **QuickMind** solves this by providing a unified, context-aware interface that handles your entire document workflow seamlessly with single-click intelligent suggestions.

---

## ✨ Features

- **📝 Text & Document Summarization**:
  - Generate crisp (1-2 paragraph) or detailed, structured summaries.
  - Supports pasted text and direct document uploads (`.pdf`, `.docx`, `.txt`).
- **❓ Grounded Question Answering**:
  - Ask questions about reference text or general topics.
  - Strict context grounding prevents hallucinations by adhering exclusively to provided document facts.
- **✍️ Content Generation**:
  - Draft emails, LinkedIn posts, executive summaries, blog posts, or casual messages.
  - Customize communication style across 5 distinct tones (Professional, Casual, Persuasive, Concise, Enthusiastic).
- **📊 Document & Text Analysis**:
  - Automatically extract main topics, 3-5 key bullet points, and actionable checklist items.
- **⚡ Intelligent Next-Step Suggestions**:
  - Contextual recommendations dynamically generated after every AI operation.
  - Clicking a suggestion button automatically feeds output content into target tools (e.g., turning a summary directly into an email or action item checklist).

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python 3.14 + FastAPI + Uvicorn |
| **Frontend Framework** | Streamlit (Interactive Glassmorphic Dark UI) |
| **AI Providers** | Google Gemini, Groq (Llama 3.3 70B), OpenAI (GPT-4o mini) |
| **Document Processing**| `pypdf` (PDF), `python-docx` (DOCX), UTF-8 text parser |
| **Environment Handling**| `python-dotenv` |

---

## ⚡ Multi-Provider Fallback & Truncation Continuation (Phase 2)

QuickMind includes advanced backend resilience features in `ai_service.py` to guarantee uninterrupted service and complete output generation:

### 1. Truncation Continuation Engine
When an AI provider cuts off a response mid-answer due to output token limits (`finish_reason == MAX_TOKENS` or `length`):
- QuickMind automatically detects the cut-off.
- It sends up to **5 continuation requests** to the **SAME provider and model** instructing it to resume exactly where it left off without repeating previous content.
- All response chunks are stitched into a single complete response in a consistent tone.

### 2. Multi-Provider Fallback Engine
If an AI provider encounters an initial connection error, authentication failure, timeout, or rate limit before generating content:
- QuickMind automatically retries the request using the next provider in the configured priority list (`PROVIDER_PRIORITY = ["gemini", "groq", "openai"]`).
- Unconfigured providers (missing API keys) are skipped cleanly without crashing.
- Fallback only triggers on initial request failure — never mid-answer during continuation.

---

## 🔐 Authentication & Persistent History (Phase 3)

QuickMind supports multi-user login and saves your workflow history securely:

### 1. User Accounts & JWT
- **Signup / Login**: Create an account with an email and password.
- Passwords are securely hashed with `bcrypt` (never stored in plain text).
- API requests are protected via JWT (JSON Web Tokens) Bearer auth.

### 2. Operation History
- **Database**: Uses SQLite (`quickmind.db`) — no external database server required.
- **Persistent log**: Every AI operation (summarize, ask, generate, analyze) is saved to the active user's history.
- **Privacy & Security**: Only a short preview (max 200 characters) of the input is saved to the database. The full document content is NEVER saved.
- **Data Ownership**: Users can view and delete their own history entries. Users cannot access other users' data.

---

## 📁 Folder Structure

```
QuickMind/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI server entry point & CORS
│   │   ├── config.py             # App & environment configuration
│   │   ├── routes/
│   │   │   ├── summarize.py      # POST /api/summarize
│   │   │   ├── ask.py            # POST /api/ask
│   │   │   ├── generate.py       # POST /api/generate
│   │   │   ├── analyze.py        # POST /api/analyze
│   │   │   └── document_extract.py # POST /api/document/extract (Text-only)
│   │   ├── services/
│   │   │   ├── ai_service.py     # Multi-provider AI engine & prompt engineering
│   │   │   └── document_service.py # PDF/DOCX/TXT/Image extraction & validation
│   │   └── tests/
│   │       └── test_routes.py    # Route & service unit test suite
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                      # API keys (gitignored)
├── frontend/
│   ├── app.py                    # Streamlit web application
│   ├── requirements.txt
│   └── .streamlit/
│       └── config.toml           # Streamlit theme customization
├── scripts/
│   └── dev/                      # One-off development & debugging scripts
├── run_tests.py                  # Automated test suite runner
├── e2e_test.py                   # End-to-end integration test runner
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- Python 3.10+ installed
- Google Gemini API Key (Get a free key from [Google AI Studio](https://aistudio.google.com/))

#### Optional: OCR Support for Scanned PDFs & Images (Phase 2 Stretch Goal)
To enable text extraction from scanned PDFs (`.pdf` without a text layer) and image files (`.jpg`, `.jpeg`, `.png`), install the following **system-level binaries** in addition to the Python packages:

**Tesseract OCR** (required by `pytesseract`):
```bash
# Linux (Debian/Ubuntu)
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Then add Tesseract to your system PATH.
```

**Poppler** (required by `pdf2image` to render scanned PDFs):
```bash
# Linux (Debian/Ubuntu)
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
# Extract and add the `Library/bin` folder to your system PATH.
```

> **Note**: If Tesseract or Poppler is not installed, QuickMind will start normally and will log a warning. All standard text documents (`.txt`, `.docx`, text-based `.pdf`) continue to work without these system binaries. OCR is only invoked for image files or scanned PDFs with no embedded text.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/QuickMind.git
cd QuickMind
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
pip install -r frontend/requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the `backend/` directory based on `.env.example`:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
PORT=8000
HOST=0.0.0.0
```

---

## 🏃 Running the Application

> **Note on Virtual Environment**: The `.venv` directory is located at the root project directory (`QuickMind\.venv`).

---

### Option A: Running from Project Root (`QuickMind\`)

#### 1. Start Backend Server (Terminal 1):
```powershell
.\.venv\Scripts\python.exe backend/app/main.py
```
*(Runs FastAPI at http://localhost:8000. API docs available at http://localhost:8000/docs)*

#### 2. Start Frontend App (Terminal 2):
```powershell
.\.venv\Scripts\streamlit.exe run frontend/app.py
```
*(Opens Streamlit app at http://localhost:8501)*

---

### Option B: Running from Subdirectories

#### If your terminal is inside `backend/` (`QuickMind\backend`):
```powershell
..\.venv\Scripts\python.exe app/main.py
```

#### If your terminal is inside `frontend/` (`QuickMind\frontend`):
```powershell
..\.venv\Scripts\streamlit.exe run app.py
```

---

### Option C: Activating Virtual Environment First

In any terminal window:
```powershell
# Activate environment (from QuickMind root)
.\.venv\Scripts\Activate.ps1

# Start Backend:
python backend/app/main.py

# Start Frontend (in second terminal):
streamlit run frontend/app.py
```

---

## 📖 API Documentation

All endpoints return structured JSON response formats.

### Standard Success Response:
```json
{
  "success": true,
  "data": {
    "result": "... Output content ...",
    "suggestions": ["Draft follow-up email", "Extract action items"]
  }
}
```

### Standard Error Response:
```json
{
  "success": false,
  "error": "Friendly error explanation message."
}
```

### Endpoints Overview

| Method | Endpoint | Description | Payload / Inputs |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/signup` | Register new user | `{ "email": "...", "password": "..." }` |
| `POST` | `/api/auth/login` | Authenticate user | `{ "email": "...", "password": "..." }` |
| `GET` | `/api/history` | Get logged-in user's history | Requires `Authorization: Bearer <token>` |
| `DELETE` | `/api/history/{id}` | Delete history entry | Requires `Authorization: Bearer <token>` |
| `POST` | `/api/summarize` | Summarize text or uploaded document | `{ "text": "...", "length": "short" \| "detailed" }` or File |
| `POST` | `/api/ask` | Context-grounded Q&A | `{ "question": "...", "reference_text": "..." }` or File |
| `POST` | `/api/generate` | Professional content creation | `{ "type": "Email", "topic": "...", "tone": "Professional" }` |
| `POST` | `/api/analyze` | Document key point & action extraction | `{ "text": "..." }` or File |
| `GET` | `/api/health` | Backend status & API key verification | None |

---

## 🖼️ Application Screenshots

*Interface Mockups & Screenshots:*

| Feature | Interface Preview |
| :--- | :--- |
| **Workspace & Summarizer** | `[Streamlit Tab 1: Summarize Text & Document]` |
| **Grounded Q&A** | `[Streamlit Tab 2: Context-Aware Q&A]` |
| **Content Generator** | `[Streamlit Tab 3: Draft Emails & Posts]` |
| **Document Analyzer** | `[Streamlit Tab 4: Topic & Action Item Checklist]` |

---

## ⚠️ Input Limits & Validation Constraints
- **Max File Size**: 10 MB per file.
- **Supported Formats**: `.pdf`, `.docx`, `.txt` (validated via file headers and extensions).
- **Max Pasted Text**: 10,000 characters (prevents API token overload and runaway cost).
- **Prompt Guardrails**: Reference text is wrapped in strict isolation tags to prevent prompt injection.

---

## 🔮 Future Improvements
- [ ] Add PDF export for generated reports and summaries.
- [ ] Support local document vector store (RAG) for multi-file querying.
- [ ] Add dark/light mode toggle switch in sidebar.
- [ ] Add user prompt history tab (session storage).

---

## 👤 Author
Developed as part of the Internship / Student Project Showcase.
Built with ❤️ using FastAPI, Streamlit, and Google Gemini API.
