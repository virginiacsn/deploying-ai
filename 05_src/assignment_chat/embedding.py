import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PATH = str(DATA_DIR / "chroma_db")
DATA_PATH = DATA_DIR / "ct_database.jsonl"

load_dotenv(SRC_DIR / ".secrets")

COLLECTION_NAME = "clinical_trials"
EMBEDDING_MODEL = "text-embedding-3-small"

embedding_function = OpenAIEmbeddingFunction(
    api_key="any value",
    api_base="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_type="openai",
    model_name=EMBEDDING_MODEL,
    default_headers={
        "x-api-key": os.getenv("API_GATEWAY_KEY")
    }
)

UNITS_PER_YEAR = {"year": 1, "month": 12, "week": 52, "day": 365, "hour": 8760, "minute": 525600}

def age_to_years(age, default):
    if not age:
        return default
    number, unit = age.lower().split()
    unit = unit.rstrip("s")
    if unit not in UNITS_PER_YEAR:
        return default
    return round(float(number) / UNITS_PER_YEAR[unit], 2)


if __name__ == "__main__":
    print("Creating embeddings from clinical trials database...")

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    collections = chroma_client.list_collections()
    if COLLECTION_NAME in [col.name for col in collections]:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    collection = chroma_client.create_collection(
        name = COLLECTION_NAME,
        embedding_function = embedding_function
    )

    with open(DATA_PATH) as f:
        trials = [json.loads(line) for line in f]

    BATCH = 100
    for i in range(0, len(trials), BATCH):
        batch = trials[i:i + BATCH]
        collection.upsert(
            ids=[t["id"] for t in batch],
            documents=[", ".join(t["conditions"]) + " " + t["inclusion"] for t in batch], 
            metadatas=[{
                "title": t["title"],
                "condition": ", ".join(t["conditions"]),
                "inclusion": t["inclusion"] or "",
                "exclusion": t["exclusion"] or "",
                "min_age": age_to_years(t["min_age"], 0),
                "max_age": age_to_years(t["max_age"], 999),
                "sex": t["sex"],
            } for t in batch],
        )
    
    print("Clinical trials database saved in chromadb")
