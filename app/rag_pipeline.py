import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from app.tools import extract_text_pdfplumber, extract_text_ocr, extract_text
from dotenv import load_dotenv

load_dotenv()

emb = OpenAIEmbeddings(model="text-embedding-3-small")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n## ", "\n### ", "\n", " ", ""]
)

async def ingest_pdf(file):
    raw_bytes = await file.read()
    file_id = str(uuid.uuid4())

    with open(f"./data/pdfs/{file_id}.pdf", "wb") as f:
        f.write(raw_bytes)

    text = extract_text(raw_bytes)      # Unique extraction logic, reads both text and image-based PDFs
    chunks = text_splitter.split_text(text)

    vectordb = Chroma(
        collection_name="smartdocs",
        embedding_function=emb,
        persist_directory="./vectorstore/chroma"
    )

    metadata = {"source": file.filename}
    vectordb.add_texts(chunks, metadatas=[metadata] * len(chunks))

    return {"status": "success", "chunks": len(chunks)}

async def query_docs(query):
    vectordb = Chroma(
        collection_name="smartdocs",
        embedding_function=emb,
        persist_directory="./vectorstore/chroma"
    )
    return vectordb.similarity_search(query, k=6)