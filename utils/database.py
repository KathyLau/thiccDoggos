from pymongo import MongoClient
import hashlib

connection = MongoClient("localhost", 27017, connect = False)
db = connection['database']
students = db['students']
teachers = db['teachers']

#hashes text, used for sensitive data
def hash(text):
    return hashlib.sha256(text).hexdigest()

#registers student and adds to database, stills requires email verif.
#sends verification email
#returns false if not registered
def register_student(email, email2, firstname, lastname, password1, password2):
    #check if email/password + confirm email/password are same
    if email1 != email2:
        return False
    if password1 != password2:
        return False

    #list of people with the same email
    alreadyRegistered = list(db.students.find( { 'email': email } ))
    #checks if above is empty
    if not(alreadyRegistered):
        #send email here
        #add to db here, only password is hashed
        db.students.insert_one(
            {
                'email': hash(email1),
                'password': hash(password1),
                'verified': False,
                'groups': [],
                'classes': [],
                #these are file ids
                'files': [],
                'profile': {
                    'name': firstname + " " + lastname
                }
            }
        )
        return True
    return False
