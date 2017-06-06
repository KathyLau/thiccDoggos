from pymongo import MongoClient
import random
import string
import accounts
import groupy

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
students = db['students']
teachers = db['teachers']
classes = db['classes']

def createClassCode():
    code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
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

#creates a class and adds to database
def createClass( teacherEmail, form ):

    def getPeriods( formWithChecklist ):
        return [ key[-1] for key in formWithChecklist.keys() if key[:-1] == 'pd' ]

    teacher = list(db.teachers.find( {'email':teacherEmail} ))[0]
    code = createClassCode()
    periods = getPeriods( form ) # list of periods
    className = form['className']
    db.classes.insert_one(
        {
            'teacherName': teacher['profile']['firstName'] + " " + teacher['profile']['lastName'],
            'teacher': teacherEmail,
            'className': className,
            'periods':{ period : { 'students': [], 'groups': [] } for period in periods },
            'code': code
        })
    db.teachers.update(
        { 'email': teacherEmail },
        { '$push':
          {'classes': code }
        })

#add a single student to class
def addToClass( code, studentEmail ):
    #code = classCode-period#
    codeList = code.split("-")
    classCode = codeList[0]

    #check to make sure they put a hyphen
    try:
        period = codeList[1]
    except IndexError:
        return "Missing the Period"
    
    #check if period is in the class
    classs = db.classes.find_one({ 'code':classCode })
    if period not in classs['periods'].keys():
        return "Period not found for the Class"
        
    db.classes.update(
        {'code': classCode },
        {'$push':
         {'periods.%s.students'%(period): studentEmail }
        })
    db.students.update(
        {'email': studentEmail },
        {'$push':
         { 'classes': code }
        })
    return True

#remove from class
def leaveClass(code, email):
    
    pass

#get data of a class
def getClass( code ):
    return db.classes.find_one(
        {'code': code }
    )

def updateName( code, newName ):
    db.classes.update(
        {'code':code},
        {'$set':
         {'className':newName}
        })

def getStudentClasses( email ):
    student = accounts.getStudent(email)
    classCodes = student['classes']
    classes = []
    for code in classCodes:
        codetemp = code.split("-")
        code = codetemp[0]
        pd = codetemp[1]
        if db.classes.count({'code': code}) > 0:
            classinfo = db.classes.find_one( {'code': code } )
        #print classinfo
            classes.append([str(classinfo['code'] + '-' + pd), str(classinfo['className']),str(classinfo['teacher']) ])
    print "\n\n\n"
    print classes
    return classes

def getTeacherClasses( email ):
    teacher = list(db.teachers.find( {'email': email} ))
    classCodes = teacher[0]['classes']
    classes=[]
    for code in classCodes:
        classinfo = list(db.classes.find({'code':code}))[0]
        classes.append([str(classinfo['code']), str(classinfo['className'])])
    print "\n\n\n"
    print classes
    return classes

#0 is for teachers to get all pds
def getStudentsInYourClass(code, pd):
    periods = list(db.classes.find({'code':code}))[0]['periods']
    if pd == 0:
        return periods
    return periods[pd]

#teachers can disband classes
def disbandClass( code ):
    Class = db.classes.find(
            {'code': code }
    )
    db.teachers.update(
        {'email': Class['teacher'] },
        {'$pull':
         { 'classes': code }
        })
    for student in Class['students']:
        db.students.update(
            {'email': student },
            {'$pull':
             { 'classes': code,
               'groups': { '$in': Class['groups'] } }
            })
    for group in Class['groups']:
        groupy.disbandGroup( group ) #group is the groupID, so we'll use this function again
    db.classes.delete_one(
        {'code': code }
    )
