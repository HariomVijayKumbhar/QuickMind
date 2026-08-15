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
| **AI Provider** | Google Gemini API (`gemini-2.5-flash` via `google-genai` SDK) |
| **Document Processing**| `pypdf` (PDF), `python-docx` (DOCX), UTF-8 text parser |
| **Environment Handling**| `python-dotenv` |

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
│   │   │   └── analyze.py        # POST /api/analyze
│   │   ├── services/
│   │   │   ├── ai_service.py     # Gemini API integration & prompt engineering
│   │   │   └── document_service.py # PDF/DOCX/TXT text extraction & limits
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
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- Python 3.10+ installed
- Google Gemini API Key (Get a free key from [Google AI Studio](https://aistudio.google.com/))

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

### Step 1: Start the FastAPI Backend Server
From the root directory:
```bash
# Set PYTHONPATH to include backend folder
# On Windows (PowerShell):
$env:PYTHONPATH=".\backend"
python backend/app/main.py

# On Linux/macOS:
PYTHONPATH=./backend python backend/app/main.py
```
The FastAPI backend will start at: `http://localhost:8000` (API documentation accessible at `http://localhost:8000/docs`).

### Step 2: Start the Streamlit Frontend
In a new terminal window (with `.venv` activated):
```bash
streamlit run frontend/app.py
```
The Streamlit app will automatically open in your browser at: `http://localhost:8501`.

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
