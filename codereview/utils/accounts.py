from pymongo import MongoClient
import random
import string
import hashlib
import utils

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
students = db['students']
teachers = db['teachers']
classes = db['classes']


#hashes text, used for sensitive data
def hash(text):
    return hashlib.sha256(text).hexdigest()

#generate a random alphanumeric verification link / id
def getVerificationLink():
    link = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
    #check if any other users have this id
    check = db.students.count(
        {
            'verificationID': link
        }
    )
    #if the id isn't unique, recursively run and get another id
    if check:
        link = getVerificationLink()
        return link
    else:
        return link

#finds account from email which is psuedo id since it's unique
def getStudent(email):
    count = db.students.count(
        {
            'email': email
        }
    )
    #print count
    if count != 1:
        return False
    else:
        # print db.students.find_one(
        #     {
        #         'email': email
        #     }
        # )
        return db.students.find_one(
            {
                'email': email
            }
        )


#gets the name of the student given an email
def getStudentName( email ):
    profile = db.students.find_one({'email': email})['profile']
    return profile


#finds account from email which is psuedo id since it's unique
def getAccount(link):
    return db.students.find(
            {
                'verificationLink': link
            }
        )
'''    count = db.students.count(
        {
            'verificationLink': link
        }
    )
    #print count
    if count != 1:
        return False
    return db.students.find_one(
            {
                'verificationLink': link
            }
        )'''

def getTeacher(email):
    count = db.teachers.count(
        {
            'email': email
        }
    )
    #print count
    if count != 1:
        return False
    else:
        # print db.students.find_one(
        #         {
        #         'email': email
        #     }
        # )
        return db.teachers.find_one(
            {
                'email': email
            }
        )

#Add A Student to the Database. Password is hashed
def addStudent( email, password, firstName, lastName, verificationLink ):
    db.students.insert_one(
        {
            'email': email,
            'password': hash(password),
            'verified': False,
            'verificationLink': verificationLink,
            'groups': [],
            'classes': [],
            #these are assignmentID:fileID key-value pairs
            'files': {},
            #these are assignmentID:[studentEmails] key-value pairs
            'assigned':{},
            'profile': {
                'firstName': firstName,
                'lastName': lastName
            }
        })

#Create a new teacher, temporary hard-coded password
def addTeacher( email, firstName, lastName, verificationLink ):
    db.teachers.insert_one(
        {
            'email': email,
            'password': 'admin',
            'verified': False,
            'classes': [],
            'profile': {
                'firstName': 'N/A',
                'lastName': 'N/A'
            }
        })

#confirms if user email matches with password
#returns duple of
#(verified, password correct)
def confirmStudent(email, pwd):
    check = getStudent(email)
    if check:
        return (check['verified'], check['password'] == hash(pwd))
    else:
        return None

#returns duple of
#(account created, password correct)
def confirmTeacher(email, pwd):
    check = getTeacher(email)
    if check:
        return (check['verified'], check['password']==hash(pwd))
    else:
        return None

def addStudentFile(email, assignmentID, fileID):
    db.students.update(
    { 'email': email },
    { '$set':
      {'files.%s'%(assignmentID): fileID }
    })

#update specified field of email account logged into
def updateField(email, field, newInfo, confirmInfo, accountType):
    if field=='password':
        if newInfo != confirmInfo:
            return False
        else:
            newInfo = hash(newInfo)
    if accountType == "student":
        check = getStudent(email)
        if check:
            if field != 'profile':
                db.students.update(
                    { 'email': email },
                    { '$set': { field: newInfo } }
                )
            else:
                fname = check['profile']['firstName']
                lname = check['profile']['lastName']
                if confirmInfo =="firstName":
                    db.students.update(
                        { 'email': email },
                        { '$set': { field: {'lastName': lname, 'firstName': newInfo}
                        }}
                    )
                else:
                    db.students.update(
                        { 'email': email },
                        { '$set': { field: {'lastName': newInfo, 'firstName': fname}
                        }}
                    )
                    return True
                return False
    else:
        check = getTeacher(email)
        if check:
            if field != 'profile':
                db.teachers.update(
                    { 'email': email },
                    { '$set': { field: newInfo } }
                )
            else:
                fname = check['profile']['firstName']
                lname = check['profile']['lastName']
                if confirmInfo =="firstName":
                    db.teachers.update(
                        { 'email': email },
                        { '$set': { field: {'lastName': lname, 'firstName': newInfo}
                        }}
                    )
                else:
                    db.teachers.update(
                        { 'email': email },
                        { '$set': { field: {'lastName': newInfo, 'firstName': fname}
                        }}
                    )
                    return True
                return False
            
