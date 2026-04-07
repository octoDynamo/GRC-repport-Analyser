"""Chat service wrapping the RAG chat engine."""
from app.ai.rag.chat_engine import answer_question


async def chat_with_report(analyse_id: str, question: str) -> dict:
    return await answer_question(analyse_id=analyse_id, question=question)
