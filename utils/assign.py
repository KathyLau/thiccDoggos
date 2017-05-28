from pymongo import MongoClient
import random
import string
import accounts, files
import datetime, time

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

def getAssignmentsByID( ID ):
    return [assignment for assignment in db.assignments.find( {'assignmentID': ID } )]

def getAssignmentSubmissions (user, assignmentID):
    prevFiles=[]
    filess = accounts.getStudent(user)['files']
    try:
        prevFiles.append(files.getFile(assignmentID))
        prevFiles = prevFiles[0]['file'].replace('\n', ' <br> ')
        start = prevFiles.find("content:")
        prevFiles = prevFiles[start + 8:]
    except: pass
    return prevFiles

def submitAssignment(email, assignmentID):
    ts = time.time()
    db.assignments.update({"assignmentID":assignmentID},
    {"$push":
    {"responses":
    {'student': email,
    'timestamp': datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
    'comments':[] # comments by other students in [classmate: comment] format
    }}})

# get information from assignment ID
# number coded
# 0 - get only students who submitted a file
# 1 - get the students with the files
def teacherGetAssignments(assignments, assignmentID, status):
    responses=[]
    if len(assignments)>0:
        students = assignments[0]['responses']
        if status == 0: responses = [ str(s['student']) for s in students]
        elif status == 1:
            for s in students: responses.append(getAssignmentSubmissions(str(s['student']),assignmentID))
    return responses
