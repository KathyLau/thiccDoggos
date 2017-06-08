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

def enableReviews( assignmentID, filesAssigned ):
    db.assignments.update(
        {'assignmentID': assignmentID },
        {'$set':{'reviewEnabled': True, 'filesAssigned': int(filesAssigned) }}
    )

def getCodeReviewStatus(assignmentID):
    return db.assignments.find_one({'assignmentID':assignmentID})['reviewEnabled']

def createAssignment( assignName, classCode, uploadDate, reviewDate, groupSize, details ):
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
            'groupSize': groupSize,
            'class': classCode,
            'uploadDate': uploadDate,
            'reviewDate': reviewDate,
            'description':details,
            'reviewEnabled': False,
            'filesAssigned': 0,
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

def getAssignmentSubmission(user, assignmentID ):
    try:
        fileID = db.students.find_one( {'email': user} )['files'][assignmentID]
        file =  files.getFile(fileID, user)['file']
        start = file.find("content:")
        return file[start+8:]
    except:
        pass

def submitAssignment(email, assignmentID):
    ts = time.time()
    #check if student already submitted first:
    if email in [response['student'] for response in db.assignments.find_one({"assignmentID":assignmentID})['responses'] ]:
        db.assignments.update({'assignmentID':assignmentID,
                               'responses.student':email},
                              {'$push':
                               {'responses.$.comments':{'submitter':'Administrator','comment':'File updated, %s'%(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')), 'timestamp': datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')} }} )
    else:
        db.assignments.update({"assignmentID":assignmentID},
                              {"$push":
                               {"responses":
                                {'student': email,
                                 'timestamp': datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                                 'comments':[] # comments by other students in { submitter, comment, timestamp } format
                                }}})


def teacherGetResponse(studentEmail, assignmentID):
    response = db.assignments.find_one({'assignmentID':assignmentID, "responses.student":studentEmail})['responses'][0]
    return [accounts.getStudentName(studentEmail)['firstName'] + " " + accounts.getStudentName(studentEmail)['lastName'], response['timestamp'], getAssignmentSubmission(studentEmail, assignmentID) ]

# get information from assignment ID
# number coded
# 0 - get only students who submitted a file
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
                studentName = "%s %s"%(studentProfile['firstName'], studentProfile['lastName'])
                if submittedDate < uploadDueDate:
                    onTimeSubmissions.append( {'student': studentName, 'email': response['student'] } )
                else:
                    lateSubmissions.append( {'student': studentName, 'email': response['student'] } )
            return {'onTime': onTimeSubmissions, 'late': lateSubmissions }

#returns two lists ( in a dictionary )
#reviewed: code that has been reviewed
#unreviewed: code that hasn't been reviewed
def teacherGetReviews(assignmentID):
    assignment = db.assignments.find_one({'assignmentID':assignmentID})
    responses = assignment['responses']
    filesAssigned = assignment['filesAssigned']
    reviewed = [ ]
    unreviewed = [ ]
    for response in responses:
        #identify unique commentators (excluding Administrator )
        count = 0
        counted = []
        for comment in response['comments']:
            if comment['submitter'] != 'Administrator' and comment['submitter'] not in counted:
                count += 1
                counted.append( comment['submitter'] )
        studentProfile = accounts.getStudentName( response['student'] )
        studentName = "%s %s"%(studentProfile['firstName'], studentProfile['lastName'])
        #if not enough reviews, put in unreviewed
        if count < filesAssigned:
            unreviewed.append( {'student': studentName, 'email': response['student']})
        else:
            reviewed.append( {'student': studentName, 'email': response['student']})
    return {'reviewed': reviewed, 'unreviewed': unreviewed }


#get all the students assigned to a student's file
def getAssignedTo(assignmentID, student):
    return [ student['email'] for student in db.students.find({'assigned.%s'%(assignmentID): student }) ]

#Num is the number of files each student has to review
def assignRandomReviews(assignmentID, num):
    students = [ response['student'] for response in db.assignments.find_one({'assignmentID':assignmentID})['responses'] ]
    for studentIndex in range(len(students)):
        student = students[studentIndex]
        #before loopy stuff, make sure that it's possible
        if len(students) > num:
            list = [ ]
            for i in range(num):
                list.append( students[(studentIndex + i + 1)% len( students ) ] )
            db.students.update({'email':student},
                               {'$set':
                                {'assigned.%s'%(assignmentID): list }
                               })
        else:
            #Do the next one down
            assignRandomReviews(assignmentID, num-1)

#assign em to each other, helper funcc
def assignGroupToReview(assignmentID, student, studentsToReview):
    db.students.update(
        {
            "email": student
        }
        ,
        {
            {
                "$push": {
                    "assigned.%s" % (assignmentID): studentsToReview
                }
            }
        }
    )

#Num is the number of groups each group has to review
def assignGroupRandomReviews(assignmentID, num):
    groups = [ response['members'] for response in db.groups.find({'assignmentID':assignmentID})]
    randomGroups = random.sample(groups, len(groups))
    #iter number
    for group in range(0, len(randomGroups) - 1):
        #for student in each group
        for student in randomGroups[group]:
            #assign each student to student
            assignGroupToReview(assignmentID, student, randomGroups[group + 1])


#Returns a list of [studentEmail, actualCode] that the student has to review
def getAssignedCodes(email, assignmentID):
    try:
        list = db.students.find_one({"email":email})['assigned'][assignmentID]
        return [ [student, getAssignmentSubmission(student, assignmentID) ] for student in list ]
    except: return []


#submits a comment from a student
def submitComment(comment, codeOwner, submitter, assignmentID):
    db.assignments.update(
        {
            'assignmentID': assignmentID,
            'responses.student': str(codeOwner)
        },
        {
            '$push': {
                "responses.$.comments": {'submitter':str(submitter), 'comment': comment, 'timestamp': datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}
            }
        }
    )
    #once they finished an assignment, they don't have to do it again
    db.students.update(
        {'email': submitter},
        {'$pull':
         {'assigned.%s'%(assignmentID):codeOwner}}
    )

    #for response in assignment['responses']:
    #    if response['student'] == codeOwner:
    #        response['comments'].append([submitter, comment])

#shows all comments for user submission of assignment
def getComments(user, assignmentID, accountType):
    assignment = db.assignments.find_one({ 'assignmentID': assignmentID })
    comments = []
    for response in assignment['responses']:
        if response['student'] == user:
            for comment in response['comments']:
            #print comment
                if comment['submitter']!=user:
                    comments.append(comment)
    return comments
