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
            #these are file ids
            'files': [],
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
        

#update specified field of email account logged into
def updateField(email, field, newInfo, confirmInfo):
    if newInfo != confirmInfo:
        return False
    check = getStudent(email)
    if check:
        db.students.update(
            { 'email': email },
            { '$set': { field: newInfo } }
        )
        return True
    return False
