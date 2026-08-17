from pymongo import MongoClient
import voyageai

ATLAS_URI = "mongodb+srv://USERNAME:PASSWORD@YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority"
VOYAGE_API_KEY = "YOUR_VOYAGE_API_KEY"

collection = MongoClient(ATLAS_URI)["plan_library"]["planBenefits"]
vo = voyageai.Client(api_key=VOYAGE_API_KEY)

query = "outpatient therapy with visit limits in Texas"
vector = vo.embed([query], model="voyage-4-large", input_type="query").embeddings[0]

pipeline = [
    {"$vectorSearch":{
        "index":"plan_benefits_vector",
        "path":"embedding",
        "queryVector":vector,
        "numCandidates":100,
        "limit":20,
        "filter":{"state":"TX"}
    }},
    {"$project":{"_id":0,"planAssignmentID":1,"version":1,"state":1,
                 "benefitCategory":1,"benefitGroup":1,"paymentLines":1,
                 "score":{"$meta":"vectorSearchScore"}}}
]

for doc in collection.aggregate(pipeline):
    print(doc)

print("\nFor the POC, fuse these vector results with lexical Atlas Search results for true hybrid retrieval.")
