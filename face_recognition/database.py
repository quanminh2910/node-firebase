import json
from pathlib import Path

DB_PATH = Path("face_db.json")

def load_db():
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text())
    return {}  # {name: [embedding_list]}

def save_db(db: dict):
    DB_PATH.write_text(json.dumps(db, indent=2))
