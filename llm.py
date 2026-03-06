import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


def fix_query(question):
    """Clean and normalize the query."""
    question = question.lower().strip()
    question = re.sub(r'[^\w\s]', '', question)
    question = re.sub(r'\s+', ' ', question)
    return question


def ask_llm(question, chunks, similarity_threshold=0.4):
    """Generate answer using Groq + llama3."""

    question = fix_query(question)

    good_chunks = [c for c in chunks if c["similarity"] >= similarity_threshold]

    if not good_chunks:
        return "I couldn't find relevant information in the document to answer that question."

    context = ""
    for chunk in good_chunks[:3]:
        context += f"[Page {chunk['page_number']}]: {chunk['text']}\n\n"

    prompt = f"""You are a helpful document assistant.
Answer the question using ONLY the context provided below.
Be concise and accurate. Mention page numbers when possible.
If the answer is not in the context, say "I don't find that in the document."

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"


def summarize_document(all_chunks):
    """Summarizes the document by sampling chunks."""

    total   = len(all_chunks)
    step    = max(1, total // 8)
    sampled = all_chunks[::step][:8]

    context = ""
    for chunk in sampled:
        context += f"[Page {chunk['page_number']}]: {chunk['text']}\n\n"

    prompt = f"""Summarize the following document excerpts in 4-5 sentences.
Cover the main topic, key findings, and conclusions.
Be clear and concise.

DOCUMENT:
{context}

SUMMARY:"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"