from pymongo import MongoClient
import random
import string
import accounts

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
students = db['students']
teachers = db['teachers']
classes = db['classes']
groups = db['groups']

#creates a group and adds to database
#prob need more code
def createGroup( studentEmail, assignmentName, groupName, limit ):
    db.groups.insert_one(
        {
            'assignmentID': assignmentName,
            'groupName': groupName,
            'members': [studentEmail],
            'assignments': [],
            'groupLimit': limit,
        })
    db.students.update(
        {'email': studentEmail },
        {'$push':
         { 'groups': assignmentName + '-' + groupName }
        })


#add a single student to group
def addToGroup( studentEmail, assignmentName, groupName ):
    print groupName
    info = list(db.groups.find({'groupName': groupName}))
    print info
    info = info[0]
    count = int(info['groupLimit'])
    num_members =int(len(info['members']))
    #fxn to count number of members in group to see if it's full
    if num_members < count and studentEmail not in info['members']:
        db.groups.update(
            {'groupName': groupName },
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
        {'groupName': name }
    )

#this fxn is wrong does not work we need a new one
def getStudentGroups( email ):
    groups = []
    student = accounts.getStudent(email)
    if len(student) < 1: return groups
    groupCodes = student['groups']
    return groupCodes
