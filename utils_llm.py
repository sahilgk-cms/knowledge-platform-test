from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core import SimpleDirectoryReader, SimpleKeywordTableIndex, VectorStoreIndex, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from llama_index.core.llama_dataset.generator import RagDatasetGenerator
from typing import List
import pandas as pd
import os
import sys
from llama_index.core.storage.docstore import SimpleDocumentStore
import llama_index
import nest_asyncio
nest_asyncio.apply()

EMBED_DIMENSION = 512
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 200

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-3.5-turbo-0613"
EMBEDDING_MODEL = "text-embedding-3-small"

Settings.embed_model = OpenAIEmbedding(model = EMBEDDING_MODEL, dimensions=EMBED_DIMENSION)



def convert_text_into_llamaindex_docs(text: str, 
                                      chunk_size: str, 
                                      chunk_overlap: str) -> List[llama_index.core.schema.Document]:
  '''
  This function converts the text into llamaindex documents
  Args:
    text
  Returns:
    list of llamaindex documents
  '''

  text_splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap)
  split_documents = text_splitter.create_documents([text])


  llama_index_documents = []
  for doc in split_documents:
    llama_index_doc = Document.from_langchain_format(doc)
    llama_index_documents.append(llama_index_doc)

  return llama_index_documents

def generate_questions(documents: List[llama_index.core.schema.Document]) -> list:
  '''
  This function generates questions from llamaindex documents
  Args:
    llamaindex documents
  Returns:
    list of questions
  '''
  llm = OpenAI(model_name = MODEL_NAME)
  dataset_generator = RagDatasetGenerator.from_documents(documents, llm, num_questions_per_chunk = 5)
  rag_dataset = dataset_generator.generate_questions_from_nodes()
  questions = [q.query for q in rag_dataset.examples]
  return questions


def embedd_documents_into_vector_index(documents: List[llama_index.core.schema.Document]) -> VectorStoreIndex:
  '''
  This function embedds the  documents into vector index
  Args:
    documents
  Returns:
    vector index
  '''
  vector_index = VectorStoreIndex.from_documents(documents, show_progress=True)
  return vector_index




def create_chat_engine(vector_index: VectorStoreIndex):
  '''
  This function create dthe chat engine
  Args:
    vector store index
  Returns:
    chat engine (current based on OpenAI)
  '''
  llm = OpenAI(model_name = MODEL_NAME)
  chat_engine = vector_index.as_chat_engine(chat_mode = "best", llm = llm, verbose = True)
  return  chat_engine



def qa_chat(query, chat_engine):
    '''
    This functions initiations the questions-answering & stoes it as a tuple in a list
    Args:
        chat engine, chat history
    Returns:
        chat history containing all questions and answers along with their sources & stores as a dictionary
    '''
    answer = chat_engine.chat(query)
    return answer.response, answer.source_nodes