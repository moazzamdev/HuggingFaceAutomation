import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_chat import message
from PIL import Image
import base64
import io
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
import os

# Streamlit app
def image():
    key = os.environ.get("api_key")
    st.markdown("""
                        <style>
                            .anim-typewriter {
                                animation: typewriter 3s steps(40) 1s 1 normal both, blinkTextCursor 800ms steps(40) infinite normal;
                                overflow: hidden;
                                white-space: nowrap;
                                border-right: 3px solid;
                                font-family: serif;
                                font-size: 0.8em;
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
    text1 = "Hello 👋, upload an image and ask questions related to it!"
    animated = f'<div class="line-1 anim-typewriter">{text1}</div>'
    with st.chat_message("assistant").markdown(animated, unsafe_allow_html=True):
        st.markdown(animated, unsafe_allow_html=True)
    def process_image(uploaded_file):
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)

        # Process the image and return the URL or other information
        # For demonstration purposes, convert the image to base64 and return a data URL
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{image_base64}"

        return image_url
    apiKey = key

    llm = ChatGoogleGenerativeAI(model="gemini-pro-vision", google_api_key=apiKey)

    image_url = None  # Initialize image_url outside the if statement
    with st.sidebar:
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image_url = process_image(uploaded_file)


    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Say something")
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": prompt,
            },  # You can optionally provide text parts
            {"type": "image_url", "image_url": image_url},
        ]
    )

    if prompt:
        with st.chat_message("user").markdown(prompt):
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )
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
        response = llm.invoke([message])
        text_output = response.content
        st.markdown('<style>.dot-pulse { visibility: hidden; }</style>', unsafe_allow_html=True)

        with st.chat_message("assistant").markdown(text_output):
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": text_output
                }
            )


