import streamlit as st
import os
import requests
import sys
from urllib.parse import quote
from utils_llm import *
from utils_gdrive import *


base_dir = os.path.dirname(os.path.abspath(__file__))

extracted_tags_docs_path = os.path.join(base_dir, "extracted_tags_docs.csv")
extracted_tags_docs_df = pd.read_csv(extracted_tags_docs_path)

extracted_tags_images_path = os.path.join(base_dir, "extracted_tags_images.csv")
extracted_tags_images_df = pd.read_csv(extracted_tags_images_path)


def search_documents(tags: str, docs_or_images: str):
    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if docs_or_images == "Documents":
        base_folder = DOCUMENTS_FOLDER
        df = extracted_tags_docs_df
    elif docs_or_images == "Images":
        base_folder = IMAGES_FOLDER
        df = extracted_tags_images_df
    else:
        st.error("Invalid selection")
     
    for tag in tags_list:
        filtered_df = df[df["extracted_tags"].str.contains(tag, case = False, na = False)]

    files = []
    seen_files = set()

    for i in range(0, len(filtered_df)):
        if filtered_df["file"].iloc[i] in seen_files:
            continue

        file_id = get_file_id_from_parent_folder(base_folder, filtered_df["file"].iloc[i])
        text = filtered_df["text"].iloc[i]
        extracted_tags = filtered_df["extracted_tags"].iloc[i]

        if file_id:
            seen_files.add(filtered_df["file"].iloc[i])
            files.append({"file_name": filtered_df["file"].iloc[i],
                          "text": text,
                          "extracted_tags": extracted_tags})
    if not files:
        st.error("FIles not found")
    return {"files": files}



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


# Search functionality
if st.button("Search"):
    if tags.strip():
        try:
            docs_or_images = selection

            # Call FastAPI to search for files
            response = search_documents(tags = tags, docs_or_images = docs_or_images)
          

            files = response.get("files", [])
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
                        file_id = get_file_id_from_parent_folder(parent_folder = IMAGES_FOLDER, file_name = file_name)
                        file_url = display_image_from_file_id(file_id)
                        download_url = download_file_from_file_id(file_id)

                        with st.container(border = True):
                            st.subheader(file_name)
                            st.image(file_url)
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

        file_id = get_file_id_from_parent_folder(parent_folder = DOCUMENTS_FOLDER, file_name = select_file)
        download_url = download_file_from_file_id(file_id)
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
                        docs = convert_text_into_llamaindex_docs(text = text, chunk_size = CHUNK_SIZE, chunk_overlap = CHUNK_OVERLAP)
                        vector_index = embedd_documents_into_vector_index(docs)
                        st.session_state.chat_states[select_file]["vector_index"] = vector_index
                        st.session_state.chat_states[select_file]["chat_engine"] = create_chat_engine(vector_index)
                        st.session_state.chat_states[select_file]["sample_questions"] = generate_questions(docs)
                        st.success("Chat engine initialized successfully.")
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
                        response = qa_chat(query, chat_engine = st.session_state.chat_states[select_file]["chat_engine"])
                        answer = response[0]
                        st.session_state.chat_states[select_file]["chat_history"].append({"role": "assistant", "message": answer})
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                #display chat history
                for chat in st.session_state.chat_states[select_file]["chat_history"]:
                    if chat["role"] == "user":
                        st.chat_message("user").write(chat["message"])
                    elif chat["role"] == "assistant":
                        st.chat_message("assistant").write(chat["message"])



       
