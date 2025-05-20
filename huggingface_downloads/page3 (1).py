import streamlit as st

from langchain_google_genai import ChatGoogleGenerativeAI

import time
import os

def details():
    api = os.environ.get("api_key")
    apiKey = api
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=apiKey)
    st.header("Introducing Gemini")
    with st.chat_message("assistant"):
        for chunk in llm.stream("Tell me about google gemini ai model"):
            st.write(chunk.content)
