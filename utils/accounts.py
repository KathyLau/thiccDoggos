from pymongo import MongoClient
import hashlib

connection = MongoClient("localhost", 27017, connect = False)
db = connection['database']
collection = db['users']

#hashes text, used for sensitive data
def hash(text):
    return hashlib.sha256(text).hexdigest()

