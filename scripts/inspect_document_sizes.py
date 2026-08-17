from bson import BSON
from pymongo import MongoClient
import math

ATLAS_URI = "mongodb+srv://USERNAME:PASSWORD@YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority"
collection = MongoClient(ATLAS_URI)["plan_library"]["plans"]

sizes, benefits = [], []
for doc in collection.find({}):
    sizes.append(len(BSON.encode(doc)))
    benefits.append(len(doc.get("medicalBenefits", [])))

if not sizes:
    raise SystemExit("No documents found.")

sizes.sort()
def pct(vals, p):
    return vals[max(0, min(len(vals)-1, math.ceil((p/100)*len(vals))-1))]

print(f"Document count: {len(sizes):,}")
print(f"Average BSON size: {sum(sizes)/len(sizes)/1024:.2f} KB")
print(f"P95 BSON size: {pct(sizes,95)/1024:.2f} KB")
print(f"P99 BSON size: {pct(sizes,99)/1024:.2f} KB")
print(f"Largest BSON document: {max(sizes)/1024:.2f} KB")
print(f"Average medicalBenefits count: {sum(benefits)/len(benefits):.2f}")
print(f"Max medicalBenefits count: {max(benefits)}")
