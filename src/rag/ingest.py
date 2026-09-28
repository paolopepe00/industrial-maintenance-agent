from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS_DIR = Path("docs/manuals")
PERSIST_DIR = "vector_db"
EMBED_MODEL = "nomic-embed-text"

def ingest():
    documents = []
    for pdf_path in DOCS_DIR.glob("*.pdf"):
        loader = PyPDFLoader(str(pdf_path))
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    Chroma.from_documents(chunks, embeddings, persist_directory=PERSIST_DIR)

    print(f"Indicizzati {len(chunks)} chunk da {len(documents)} pagine.")


if __name__ == "__main__":
    ingest()