import pytest

from src.rag.retriever import get_retriever

pytestmark = pytest.mark.needs_ollama


def test_retriever_returns_relevant_chunks():
    retriever = get_retriever(k=3)
    docs = retriever.invoke("What causes vibration at 2x running speed?")

    assert len(docs) > 0
    assert len(docs) <= 3
    combined_text = " ".join(d.page_content.lower() for d in docs)
    assert "misalignment" in combined_text or "2x" in combined_text


def test_retriever_sources_are_tracked():
    retriever = get_retriever(k=3)
    docs = retriever.invoke("immediate shutdown threshold for bearing temperature")

    sources = {d.metadata.get("source", "") for d in docs}
    assert any("safety" in s.lower() for s in sources)