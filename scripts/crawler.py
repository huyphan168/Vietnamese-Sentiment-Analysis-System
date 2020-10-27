from pymongo import MongoClient
class Crawler():
    def __init__(self):
        self.x = 1
        self.y = 2
        self.client = MongoClient('mongodb://database:27017', username='devC', password='devC_for_good')
    def crawling(self, target):
        A = []
        db = self.client["database_devC"]
        collection = db.comment
        print(collection)
        cursor = collection.find()
        for document in cursor:
            A.append(document)
        return A