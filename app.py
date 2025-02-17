"""
app.py
"""
import streamlit as st
import re  # ★ 追加：正規表現ライブラリ
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock 

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_ID"]

# Initialise the OpenAI client, and retrieve the assistant
client = OpenAI(api_key=OPENAI_API_KEY)
assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)

# Initialise session state to store conversation history locally to display on UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Title
st.title("GOTO AI β版 ver0.1")

# Display messages in chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Textbox and streaming process
if user_query := st.chat_input("Ask me a question"):

    # Create a new thread if it does not exist
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # Display the user's query
    with st.chat_message("user"):
        st.markdown(user_query)

    # Store the user's query into the history
    st.session_state.chat_history.append(
        {"role": "user", "content": user_query}
    )
    
    # Add user query to the thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_query
    )

    # Stream the assistant's reply
    with st.chat_message("assistant"):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            stream=True
        )
        
        # Empty container to display the assistant's reply
        assistant_reply_box = st.empty()
        
        # A blank string to store the assistant's reply
        assistant_reply = ""

        # Regex pattern to remove 【...】-enclosed text
        regex_pattern = r"【.*?】"

        # Iterate through the stream 
        for event in stream:
            # Here, we only consider if there's a delta text
            if isinstance(event, ThreadMessageDelta):
                if isinstance(event.data.delta.content[0], TextDeltaBlock):
                    # Get the current chunk of text
                    text_chunk = event.data.delta.content[0].text.value

                    # Remove 【...】 from the chunk
                    cleaned_chunk = re.sub(regex_pattern, '', text_chunk)

                    # Append to the total assistant reply
                    assistant_reply += cleaned_chunk

                    # Update the displayed text
                    assistant_reply_box.empty()
                    assistant_reply_box.markdown(assistant_reply)
        
        # Once the stream is over, update chat history with cleaned text
        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_reply}
        )
