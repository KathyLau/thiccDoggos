from pymongo import MongoClient
import random
import string
import hashlib
import utils

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['database']
students = db['students']
teachers = db['teachers']
classes = db['classes']

#get secret data
secrets = utils.getSecretData()

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
#returns false if failed, or if more than 1 acc with that email
def getStudent(email):
    count = db.students.count(
        {
            'email': email
        }
    )
    if count != 1:
        return False
    else:
        return db.students.find(
            {
                'email': email
            }
        )

def getTeacher(email):
    count = db.teachers.count(
        {
            'email': email
        }
    )
    if count != 1:
        return False
    else:
        return db.teachers.find(
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
            #these are file ids
            'files': [],
            'profile': {
                'firstName': firstName,
                'lastName': lastName
            }
        })

#Create a new teacher, temporary hard-coded password
def addTeacher( email, firstName, lastName, verificationLink ):
    db.students.insert_one(
        {
            'email':email,
            'password': 'admin',
            'verified': False,
            'verificationLink': verificationLink,
            'classes': [],
            'profile': {
                'firstName': 'N/A',
                'lastName': 'N/A'
            }
        })

#confirms if user email matches with password
def confirmStudent(email, pwd):
    check = list(db.students.find({'email': email}))
    if check != []:
        return check[0]['password']==hash(pwd)

def confirmTeacher(email, pwd):
    check = list(db.teachers.find({'email': email}))
    if check != []:
        return check[0]['password']==hash(pwd)


#update specified field of email account logged into
def updateField(email, field, newInfo, confirmInfo):
    if newInfo != confirmInfo:
        return False
    check = list(db.students.find({field: email}))
    if check != []:
        db.students.update(
        {
        'email': email
        },
        {'$set':
        {field: newInfo
        }
        }
        )
        return True
    return False
