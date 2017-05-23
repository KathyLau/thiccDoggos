from pymongo import MongoClient

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['STUY_CS_CODE_REVIEW']

def drop_all():
    db.dropDatabase()

drop_all()
