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
    if len(filess) == 0: return prevFiles
    try:
        prevFiles.append(files.getFile(user + '-' + assignmentID, user))
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
def teacherGetAssignments(assignments, assignmentID, status, email):
    responses=[]
    retL = []
    if len(assignments)>0:
        students = assignments[0]['responses']
        for s in students:
            if str(s['student']) not in responses:  responses.append(str(s['student']) )
        if status == 0: return responses
        elif status == 1:
            for s in responses:
                if s==email:
                    try:
                        retL.append(getAssignmentSubmissions(str(s),assignmentID))
                    except: pass
                #print getAssignmentSubmissions(str(s['student']), assignmentID)
    return retL
