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
#prob need more code
def createGroup( studentEmail, assignmentName, groupName ):
    teacher = list(db.teachers.find( {'email':teacherEmail} ))[0]
    code = createClassCode()
    db.groups.insert_one(
        {
            'name': groupName,
            'members': [studentEmail],
            'assignments': [],
              })


#add a single student to class
def addToGroup( studentEmail, assignmentName, groupName ):
    db.groups.update(
        {'name': groupName },
        {'$push':
         { 'members': studentEmail }
        })
    db.students.update(
        {'email': studentEmail },
        {'$push':
         { 'groups': assignmentName + '-' + groupName }
        })
        ##important
        #code to update db.classes

#get data of a group
def getGroup( name ):
    return db.groups.find(
        {'name': name }
    )
