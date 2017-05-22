from pymongo import MongoClient
import random
import string
import accounts

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['database']
students = db['students']
teachers = db['teachers']
classes = db['classes']
groups = db['groups']

#creates a group and adds to database
def createGroup( studentEmail, assignmentName, groupName ):
    teacher = list(db.teachers.find( {'email':teacherEmail} ))[0]
    code = createClassCode()
    db.groups.insert_one(
        {
            'name': groupName,
            'members': [studentEmail],
            'assignments': [],
              })
  
