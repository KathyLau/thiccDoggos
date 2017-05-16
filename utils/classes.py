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
    code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5))
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

print createClassCode()
    
#creates a class and adds to database
def createClass(teacher):
    pass

#add array of student emails to class
def addToClass(students):
    pass

#get data of a class
def getClass(classID):
    pass

#teachers can disband classes
def disbandClass(classID):
    pass
