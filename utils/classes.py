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
