from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader, Docx2txtLoader
from app.Utils.web_scraping import extract_content_from_url
from typing import List
import nltk
from config import settings
import os
from pinecone import Pinecone as Pinecone_Init, ServerlessSpec
import openai
import tiktoken
import time


tokenizer = tiktoken.get_encoding('cl100k_base')

# Initialize Pinecone client
pc = Pinecone_Init(
    api_key=settings.PINECONE_API_KEY
)

index_name = settings.PINECONE_INDEX
embeddings = OpenAIEmbeddings()

# Function to calculate the length of tokens
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)



# Function to delete all data from the Pinecone index
def delete_all_data():
    # Initialize Pinecone client with the correct environment
    pinecone.init(api_key=api_key, environment=os.getenv('PINECONE_ENV'))

    # Check if the index exists before attempting to delete it
    if index_name in pinecone.list_indexes():
        # Delete the index
        pinecone.delete_index(index_name)
        print("Index successfully deleted.")
    else:
        print("Index not found.")

    # Create a new index with the specified parameters
    pinecone.create_index(
        index_name,
        dimension=1536,
        metric='cosine',
        pods=1,
        replicas=1,
        pod_type='p1.x1'
    )
    print("Index list after creation: ", pinecone.list_indexes())


# Function to split a document into chunks based on character count
def split_document(doc: Document):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
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

    # Create a single Document object with all the page content concatenated
    doc = Document(page_content=total_content, metadata={"source": filename})
    
    # Split the document into chunks suitable for indexing    
    chunks = split_document(doc)
    
    # Index the document chunks with the specified namespace
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


# Function to train a PDF file and load it into the Pinecone index
def train_pdf(filename: str, namespace: str):
    print("Begin train_pdf")
    start_time = time.time()
    # Load the PDF file using the PyPDFLoader
    loader = PyPDFLoader(file_path=f"./train-data/{namespace}-{filename}")
    documents = loader.load()
    total_content = ""
    for document in documents:
        total_content += "\n\n" + document.page_content
    doc = Document(page_content=total_content, metadata={"source": filename})
    # Split the document into chunks suitable for indexing
    chunks = split_document(doc)
    print("Chunks: ", chunks)
    # Index the document chunks with the specified namespace
    Pinecone.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name,
        namespace=namespace
    )
    print("Train namespace: ", namespace)
    print("End PDF loading")
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


# Function to train a text file and load it into the Pinecone index
def train_txt(filename: str, namespace: str):
    start_time = time.time()
    # Load the text file using the TextLoader
    loader = TextLoader(file_path=f"./train-data/{namespace}-{filename}")
    documents = loader.load()
    total_content = ""
    for document in documents:
        total_content += "\n\n" + document.page_content
    doc = Document(page_content=total_content, metadata={"source": filename})
    print(filename)
    # Split the document into chunks suitable for indexing
    chunks = split_document(doc)
    print("Namespace: ", namespace)
    # Index the document chunks with the specified namespace
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return True


# Function to train a Microsoft Word document and load it into the Pinecone index
def train_ms_word(filename: str, namespace: str):
    start_time = time.time()
    # Load the Word document using the Docx2txtLoader
    loader = Docx2txtLoader(file_path=f"./train-data/{namespace}-{filename}")
    documents = loader.load()
    # Since only one document is expected, directly pass it to split_document
    chunks = split_document(documents[0])
    print(chunks)
    # Index the document chunks with the specified namespace
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)

# Function to train content from a URL and load it into the Pinecone index
def train_url(url: str, namespace: str):
    # Extract content from the URL
    content = extract_content_from_url(url)
    doc = Document(page_content=content, metadata={"source": url})
    # Split the document into chunks suitable for indexing
    chunks = split_document(doc)
    # Index the document chunks with the specified namespace
    Pinecone.from_documents(
        chunks, embeddings, index_name=index_name, namespace=namespace)



# Function to retrieve context based on a message and namespace
def get_context(msg: str, namespace: str):
    print("Message: " + msg)
    matching_metadata = []
    similarity_value_limit = 0.6  # Define a similarity threshold
    results = tuple()

    # Retrieve documents from the existing index that are similar to the input message
    db = Pinecone.from_existing_index(
        index_name=index_name, namespace=namespace, embedding=embeddings)
    results = db.similarity_search_with_score(msg, k=3)
    
    # Filter results based on similarity score and collect matching metadata
    for result in results:
        if result[1] >= similarity_value_limit:
            matching_metadata.append(result[0].metadata['source'])
    matching_metadata = list(set(matching_metadata))
    
    # Concatenate the content of matching documents to form the context
    context = ""
    for result in results:
        if result[1] >= similarity_value_limit:
            context += f"\n\n{result[0].page_content}"
    return context


# Function to delete data from the Pinecone index based on metadata
def delete_data_by_metadata(filename: str, namespace: str):
    # Instantiate the Pinecone index object
    index = pinecone.Index(index_name=index_name)
    # Delete the documents from the index with the specified metadata
    query_response = index.delete(
        namespace=namespace,
        filter={
            "source": filename
        }
    )
    print(query_response)


