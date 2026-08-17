import json
from pathlib import Path
from pymongo import MongoClient

ATLAS_URI = "mongodb+srv://USERNAME:PASSWORD@YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority"
DB = "plan_library"

client = MongoClient(ATLAS_URI)
db = client[DB]
base = Path(__file__).resolve().parents[1]

plan = json.loads((base/"data/sample_plan.json").read_text())
mandates = json.loads((base/"data/sample_mandates.json").read_text())

db.plans.replace_one({"planAssignmentID":plan["planAssignmentID"],"version":plan["version"]}, plan, upsert=True)
for m in mandates:
    db.mandates.replace_one({"mandateId":m["mandateId"]}, m, upsert=True)

print("Loaded sample plan and mandate data.")
