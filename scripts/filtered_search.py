from pymongo import MongoClient
ATLAS_URI = "mongodb+srv://USERNAME:PASSWORD@YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority"
collection = MongoClient(ATLAS_URI)["plan_library"]["plans"]
INDEX = "plan_library_search"

query = "physical therapy"
pipeline = [
    {"$search":{"index":INDEX,"compound":{
        "must":[{"text":{"query":query,"path":[
            "medicalBenefits.benefitCategory",
            "medicalBenefits.benefitCategoryDisplayName",
            "medicalBenefits.paymentLines.paymentLineDescription",
            "medicalBenefits.paymentLines.limits.outputValue"
        ]}}],
        "filter":[
            {"equals":{"path":"planDetails.stateAbbr","value":"TX"}},
            {"equals":{"path":"planDetails.productType","value":"HMO"}}
        ]
    }}},
    {"$project":{"_id":0,"planAssignmentID":1,"planDetails.planCode":1,
                 "planDetails.stateAbbr":1,"medicalBenefits":1,
                 "score":{"$meta":"searchScore"}}},
    {"$limit":10}
]
for doc in collection.aggregate(pipeline):
    print(doc)
