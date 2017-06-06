from pymongo import MongoClient

connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
teachers = db['teachers']
students = db['students']

def adminCreation():
    #add the teacher first
    db.teachers.insert_one(
        {
            'email':'admin@admin.edu',
            'password':'8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
            'verified':True,
            'classes':[],
            'profile': {
                'firstName':'Admin',
                'lastName':'Admin'
            }
        })

    #Add Five Students
    for i in range(5):
        db.students.insert_one(
        {
            'email':'student%s@admin.edu'%(i+1),
            'password':'8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
            'verified':True,
            'classes':[],
            'groups':[],
            'files':{},
            'profile':{
                'firstName':'Student',
                'lastName':'%s'%(i+1)
            }
        })
    

    
adminCreation()
