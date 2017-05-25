from pymongo import MongoClient
import gridfs
import urllib2

#connect to mongo
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
fs = gridfs.GridFS(db)
students = db['students']
teachers = db['teachers']
classes = db['classes']

#how a user uploads a file
#takes name of uploader, assignment, and file OBJECT
def uploadFile(upload, uploaderName, assignmentName):
    fileID = fs.put(upload, uploader = uploader, assignment = assignmentName, link = '')
    return fileID

#get a file
#returns dictionary of
#{ 'assignment', 'uploader', 'file' }
#NOTE: the file is a string
def getFile(fileID):
    data = fs.get(fileID)
    return {
        'assignment': data.assignment,
        'uploader': data.uploader,
        'link': data.link,
        'file': data.read()
    }

#upload file from github link
def getFileFromGithub(user, repository, fileName):
    response = urllib2.urlopen('https://raw.githubusercontent.com/{0}/{1}/master/{2}'.format(user, repository, fileName))
    responseString = response.read()
    return responseString

x = getFileFromGithub("eccentricayman", "notes", "index.html")
print x
