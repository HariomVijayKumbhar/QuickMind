# Quickmind — AI-powered productivity assistant

Quickmind is a web app that helps users be more productive using AI. It provides five core features: text summarization, question answering, content generation, document analysis, and intelligent suggestions.

## Tech Stack

- **Backend:** Python + FastAPI
- **Frontend:** React (Vite)
- **AI:** Anthropic Claude / OpenAI GPT / Google Gemini / OpenRouter (abstracted behind a single interface)

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- An API key from one of: Anthropic, OpenAI, Google Gemini, or OpenRouter

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set:
- `AI_PROVIDER` to `anthropic`, `openai`, `gemini`, or `openrouter`
- The matching API key, e.g. `OPENAI_API_KEY` or `OPENROUTER_API_KEY`

Run:
```bash
uvicorn main:app --reload
```

API docs will be at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Run:
```bash
npm run dev
```

Open `http://localhost:5173`.

## How to Run Locally

1. Start the backend (above).
2. Start the frontend (above).
3. Ensure `backend/.env` has `FRONTEND_URL=http://localhost:5173` and the frontend `.env` has `VITE_API_URL=http://localhost:8000`.

## API Keys

Supported providers and their environment variables:

| Provider | Env var | Key name |
|----------|---------|----------|
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Google | `gemini` | `GEMINI_API_KEY` |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` |

Only **one** valid key is required.

## Deployment

### Backend — Render

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, connect the repo.
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python version:** 3.11
 4. Add environment variables in Render dashboard:
    - `AI_PROVIDER` = `openai` (or your chosen provider)
    - `OPENAI_API_KEY` (or matching key for your provider: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`)
    - `FRONTEND_URL` = your Vercel frontend URL (set after frontend deploy)
5. Deploy. Confirm `/api/health` responds.

### Frontend — Vercel

1. Import the repo in Vercel (or use the Vercel CLI).
2. Set environment variable:
   - `VITE_API_URL` = your Render backend URL (e.g. `https://quickmind-api.onrender.com`)
3. Deploy.
4. Copy the live Vercel URL back into Render's `FRONTEND_URL` env var and redeploy the backend.

## Security

- API keys are loaded only from environment variables. They are never committed or exposed to the frontend.
- CORS is restricted to the frontend origin configured via `FRONTEND_URL`.
- Rate limiting is enabled (20 requests/minute per IP).
- Inputs are validated and capped.

## Screenshots

_Add screenshots here after deploying._

## Known Limitations

- No user accounts or persistence in v1.
- Rate limiting is basic in-memory IP tracking (resets on backend restart).
- Maximum input length is capped at 8000 characters for most inputs.
