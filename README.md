# Quickmind — AI-powered productivity assistant

Quickmind is a web app that helps users be more productive using AI. It provides five core features: text summarization, question answering, content generation, document analysis, and intelligent suggestions. It also supports user authentication (email/password + Google) and file upload for document analysis.

## Tech Stack

- **Backend:** Python + FastAPI
- **Frontend:** React (Vite)
- **AI:** OpenRouter (unified gateway for multiple AI models)
- **Database:** SQLite for local development, PostgreSQL in production (Neon recommended, Render Postgres also supported)

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenRouter API key from [openrouter.ai](https://openrouter.ai)
- (Optional) PostgreSQL for production auth (Neon recommended), or SQLite is used automatically for local development

### Backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# Linux/macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set:
- `OPENROUTER_API_KEY` to your OpenRouter key
- `OPENROUTER_MODEL` to the model you want to use (default: `google/gemini-2.5-flash`)
- `JWT_SECRET` to a strong random string (required for auth)
- `DATABASE_URL` to your Postgres connection string in production (omit for local SQLite)
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` if you want Google login (optional)

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

## AI Configuration

Quickmind uses [OpenRouter](https://openrouter.ai) as its single AI gateway. OpenRouter lets you access models from multiple providers (Google, Anthropic, OpenAI, etc.) through one API key.

### Getting Started

1. Create an account at [openrouter.ai](https://openrouter.ai).
2. Generate an API key in your OpenRouter dashboard.
3. Copy `.env.example` to `.env` in the `backend` folder.
4. Add your OpenRouter key:
   ```env
   OPENROUTER_API_KEY=your_key_here
   ```
5. Set the model you want to use:
   ```env
   OPENROUTER_MODEL=google/gemini-2.5-flash
   ```
6. Start the backend.

### Switching Models

You can switch models by changing one environment variable:

```env
OPENROUTER_MODEL=anthropic/claude-sonnet-4
```

or:

```env
OPENROUTER_MODEL=openai/gpt-4o
```

or:

```env
OPENROUTER_MODEL=google/gemini-2.5-flash
```

No code changes are required.

### Supported Models

Any model available on OpenRouter can be used. Popular options:

| Model | Example value |
|-------|---------------|
| Google Gemini 2.5 Flash | `google/gemini-2.5-flash` |
| Anthropic Claude Sonnet 4 | `anthropic/claude-sonnet-4` |
| OpenAI GPT-4o | `openai/gpt-4o` |
| Meta Llama 3.1 70B | `meta-llama/llama-3.1-70b-instruct` |

## How to Run Locally

1. Start the backend (above).
2. Start the frontend (above).
3. Ensure `backend/.env` has `FRONTEND_URL=http://localhost:5173` and the frontend `.env` has `VITE_API_URL=http://localhost:8000` and (optional) `VITE_GOOGLE_CLIENT_ID`.

## API Keys

Quickmind requires only one AI key:

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for all AI requests |
| `OPENROUTER_MODEL` | Model to use (default: `google/gemini-2.5-flash`) |

Legacy keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are no longer required.

### Auth Environment Variables

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | Strong random string for signing JWTs |
| `DATABASE_URL` | Postgres connection string in production (omit for local SQLite) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (optional) |

## Deployment

### Backend — Neon Database

1. Create a free database at [neon.tech](https://neon.tech).
2. Copy the connection string (it looks like `postgresql://user:password@ep-xxx.aws.neon.tech/dbname`).
3. Set `DATABASE_URL` in your backend `.env` or hosting platform to that connection string.
4. The app automatically enables SSL (`sslmode=require`) for Neon/Postgres connections.

### Backend — Render (optional alternative)

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, connect the repo.
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python version:** 3.11
  4. Add environment variables in Render dashboard:
     - `AI_PROVIDER` = `openrouter`
     - `OPENROUTER_API_KEY` = your OpenRouter key
     - `OPENROUTER_MODEL` = your chosen model
     - `FRONTEND_URL` = your Vercel frontend URL (set after frontend deploy)
     - `JWT_SECRET` = a strong random string (Render can generate one)
     - `DATABASE_URL` = your Render Postgres connection string (create a Postgres add-on in Render)
     - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (optional, for Google login)
   5. Deploy. Confirm `/api/health` responds.
   6. Test auth endpoints at `/api/auth/register`, `/api/auth/login`, `/api/auth/me`.

### Frontend — Vercel

1. Import the repo in Vercel (or use the Vercel CLI).
2. Set environment variables:
   - `VITE_API_URL` = your Render backend URL (e.g. `https://quickmind-api.onrender.com`)
   - `VITE_GOOGLE_CLIENT_ID` = your Google OAuth client ID (optional, for Google login)
3. Deploy.
4. Copy the live Vercel URL back into Render's `FRONTEND_URL` env var and redeploy the backend.

## Security

- API keys are loaded only from environment variables. They are never committed or exposed to the frontend.
- CORS is restricted to the frontend origin configured via `FRONTEND_URL`.
- Rate limiting is enabled (20 requests/minute per IP for general routes, 5 requests/minute for auth routes).
- Inputs are validated and capped.
- Passwords are hashed with bcrypt.
- JWTs are signed with a strong secret from env and expire after 24 hours.
- Google ID tokens are verified server-side with `google-auth`.
- File uploads are validated by MIME type and extension, capped at 10MB, and parsed in memory or temp files that are deleted immediately after.

## Screenshots

_Add screenshots here after deploying._

## Known Limitations

- Rate limiting is basic in-memory IP tracking (resets on backend restart).
- Maximum input length is capped at 30,000 characters for text inputs.
- File upload supports PDF, DOCX, TXT, PNG, JPG, JPEG up to 10MB.
- OCR for images requires the `tesseract-ocr` system package (preinstalled on Render, install locally as needed).
