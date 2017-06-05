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

def enableReviews( assignID, filesAssigned ):
    db.assignments.update(
        {'assignmentID': assignID },
        {'$set':{'reviewEnabled': True, 'filesAssigned': int(filesAssigned) }}
    )

def createAssignment( assignName, classCode, uploadDate, reviewDate, groupsAllowed, details ):
    #check that dates are valid:
    for date in [ uploadDate, reviewDate ]:
        today = datetime.date.today()
        
        dateList = date.split("-")
        submittedYear = int(dateList[0])
        submittedMonth = int(dateList[1])
        submittedDay = int(dateList[2])

        submitted = datetime.date( submittedYear, submittedMonth, submittedDay )
        #if it's not the currYear or later, automatically boot
        if submitted < today:
            return "InvalidDate"
                
    db.assignments.insert_one(
        {
            'assignmentID':createAssignmentCode(),
            'assignmentName': assignName,
            'groupsAllowed': groupsAllowed,
            'class': classCode,
            'uploadDate': uploadDate,
            'reviewDate': reviewDate,
            'description':details,
            'reviewEnabled': False,
            'filesAssigned': 0,
            'pairs': [],
            'responses': []
    })
    #Successful completion
    return True 

def deleteAssignment( assignmentID ):
    db.assignments.delete_one({'assignmentID': assignmentID} )

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
        #print prevFiles
        prevFiles = prevFiles[0]['file']#.replace('\n', ' <br> ')
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
    retL = []
    if len(assignments)>0:
        responses = assignments[0]['responses']
        if status == 0:
            returnVal = { }
            onTimeSubmissions = [ ]
            lateSubmissions = [ ]
            uploadDueDateList = assignments[0]['uploadDate'].split("-")
            uploadDueDate = datetime.date(int(uploadDueDateList[0]), int(uploadDueDateList[1]), int(uploadDueDateList[2]))
            for response in responses:
               timestamp = response['timestamp']
               timeList = timestamp.split(" ")[0].split("-")
               submittedDate = datetime.date(int(timeList[0]), int(timeList[1]), int(timeList[2]))
               studentProfile = accounts.getStudentName( response['student'] )
               studentName = "%s, %s"%(studentProfile['lastName'], studentProfile['firstName'])
               if submittedDate < uploadDueDate:
                   onTimeSubmissions.append( {'student': studentName, 'email': response['student'] } )
               else:
                   lateSubmissions.append( {'student': studentName, 'email': response['student'] } )
            return {'onTime': onTimeSubmissions, 'late': lateSubmissions }
        elif status == 1:
            responses = assignments[0]['responses']
            for responses in responses:
                if response['student']==email:
                    try:
                        retL.append(getAssignmentSubmissions(str(response['student']),assignmentID))
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
#gives commenter if teacher
def getComments(user, assignmentID, accountType):
    assignment = db.assignments.find_one({ 'assignmentID': assignmentID })
    comments = []
    for response in assignment['responses']:
        if response['student'] == user:
            if accountType == "teacher":
                return response['comments']
            else:
                for comment in response['comments']:
                    #dont append names
                    comments.append(comment[1])
                return comments