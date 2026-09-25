from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma 

EMBED_MODEL = "nomic-embed-text"
PERSIST_DIR = "vector_db"


def get_retriever(k=3):
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    return db.as_retriever(search_kwargs={"k": k})