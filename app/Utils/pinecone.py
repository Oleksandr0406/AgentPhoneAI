from langchain.schema import Document
import pandas as pd
from fastapi import UploadFile, File
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import CSVLoader, PyPDFLoader, TextLoader, Docx2txtLoader
from app.Utils.web_scraping import extract_content_from_url
from typing import List
import nltk

from dotenv import load_dotenv
import os
import pinecone
import openai
import tiktoken
import time
# from pinecone import Index

load_dotenv()
tokenizer = tiktoken.get_encoding('cl100k_base')

api_key = os.getenv('PINECONE_API_KEY')

pinecone.init(
    api_key=api_key,  # find at app.pinecone.io
    environment=os.getenv('PINECONE_ENV'),  # next to api key in console
)

index_name = os.getenv('PINECONE_INDEX')
embeddings = OpenAIEmbeddings()



def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)


def delete_all_data():
    # Initialize Pinecone client
    pinecone.init(api_key=api_key, environment=os.getenv('PINECONE_ENV'))

    if index_name in pinecone.list_indexes():
        # Delete the index
        pinecone.delete_index(index_name)
        print("Index successfully deleted.")
    else:
        print("Index not found.")

    pinecone.create_index(
        index_name,
        dimension=1536,
        metric='cosine',
        pods=1,
        replicas=1,
        pod_type='p1.x1'
    )
    print("new: ", pinecone.list_indexes())


def split_document(doc: Document):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents([doc])
    return chunks


def train_csv(filename: str, namespace: str):
    start_time = time.time()
    loader = CSVLoader(file_path=f"./train-data/{namespace}-{filename}")
    data = loader.load()
    total_content = ""
    for d in data:
        total_content += "\n\n" + d.page_content
    doc = Document(page_content=total_content, metadata={"source": filename})
    chunks = split_document(doc)
    Pinecone.from_documents(
        chunks, embeddings, p=index_name, namespace=namespace)

    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


def train_pdf(filename: str, namespace: str):
    print("begin train_pdf")
    start_time = time.time()
    loader = PyPDFLoader(file_path=f"./train-data/{namespace}-{filename}")
    documents = loader.load()
    # chunks = split_document(documents)
    # print(type(documents))
    total_content = ""
    for document in documents:
        total_content += "\n\n" + document.page_content
    doc = Document(page_content=total_content, metadata={"source": filename})
    chunks = split_document(doc)
    print("chunks: ", chunks)
    Pinecone.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name,
        namespace=namespace
    )
    print("train_namesapce", namespace)
    print("end pdf-loading")
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


def train_txt(filename: str, namespace: str):
    start_time = time.time()
    loader = TextLoader(file_path=f"./train-data/{namespace}-{filename}")
    documents = loader.load()
    total_content = ""
    for document in documents:
        total_content += "\n\n" + document.page_content
    doc = Document(page_content=total_content, metadata={"source": filename})
    print(filename)
    chunks = split_document(doc)
    print("namespace: ", namespace)
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


def train_ms_word(filename: str, namespace: str):
    start_time = time.time()
    loader = Docx2txtLoader(file_path=f"./train-data/{namespace}-{filename}")
    documents = loader.load()
    chunks = split_document(documents[0])
    print(chunks)
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)


def train_url(url: str, namespace: str):
    content = extract_content_from_url(url)
    doc = Document(page_content=content, metadata={"source": url})
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents([doc])
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)


def set_prompt(new_prompt: str):
    global prompt
    prompt = new_prompt


def get_context(msg: str, namespace: str):
    print("message" + msg)
    matching_metadata = []
    similarity_value_limit = 0.6
    results = tuple()
    
    db = Pinecone.from_existing_index(
        index_name=index_name, namespace=namespace, embedding=embeddings)
    results = db.similarity_search_with_score(msg, k=1)
    for result in results:
        if result[1] >= similarity_value_limit:
            matching_metadata.append(result[0].metadata['source'])
    matching_metadata = list(set(matching_metadata))
    
    context = ""
    for result in results:
        if result[1] >= similarity_value_limit:
            context += f"\n\n{result[0].page_content}"
    return context


def delete_data_by_metadata(filename: str, namespace: str):

    index = pinecone.Index(index_name=index_name)
    query_response = index.delete(
        namespace=namespace,
        filter={
            "source": filename
        }
    )
    print(query_response)

