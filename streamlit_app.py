
import os
import json
import requests
import streamlit as st


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Ask Sphere | Free Fire Esports AI",
    page_icon="🎮",
    layout="centered",
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1/chat"

try:
    API_URL = st.secrets.get("API_URL", DEFAULT_API_URL)
except Exception:
    API_URL = os.getenv("API_URL", DEFAULT_API_URL)

REQUEST_TIMEOUT = 120


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


# --------------------------------------------------
# RESPONSE PARSER
# --------------------------------------------------

def extract_answer(data):
    """
    Extract a readable answer from common FastAPI response formats.
    """

    if isinstance(data, str):
        return data

    if isinstance(data, dict):

        possible_keys = [
            "answer",
            "response",
            "reply",
            "message",
            "content",
            "output",
            "result",
        ]

        for key in possible_keys:

            value = data.get(key)

            if isinstance(value, str):
                return value

            if isinstance(value, dict):
                nested_answer = extract_answer(value)

                if nested_answer:
                    return nested_answer

        return json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )

    return str(data)


# --------------------------------------------------
# API REQUEST
# --------------------------------------------------

def ask_sphere(question):

    payload = {
        "question": question,
        "conversation_id": st.session_state.conversation_id,
    }

    response = requests.post(
        API_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    # Update conversation ID if the backend returns one.
    if isinstance(data, dict):

        returned_conversation_id = data.get(
            "conversation_id"
        )

        if returned_conversation_id:
            st.session_state.conversation_id = (
                returned_conversation_id
            )

    return extract_answer(data)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("🎮 Ask Sphere")

    st.caption(
        "AI-powered Free Fire esports assistant"
    )

    st.divider()

    st.subheader("About")

    st.write(
        """
        Ask Sphere helps you explore Free Fire esports
        information using your RAG-powered backend.
        """
    )

    st.divider()

    # st.subheader("Backend")

    # st.code(API_URL)

    if st.button(
        "🗑️ New Chat",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.conversation_id = None

        st.rerun()

    st.divider()

    st.caption(
        "Powered by ESPORTSPHERE"
    )


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.title("🎮 Ask Sphere")

st.markdown(
    """
    ### Your Free Fire Esports AI Assistant

    Ask questions about tournaments, teams, players,
    esports history and competitive Free Fire.
    """
)

st.divider()


# --------------------------------------------------
# SUGGESTED QUESTIONS
# --------------------------------------------------

if not st.session_state.messages:

    st.subheader("Try asking")

    suggestions = [
        "Tell me about Free Fire esports tournaments.",
        "Which teams are popular in Free Fire esports?",
        "Explain the Free Fire competitive scene.",
        "What information is available about Free Fire teams?",
    ]

    cols = st.columns(2)

    for index, suggestion in enumerate(suggestions):

        with cols[index % 2]:

            if st.button(
                suggestion,
                use_container_width=True,
                key=f"suggestion_{index}",
            ):

                st.session_state.pending_question = (
                    suggestion
                )

                st.rerun()


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

question = st.chat_input(
    "Ask anything about Free Fire esports..."
)

# Handle suggested questions.
if "pending_question" in st.session_state:

    question = st.session_state.pop(
        "pending_question"
    )


# --------------------------------------------------
# PROCESS USER QUESTION
# --------------------------------------------------

if question:

    question = question.strip()

    if question:

        # Display user message.
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        # Generate assistant response.
        with st.chat_message("assistant"):

            with st.spinner(
                "Ask Sphere is searching esports knowledge..."
            ):

                try:

                    answer = ask_sphere(question)

                    st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                except requests.exceptions.Timeout:

                    error_message = (
                        "The backend took too long to respond. "
                        "Please try again."
                    )

                    st.error(error_message)

                except requests.exceptions.ConnectionError:

                    error_message = (
                        "Unable to connect to the Ask Sphere backend. "
                        "Please check whether the FastAPI server is running."
                    )

                    st.error(error_message)

                except requests.exceptions.HTTPError as error:

                    error_message = (
                        f"Backend returned an HTTP error: {error}"
                    )

                    try:
                        details = error.response.json()

                        st.error(
                            f"{error_message}\n\n"
                            f"Details: {details}"
                        )

                    except Exception:

                        st.error(error_message)

                except Exception as error:

                    st.error(
                        f"Unexpected error: {error}"
                    )
