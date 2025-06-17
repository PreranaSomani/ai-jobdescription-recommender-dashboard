from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os
import warnings
import logging

# Suppress TensorFlow logs and warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Constants
EMBED_MODEL = "all-mpnet-base-v2"
STORAGE_PATH = "./chroma_store"
COLLECTION = "job_descriptions"
JSON_PATH = "jds.json"

# FastAPI App
app = FastAPI()

# ChromaDB Setup
client = chromadb.PersistentClient(path=STORAGE_PATH, settings=Settings())
embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

# Load and reload function
def reload_chromadb_data():
    existing = [c.name for c in client.list_collections()]
    if COLLECTION in existing:
        print("⚠️ Deleting existing collection...")
        client.delete_collection(name=COLLECTION)

    collection = client.create_collection(name=COLLECTION, embedding_function=embed_fn)

    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError("jds.json file not found")

    with open(JSON_PATH, "r") as f:
        jds = json.load(f)

    print(f"📦 Found {len(jds)} job descriptions in {JSON_PATH}")

    for idx, item in enumerate(jds):
        # Title-weighted embedding: duplicate title 3x for stronger influence
        doc_with_weight = f"{item['title']} {item['title']} {item['title']} - {item['jd']}"
        collection.add(
            documents=[doc_with_weight],
            metadatas=[{"title": item["title"]}],
            ids=[f"jd_{idx}"]
        )

    print("✅ All job descriptions reloaded into ChromaDB.")
    return {"status": "success", "message": f"{len(jds)} job descriptions loaded."}

# ✅ Auto-reload JSON data on app startup
@app.on_event("startup")
def startup_event():
    try:
        reload_chromadb_data()
    except Exception as e:
        print(f"❌ Failed to load data on startup: {e}")

# Endpoint to manually reload ChromaDB from JSON
@app.post("/reload_data/")
def reload_data_endpoint():
    try:
        result = reload_chromadb_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Request model
class JDRequest(BaseModel):
    position_name: str

# Recommendation endpoint
@app.post("/recommend_job_description/")
def recommend_jd(request: JDRequest):
    position = request.position_name.strip()

    try:
        collection = client.get_collection(name=COLLECTION, embedding_function=embed_fn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection not found. Reload data first. Error: {e}")

    try:
        # Title-weighted search
        query_weighted = f"{position} {position} {position}"
        results = collection.query(query_texts=[query_weighted], n_results=3)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            raise ValueError("No results found.")

        # Clean up JD output (remove title triple repeat)
        recommendations = []
        for doc, meta in zip(documents, metadatas):
            original_jd = doc.split(" - ", 1)[-1]  # Remove repeated title
            recommendations.append({
                "title": meta["title"],
                "jd": original_jd
            })

        return {"recommendations": recommendations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))