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
def createGroup( studentEmail, assignmentName, groupName, limit ):
    db.classes.update(
        {'code': code},
        {'$push':
        {
        'groups': groupName
        }
        }
    )
    db.groups.insert_one(
        {
            'name': groupName,
            'members': [studentEmail],
            'assignments': [],
            'groupLimist': limit,
              })


#add a single student to class
def addToGroup( studentEmail, assignmentName, groupName ):
    count = int(list(db.groups.find({'name': groupName}))[0]['groupLimit'])
    num_members =int(list(db.groups.find({'groupName': groupName}))[0]['members'])
    #fxn to count number of members in group to see if it's full
    if num_members <= count:
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
