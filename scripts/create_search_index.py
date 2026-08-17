import json
from pathlib import Path
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

ATLAS_URI = "mongodb+srv://USERNAME:PASSWORD@YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority"
DB = "plan_library"
COLLECTION = "plans"

collection = MongoClient(ATLAS_URI)[DB][COLLECTION]
cfg = json.loads((Path(__file__).resolve().parents[1]/"config/search_index.json").read_text())

model = SearchIndexModel(definition=cfg["definition"], name=cfg["name"])
print(collection.create_search_index(model=model))
