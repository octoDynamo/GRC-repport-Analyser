"""RAG chat engine — combines ChromaDB retrieval with Mistral generation."""
from app.ai.rag.vector_store import search_similar_chunks
from app.ai.mistral_client import call_mistral

CHAT_SYSTEM_PROMPT = """You are a GRC assistant. Answer questions based ONLY on the provided
report context. Always cite the source section.
If the answer is not in the context, say so clearly.
Respond in the same language as the question."""

CHAT_USER_PROMPT = """REPORT CONTEXT:
{context_chunks}

QUESTION: {question}

Answer citing the relevant sections from the context.
"""


async def answer_question(analyse_id: str, question: str, top_k: int = 5) -> dict:
    """
    RAG pipeline:
    1. Retrieve top-k similar chunks from ChromaDB
    2. Build context string
    3. Call Mistral with system + user prompt
    4. Return answer + source chunks
    """
    # Step 1: Retrieve similar chunks
    results = await search_similar_chunks(analyse_id, question, top_k=top_k)

    if not results:
        return {
            "reponse": "Je n'ai pas trouvé d'informations pertinentes dans ce rapport pour répondre à votre question.",
            "sources": [],
        }

    # Step 2: Build context
    context_parts = [f"[Extrait {i+1}]: {r['text']}" for i, r in enumerate(results)]
    context_chunks = "\n\n".join(context_parts)

    # Step 3: Build prompt and call Mistral
    user_prompt = CHAT_USER_PROMPT.format(
        context_chunks=context_chunks,
        question=question,
    )

    try:
        response_text = await call_mistral(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024,
        )
    except Exception:
        response_text = "Une erreur s'est produite lors de la génération de la réponse."

    return {
        "reponse": response_text,
        "sources": [r["text"][:300] for r in results],  # Truncate for response
    }
