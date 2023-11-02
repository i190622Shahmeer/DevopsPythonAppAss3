from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import json
from bson import ObjectId
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


app = Flask(__name__)
CORS(app)

mongo_uri = "mongodb+srv://vzirshehryar:jT6lEp4dMiUulENC@cluster0.njkks9n.mongodb.net/SmartShop?retryWrites=true&w=majority"
# Establish a connection to MongoDB Atlas
mongo_client = MongoClient(mongo_uri)
db = mongo_client.get_database()

prodcutsCollection = db['products']
ordersCollection = db['Orders']

results = prodcutsCollection.find()
allProducts = list(results)
df = pd.DataFrame(allProducts)

tfid = TfidfVectorizer(stop_words="english")
tfId_matrix = tfid.fit_transform(df['description'])

cosineSim = linear_kernel(tfId_matrix, tfId_matrix)

indices = pd.Series(df.index, index=df['name']).drop_duplicates()

def getRecomedations(title, cosine_sim=cosineSim):
    print(title)
    idx = indices[title]
    simScores = enumerate(cosine_sim[idx])
    # for i in simScores:
    #     ...
    simScores = sorted(simScores, key=lambda x:x[1], reverse=True)
    simScores = simScores[1:11]   #for top 10 recomendation
    sim_index = [i[0] for i in simScores]
    # print(type(simScores))
    # for i in simScores:
    #     print(i)
    # print(df[['name', 'description']].iloc[sim_index])
    return simScores


@app.route('/get_products', methods=['POST'])
def get_productsOnCart():
    names = request.json['names']
    recommendedList = []
    for name in names:
        recommendedList.extend(getRecomedations(name))
    
    uniqueRecommendedIndex = set()
    newRecommendedList = []
    sizeOfUnique = 0
    for i in range(len(recommendedList)-1):
        uniqueRecommendedIndex.add(recommendedList[i][0])
        if len(uniqueRecommendedIndex) != sizeOfUnique:
            sizeOfUnique = len(uniqueRecommendedIndex)
            newRecommendedList.append(recommendedList[i])

    newRecommendedList = sorted(newRecommendedList, key=lambda x:x[1], reverse=True)
    newRecommendedList = newRecommendedList[0:15]

    # for i in newRecommendedList:
    #     print(i)
    
    recommendedItems = []
    for i in newRecommendedList:
        recommendedItems.append(allProducts[i[0]])

    return json.dumps(recommendedItems, default=str)


@app.route('/get_products/<string:user_id>', methods=['GET'])
def get_products(user_id):

    # Get the array of product names from the request
    oid2 = ObjectId(user_id)
    
    cursor = ordersCollection.find({"userID": oid2})
    orders = list(cursor)
    if len(orders) == 0 :
        return jsonify({"success": False})

    product_ids = [product['productID'][0] for order in orders for product in order['products']]
    # Remove duplicate product IDs, if any
    unique_product_ids = list(set(product_ids))
    unique_product_ids = unique_product_ids[-10:-1]
    # for id in unique_product_ids:
    #     print(id)

    recommendedList = []
    for productID in unique_product_ids:
        for product in allProducts:
            # print("I am from orders " + str(product['_id']))
            # print("I am from Products " + str(productID))
            if product['_id'] == productID:
                # print("Hello from Shehryar Ali " + product["name"])
                recommendedList.extend(getRecomedations(product["name"]))

    uniqueRecommendedIndex = set()
    newRecommendedList = []
    sizeOfUnique = 0
    for i in range(len(recommendedList)-1):
        uniqueRecommendedIndex.add(recommendedList[i][0])
        if len(uniqueRecommendedIndex) != sizeOfUnique:
            sizeOfUnique = len(uniqueRecommendedIndex)
            newRecommendedList.append(recommendedList[i])

    newRecommendedList = sorted(newRecommendedList, key=lambda x:x[1], reverse=True)
    newRecommendedList = newRecommendedList[0:15]
    # for i in newRecommendedList:
    #     print(i)

    recommendedItems = []
    for i in newRecommendedList:
        recommendedItems.append(allProducts[i[0]])

    return json.dumps(recommendedItems, default=str)


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8080)


# product_names = request_data.get('product_names', [])

    # Query MongoDB for products with the given names
    # results = []
    # for product_name in product_names:
    #     product_data = collection.find_one({'name': product_name})
    #     if product_data:
    #         results.append(product_data)