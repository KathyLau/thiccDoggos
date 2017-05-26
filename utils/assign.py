from pymongo import MongoClient
import random
import string

connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
assignments = db['assignments']

def createAssignmentCode():
    code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    #check if any other users have this id
    check = db.assignments.count(
        {
            'assignmentID': code
        }
    )
    #if the id isn't unique, recursively run and get another id
    if check:
        code = createClassCode()
        return code
    else:
        return code

def createAssignment( assignName, classCode, dueDate, groupsAllowed, details ):
    db.assignments.insert_one(
        {
            'assignmentID':createAssignmentCode(),
            'assignmentName': assignName,
            'groupsAllowed': groupsAllowed,
            'class': classCode,
            'dueDate': dueDate,
            'description':details,
            'responses': [ ] 
    })

def getAssignments( classCode ):
    return [assignment for assignment in db.assignments.find( {'class':classCode } )] 
