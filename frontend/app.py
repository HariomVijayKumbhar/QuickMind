import sys
import os
from pathlib import Path
import streamlit as st
import requests

# Add backend directory to sys.path for fallback imports
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.services.document_service import document_service
    from app.config import settings
except ImportError:
    document_service = None
    settings = None

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="QuickMind AI — Smart Productivity Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-Modern CSS Theme Injection (Glassmorphism + Neon Accents + Custom Typography)
# Ultra-Modern Responsive CSS Theme (Tested against Streamlit 1.32.0+)
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">

<style>
    /* Global Base & Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        overflow-x: hidden;
    }
    .stApp {
        background: radial-gradient(circle at 15% 15%, #1e1b4b 0%, #0f172a 45%, #020617 100%);
        color: #f8fafc;
    }
    
    /* Code & Long text word wrapping safety */
    code, pre, .inline-code, span, p, div, li, td, th {
        overflow-wrap: break-word !important;
        word-break: break-word !important;
    }
    code {
        white-space: pre-wrap !important;
    }
    
    /* Hide Default Header/Footer elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Headings */
    .brand-title {
        font-family: 'Outfit', sans-serif;
        font-size: clamp(1.8rem, 4vw, 2.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.6rem;
    }
    .brand-subtitle {
        font-size: clamp(0.85rem, 2vw, 1.05rem);
        color: #94a3b8;
        margin-bottom: 1.5rem;
        font-weight: 400;
        line-height: 1.4;
    }
    
    /* Top Metric Cards */
    .dash-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        backdrop-filter: blur(16px);
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }
    .dash-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
    }
    .dash-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 0.3rem;
    }
    .dash-value {
        font-size: clamp(1rem, 2.5vw, 1.25rem);
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'Outfit', sans-serif;
    }

    /* Glassmorphic Result Card */
    .glass-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 16px;
        padding: clamp(1rem, 3vw, 1.8rem);
        margin-top: 1.2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        position: relative;
        overflow-wrap: break-word;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #a855f7, #6366f1, #38bdf8);
        border-radius: 16px 16px 0 0;
    }
    .card-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #c084fc;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        max-width: 100%;
        overflow-wrap: break-word;
    }
    .status-online {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.3);
    }
    .status-pending {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }

    /* Button Styling & Touch-Friendly Sizing (Min 44px on mobile) */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        min-height: 42px;
        padding: 0.65rem 1.2rem;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
        transform: translateY(-1px);
    }
    
    /* Responsive Breakpoints (< 768px Tablet & Mobile) */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.75rem 2rem 0.75rem !important;
            max-width: 100% !important;
        }
        /* Stack column blocks vertically on small screens */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.6rem !important;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        .stButton > button {
            min-height: 46px !important;
            font-size: 0.95rem !important;
        }
        .dash-card {
            margin-bottom: 0.5rem !important;
        }
        /* Mobile-safe sidebar relative sizing */
        section[data-testid="stSidebar"] {
            width: 100% !important;
            max-width: 100vw !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Summarizer"
if "active_document_text" not in st.session_state:
    st.session_state.active_document_text = ""
if "active_document_name" not in st.session_state:
    st.session_state.active_document_name = ""
if "latest_result" not in st.session_state:
    st.session_state.latest_result = ""
if "latest_suggestions" not in st.session_state:
    st.session_state.latest_suggestions = []
if "preset_input" not in st.session_state:
    st.session_state.preset_input = ""
if "target_tab_trigger" not in st.session_state:
    st.session_state.target_tab_trigger = None
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def get_auth_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

# -----------------------------------------------------------------------------
# AUTHENTICATION UI INTERCEPT
# -----------------------------------------------------------------------------
if not st.session_state.token:
    st.markdown('<div class="brand-title" style="justify-content: center; margin-top: 5rem;">⚡ QuickMind AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle" style="text-align: center;">Log in to access your intelligent workspace and persistent history.</div>', unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        auth_mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        
        auth_email = st.text_input("Email", placeholder="you@example.com")
        auth_pass = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.button(auth_mode, type="primary", use_container_width=True):
            if not auth_email or not auth_pass:
                st.error("Please enter email and password.")
            else:
                endpoint = "/api/auth/login" if auth_mode == "Login" else "/api/auth/signup"
                try:
                    resp = requests.post(f"{BACKEND_URL}{endpoint}", json={"email": auth_email, "password": auth_pass}, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.token = data.get("token")
                        st.session_state.user_email = data.get("email")
                        st.rerun()
                    else:
                        err = resp.json().get("detail", "Authentication failed.") if resp.text else "Failed"
                        st.error(err)
                except Exception as e:
                    st.error(f"Connection error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
# -----------------------------------------------------------------------------

# Header Branding
st.markdown('<div class="brand-title">⚡ QuickMind AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-subtitle">Your intelligent, multi-provider AI workspace with truncation continuation & context grounding.</div>', unsafe_allow_html=True)

# Top Dashboard Metrics
doc_status = st.session_state.active_document_name or "No Document"
doc_length = f"{len(st.session_state.active_document_text):,} chars" if st.session_state.active_document_text else "0 chars"

col_d1, col_d2, col_d3, col_d4 = st.columns(4)
with col_d1:
    st.markdown(f'''
    <div class="dash-card">
        <div class="dash-label">Active Document</div>
        <div class="dash-value">{doc_status[:18]}{"..." if len(doc_status)>18 else ""}</div>
    </div>
    ''', unsafe_allow_html=True)
with col_d2:
    st.markdown(f'''
    <div class="dash-card">
        <div class="dash-label">Context Size</div>
        <div class="dash-value">{doc_length}</div>
    </div>
    ''', unsafe_allow_html=True)
with col_d3:
    st.markdown('''
    <div class="dash-card">
        <div class="dash-label">AI Engine</div>
        <div class="dash-value">Gemini / Groq / OpenAI</div>
    </div>
    ''', unsafe_allow_html=True)
with col_d4:
    st.markdown('''
    <div class="dash-card">
        <div class="dash-label">Resilience</div>
        <div class="dash-value">Fallback + Continuation</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Sidebar Setup
with st.sidebar:
    st.title("⚡ Control Panel")
    st.markdown("---")
    
    # API Health Check
    st.markdown("### 🔌 API Service Status")
    try:
        health_resp = requests.get(f"{BACKEND_URL}/api/health", timeout=2)
        if health_resp.status_code == 200 and health_resp.json().get("gemini_api_configured"):
            st.markdown('<div class="status-badge status-online">✔ Multi-Provider API Ready</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge status-pending">⚡ API Online (Checking Keys)</div>', unsafe_allow_html=True)
    except Exception:
        st.error("Backend Server (Port 8000) not reachable.")
        st.caption("Run: `python backend/app/main.py`")

    st.markdown("---")
    
    # Document Upload Section
    st.markdown("### 📄 Document Uploader")
    uploaded_file = st.file_uploader(
        "Upload reference file (.pdf, .docx, .txt, .jpg, .png)",
        type=["pdf", "docx", "txt", "jpg", "jpeg", "png"],
        help="Max size 10MB. Image/scanned files use OCR. Text is preserved across all tools."
    )
    
    if uploaded_file is not None:
        if st.session_state.active_document_name != uploaded_file.name:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("File size exceeds 10 MB limit.")
            else:
                _ext = uploaded_file.name.lower().rsplit(".", 1)[-1]
                _is_ocr = _ext in {"jpg", "jpeg", "png"}
                _spinner_msg = (
                    "🔍 Reading scanned document... this may take a moment."
                    if _is_ocr
                    else "Parsing document content..."
                )
                with st.spinner(_spinner_msg):
                    try:
                        if document_service:
                            raw_text = document_service.extract_text(uploaded_file.getvalue(), uploaded_file.name)
                            st.session_state.active_document_text = raw_text
                            st.session_state.active_document_name = uploaded_file.name
                            st.success(f"✅ Loaded: {uploaded_file.name}" + (" (OCR)" if _is_ocr else ""))
                        else:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            resp = requests.post(f"{BACKEND_URL}/api/analyze", files=files, headers=get_auth_headers(), timeout=60)
                            if resp.status_code == 200 and resp.json().get("success"):
                                data = resp.json().get("data", {})
                                raw_text = data.get("main_topic", "") + "\n" + "\n".join(data.get("key_points", []))
                                st.session_state.active_document_text = raw_text
                                st.session_state.active_document_name = uploaded_file.name
                                st.success(f"✅ Loaded: {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")

    if st.session_state.active_document_name:
        st.info(f"📌 Active: **{st.session_state.active_document_name}**")
        if st.button("🗑️ Clear Active Document"):
            st.session_state.active_document_text = ""
            st.session_state.active_document_name = ""
            st.rerun()

    st.markdown("---")
    st.markdown("### 🛡️ Smart Features")
    st.caption("• **Continuation Engine**: Resumes truncated responses automatically up to 5 rounds.")
    st.caption("• **Fallback Engine**: Retries failed calls across Gemini → Groq → OpenAI.")
    st.caption("• **OCR Engine**: Extracts text from scanned PDFs and images via Tesseract.")

    st.markdown("---")
    st.markdown(f"👤 **Logged in as:**\n\n`{st.session_state.user_email}`")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.token = None
        st.session_state.user_email = None
        st.rerun()

# Next-Step Suggestions Component
def render_suggestions(suggestions_list: list):
    if not suggestions_list:
        return
    st.markdown("#### ⚡ Intelligent Next Steps")
    cols = st.columns(min(len(suggestions_list), 4))
    for idx, sug in enumerate(suggestions_list[:4]):
        with cols[idx]:
            if st.button(f"👉 {sug}", key=f"sug_btn_{idx}_{hash(sug)}", use_container_width=True):
                text_content = st.session_state.latest_result or st.session_state.active_document_text
                sug_lower = sug.lower()
                
                if "question" in sug_lower or "ask" in sug_lower:
                    st.session_state.preset_input = text_content
                    st.session_state.target_tab_trigger = "Ask Q&A"
                elif "action item" in sug_lower or "analyze" in sug_lower:
                    st.session_state.preset_input = text_content
                    st.session_state.target_tab_trigger = "Document Analyzer"
                elif "linkedin" in sug_lower or "email" in sug_lower or "post" in sug_lower or "draft" in sug_lower:
                    st.session_state.preset_input = text_content
                    st.session_state.target_tab_trigger = "Content Generator"
                else:
                    st.session_state.preset_input = text_content
                    st.session_state.target_tab_trigger = "Summarizer"
                st.rerun()

# Tab Routing
tab_options = ["Summarizer", "Ask Q&A", "Content Generator", "Document Analyzer", "History"]
selected_index = tab_options.index(st.session_state.target_tab_trigger) if st.session_state.target_tab_trigger in tab_options else 0
if st.session_state.target_tab_trigger:
    st.session_state.target_tab_trigger = None

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Text Summarizer", 
    "❓ Grounded Q&A", 
    "✍️ Content Generator", 
    "📊 Document Analyzer",
    "🕰️ History"
])

# TAB 1: SUMMARIZER
with tab1:
    st.markdown("### 📝 Text & Document Summarizer")
    st.caption("Generate clear executive summaries or detailed section breakdowns.")
    
    col_input, col_opt = st.columns([3, 1])
    
    with col_opt:
        summary_length = st.radio(
            "Summary Length",
            options=["short", "detailed"],
            format_func=lambda x: "Short (1-2 Paras)" if x == "short" else "Detailed Breakdown"
        )
        use_active_doc = st.checkbox(
            "Use Active Uploaded Document",
            value=bool(st.session_state.active_document_text),
            disabled=not bool(st.session_state.active_document_text)
        )
    
    with col_input:
        default_val = st.session_state.active_document_text if use_active_doc else st.session_state.preset_input
        input_text = st.text_area(
            "Pasted text to summarize",
            value=default_val,
            height=200,
            max_chars=10000,
            placeholder="Paste text here or upload a document in the sidebar..."
        )
        st.caption(f"Character meter: {len(input_text):,}/10,000")

    if st.button("✨ Generate Summary", type="primary", use_container_width=True):
        if not input_text.strip():
            st.error("Please enter text or upload a document to summarize.")
        else:
            with st.spinner("Processing summary with AI engine..."):
                try:
                    payload = {"text": input_text.strip(), "length": summary_length}
                    resp = requests.post(f"{BACKEND_URL}/api/summarize", json=payload, headers=get_auth_headers(), timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            st.session_state.latest_result = data.get("result", "")
                            st.session_state.latest_suggestions = data.get("suggestions", [])
                            st.success("Summary ready!")
                        else:
                            st.error(res_json.get("error", "Failed to generate summary."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}).")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if st.session_state.latest_result and tab_options[selected_index] == "Summarizer":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📄 Summary Output</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.latest_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# TAB 2: QUESTION ANSWERING
with tab2:
    st.markdown("### ❓ Grounded Question Answering")
    st.caption("Strict context-grounded Q&A ensures answers adhere strictly to document facts without hallucinating.")
    
    use_doc_context = st.checkbox(
        "Ground answer in Active Uploaded Document",
        value=bool(st.session_state.active_document_text),
        disabled=not bool(st.session_state.active_document_text),
        key="qa_use_doc"
    )
    
    qa_question = st.text_input(
        "Enter your question",
        placeholder="e.g., What are the main findings or metrics in the text?",
    )
    
    qa_context_text = st.text_area(
        "Reference Context / Document Snippet (Optional)",
        value=st.session_state.active_document_text if use_doc_context else st.session_state.preset_input,
        height=120,
        placeholder="Background text to ground the answer..."
    )
    
    if st.button("🔍 Get Answer", type="primary", use_container_width=True):
        if not qa_question.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("Searching document facts and generating answer..."):
                try:
                    payload = {
                        "question": qa_question.strip(),
                        "reference_text": qa_context_text.strip() if qa_context_text else None
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/ask", json=payload, headers=get_auth_headers(), timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            st.session_state.latest_result = data.get("result", "")
                            st.session_state.latest_suggestions = data.get("suggestions", [])
                            st.success("Answer ready!")
                        else:
                            st.error(res_json.get("error", "Failed to answer question."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}).")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if st.session_state.latest_result and tab_options[selected_index] == "Ask Q&A":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">💡 Answer Result</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.latest_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# TAB 3: CONTENT GENERATOR
with tab3:
    st.markdown("### ✍️ Professional Content Generator")
    st.caption("Draft polished emails, LinkedIn posts, executive summaries, or messages in seconds.")
    
    col1, col2 = st.columns(2)
    with col1:
        content_type = st.selectbox(
            "Content Format",
            options=["Email", "LinkedIn post", "Executive Summary", "Blog Draft", "Casual Message"],
        )
    with col2:
        tone = st.selectbox(
            "Communication Tone",
            options=["Professional", "Casual", "Persuasive", "Concise", "Enthusiastic"],
        )
        
    topic = st.text_input(
        "Topic / Objective",
        value=st.session_state.preset_input[:100] if st.session_state.preset_input else "",
        placeholder="e.g., Weekly progress update on project milestones",
    )
    
    key_points = st.text_area(
        "Key Points or Source Context (Optional)",
        value=st.session_state.preset_input if st.session_state.preset_input else "",
        height=120,
        placeholder="Bullet points to include in the generated draft..."
    )
    
    if st.button("🚀 Draft Content", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a topic or objective.")
        else:
            with st.spinner(f"Drafting {content_type}..."):
                try:
                    payload = {
                        "content_type": content_type,
                        "topic": topic.strip(),
                        "tone": tone,
                        "key_points": key_points.strip() if key_points else None
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/generate", json=payload, headers=get_auth_headers(), timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            st.session_state.latest_result = data.get("result", "")
                            st.session_state.latest_suggestions = data.get("suggestions", [])
                            st.success(f"{content_type} drafted!")
                        else:
                            st.error(res_json.get("error", "Failed to generate content."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}).")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if st.session_state.latest_result and tab_options[selected_index] == "Content Generator":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">✨ Generated {content_type}</div>', unsafe_allow_html=True)
        st.code(st.session_state.latest_result, language="markdown")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# TAB 4: DOCUMENT ANALYZER
with tab4:
    st.markdown("### 📊 Document & Text Analyzer")
    st.caption("Automatically extract main topic summaries, key bullet takeaways, and action items.")
    
    analysis_text = st.text_area(
        "Source Content to Analyze",
        value=st.session_state.active_document_text if st.session_state.active_document_text else st.session_state.preset_input,
        height=180,
        placeholder="Paste text here or upload a document in the sidebar..."
    )
    
    if st.button("🔬 Analyze Document", type="primary", use_container_width=True):
        if not analysis_text.strip():
            st.error("Please provide text or upload a document to analyze.")
        else:
            with st.spinner("Analyzing document structure and action items..."):
                try:
                    payload = {"text": analysis_text.strip()}
                    resp = requests.post(f"{BACKEND_URL}/api/analyze", json=payload, headers=get_auth_headers(), timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            st.session_state.latest_analysis = data
                            st.session_state.latest_suggestions = data.get("suggestions", [])
                            st.success("Analysis complete!")
                        else:
                            st.error(res_json.get("error", "Failed to analyze document."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}).")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if "latest_analysis" in st.session_state and st.session_state.latest_analysis:
        analysis = st.session_state.latest_analysis
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📌 Main Topic</div>', unsafe_allow_html=True)
        st.write(analysis.get("main_topic", "N/A"))
        
        st.markdown('<div class="card-title" style="margin-top: 1.2rem;">🔑 Key Takeaways</div>', unsafe_allow_html=True)
        for point in analysis.get("key_points", []):
            st.markdown(f"• {point}")
            
        st.markdown('<div class="card-title" style="margin-top: 1.2rem;">✅ Action Items Checklist</div>', unsafe_allow_html=True)
        action_items = analysis.get("action_items", [])
        if action_items:
            for item in action_items:
                st.checkbox(item, key=f"action_{hash(item)}")
        else:
            st.info("No explicit action items identified in this document.")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# TAB 5: HISTORY
with tab5:
    st.markdown("### 🕰️ Operation History")
    st.caption("Your recent AI requests, securely saved across sessions. Full document text is never stored.")
    
    if st.button("🔄 Refresh History"):
        st.rerun()

    try:
        hist_resp = requests.get(f"{BACKEND_URL}/api/history", headers=get_auth_headers(), timeout=15)
        if hist_resp.status_code == 200:
            history_data = hist_resp.json().get("data", [])
            if not history_data:
                st.info("No history entries found yet. Try summarizing some text!")
            else:
                for entry in history_data:
                    with st.expander(f"**{entry['operation_type'].upper()}** — {entry['created_at'][:16].replace('T', ' ')}"):
                        st.markdown("**Input Preview:**")
                        st.caption(f"_{entry['input_summary']}_")
                        st.markdown("**Result:**")
                        st.markdown(entry['result'])
                        
                        if st.button("🗑️ Delete", key=f"del_{entry['id']}", help="Permanently delete this entry"):
                            del_resp = requests.delete(f"{BACKEND_URL}/api/history/{entry['id']}", headers=get_auth_headers())
                            if del_resp.status_code == 200:
                                st.rerun()
                            else:
                                st.error("Failed to delete entry.")
        else:
            st.error("Failed to load history. Please try again.")
    except Exception as e:
        st.error(f"Could not fetch history: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem; font-weight: 500;'>"
    "⚡ QuickMind AI Suite • Built with FastAPI, Streamlit, and Multi-Provider AI Engine"
    "</div>",
    unsafe_allow_html=True
)
