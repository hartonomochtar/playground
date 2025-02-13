import streamlit as st
import json
from agents.triage import TriageAgent

# App title
st.set_page_config(page_title="Troubleshooting Agent")

assistant_image_url = "https://upload.wikimedia.org/wikipedia/commons/b/bc/Telkomsel_2021_icon.svg"

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Hello, I am a troubleshooting agent. How may I assist you today?\n\n As a start, please provide the **ITOC WA chat and sample logs**."}]

if "agent" not in st.session_state:
    st.session_state.agent = TriageAgent()

# Custom CSS for chat layout
st.markdown(
    """
<style>
    .st-emotion-cache-1c7y2kd {
        flex-direction: row-reverse;
    }
    .st-emotion-cache-1ghhuty {
        background-color: orange !important;
    }
</style>
""",
    unsafe_allow_html=True,
)



def query_special_sop(service_name):
    """Query memory database if any special SOP needs to be performed for service_name."""
    print("Querying memory database if any special SOP needs to be performed for ", service_name)
    
    special_sop = ""
    
    if "rbt" in service_name.lower():
        special_sop = "Perform health check for Eluon."
    elif "productoffer" in service_name.lower():
        special_sop = "Perform health check for SCV."
    
    return special_sop


def eluon_health_check():
    """Perform health check for Eluon."""

    print("Performing curl test to Eluon")
    return """
        curl -X GET "https://rbtapi.nuon.id:8200" \
        -G \
        --data-urlencode "msisdn=1234567890" \
        --max-time 10

        HTTP/1.1 504 Request Timeout
        Content-Type: application/json
        Content-Length: 78
        Connection: keep-alive

        {
            "error": "Request timeout",
            "message": "The request took too long to process."
        }
    """

def scv_health_check():
    """Perform health check for SCV."""

    print("Performing curl test to SCV")
    return """
        curl -X GET "https://scv-bs-v2.digitalcore.com:8200" \
        -G \
        --data-urlencode "msisdn=1234567890" \
        --max-time 10 \
        -i

        HTTP/1.1 503 Service Unavailable
        Content-Type: application/json
        Content-Length: 100
        Connection: keep-alive
        Date: Tue, 06 Feb 2025 00:00:00 GMT

        {
            "error": "Service Unavailable",
            "message": "The server is temporarily unavailable, please try again later."
        }
    """

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'last_user_message' not in st.session_state:
    st.session_state.last_user_message = ''

# Display previous messages
for message in st.session_state.messages:
    #print(message)
    if message["content"]:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant", avatar=assistant_image_url):
                st.markdown(message["content"], unsafe_allow_html=True)

# Get user input
user_message = st.chat_input("Type your message")

if user_message and user_message != st.session_state.last_user_message:

    # Update last_user_message
    st.session_state.last_user_message = user_message

    # Add user message to messages
    st.session_state.messages.append({"role": "user", "content": user_message})
    messages = st.session_state.messages.copy()
    with st.chat_message("user"):
        st.markdown(user_message)

    # Run assistant response
    with st.spinner("Thinking.....", show_time=True):
        print("Executing Agent: " + st.session_state.agent.name)
        response = st.session_state.agent.execute(messages)
        st.session_state.agent = response.agent
        st.session_state.messages.extend(response.messages)

        # Display new messages
        for message in response.messages:
            #print(message)
            if message["content"]:
                if message["role"] == "assistant":
                    with st.chat_message("assistant", avatar=assistant_image_url):
                        st.markdown(message["content"], unsafe_allow_html=True)