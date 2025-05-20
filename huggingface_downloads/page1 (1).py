import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from streamlit_chat import message
import time
import random
import os
api = os.environ.get("api_key")

def text():
    st.markdown("""
                <style>
                    .anim-typewriter {
                        animation: typewriter 3s steps(40) 1s 1 normal both, blinkTextCursor 800ms steps(40) infinite normal;
                        overflow: hidden;
                        white-space: nowrap;
                        border-right: 3px solid;
                        font-family: serif;
                        font-size: 0.9em;
                    }
                    @keyframes typewriter {
                        from {
                            width: 0;
                        }
                        to {
                            width: 100%;
                            height: 100%
                        }
                    }
                    @keyframes blinkTextCursor {
                        from {
                            border-right-color: rgba(255, 255, 255, 0.75);
                        }
                        to {
                            border-right-color: transparent;
                        }
                    }
                </style>
            """, unsafe_allow_html=True)
    text ="Hello 👋, how may I assist you today?"
    animated_output = f'<div class="line-1 anim-typewriter">{text}</div>'

    with st.chat_message("assistant").markdown(animated_output,unsafe_allow_html=True ):
        st.markdown(animated_output,unsafe_allow_html=True)
    apiKey = api
    msgs = StreamlitChatMessageHistory(key="special_app_key")

    memory = ConversationBufferMemory(memory_key="history", chat_memory=msgs)
    if len(msgs.messages) == 0:
        msgs.add_ai_message("How can I help you?")
    template = """You are an AI chatbot having a conversation with a human.

    {history}
    Human: {human_input}
    AI: """
    prompt = PromptTemplate(input_variables=["history", "human_input"], template=template)
    llm_chain = LLMChain( llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=apiKey), prompt=prompt, memory = memory)

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Say something")

    if prompt:
        with st.chat_message("user").markdown(prompt):
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )
        # Custom HTML and CSS for three-dot animation
        spinner_html = """
        <div class="col-3">
        <div class="snippet" data-title="dot-pulse">
          <div class="stage">
            <div class="dot-pulse"></div>
          </div>
        </div>
      </div>
        """

        spinner_css = """
        .dot-pulse {
  position: relative;
  left: -9999px;

  width: 10px;
  height: 10px;
  border-radius: 5px;
  background-color: #9880ff;
  color: #9880ff;
  box-shadow: 9999px 0 0 -5px;
  animation: dot-pulse 1.5s infinite linear;
  animation-delay: 0.25s;
}
.dot-pulse::before, .dot-pulse::after {
  content: "";
  display: inline-block;
  position: absolute;
  top: 0;
  width: 10px;
  height: 10px;
  border-radius: 5px;
  background-color: #9880ff;
  color: #9880ff;
}
.dot-pulse::before {
  box-shadow: 9984px 0 0 -5px;
  animation: dot-pulse-before 1.5s infinite linear;
  animation-delay: 0s;
}
.dot-pulse::after {
  box-shadow: 10014px 0 0 -5px;
  animation: dot-pulse-after 1.5s infinite linear;
  animation-delay: 0.5s;
}

@keyframes dot-pulse-before {
  0% {
    box-shadow: 9984px 0 0 -5px;
  }
  30% {
    box-shadow: 9984px 0 0 2px;
  }
  60%, 100% {
    box-shadow: 9984px 0 0 -5px;
  }
}
@keyframes dot-pulse {
  0% {
    box-shadow: 9999px 0 0 -5px;
  }
  30% {
    box-shadow: 9999px 0 0 2px;
  }
  60%, 100% {
    box-shadow: 9999px 0 0 -5px;
  }
}
@keyframes dot-pulse-after {
  0% {
    box-shadow: 10014px 0 0 -5px;
  }
  30% {
    box-shadow: 10014px 0 0 2px;
  }
  60%, 100% {
    box-shadow: 10014px 0 0 -5px;
  }
}
        """

        st.markdown(f'<style>{spinner_css}</style>', unsafe_allow_html=True)
        st.markdown(spinner_html, unsafe_allow_html=True)

        for chunk in llm_chain.stream(prompt):
            text_output = chunk.get("text", "")
        st.markdown('<style>.dot-pulse { visibility: hidden; }</style>', unsafe_allow_html=True)

        with st.chat_message("assistant").markdown(text_output):
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": text_output
                }
            )

        #with st.chat_message("assistant"):
            #message_placeholder = st.empty()
            #full_response = ""
            #assistant_response = random.choice(
            #[
                #"Hello there! How can I assist you today?",
                #"Hi, human! Is there anything I can help you with?",
               # "Do you need help?",
           # ]
      #  )
        # Simulate stream of response with milliseconds delay
           # for chunk in text_output.split():
              #  full_response += chunk + " "
           #     time.sleep(0.05)
            # Add a blinking cursor to simulate typing
          #      message_placeholder.markdown(full_response + "▌")
        #    message_placeholder.markdown(full_response)
    # Add assistant response to chat history
      #  st.session_state.messages.append({"role": "assistant", "content": full_response})
