from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import os
import fastapi
from urllib.parse import unquote
from utils import *
from pydantic import BaseModel



class InitilalizeChatPayload(BaseModel):
    file_name: str
    text: str

class ChatPayload(BaseModel):
    file_name: str
    query: str


app = FastAPI()

base_dir = os.path.dirname(os.path.abspath(__file__))

documents_folder = os.path.join(base_dir, "Documents")
images_folder = os.path.join(base_dir, "Images")

extracted_tags_docs_path = os.path.join(base_dir, "extracted_tags_docs.csv")
extracted_tags_docs_df = pd.read_csv(extracted_tags_docs_path)

extracted_tags_images_path = os.path.join(base_dir, "extracted_tags_images.csv")
extracted_tags_images_df = pd.read_csv(extracted_tags_images_path)

# chat_engines[file_name] = {vector_index: , chat_engine: }
chat_engines = {}

@app.get("/search")
def search_documents(tags: str = Query(..., description = "Comma separated tags"),
                     docs_or_images: str = Query(..., description = "Documents or Images")):
    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    if docs_or_images == "Documents":
        base_folder = documents_folder
        df = extracted_tags_docs_df
    elif docs_or_images == "Images":
        base_folder = images_folder
        df = extracted_tags_images_df
    else:
        raise HTTPException(status_code = 400, detail = "Invalid selection")
     
    for tag in tags_list:
        filtered_df = df[df["extracted_tags"].str.contains(tag, case = False, na = False)]


    files = []
    seen_files = set()

    for i in range(0, len(filtered_df)):
        if filtered_df["file"].iloc[i] in seen_files:
            continue

        file_path = os.path.join(base_folder, filtered_df["file"].iloc[i])
        text = filtered_df["text"].iloc[i]
        extracted_tags = filtered_df["extracted_tags"].iloc[i]

        if os.path.exists(file_path):
            seen_files.add(filtered_df["file"].iloc[i])
            files.append({"file_name": os.path.basename(file_path),
                          "file_path": file_path,
                          "text": text,
                          "extracted_tags": extracted_tags})
    if not files:
        raise HTTPException(status_code = 404, detail = "No matching document found")
    

    return {"files": files}



@app.get("/download/{file_name}")
def get_file(file_name: str,
             docs_or_images: str = Query(..., description = "Documents or Images")):
    
    if docs_or_images == "Documents":
        base_folder = documents_folder
        df = extracted_tags_docs_df
    elif docs_or_images == "Images":
        base_folder = images_folder
        df = extracted_tags_images_df
    else:
        raise HTTPException(status_code = 400, detail = "Invalid selection")
    
    decoded_file_name = unquote(file_name)
    file_path = os.path.join(base_folder, decoded_file_name)
    if os.path.exists(file_path):
       # headers = {"Content-Disposition": f"inline; filename = '{file_name}'"}
        return FileResponse(file_path, media_type="application/octet-stream", filename = decoded_file_name)
    raise HTTPException(status_code = 404, detail = f"{decoded_file_name} not found")


@app.post("/initialize_chat")
def initialize_chat(request: InitilalizeChatPayload):
    file_name = request.file_name
    text = request.text

    if file_name in chat_engines:
        return {"vector_index": chat_engines[file_name]["vector_index"],
                "chat_engine": chat_engines[file_name]["chat_engine"],
                "sample_questions": chat_engines[file_name]["sample_questions"],
                "message": "Chat engine already initialzed for this file"}
    
    try:
        documents = convert_text_into_llamaindex_docs(text, chunk_size = CHUNK_SIZE, chunk_overlap = CHUNK_OVERLAP)
        vector_index = embedd_documents_into_vector_index(documents)
        chat_engine = create_chat_engine(vector_index)
        sample_questions = generate_questions(documents)

        chat_engines[file_name] = {"vector_index": vector_index, "chat_engine": chat_engine, "sample_questions": sample_questions}

        return {"vector_index": vector_index,
                "chat_engine": chat_engine,
                "sample_questions": sample_questions,
                "message": "Chat engine initialized successfully."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail = f"Error initializing chat engine: {e}")

@app.post("/chat")
def chat(request: ChatPayload):
    file_name = request.file_name
    query = request.query

    if file_name not in chat_engines:
        return {"message": "Chat engine is not initialzed for this file"}
    
    try:
        chat_engine = chat_engines[file_name]["chat_engine"]
        result = qa_chat(query, chat_engine)
        return {"answer": result[0], "source_node": result[1:]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during chat: {e}")

