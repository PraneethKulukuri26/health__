import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai

# Config
DB_PATH = os.environ.get("RAG_DB_PATH", "rag_db")
COLLECTION_NAME = os.environ.get("RAG_COLLECTION", "medical_knowledge")

os.makedirs(DB_PATH, exist_ok=True)

# Initialize ChromaDB
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

# Embedding model
embedder = SentenceTransformer(os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2"))

# Gemini model setup
API_KEY = os.environ.get("GENAI_API_KEY")
MODEL_NAME = os.environ.get("GENAI_MODEL", "gemini-2.5-flash")
if API_KEY:
    genai.configure(api_key=API_KEY)
gemini_model = genai.GenerativeModel(MODEL_NAME)


def ingest_dataset_stream(file_path: str):
    """Generator that yields ingestion progress dicts."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f if line.strip()]

    existing_docs = set(collection.get()["documents"]) if collection.count() > 0 else set()
    total = len(data)
    new_count = 0

    for i, item in enumerate(data, start=1):
        query = item.get("query")
        response = item.get("response")

        if query not in existing_docs:
            embedding = embedder.encode(query).tolist()
            collection.add(
                ids=[f"doc_{collection.count() + i}"],
                documents=[query],
                embeddings=[embedding],
                metadatas=[{"response": response}],
            )
            new_count += 1

        yield f"data: {{\"processed\": {i}, \"new_added\": {new_count}, \"total\": {total}}}\n\n"

    yield f"data: {{\"status\": \"completed\", \"total_in_db\": {collection.count()}}}\n\n"


def query_disease(symptom_text: str):
    """Retrieve relevant diseases and ask generative model for prediction."""
    symptom_embedding = embedder.encode(symptom_text).tolist()

    results = collection.query(
        query_embeddings=[symptom_embedding],
        n_results=5
    )

    retrieved_docs = [
        {"symptoms": doc, "predicted_disease": meta.get("response")}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]

    print(retrieved_docs)

    context = "\n".join([
        f"- Symptoms: {r['symptoms']} → Disease: {r['predicted_disease']}"
        for r in retrieved_docs
    ])

    prompt = f"""
You are a medical assistant AI. Given the user's symptoms and the similar records:
Symptoms: {symptom_text}
Retrieved medical knowledge:
{context}
Based on similarity and reasoning, what is the most probable disease?
"""

    try:
        gemini_reply = gemini_model.generate_content(prompt)
        gemini_text = getattr(gemini_reply, "text", None)
        if gemini_text is None:
            gemini_text = str(gemini_reply)
        gemini_text = gemini_text.strip()
    except Exception as e:
        gemini_text = f"Error calling generative model ({MODEL_NAME}): {e}"

    return {
        "retrieved_matches": retrieved_docs,
        "gemini_prediction": gemini_text,
    }
