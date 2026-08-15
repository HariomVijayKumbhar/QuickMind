import sys
import os
from pathlib import Path
import streamlit as st
import requests

# Add backend directory to sys.path for fallback service imports if needed
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.services.document_service import document_service
    from app.config import settings
except ImportError:
    document_service = None
    settings = None

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page Config
st.set_page_config(
    page_title="QuickMind — AI Productivity Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphic UI)
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* Headers & Typography */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    
    /* Result Card Styling */
    .result-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(129, 140, 248, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    .result-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #818cf8;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Badge tags */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border: 1px solid rgba(129, 140, 248, 0.3);
    }
    .badge-success {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border-color: rgba(74, 222, 128, 0.3);
    }
    
    /* Metric Card */
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 8px;
        padding: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
    }
    .metric-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
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

# Header Section
st.markdown('<div class="main-header">⚡ QuickMind AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your intelligent workspace for summarization, Q&A, content generation, and document analysis.</div>', unsafe_allow_html=True)

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/brain.png", width=64)
    st.title("QuickMind Workspace")
    st.markdown("---")
    
    # API Status Check
    st.markdown("### 🔌 API Connection")
    try:
        health_resp = requests.get(f"{BACKEND_URL}/api/health", timeout=2)
        if health_resp.status_code == 200 and health_resp.json().get("gemini_api_configured"):
            st.markdown('<span class="badge badge-success">API Connected & Key Ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge">API Online (Key Pending)</span>', unsafe_allow_html=True)
            st.warning("GEMINI_API_KEY is not configured in backend/.env file.")
    except Exception:
        st.error("Backend Server (Port 8000) not reachable.")
        st.info("Start backend: `uvicorn app.main:app --reload`")

    st.markdown("---")
    
    # Document Upload Section (Global Context)
    st.markdown("### 📄 Document Context")
    uploaded_file = st.file_uploader(
        "Upload reference document (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        help="Max size 10MB. Content will be available across all tools."
    )
    
    if uploaded_file is not None:
        if st.session_state.active_document_name != uploaded_file.name:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("File size exceeds 10 MB limit.")
            else:
                with st.spinner("Parsing document text..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        resp = requests.post(f"{BACKEND_URL}/api/analyze", files=files, timeout=30)

                        if resp.status_code == 200 and resp.json().get("success"):
                            data = resp.json().get("data", {})
                            # If document service local available, read raw text directly
                            if document_service:
                                raw_text = document_service.extract_text(uploaded_file.getvalue(), uploaded_file.name)
                            else:
                                raw_text = data.get("main_topic", "") + "\n" + "\n".join(data.get("key_points", []))
                            
                            st.session_state.active_document_text = raw_text
                            st.session_state.active_document_name = uploaded_file.name
                            st.success(f"Loaded: {uploaded_file.name}")
                        else:
                            # Fallback parse via document_service
                            if document_service:
                                raw_text = document_service.extract_text(uploaded_file.getvalue(), uploaded_file.name)
                                st.session_state.active_document_text = raw_text
                                st.session_state.active_document_name = uploaded_file.name
                                st.success(f"Loaded: {uploaded_file.name}")
                            else:
                                st.error("Failed to parse uploaded document.")
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")

    if st.session_state.active_document_name:
        st.info(f"📌 Active Document: **{st.session_state.active_document_name}** ({len(st.session_state.active_document_text):,} chars)")
        if st.button("Clear Document"):
            st.session_state.active_document_text = ""
            st.session_state.active_document_name = ""
            st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Quick Tips")
    st.caption("• Click intelligent suggestions after any result to quickly chain actions.")
    st.caption("• Reference documents are limited to 10,000 characters for optimal AI prompt safety.")

# Function to render Intelligent Suggestions
def render_suggestions(suggestions_list: list):
    if not suggestions_list:
        return
    st.markdown("#### ⚡ Suggested Next Steps")
    cols = st.columns(min(len(suggestions_list), 4))
    for idx, sug in enumerate(suggestions_list[:4]):
        with cols[idx]:
            if st.button(f"👉 {sug}", key=f"sug_btn_{idx}_{hash(sug)}"):
                # Handle suggestion action routing
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
                elif "shorter" in sug_lower or "summarize" in sug_lower or "detailed" in sug_lower:
                    st.session_state.preset_input = text_content
                    st.session_state.target_tab_trigger = "Summarizer"
                else:
                    st.session_state.preset_input = text_content
                    st.session_state.target_tab_trigger = "Summarizer"
                st.rerun()

# Determine Tab selection state
tab_options = ["Summarizer", "Ask Q&A", "Content Generator", "Document Analyzer"]

if st.session_state.target_tab_trigger in tab_options:
    selected_index = tab_options.index(st.session_state.target_tab_trigger)
    st.session_state.target_tab_trigger = None
else:
    selected_index = 0

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Text Summarizer", 
    "❓ Question Answering", 
    "✍️ Content Generator", 
    "📊 Document Analyzer"
])

# ----------------------------------------------------
# TAB 1: TEXT SUMMARIZER
# ----------------------------------------------------
with tab1:
    st.markdown("### 📝 Summarize Text or Document")
    st.caption("Generate concise or detailed summaries from pasted text or active uploaded documents.")
    
    col_input, col_opt = st.columns([3, 1])
    
    with col_opt:
        summary_length = st.radio(
            "Summary Length",
            options=["short", "detailed"],
            format_func=lambda x: "Short (1-2 Paras)" if x == "short" else "Detailed (In-depth)",
            help="Short gives a quick executive summary. Detailed provides structured sections."
        )
        use_active_doc = st.checkbox(
            "Use Active Uploaded Document",
            value=bool(st.session_state.active_document_text),
            disabled=not bool(st.session_state.active_document_text)
        )
    
    with col_input:
        default_val = st.session_state.active_document_text if use_active_doc else st.session_state.preset_input
        input_text = st.text_area(
            "Enter or paste text to summarize",
            value=default_val,
            height=200,
            max_chars=10000,
            placeholder="Paste text here or upload a document in the sidebar..."
        )
        st.caption(f"Character count: {len(input_text):,}/10,000")

    if st.button("✨ Summarize Now", type="primary", use_container_width=True):
        if not input_text.strip():
            st.error("Please enter text or upload a document to summarize.")
        else:
            with st.spinner("Analyzing text and generating summary..."):
                try:
                    payload = {"text": input_text.strip(), "length": summary_length}
                    resp = requests.post(f"{BACKEND_URL}/api/summarize", json=payload, timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            result_text = data.get("result", "")
                            suggestions = data.get("suggestions", [])
                            
                            st.session_state.latest_result = result_text
                            st.session_state.latest_suggestions = suggestions
                            
                            st.success("Summary generated successfully!")
                        else:
                            st.error(res_json.get("error", "Failed to generate summary."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}). Please verify the backend service.")
                except Exception as e:
                    st.error(f"Connection error: Could not reach backend server at {BACKEND_URL}. Details: {str(e)}")

    if st.session_state.latest_result:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">📄 Summary Result</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.latest_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# ----------------------------------------------------
# TAB 2: QUESTION ANSWERING
# ----------------------------------------------------
with tab2:
    st.markdown("### ❓ Grounded Question Answering")
    st.caption("Ask questions about your document or general queries. Context-grounded Q&A strictly prevents hallucinations.")
    
    use_doc_context = st.checkbox(
        "Ground answer in Active Uploaded Document",
        value=bool(st.session_state.active_document_text),
        disabled=not bool(st.session_state.active_document_text)
    )
    
    if use_doc_context and st.session_state.active_document_name:
        st.info(f"Using document context: **{st.session_state.active_document_name}**")
        
    qa_question = st.text_input(
        "Enter your question",
        placeholder="e.g., What are the main findings in section 3?",
        help="Type a question related to your text or a general knowledge inquiry."
    )
    
    qa_context_text = st.text_area(
        "Reference Context / Document Snippet (Optional)",
        value=st.session_state.active_document_text if use_doc_context else st.session_state.preset_input,
        height=120,
        placeholder="Optional background text to ground the answer..."
    )
    
    if st.button("🔍 Get Answer", type="primary", use_container_width=True):
        if not qa_question.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("Searching context and generating answer..."):
                try:
                    payload = {
                        "question": qa_question.strip(),
                        "reference_text": qa_context_text.strip() if qa_context_text else None
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/ask", json=payload, timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            result_text = data.get("result", "")
                            suggestions = data.get("suggestions", [])
                            
                            st.session_state.latest_result = result_text
                            st.session_state.latest_suggestions = suggestions
                            st.success("Answer ready!")
                        else:
                            st.error(res_json.get("error", "Failed to answer question."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}).")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if st.session_state.latest_result and tab_options[selected_index] == "Ask Q&A":
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">💡 Answer</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.latest_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# ----------------------------------------------------
# TAB 3: CONTENT GENERATOR
# ----------------------------------------------------
with tab3:
    st.markdown("### ✍️ Professional Content Generator")
    st.caption("Instantly draft emails, LinkedIn posts, reports, or messages tailored to your tone and topic.")
    
    col1, col2 = st.columns(2)
    with col1:
        content_type = st.selectbox(
            "Content Type",
            options=["Email", "LinkedIn post", "Executive Summary", "Blog Draft", "Casual Message"],
            help="Select the format of content you wish to generate."
        )
    with col2:
        tone = st.selectbox(
            "Desired Tone",
            options=["Professional", "Casual", "Persuasive", "Concise", "Enthusiastic"],
            help="Select the voice and communication style."
        )
        
    topic = st.text_input(
        "Topic / Purpose",
        value=st.session_state.preset_input[:100] if st.session_state.preset_input else "",
        placeholder="e.g., Weekly progress update on the QuickMind project",
        help="Briefly describe what you want to write about."
    )
    
    key_points = st.text_area(
        "Key Points or Context Snippet (Optional)",
        value=st.session_state.preset_input if st.session_state.preset_input else "",
        height=120,
        placeholder="Bullet points or reference text to include in the draft..."
    )
    
    if st.button("🚀 Generate Content", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a topic or purpose for content generation.")
        else:
            with st.spinner(f"Drafting {content_type}..."):
                try:
                    payload = {
                        "content_type": content_type,
                        "topic": topic.strip(),
                        "tone": tone,
                        "key_points": key_points.strip() if key_points else None
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/generate", json=payload, timeout=45)
                    
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("success"):
                            data = res_json.get("data", {})
                            result_text = data.get("result", "")
                            suggestions = data.get("suggestions", [])
                            
                            st.session_state.latest_result = result_text
                            st.session_state.latest_suggestions = suggestions
                            st.success(f"{content_type} generated!")
                        else:
                            st.error(res_json.get("error", "Failed to generate content."))
                    else:
                        st.error(f"Backend API error ({resp.status_code}).")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if st.session_state.latest_result and tab_options[selected_index] == "Content Generator":
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="result-title">✨ Generated {content_type}</div>', unsafe_allow_html=True)
        st.code(st.session_state.latest_result, language="markdown")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# ----------------------------------------------------
# TAB 4: DOCUMENT ANALYZER
# ----------------------------------------------------
with tab4:
    st.markdown("### 📊 Document & Text Analyzer")
    st.caption("Automatically extract main topics, bullet key points, and actionable next steps.")
    
    analysis_text = st.text_area(
        "Text to Analyze",
        value=st.session_state.active_document_text if st.session_state.active_document_text else st.session_state.preset_input,
        height=180,
        placeholder="Paste text here or upload a document in the sidebar..."
    )
    
    if st.button("🔬 Analyze Document", type="primary", use_container_width=True):
        if not analysis_text.strip():
            st.error("Please provide text or upload a document to analyze.")
        else:
            with st.spinner("Extracting topic, key points, and action items..."):
                try:
                    payload = {"text": analysis_text.strip()}
                    resp = requests.post(f"{BACKEND_URL}/api/analyze", json=payload, timeout=45)
                    
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
        
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">📌 Main Topic</div>', unsafe_allow_html=True)
        st.write(analysis.get("main_topic", "N/A"))
        
        st.markdown('<div class="result-title" style="margin-top: 1rem;">🔑 Key Points</div>', unsafe_allow_html=True)
        for point in analysis.get("key_points", []):
            st.markdown(f"• {point}")
            
        st.markdown('<div class="result-title" style="margin-top: 1rem;">✅ Action Items</div>', unsafe_allow_html=True)
        action_items = analysis.get("action_items", [])
        if action_items:
            for item in action_items:
                st.checkbox(item, key=f"action_{hash(item)}")
        else:
            st.info("No explicit action items identified in this text.")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        render_suggestions(st.session_state.latest_suggestions)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "QuickMind AI Productivity Assistant • Powered by FastAPI & Google Gemini API"
    "</div>",
    unsafe_allow_html=True
)
