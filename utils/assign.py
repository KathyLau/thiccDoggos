from pymongo import MongoClient
import random
import string
import accounts, files
import datetime, time, random

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
            'pairs': [],
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

def assignRandomReviews(assignmentID, num):
    assigns = getAssignmentsByID(assignmentID)
    responses = teacherGetAssignments(assigns, assignmentID, 0, '')
    randomStudents = random.sample(responses, len(responses))
    pairs = []
    for student in range(0, len(randomStudents), num):
        pair = []
        for pairNumber in range(0, num):
            pair.append(randomStudents[student + pairNumber])
        pairs.append(pair)
    db.assignments.update(
        { "assignmentID": assignmentID },
        { "$set":
          {
              'pairs': pairs
          }
        })
    return pairs

#gets assigned code for a student with his email
#returns [person assigned to, that person's code]
def getAssignedCode(email, assignmentID):
    assignment = db.assignments.find_one({
        'assignmentID': assignmentID
    })
    if not(assignment['pairs']):
        return ["", False]
    else:
        pairs = assignment['pairs']
        for pair in pairs:
            if (pair[0] == email):
                print getAssignmentSubmissions(pair[1], assignmentID)
                return [pair[1], getAssignmentSubmissions(pair[1], assignmentID)]
            elif (pair[1] == email):
                print getAssignmentSubmissions(pair[0], assignmentID)
                return [pair[0], getAssignmentSubmissions(pair[0], assignmentID)]
    
#submits a comment from a student
def submitComment(comment, codeOwner, submitter, assignmentID):
    db.assignments.update(
        {
            'assignmentID': assignmentID,
            'responses.student': str(codeOwner)
        },
        {
            '$push': {
                "responses.$.comments": [str(submitter), comment]
            }
        }
    )
    #for response in assignment['responses']:
    #    if response['student'] == codeOwner:
    #        response['comments'].append([submitter, comment])

#shows all comments for user submission of assignment
def getComments(user, assignmentID):
    assignment = db.assignments.find_one({ 'assignmentID': assignmentID })
    comments = []
    for response in assignment['responses']:
        if response['student'] == user:
            for comment in response['comments']:
                #dont append names
                comments.append(comment[1])
            break
    return comments
