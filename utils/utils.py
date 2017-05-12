import smtplib
from pymongo import MongoClient
import hashlib
import re
from random import randrange
import datetime

connection = MongoClient("localhost", 27017, connect=False)
db = connection['database']
collection = db['users']

"""
Returns hashed password
Args:
    text - string to be hashed
Returns:
    hashed string
"""
def hash(text):
    return hashlib.sha256(text).hexdigest()

"""
~~-----------------------------USERS----------------------------------------~~
"""


"""
Checks whether username is allowed
Args:
    username - string to be checked
Returns:
    True if string is allowed
    False if it is not
"""
def check_username(username):
    return not re.search('[^a-zA-Z\s]', username) and len(username) > 0


"""
Registers an user with their email and password.
Args:
    email - user email address
    password - password for the user
Returns:
    True if user does not exist and registered
    False if user already exists
"""
def register_user(email, pwd1, pwd2):
    if pwd1 != pwd2:
        return False
    check = list(db.users.find({'email':email}))
    if check == []:
        t = {'email': email, 'pwd': hash(pwd), 'confirm': False, 'groups': [], 'classes' : [], 'files': [], 'profile': {'firstname': '', 'lastname': ''} }
        db.users.insert(t)
        return True
    return False


"""
Confirms a user with email and osis.
Args:
    email - user email address
    pwd - password for the user
Returns:
    True if user exist
    False if user does not exist
"""
def confirm_user(email, pwd):
    check = list(db.users.find({'email':email}))

    if check != []:
        if check[0]['pwd']== hash(pwd):
            return True
    return False
