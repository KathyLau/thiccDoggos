from pymongo import MongoClient

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']

def drop_all():
    db.teachers.drop()
    db.students.drop()
    db.classes.drop()
    db.assignments.drop()
    db.fs.files.drop()
    db.fs.chunks.drop()

drop_all()
