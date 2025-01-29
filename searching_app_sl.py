import streamlit as st
import os
import requests
import sys
from urllib.parse import quote
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import *

st.title("Catalyst Knowledge Hub")
st.write("Discover and explore our comprehensive repository of documents and media from across the Catalyst Group's global initiatives")

# Initialize session states
if "chat_states" not in st.session_state:
    st.session_state.chat_states = {}

if "file_details" not in st.session_state:
    st.session_state.file_details = {}

# Input options
selection = st.radio("Select for", ["Documents", "Images"])
tags = st.text_input(label="Enter tags separated by commas")

API_BASE_URL = "http://127.0.0.1:8000"

# Search functionality
if st.button("Search"):
    if tags.strip():
        try:
            docs_or_images = selection

            # Call FastAPI to search for files
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"tags": tags, "docs_or_images": docs_or_images},
            )
            response.raise_for_status()

            files = response.json().get("files", [])
            if files:
                # store documents data - file name & extracted text in session states  so that we can use for chat later
                if docs_or_images == "Documents":
                    st.success(f"Matching documents found: {len(files)}")
                    st.session_state.file_details = {file["file_name"]: file["text"] for file in files}

                # display images
                else:
                    st.success(f"Matching images found: {len(files)}")
                    for file in files:
                        file_name = file["file_name"]
                        encoded_file_name = quote(file_name)
                        download_url = f"{API_BASE_URL}/download/{encoded_file_name}?docs_or_images={docs_or_images}"
                        with st.container(border = True):
                            st.subheader(file_name)
                            st.image(download_url)
                            st.markdown(f"[Download]({download_url})", unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Error: {e}")


# Proceed if file details are available
if st.session_state.file_details and selection == "Documents":
    # File selection dropdown
    select_file = st.selectbox("Please select a file", options=st.session_state.file_details.keys(), key="select_file")
    

    if select_file:
        # Initialize chat states if not already done
        if select_file not in st.session_state.chat_states:
            st.session_state.chat_states[select_file] = {
                "chat_active": False,
                "vector_index": None,
                "chat_engine": None,
                "sample_questions": None
            }

        # Text content of the selected file
        text = st.session_state.file_details[select_file]
        with st.expander("Text"):
            st.write(text)

        encoded_file_name = quote(select_file)
        download_url = f"{API_BASE_URL}/download/{encoded_file_name}?docs_or_images={selection}"
        st.markdown(f"[Download]({download_url})", unsafe_allow_html=True)

        # Chat Interaction
        chat_active = st.checkbox("Chat with document", key=f"chat_active_{select_file}")
        st.session_state.chat_states[select_file]["chat_active"] = chat_active

        if chat_active:
            # Initialize chat if not already done
            # convert text into llamaindex documents
            # embedd documentts into vector index
            # load chat engine
            # generate sample questions
            if not st.session_state.chat_states[select_file].get("vector_index"):
                try:
                    with st.spinner("Initializing chat engine....."):
                        response = requests.post(
                            f"{API_BASE_URL}/initialize_chat",
                            json={"file_name": select_file, "text": text},
                        )
                        if response.status_code == 200:
                            response_data = response.json()
                            st.success(response_data["message"])
                            st.session_state.chat_states[select_file]["vector_index"] = response_data["vector_index"]
                            st.session_state.chat_states[select_file]["chat_engine"] = response_data["chat_engine"]
                            st.session_state.chat_states[select_file]["sample_questions"] = response_data["sample_questions"]
                        else:
                            st.error(f"Failed to initialize chat: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {e}")

            # Chat interface logic
            if st.session_state.chat_states[select_file].get("chat_engine"):
                if "chat_history" not in st.session_state.chat_states[select_file]:
                    st.session_state.chat_states[select_file]["chat_history"] = []
                
                #display sample questions
                st.info(f"Sample questions generated: {len(st.session_state.chat_states[select_file]["sample_questions"])}")
                with st.expander("Five sample questions"):
                    st.write("\n".join(st.session_state.chat_states[select_file]["sample_questions"][:5]))

                #query - answer
                query = st.chat_input(f"Ask a question ({select_file}):", key=f"query_{select_file}")
                if query:
                    st.session_state.chat_states[select_file]["chat_history"].append({"role": "user", "message": query})

                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/chat",
                            json={"file_name": select_file, "query": query},
                        )
                        if response.status_code == 200:
                            response_data = response.json()
                            answer = response_data["answer"]
                            st.session_state.chat_states[select_file]["chat_history"].append({"role": "assistant", "message": answer})

                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                #display chat history
                for chat in st.session_state.chat_states[select_file]["chat_history"]:
                    if chat["role"] == "user":
                        st.chat_message("user").write(chat["message"])
                    elif chat["role"] == "assistant":
                        st.chat_message("assistant").write(chat["message"])



       
