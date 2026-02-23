"""
Financial Advisor Chatbot — Streamlit UI

Production UI features:
- Chat-style interface with message history
- Session isolation (each browser tab = independent session)
- Loading indicators during API calls
- Error handling with user-friendly messages
- New conversation button
- Responsive layout
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to Python path so 'app' package is importable
# when Streamlit runs this file directly (streamlit run app/main.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid

import streamlit as st

from app.core.exceptions import ChatbotError
from app.memory.conversation import ConversationMemory
from app.services.chat_service import ChatService


# ── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="FinBot — Financial Advisor",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS for Premium Look ─────────────────────────────────
st.markdown(
    """
    <style>
    /* Main container */
    .stApp {
        max-width: 900px;
        margin: 0 auto;
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
        border-bottom: 2px solid #1a73e8;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        color: #1a73e8;
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: #5f6368;
        font-size: 0.95rem;
    }

    /* Chat messages */
    .stChatMessage {
        padding: 0.75rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }

    /* Disclaimer styling */
    .disclaimer-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        color: #856404;
        margin-top: 1rem;
    }

    /* Sidebar info */
    .sidebar-info {
        font-size: 0.85rem;
        color: #5f6368;
        padding: 0.5rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session State Initialization ────────────────────────────────
def init_session_state() -> None:
    """
    Initialize Streamlit session state for this user session.

    Each browser tab gets its own session_id, memory, and service instance.
    This ensures complete session isolation.
    """
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
    """Render sidebar with controls and information."""
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

        st.markdown("## 📊 Session Info")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
        st.markdown(f"**Turns:** {st.session_state.memory.turn_count}")
        st.markdown(f"**Est. Tokens:** {st.session_state.memory.total_tokens:,}")

        st.divider()

        st.markdown("## 💡 Topics I Can Help With")
        st.markdown(
            """
            - 💰 Personal Finance
            - 📈 Investment Concepts
            - 🏦 Retirement Planning
            - 💳 Debt Management
            - 📋 Tax Concepts
            - 🛡️ Insurance Basics
            """
        )

        st.divider()

        st.markdown(
            '<div class="sidebar-info">'
            "⚠️ This is an educational tool. Not financial advice."
            "</div>",
            unsafe_allow_html=True,
        )


# ── Main Chat Interface ────────────────────────────────────────
def render_header() -> None:
    """Render the application header."""
    st.markdown(
        """
        <div class="main-header">
            <h1>💰 FinBot</h1>
            <p>Your AI-Powered Financial Education Assistant</p>
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
        # Display user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response with loading indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
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

        # Save assistant response to session
        st.session_state.messages.append({"role": "assistant", "content": response})


# ── App Entry Point ─────────────────────────────────────────────
def main() -> None:
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    render_header()

    # Show welcome message if no messages yet
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            welcome = (
                "Welcome! I'm **FinBot**, your Financial Advisor Assistant. 👋\n\n"
                "I can help you understand:\n"
                "- 💰 **Personal Finance** — budgeting, saving, emergency funds\n"
                "- 📈 **Investing** — stocks, bonds, mutual funds, ETFs\n"
                "- 🏦 **Retirement** — 401(k), IRA, planning strategies\n"
                "- 💳 **Debt Management** — payoff strategies, credit scores\n"
                "- 📋 **Tax Concepts** — deductions, brackets, planning\n"
                "- 🛡️ **Insurance** — types, coverage, planning\n\n"
                "What financial topic would you like to explore today?\n\n"
                "⚠️ *Disclaimer: I provide educational information only, not "
                "personalized financial advice. Please consult a qualified "
                "financial advisor for decisions specific to your situation.*"
            )
            st.markdown(welcome)

    render_chat_history()
    handle_user_input()


if __name__ == "__main__":
    main()
