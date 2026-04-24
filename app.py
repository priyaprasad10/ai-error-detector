# app.py — AI Error Detective Streamlit UI
import streamlit as st
from datetime import datetime
from backend import (
    analyze_error,
    get_quick_fix,
    chat_about_error,
    extract_text_from_image,
    get_severity_color,
    get_severity_emoji,
    format_download_report,
)

st.set_page_config(
    page_title="AI Error Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #e2e8f0; }
    .stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #7B2FFF, #00D4FF) !important;
        color: #ffffff !important; border: none !important;
        border-radius: 10px !important; font-weight: 700 !important;
        font-size: 15px !important; padding: 12px 24px !important;
        box-shadow: 0 4px 15px rgba(123,47,255,0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #9B4FFF, #00E5FF) !important;
        color: #ffffff !important; transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(123,47,255,0.6) !important;
    }
    .stButton > button[kind="primary"]:active,
    .stButton > button[kind="primary"]:focus,
    .stButton > button[kind="primary"]:focus:not(:active) {
        background: linear-gradient(135deg, #6B1FEF, #00C4EE) !important;
        color: #ffffff !important; outline: none !important;
        box-shadow: 0 0 0 3px rgba(123,47,255,0.5) !important;
    }
    .stButton > button[kind="secondary"] {
        background: #1a1d27 !important; color: #00D4FF !important;
        border: 1.5px solid #00D4FF !important; border-radius: 10px !important;
        font-weight: 600 !important; transition: all 0.3s ease !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(0,212,255,0.15) !important; color: #00D4FF !important;
        border-color: #00D4FF !important;
    }
    .stButton > button[kind="secondary"]:active,
    .stButton > button[kind="secondary"]:focus {
        background: rgba(0,212,255,0.2) !important; color: #00D4FF !important;
        border-color: #00D4FF !important; outline: none !important;
    }
    .stButton > button {
        background: #1a1d27 !important; color: #e2e8f0 !important;
        border: 1.5px solid #2d3048 !important; border-radius: 10px !important;
        font-weight: 600 !important; transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: #2d3048 !important; color: #ffffff !important;
        border-color: #7B2FFF !important;
    }
    .stButton > button:active,
    .stButton > button:focus,
    .stButton > button:focus:not(:active) {
        background: #2d3048 !important; color: #ffffff !important;
        border-color: #7B2FFF !important; outline: none !important;
        box-shadow: 0 0 0 2px rgba(123,47,255,0.4) !important;
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00B050, #00D480) !important;
        color: #ffffff !important; border: none !important;
        border-radius: 10px !important; font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0,176,80,0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #00C060, #00E890) !important;
        color: #ffffff !important; transform: translateY(-2px) !important;
    }
    .stDownloadButton > button:active,
    .stDownloadButton > button:focus {
        background: linear-gradient(135deg, #009040, #00C070) !important;
        color: #ffffff !important; outline: none !important;
    }
    .stChatInput textarea {
        background: #1a1d27 !important; color: #e2e8f0 !important;
        border: 1.5px solid #2d3048 !important; border-radius: 10px !important;
    }
    .stChatInput textarea:focus {
        border-color: #7B2FFF !important;
        box-shadow: 0 0 0 2px rgba(123,47,255,0.3) !important;
    }
    .stTextArea textarea {
        background: #1a1d27 !important; color: #e2e8f0 !important;
        border: 1.5px solid #2d3048 !important; border-radius: 10px !important;
    }
    .stTextArea textarea:focus {
        border-color: #7B2FFF !important;
        box-shadow: 0 0 0 2px rgba(123,47,255,0.3) !important;
    }
    .stSelectbox > div > div {
        background: #1a1d27 !important; color: #e2e8f0 !important;
        border: 1.5px solid #2d3048 !important; border-radius: 10px !important;
    }
    .stFileUploader > div {
        background: #1a1d27 !important; border: 1.5px dashed #2d3048 !important;
        border-radius: 10px !important; color: #e2e8f0 !important;
    }
    .streamlit-expanderHeader {
        background: #1a1d27 !important; color: #e2e8f0 !important;
        border: 1px solid #2d3048 !important; border-radius: 10px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1d27 !important; border-radius: 10px !important;
        padding: 4px !important; gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; color: #888 !important;
        border-radius: 8px !important; font-weight: 600 !important;
        padding: 8px 16px !important; transition: all 0.2s !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg,#7B2FFF,#00D4FF) !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] {
        background: #0d1017 !important; border-right: 1px solid #1a1d27 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #1a1d27 !important; color: #e2e8f0 !important;
        border: 1px solid #2d3048 !important; width: 100% !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #2d3048 !important; color: #ffffff !important;
        border-color: #7B2FFF !important;
    }
    [data-testid="stSidebar"] .stButton > button:active,
    [data-testid="stSidebar"] .stButton > button:focus {
        background: #2d3048 !important; color: #ffffff !important;
        border-color: #7B2FFF !important; outline: none !important;
    }
    .stAlert { border-radius: 10px !important; border: none !important; }
    .main-title {
        font-size: 3rem; font-weight: 900;
        background: linear-gradient(90deg, #00D4FF, #7B2FFF, #FF6B6B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; text-align: center; padding: 10px 0;
    }
    .subtitle { text-align: center; color: #888; font-size: 1.1rem; margin-bottom: 20px; }
    .info-card { background: #1a1d27; border: 1px solid #2d3048; border-radius: 12px; padding: 20px; margin: 10px 0; }
    .stat-box { background: #1a1d27; border: 1px solid #2d3048; border-radius: 10px; padding: 15px; text-align: center; }
    .about-card { background: linear-gradient(135deg, #1a1d27, #0d1117); border: 1px solid #7B2FFF; border-radius: 16px; padding: 28px; margin: 10px 0; }
    .chat-user { background: #1e3a5f; border-radius: 10px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #00D4FF; }
    .chat-bot { background: #1a2332; border-radius: 10px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #7B2FFF; }
    .custom-divider { height: 2px; background: linear-gradient(90deg, #00D4FF, #7B2FFF, #FF6B6B); border: none; margin: 20px 0; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

defaults = {
    "current_result":  None,
    "chat_history":    [],
    "session_history": [],
    "error_count":     0,
    "show_about":      False,
    "screenshot_result": None,
    "screenshot_extracted": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:10px 0'>
        <div style='font-size:3rem'>🔍</div>
        <div style='font-size:1.3rem; font-weight:800;
             background:linear-gradient(90deg,#00D4FF,#7B2FFF);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            AI Error Detective
        </div>
        <div style='color:#888; font-size:0.8rem'>Powered by Groq LLaMA 3.3</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class='stat-box'>
            <div style='font-size:1.8rem;font-weight:800;color:#00D4FF'>{st.session_state.error_count}</div>
            <div style='color:#888;font-size:0.75rem'>Errors<br>Analyzed</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='stat-box'>
            <div style='font-size:1.8rem;font-weight:800;color:#7B2FFF'>{len(st.session_state.chat_history) // 2}</div>
            <div style='color:#888;font-size:0.75rem'>Follow-up<br>Questions</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### ⚙️ Error Platform")
    error_type = st.selectbox("Select platform:", [
        "SAP BTP", "CAP (Cloud Application Programming)", "ABAP Cloud",
        "ABAP On-Premise", "SAP Fiori / UI5", "SAP S/4HANA",
        "SAP Integration Suite", "SAP HANA", "SAP Build Apps", "Other SAP",
    ], label_visibility="collapsed")
    st.markdown("---")
    if st.session_state.session_history:
        st.markdown("### 🕐 Recent Errors")
        for i, item in enumerate(reversed(st.session_state.session_history[-5:])):
            emoji = get_severity_emoji(item["severity"])
            with st.expander(f"{emoji} {item['type']} — {item['time']}", expanded=False):
                st.caption(item["preview"])
    st.markdown("---")
    if st.button("🗑️ Clear Session", use_container_width=True):
        for key in ["current_result", "chat_history", "session_history", "error_count", "screenshot_result", "screenshot_extracted"]:
            st.session_state[key] = ([] if isinstance(st.session_state[key], list)
                                     else (0 if isinstance(st.session_state[key], int) else None))
        st.rerun()
    if st.button("ℹ️ About This App", use_container_width=True, type="secondary"):
        st.session_state.show_about = not st.session_state.show_about

# ── HEADER ──
st.markdown("<div class='main-title'>🔍 AI Error Detective</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Slash Debugging Time for BTP & ABAP Developers · Powered by Free AI</div>", unsafe_allow_html=True)
st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

# ── ABOUT ──
if st.session_state.show_about:
    st.markdown("""<div class='about-card'>
        <h2 style='color:#00D4FF;margin-top:0'>🎯 What is AI Error Detective?</h2>
        <p style='color:#ccc;font-size:1rem;line-height:1.7'>
            AI Error Detective is an intelligent debugging co-pilot built specifically for SAP developers.
            It uses state-of-the-art LLMs to instantly analyze cryptic SAP errors and provide clear,
            actionable fixes — saving hours of manual investigation.
        </p>
        <h3 style='color:#7B2FFF'>❓ The Problem It Solves</h3>
        <p style='color:#aaa'>SAP developers waste <b style='color:#FF6B6B'>2-4 hours per day</b>
        debugging cryptic error messages across BTP, CAP, ABAP, and Fiori.</p>
        <div style='text-align:center;margin-top:20px;padding:15px;background:#0d1117;border-radius:10px'>
            <span style='color:#888'>Built with </span><b style='color:#00D4FF'>Groq LLaMA 3.3</b>
            <span style='color:#888'> · </span><b style='color:#7B2FFF'>LangChain</b>
            <span style='color:#888'> · </span><b style='color:#FF6B6B'>Streamlit</b>
            <span style='color:#888'> · 100% Free AI APIs</span>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

# ── TABS ──
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Analyze Error", "📸 Upload Screenshot",
    "💬 Chat with Detective", "📋 Session History",
])

# ══ TAB 1 ══
with tab1:
    st.markdown("### 📝 Paste Your SAP Error")
    st.caption("Works with BTP, CAP, ABAP, Fiori errors — paste the full error message for best results")
    with st.expander("💡 Load a Sample Error to Test", expanded=False):
        s1, s2, s3 = st.columns(3)
        with s1:
            if st.button("📗 CAP Error", use_container_width=True):
                st.session_state["sample_error"] = (
                    "Error: SQLITE_ERROR: no such table: my_BookShop_Books\n"
                    "at /home/user/projects/bookshop/node_modules/@sap/cds/lib/db/sql-builder.js:123\n"
                    "CDS Build failed with error code: MODULE_NOT_FOUND\n"
                    "Service: CatalogService — entity: Books not deployed"
                )
        with s2:
            if st.button("📘 ABAP Error", use_container_width=True):
                st.session_state["sample_error"] = (
                    "Runtime Error: DYNPRO_SEND_IN_BACKGROUND\n"
                    "Short text: Screen output without connection to user\n"
                    "Program: ZTEST_REPORT\nInclude: ZTEST_REPORT\n"
                    "Row: 45, Module: USER_COMMAND_0100\n"
                    "ABAP Runtime Error occurred at: 25.01.2025 10:23:45"
                )
        with s3:
            if st.button("📙 BTP Error", use_container_width=True):
                st.session_state["sample_error"] = (
                    "CF CLI Error: Server error, status code: 502\n"
                    "App 'my-app' failed to start\nFAILED State: CRASHED\n"
                    "Error: Failed to fetch environment variables\n"
                    "VCAP_SERVICES binding error: Service 'hana' not found\n"
                    "Buildpack: nodejs_buildpack"
                )
    prefill = st.session_state.pop("sample_error", "")
    error_text = st.text_area("Error Message", value=prefill, height=200,
        placeholder="Paste your full error message here...\n\nExample:\nError: SQLITE_ERROR: no such table: Books\nCDS Build failed at module: CatalogService\n...",
        label_visibility="collapsed")
    if error_text:
        st.caption(f"📝 {len(error_text)} characters · Platform: **{error_type}**")
    b1, b2, b3 = st.columns([2, 1, 1])
    with b1:
        analyze_btn = st.button("🔍 Analyze Error Now", type="primary", use_container_width=True)
    with b2:
        quick_btn = st.button("⚡ Quick Fix", use_container_width=True)
    with b3:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    if clear_btn:
        st.session_state.current_result = None
        st.session_state.chat_history = []
        st.rerun()
    if quick_btn:
        if not error_text.strip():
            st.error("⚠️ Please paste an error message first.")
        else:
            with st.spinner("⚡ Getting quick fix..."):
                try:
                    quick = get_quick_fix(error_text, error_type)
                    st.markdown(f"""<div style='background:#1a2a1a;border:1px solid #00B050;
                        border-radius:10px;padding:16px;margin:10px 0'>
                        <b style='color:#00B050'>⚡ Quick Fix:</b><br>
                        <span style='color:#e2e8f0'>{quick}</span>
                    </div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    if analyze_btn:
        if not error_text.strip():
            st.error("⚠️ Please paste an error message before analyzing.")
        else:
            with st.spinner("🔍 AI Detective is investigating your error..."):
                try:
                    result = analyze_error(error_text, error_type)
                    st.session_state.current_result = result
                    st.session_state.chat_history = []
                    st.session_state.error_count += 1
                    st.session_state.session_history.append({
                        "severity": result["severity"], "type": error_type,
                        "preview": error_text[:80] + "...",
                        "time": datetime.now().strftime("%H:%M"), "result": result,
                    })
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    st.stop()
    if st.session_state.current_result:
        result = st.session_state.current_result
        severity = result["severity"]
        if not error_text.strip():
            st.markdown("""<div style='background:#1e3a5f;border:1px solid #00D4FF;
                border-radius:10px;padding:14px;margin:10px 0;text-align:center'>
                <b style='color:#00D4FF'>📸 Results from your uploaded screenshot</b>
            </div>""", unsafe_allow_html=True)
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
        sev_colors = {"CRITICAL": "#FF0000", "HIGH": "#FF6B00", "MEDIUM": "#FFB800", "LOW": "#00B050", "UNKNOWN": "#808080"}
        color = sev_colors.get(severity, "#808080")
        emoji = get_severity_emoji(severity)
        st.markdown(f"""<div style='background:linear-gradient(90deg,{color}22,transparent);
            border-left:4px solid {color};border-radius:8px;padding:16px;margin:10px 0'>
            <span style='font-size:1.3rem;font-weight:800;color:{color}'>{emoji} SEVERITY: {severity}</span>
            <span style='color:#888;margin-left:20px;font-size:0.9rem'>Platform: {result['error_type']}</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("### 🧠 Full Analysis")
        st.markdown(result["analysis"])
        st.markdown("---")
        report = format_download_report(result, st.session_state.chat_history)
        st.download_button(label="📥 Download Resolution Report", data=report,
            file_name=f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain", use_container_width=True)
        st.info("💬 Switch to **Chat with Detective** tab to ask follow-up questions!")

# ══ TAB 2 — Upload Screenshot (REDESIGNED) ══
with tab2:
    st.markdown("### 📸 Upload Error Screenshot")
    st.caption("Upload a screenshot of your SAP error — AI Vision will extract the text and analyze it")

    uploaded = st.file_uploader(
        "Upload error screenshot",
        type=["png", "jpg", "jpeg"],
        help="Screenshots from SAP GUI, BTP Cockpit, VS Code, etc.",
        key="screenshot_uploader"
    )

    if uploaded:
        # Show the screenshot full-width (clean, no clutter)
        st.image(uploaded, caption="Uploaded Screenshot", use_container_width=True)

        # Extract text (run once, store in session state)
        if st.session_state.screenshot_extracted is None:
            with st.spinner("🔍 AI Vision reading screenshot..."):
                extracted = extract_text_from_image(uploaded)
                st.session_state.screenshot_extracted = extracted

        extracted = st.session_state.screenshot_extracted

        if extracted and "not available" not in extracted.lower() and "Could not read" not in extracted:
            # ✅ Just show success — no text area
            st.success("✅ Text extracted successfully!")

            if st.button("🔍 Analyze This Error", type="primary", use_container_width=True, key="analyze_screenshot"):
                with st.spinner("🔍 AI Detective is investigating your error..."):
                    try:
                        result = analyze_error(extracted, error_type)
                        st.session_state.screenshot_result = result
                        st.session_state.current_result = result
                        st.session_state.chat_history = []
                        st.session_state.error_count += 1
                        st.session_state.session_history.append({
                            "severity": result["severity"], "type": error_type,
                            "preview": extracted[:80] + "...",
                            "time": datetime.now().strftime("%H:%M"), "result": result,
                        })
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")

            # Show analysis result inline on this tab
            if st.session_state.screenshot_result:
                result = st.session_state.screenshot_result
                severity = result["severity"]

                st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

                sev_colors = {"CRITICAL": "#FF0000", "HIGH": "#FF6B00", "MEDIUM": "#FFB800", "LOW": "#00B050", "UNKNOWN": "#808080"}
                color = sev_colors.get(severity, "#808080")
                emoji = get_severity_emoji(severity)

                st.markdown(f"""<div style='background:linear-gradient(90deg,{color}22,transparent);
                    border-left:4px solid {color};border-radius:8px;padding:16px;margin:10px 0'>
                    <span style='font-size:1.3rem;font-weight:800;color:{color}'>{emoji} SEVERITY: {severity}</span>
                    <span style='color:#888;margin-left:20px;font-size:0.9rem'>Platform: {result['error_type']}</span>
                </div>""", unsafe_allow_html=True)

                st.markdown("### 🧠 Full Analysis")
                st.markdown(result["analysis"])

                st.markdown("---")
                report = format_download_report(result, [])
                st.download_button(
                    label="📥 Download Resolution Report", data=report,
                    file_name=f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", use_container_width=True, key="dl_screenshot"
                )
                st.info("💬 Switch to **Chat with Detective** tab to ask follow-up questions!")
        else:
            st.error("⚠️ Could not extract text from the image. Please copy-paste the error text in the **Analyze Error** tab.")

    else:
        # Clear stored screenshot result when no file uploaded
        st.session_state.screenshot_extracted = None
        st.session_state.screenshot_result = None

# ══ TAB 3 ══
with tab3:
    st.markdown("### 💬 Chat with AI Error Detective")
    if not st.session_state.current_result:
        st.markdown("""<div style='text-align:center;padding:60px 20px;
             background:#1a1d27;border-radius:16px;border:1px dashed #2d3048'>
            <div style='font-size:3rem'>🔍</div>
            <h3 style='color:#888'>No Error Analyzed Yet</h3>
            <p style='color:#555'>Go to <b>Analyze Error</b> tab first, then come back here to chat.</p>
        </div>""", unsafe_allow_html=True)
    else:
        result = st.session_state.current_result
        st.caption(f"Discussing: **{result['error_type']}** · Severity: **{result['severity']}**")
        st.markdown("**💡 Quick Questions:**")
        q1, q2 = st.columns(2)
        suggestions = [
            "How do I prevent this in future?", "Which SAP Note is related?",
            "Explain the fix in simpler terms", "What transaction code should I check?",
            "Is there an alternative solution?", "How long will this fix take?",
        ]
        for i, s in enumerate(suggestions):
            with (q1 if i % 2 == 0 else q2):
                if st.button(s, key=f"q_{i}", use_container_width=True):
                    st.session_state["prefill_q"] = s
        st.markdown("---")
        if not st.session_state.chat_history:
            st.markdown("<div style='text-align:center;color:#555;padding:20px'>🤖 Ask anything about this error...</div>", unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""<div class='chat-user'>
                        <b style='color:#00D4FF'>👨‍💻 Developer:</b><br>
                        <span style='color:#eee'>{msg['content']}</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class='chat-bot'>
                        <b style='color:#7B2FFF'>🔍 AI Detective:</b><br>
                        <span style='color:#eee'>{msg['content']}</span>
                    </div>""", unsafe_allow_html=True)
        prefill_q = st.session_state.pop("prefill_q", "")
        user_input = st.chat_input("Ask a follow-up question...")
        question = prefill_q or user_input
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.spinner("🔍 Detective is thinking..."):
                try:
                    answer = chat_about_error(
                        error_text=result["error_text"],
                        previous_analysis=result["analysis"],
                        question=question,
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.session_state.chat_history.pop()
                    st.error(f"❌ Error: {str(e)}")
            st.rerun()
        if st.session_state.chat_history:
            st.markdown("---")
            dl1, dl2 = st.columns(2)
            with dl1:
                report = format_download_report(result, st.session_state.chat_history)
                st.download_button("📥 Download Full Report", data=report,
                    file_name=f"resolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", use_container_width=True)
            with dl2:
                if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
                    st.session_state.chat_history = []
                    st.rerun()

# ══ TAB 4 ══
with tab4:
    st.markdown("### 📋 Session Error History")
    if not st.session_state.session_history:
        st.markdown("""<div style='text-align:center;padding:60px 20px;
             background:#1a1d27;border-radius:16px;border:1px dashed #2d3048'>
            <div style='font-size:3rem'>📋</div>
            <h3 style='color:#888'>No History Yet</h3>
            <p style='color:#555'>Analyzed errors will appear here.</p>
        </div>""", unsafe_allow_html=True)
    else:
        total = len(st.session_state.session_history)
        critical = sum(1 for h in st.session_state.session_history if h["severity"] == "CRITICAL")
        high = sum(1 for h in st.session_state.session_history if h["severity"] == "HIGH")
        m1, m2, m3, m4 = st.columns(4)
        for col, label, val, color in [
            (m1, "Total", total, "#00D4FF"), (m2, "Critical", critical, "#FF0000"),
            (m3, "High", high, "#FF6B00"), (m4, "Resolved", total, "#00B050"),
        ]:
            with col:
                st.markdown(f"""<div class='stat-box'>
                    <div style='font-size:2rem;font-weight:800;color:{color}'>{val}</div>
                    <div style='color:#888;font-size:0.8rem'>{label}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown("---")
        for i, item in enumerate(reversed(st.session_state.session_history)):
            emoji = get_severity_emoji(item["severity"])
            with st.expander(f"{emoji} [{item['severity']}] {item['type']} — {item['time']}", expanded=False):
                st.caption(f"**Error:** {item['preview']}")
                st.markdown(item["result"]["analysis"])
                report = format_download_report(item["result"], [])
                st.download_button("📥 Download", data=report,
                    file_name=f"error_{i}.txt", mime="text/plain", key=f"dl_{i}")

st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
st.markdown("""<div style='text-align:center;color:#555;padding:10px;font-size:0.85rem'>
    🔍 <b style='color:#00D4FF'>AI Error Detective</b> · Built for SAP DCOM 2025 ·
    Powered by <b style='color:#7B2FFF'>Groq LLaMA 3.3</b> +
    <b style='color:#FF6B6B'>LangChain</b> + <b style='color:#00D4FF'>Streamlit</b> · 100% Free AI Tools
</div>""", unsafe_allow_html=True)