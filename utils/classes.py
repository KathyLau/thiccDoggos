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

def createClassCode():
    code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    #check if any other users have this id
    check = db.classes.count(
        {
            'code': code
        }
    )
    #if the id isn't unique, recursively run and get another id
    if check:
        code = createClassCode()
        return code
    else:
        return code
    
#creates a class and adds to database
def createClass( teacher, className, groupLimit ):
    db.classes.insert_one(
        {
            'teacher': teacher,
            'className': className,
            'groupLimit': groupLimit,
            'students': [],
            'groups': [],
            'code': generateClassCode()
        })

#add a single student to class
def addToClass( classID, studentID ):
    db.classes.update(
        {'_id': classID },
        {'$push':
         { 'students': studentID }
        })

#get data of a class
def getClass( classID ):
    pass

#teachers can disband classes
def disbandClass( classID ):
    Class = db.classes.find_one(
            {'_id': classID }
    )
    db.teachers.update(
        {'_id': Class['teacher'] },
        {'$pull':
         { 'classes': classID }
        })
    for student in Class['students']:
        db.students.update(
            {'_id': student },
            {'$pull':
             { 'classes': classID,
               'groups': '$in': Class['groups'] }
            })
    for group in Class['groups']:
        disbandGroup( group ) #group is the groupID, so we'll use this function again
    db.classes.delete_one(
        {'_id': classID }
    )
    
