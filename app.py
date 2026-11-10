
# ============================================================
# LONDON WEATHER AI AGENT
# STREAMLIT FRONTEND
# ============================================================

import streamlit as st

from agent import run_agent


# ============================================================
# STEP 1: CONFIGURE STREAMLIT PAGE
# ============================================================

st.set_page_config(

    page_title="London Weather AI Agent",

    page_icon="🌦️",

    layout="centered"

)


# ============================================================
# STEP 2: DISPLAY APPLICATION TITLE
# ============================================================

st.title("🌦️ London Weather AI Agent")

st.write(
    "Your AI-powered weather assistant. "
    "Ask about current weather and forecasts."
)

st.divider()


# ============================================================
# STEP 3: INITIALIZE CONVERSATION HISTORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# STEP 4: DISPLAY PREVIOUS CONVERSATION
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# ============================================================
# STEP 5: GET USER INPUT
# ============================================================

user_question = st.chat_input(
    "Ask about the weather..."
)


# ============================================================
# STEP 6: CONNECT TO AGENT HARNESS
# ============================================================

if user_question:

    # Display user question

    with st.chat_message("user"):

        st.markdown(user_question)


    # Prepare conversation history

    chat_history = st.session_state.messages + [

        {
            "role": "user",

            "content": user_question

        }

    ]


    # Execute Agent Harness

    with st.chat_message("assistant"):

        with st.spinner("Weather Agent is thinking..."):

            try:

                response = run_agent(

                    user_question=user_question,

                    chat_history=chat_history

                )

                st.markdown(response)

            except Exception as error:

                response = f"An error occurred: {error}"

                st.error(response)


    # Save conversation

    st.session_state.messages.append({

        "role": "user",

        "content": user_question

    })

    st.session_state.messages.append({

        "role": "assistant",

        "content": response

    })


# ============================================================
# STEP 7: SIDEBAR
# ============================================================

st.sidebar.title("About This Agent")

st.sidebar.write(
    """
    **LLM:** Groq GPT-OSS-20B

    **Weather Tool:** Open-Meteo

    **Geocoding:** Open-Meteo

    **Backend:** Custom Agent Harness

    **Frontend:** Streamlit
    """
)


# ============================================================
# STEP 8: CLEAR CONVERSATION
# ============================================================

if st.sidebar.button("Clear Conversation"):

    st.session_state.messages = []

    st.rerun()


# ============================================================
# END OF STREAMLIT APP
# ============================================================
