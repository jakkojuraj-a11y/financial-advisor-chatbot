"""
Financial Advisor Chatbot — Streamlit UI (Premium Edition)

Production UI features:
- Stunning dark theme with glassmorphism
- Animated gradient header with glow effects
- Premium chat bubbles with micro-animations
- Topic quick-action chips
- Session stats dashboard in sidebar
- Fully responsive layout
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid

import streamlit as st

from app.core.exceptions import ChatbotError
from app.memory.conversation import ConversationMemory
from app.services.chat_service import ChatService


# ── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="FinBot — AI Financial Advisor",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Premium CSS ─────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── ROOT VARIABLES ── */
    :root {
        --bg-dark: #0b0f19;
        --bg-card: rgba(17, 24, 39, 0.65);
        --glass-border: rgba(255, 255, 255, 0.06);
        --gold: #f59e0b;
        --gold-dim: rgba(245, 158, 11, 0.15);
        --cyan: #06b6d4;
        --cyan-dim: rgba(6, 182, 212, 0.12);
        --purple: #a78bfa;
        --green: #34d399;
        --rose: #fb7185;
        --text-main: #f1f5f9;
        --text-sub: #94a3b8;
        --text-muted: #64748b;
    }

    /* ── GLOBAL ── */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .stApp {
        max-width: 960px;
        margin: 0 auto;
    }

    /* Dark theme overrides */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0b0f19 0%, #0f172a 40%, #0b0f19 100%) !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #0b0f19) !important;
        border-right: 1px solid var(--glass-border) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-sub) !important;
    }

    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] strong {
        color: var(--text-main) !important;
    }

    /* ── HERO HEADER ── */
    .hero-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        margin-bottom: 0.5rem;
        position: relative;
        overflow: hidden;
    }

    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(245,158,11,0.06) 0%, transparent 50%),
                    radial-gradient(circle at 70% 30%, rgba(6,182,212,0.06) 0%, transparent 50%);
        animation: subtle-rotate 20s linear infinite;
    }

    @keyframes subtle-rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .hero-header .logo {
        font-size: 3.2rem;
        margin-bottom: 0.2rem;
        display: block;
        position: relative;
        filter: drop-shadow(0 0 20px rgba(245,158,11,0.4));
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }

    .hero-header h1 {
        font-size: 2.4rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin: 0.2rem 0 0.4rem 0;
        position: relative;
        background: linear-gradient(135deg, #f1f5f9 0%, #f59e0b 50%, #06b6d4 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 4s linear infinite;
    }

    @keyframes shimmer {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }

    .hero-header .subtitle {
        font-size: 1rem;
        color: var(--text-sub);
        font-weight: 400;
        position: relative;
        margin: 0;
    }

    .hero-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--cyan), transparent);
        border: none;
        margin: 0 2rem 1rem;
        border-radius: 2px;
        opacity: 0.6;
    }

    /* ── TOPIC CHIPS ── */
    .topic-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        padding: 0.5rem 0 1.5rem;
        position: relative;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 100px;
        font-size: 0.82rem;
        font-weight: 600;
        border: 1px solid var(--glass-border);
        background: var(--bg-card);
        color: var(--text-sub);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        cursor: default;
    }

    .chip:hover {
        border-color: var(--gold);
        color: var(--gold);
        background: var(--gold-dim);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(245,158,11,0.15);
    }

    /* ── CHAT MESSAGES ── */
    [data-testid="stChatMessage"] {
        background: var(--bg-card) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 12px !important;
        animation: msg-in 0.4s ease-out;
    }

    @keyframes msg-in {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {
        color: var(--text-main) !important;
        font-size: 0.97rem !important;
        line-height: 1.7 !important;
    }

    [data-testid="stChatMessage"] strong {
        color: var(--gold) !important;
    }

    [data-testid="stChatMessage"] code {
        background: rgba(0,0,0,0.3) !important;
        color: var(--cyan) !important;
        padding: 2px 8px !important;
        border-radius: 6px !important;
    }

    /* ── CHAT INPUT ── */
    [data-testid="stChatInput"] {
        border-color: var(--glass-border) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 14px !important;
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 14px 20px !important;
        transition: border-color 0.3s !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(245,158,11,0.15) !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-muted) !important;
    }

    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, var(--gold), #d97706) !important;
        border-radius: 12px !important;
        color: #000 !important;
    }

    /* ── SPINNER ── */
    .stSpinner > div {
        border-top-color: var(--gold) !important;
    }
    .stSpinner > div > span {
        color: var(--text-sub) !important;
    }

    /* ── SIDEBAR BUTTON ── */
    [data-testid="stSidebar"] button {
        background: linear-gradient(135deg, var(--gold-dim), var(--cyan-dim)) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--gold) !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
    }

    [data-testid="stSidebar"] button:hover {
        border-color: var(--gold) !important;
        box-shadow: 0 0 20px rgba(245,158,11,0.15) !important;
        transform: translateY(-1px) !important;
    }

    /* ── SIDEBAR STATS ── */
    .stat-card {
        background: var(--bg-card);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .stat-card .label {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stat-card .value {
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--gold);
    }

    /* ── DISCLAIMER ── */
    .disclaimer {
        text-align: center;
        padding: 12px 20px;
        font-size: 0.78rem;
        color: var(--text-muted);
        border-top: 1px solid var(--glass-border);
        margin-top: 1.5rem;
    }

    .disclaimer .warn-icon {
        color: var(--gold);
        font-weight: 700;
    }

    /* ── WELCOME CARD ── */
    .welcome-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 10px;
        margin: 1rem 0;
    }

    .welcome-item {
        background: var(--bg-card);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 14px 16px;
        transition: all 0.3s;
    }

    .welcome-item:hover {
        border-color: var(--gold);
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(245,158,11,0.08);
    }

    .welcome-item .wi-icon {
        font-size: 1.4rem;
        margin-bottom: 6px;
        display: block;
    }

    .welcome-item .wi-title {
        font-weight: 700;
        font-size: 0.92rem;
        color: var(--text-main);
        margin-bottom: 2px;
    }

    .welcome-item .wi-desc {
        font-size: 0.8rem;
        color: var(--text-muted);
        line-height: 1.4;
    }

    /* ── HIDE STREAMLIT EXTRAS ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session State Initialization ────────────────────────────────
def init_session_state() -> None:
    """Initialize Streamlit session state for this user session."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory()
    if "chat_service" not in st.session_state:
        st.session_state.chat_service = ChatService(
            memory=st.session_state.memory,
            session_id=st.session_state.session_id,
        )
    if "messages" not in st.session_state:
        st.session_state.messages = []


# ── Sidebar ─────────────────────────────────────────────────────
def render_sidebar() -> None:
    """Render premium sidebar with stats and controls."""
    with st.sidebar:
        st.markdown("## ⚙️ Controls")

        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.chat_service.clear_conversation()
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.memory = ConversationMemory()
            st.session_state.chat_service = ChatService(
                memory=st.session_state.memory,
                session_id=st.session_state.session_id,
            )
            st.rerun()

        st.divider()
        st.markdown("## 📊 Session Dashboard")

        msg_count = len(st.session_state.messages)
        turns = st.session_state.memory.turn_count
        tokens = st.session_state.memory.total_tokens

        st.markdown(
            f"""
            <div class="stat-card">
                <span class="label">Messages</span>
                <span class="value">{msg_count}</span>
            </div>
            <div class="stat-card">
                <span class="label">Turns</span>
                <span class="value">{turns}</span>
            </div>
            <div class="stat-card">
                <span class="label">Est. Tokens</span>
                <span class="value">{tokens:,}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("## 🛡️ Security Status")
        st.markdown("✅ Prompt injection defense active")
        st.markdown("✅ Rate limiting enabled")
        st.markdown("✅ Input sanitization on")

        st.divider()
        st.markdown(
            '<div style="font-size:0.78rem; color:#64748b; text-align:center; padding:8px;">'
            "⚠️ Educational tool only · Not financial advice"
            "</div>",
            unsafe_allow_html=True,
        )


# ── Main Chat Interface ────────────────────────────────────────
def render_header() -> None:
    """Render premium animated header."""
    st.markdown(
        """
        <div class="hero-header">
            <span class="logo">💰</span>
            <h1>FinBot</h1>
            <p class="subtitle">Your AI-Powered Financial Education Assistant</p>
        </div>
        <hr class="hero-divider">
        """,
        unsafe_allow_html=True,
    )


def render_topic_chips() -> None:
    """Render floating topic chips below header."""
    st.markdown(
        """
        <div class="topic-chips">
            <span class="chip">💰 Personal Finance</span>
            <span class="chip">📈 Investing</span>
            <span class="chip">🏦 Retirement</span>
            <span class="chip">💳 Debt</span>
            <span class="chip">📋 Tax</span>
            <span class="chip">🛡️ Insurance</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    """Display all previous messages in the conversation."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_user_input() -> None:
    """Handle new user input from the chat box."""
    if prompt := st.chat_input("Ask me about personal finance, investing, retirement..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("✨ Analyzing your question..."):
                try:
                    response = st.session_state.chat_service.process_message(prompt)
                except ChatbotError as e:
                    response = e.user_message
                except Exception:
                    response = (
                        "I apologize, but something went wrong. "
                        "Please try again or start a new conversation."
                    )
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


# ── App Entry Point ─────────────────────────────────────────────
def main() -> None:
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    render_header()

    if not st.session_state.messages:
        render_topic_chips()
        with st.chat_message("assistant"):
            st.markdown(
                "**Hey there! 👋 I'm FinBot**, your AI financial education assistant.\n\n"
                "I'm here to help you understand complex financial concepts in simple terms. "
                "Pick a topic above or ask me anything about:\n\n"
            )
            st.markdown(
                """
                <div class="welcome-grid">
                    <div class="welcome-item">
                        <span class="wi-icon">💰</span>
                        <div class="wi-title">Personal Finance</div>
                        <div class="wi-desc">Budgeting, saving, emergency funds</div>
                    </div>
                    <div class="welcome-item">
                        <span class="wi-icon">📈</span>
                        <div class="wi-title">Investing</div>
                        <div class="wi-desc">Stocks, bonds, ETFs, mutual funds</div>
                    </div>
                    <div class="welcome-item">
                        <span class="wi-icon">🏦</span>
                        <div class="wi-title">Retirement</div>
                        <div class="wi-desc">401(k), IRA, planning strategies</div>
                    </div>
                    <div class="welcome-item">
                        <span class="wi-icon">💳</span>
                        <div class="wi-title">Debt Management</div>
                        <div class="wi-desc">Payoff strategies, credit scores</div>
                    </div>
                    <div class="welcome-item">
                        <span class="wi-icon">📋</span>
                        <div class="wi-title">Tax Concepts</div>
                        <div class="wi-desc">Deductions, brackets, planning</div>
                    </div>
                    <div class="welcome-item">
                        <span class="wi-icon">🛡️</span>
                        <div class="wi-title">Insurance</div>
                        <div class="wi-desc">Types, coverage basics</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="disclaimer">'
            '<span class="warn-icon">⚠️</span> '
            "I provide educational information only — not personalized financial advice. "
            "Always consult a qualified financial advisor for your specific situation."
            "</div>",
            unsafe_allow_html=True,
        )

    render_chat_history()
    handle_user_input()


if __name__ == "__main__":
    main()
