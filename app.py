from flask import Flask, render_template, request, session, redirect, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
import gridfs
from werkzeug.utils import secure_filename
from utils import utils, accounts, classy, groupy, assign, files
from threading import Thread
import os
import datetime

#connect to mongo
#connection = MongoClient("localhost", 27017, connect = False)
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
fs = gridfs.GridFS(db)
students = db['students']
teachers = db['teachers']
classes = db['classes']
groups = db['groups']

#get secret data
secrets = utils.getSecretData() #Can't Do this cause no secrets.txt on heroku (gotta deploy manually LMAO)

app = Flask(__name__)
#app.secret_key = os.environ['app-secret-key']
app.secret_key = secrets['app-secret-key']

UPLOAD_FOLDER = './data/'
ALLOWED_EXTENSIONS = set(['java', 'py', 'rkt', 'nlogo'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#mail configs
app.config['MAIL_SERVER'] ='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = secrets['email']
app.config['MAIL_PASSWORD'] = secrets['email-password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = ("StuyCS Code Review", secrets['email'])

#initialize mail after config
mail = Mail(app)

#here is async wrapper for mail
def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

#forces flask-mail to send email asynchronously
@async
def sendEmailAsync(app, message):
    with app.app_context():
        mail.send(message)

#this sends a mail, with email and verification link
def sendVerificationEmail(email, verificationLink):
    message = Message()
    message.recipients = [ email ]
    message.subject = "Confirm Your StuyCS Code Review Account"
    message.html = '''
    <center>
<h1 style="font-weight: 500 ; font-family: Arial">StuyCS Code Review</h1>
    <p style="font-weight: 500 ; font-family: Arial">Thanks for signing up for StuyCS Code Review! Please press the button below to verify your account.</p>
    <br><br>
    <a href="{0}" style="padding: 1.5% ; text-decoration: none ; color: #404040; border: 1px solid black ; text-transform: uppercase ; font-weight: 500 ; font-family: Arial ; padding-left: 10% ; padding-right: 10%">Verify Email</a>
</center>
    '''.format("http://127.0.0.1:5000/verify/" + verificationLink)
    sendEmailAsync(app, message)

#this sends a mail to register a teacher account
def sendRegistrationEmail(email, referrer, verificationLink):
    message = Message()
    message.recipients = [ email ]
    message.subject = "Create Your StuyCS Code Review Account"
    message.html = '''
    <center>
    <h1 style="font-weight: 500 ; font-family: Arial">StuyCS Code Review</h1>
    <p style="font-weight: 500 ; font-family: Arial">{0} has referred you to join StuyCS Code Review as a teacher. Please press the button below to create your teacher account.</p>
    <br>
    <a href="{1}" style="padding: 5% ; text-decoration: none ; border: 1px solid black ; text-transform: uppercase ; font-weight: 500 ; font-family: Arial ; padding-left: 10% ; padding-right: 10%">Create Account</a>
    </center>
    '''.format(whoReferred['name'], "http://127.0.0.1:5000/verify/" + verificationLink)
    sendEmailAsync(app, message)

#registers student and adds to database, stills requires email verif.
#sends verification email
#returns false if not registered
def registerStudent(email, email1, firstName, lastName, password1, password2):
    #check if email/password + confirm email/password are same
    if email != email1:
        return False
    if password1 != password2:
        return False

    #create verification link/profile link
    verificationLink = accounts.getVerificationLink()

    #list of people with the same email
    alreadyRegistered = accounts.getStudent(email)
    #checks if above is empty
    if not(alreadyRegistered):
        #send email here
        sendVerificationEmail(email, verificationLink)
        accounts.addStudent( email1, password1, firstName, lastName, verificationLink )
        return True
    return False

def registerTeacher(referrer, email):
    #create verification link/profile link
    verificationLink = utils.getVerificationLink()

    #the teacher who referred this one to signup
    whoReferred = accounts.getTeacher(referrer)

    #list of people with the same email
    alreadyRegistered = accounts.getTeacher(email)

    if not(alreadyRegistered):
        #send email here
        sendRegistrationEmail(email, referrer, verificationLink)
        addTeacher( email, verificationLink )

        return True
    return False

@app.route("/", methods=["GET", "POST"])
def root():
    if 'user' in session:
        #status will always be set if user's set
        if session['status'] == "student":
            student = accounts.getStudent(session['user'])
            if student:
                #home page of classes
                return redirect( url_for( 'home', notifications = None ) )
            else:
                #cant find account, prolly error so force logout and go to login page
                del session['user']
                return render_template("index.html", message = "Account error. Please try logging in again.")
        #wowee we got ourrselves a teacher on our hands
        else:
            teacher = accounts.getTeacher(session['user'])
            if teacher:
                #home page of classes / notifications
                #replace current notifications with this once ayman makes it
                #utils.getTeacherNotifications(teacher['email'])
                return redirect( url_for( 'home', notifications = None ) )
            else:
                #cant find account, prolly error so force logout and go to login page
                del session['user']
                return render_template("index.html", message = "Account error. Please try logging in again.")
    else:
        print request.form
        #User is Not Logged In
        # FOR STUDENTS
        if request.form:
            if request.form["submit"]=="login":
                email = request.form["email"]
                pwd = request.form["pwd"]
                check = accounts.confirmStudent(email, pwd)
                #if account exists
                if check:
                    #if verified
                    if check[0]:
                        #password correct
                        if check[1]:
                            session['status'] = 'student'
                            session['user'] = email
                            session['verified'] = True
                            return redirect( url_for( 'home') )
                        #password incorrect
                        else:
                            return render_template("index.html", message = "Incorrect Password")
                    #if not verified
                    else:
                        #print accounts.getStudent(email)['verificationLink']
                        return render_template("index.html", message = "Your account isn't verified!", verificationLink = accounts.getStudent(email)['verificationLink'])
                else:

                    #now moving onto teachers
                    check = accounts.confirmTeacher(email, pwd)
                    if check:
                        if check[0]:
                            if check[1]:
                                session['status'] = 'teacher'
                                session['user'] = email
                                session['verified'] = True
                                return redirect( url_for( 'home' ))
                            else:
                                return render_template("index.html", message = "Incorrect Password")
                        else:
                            return render_template("index.html", message = "Your account isn't verified, please check your email to enable your account.")
                    else:
                        return render_template("index.html", message = "Account doesn't exist.")

            elif request.form["submit"]=="signup":
                email = request.form["email"]
                pwd = request.form["pwd"]
                pwd2 = request.form["pwd2"]
                registerStudent(email, email, '', '',pwd, pwd2)
                return render_template("index.html", message = "Signed up!")
        else:
            if 'message' in request.args:
                return render_template("index.html", message = request.args['message'])
            else:
                return render_template("index.html")

@app.route("/home")
def home():
    if 'user' in session:
        return render_template("home.html", status = session['status'], verified = session['verified'] )
    else:
        return redirect( url_for("root", message = "Please Login or Sign-Up First") )

@app.route("/verify/<link>")
def verify(link):
    #print link
    #print accounts.getAccount(link)
    email = accounts.getAccount(link)[0]['email']
    accounts.updateField(email, 'verified', True, True, "student")
    return redirect(url_for('home'))

@app.route("/logout")
@app.route("/logout/")
def logout():
    session.pop("user")
    session.pop("status")
    return redirect( url_for("root", message = "Logout Successful"))

@app.route("/classes", methods=["POST", "GET"])
def classes():
    if 'user' in session:
        if session['status'] == 'student':
            if request.method=="POST":
                code = request.form["code"]
                period = request.form["period"]
                returnVal = classy.addToClass(code + "-" + period, session['user'])
                if returnVal != True:
                    return render_template("classes.html", status=session['status'], verified=session['verified'], your_classes = classy.getStudentClasses(session['user']), errorMessage=returnVal)
            your_classes = classy.getStudentClasses( session['user'] )
        elif session['status'] == 'teacher':
            your_classes = classy.getTeacherClasses( session['user'] )
        return render_template("classes.html", status = session['status'], verified=session['verified'], your_classes=your_classes)
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))

@app.route("/createClass", methods=['GET', 'POST'])
def createaClass():
    if 'user' in session:
        if request.form:
            if 'className' in request.form:
                print request.form
                classy.createClass( session['user'], request.form )
                return redirect( url_for( 'classes', message = "Class Creation Successful" ))
        elif request.args:
            if 'message' in request.args:
                return render_template( "createClass.html", message = request.args['message'])
            else:
                print request.args
        else:
            if session['status'] != 'teacher':
                session.pop('user')
                session.pop('status')
                session.pop('verified')
                return redirect( url_for( "root", message = "Please Sign in as a Teacher to Access the Class Creation Feature" ) )
            return render_template( "createClass.html", status = session['status'], verified=session['verified'] )
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))

@app.route("/class/<classCode>")
def viewClass(classCode):
    if 'user' in session:
        message = ""
        if request.args:
            if message in request.args:
                message = request.args['message']

        if session['status'] == 'teacher':
            theClass = classy.getClass(classCode)
            periods = classy.getStudentsInYourClass(classCode, 0)
            return render_template("class.html", status = session['status'], verified=session['verified'], className = theClass['className'], classCode = classCode, periods=periods, message=message, assignments=assign.getAssignments(classCode))

        else:
            codetemp = classCode.split("-")
            code = codetemp[0]
            pd = codetemp[1]
            theClass = classy.getClass(code)
            peepsInfo = classy.getStudentsInYourClass(code, pd)
            #print peepsInfo
            peeps = [ accounts.getStudentName(email)['firstName'] + " " + accounts.getStudentName(email)['lastName'] for email in peepsInfo['students'] ]
            return render_template("class.html", status = session['status'], verified=session['verified'], className = theClass['className'], classCode = classCode, peeps=peeps, message=message,  assignments=assign.getAssignments(code))
    else:
        return redirect( url_for( "root", message = "Please Sign In First", ccode=classCode ))

@app.route("/leaveClass/<code>", methods=["POST"])
def leaveClass(code):
    classy.leaveClass(code, session['user'])
    return redirect(url_for("classes"), message = "You have left the class.")

@app.route("/changeClassName", methods=['POST'])
def changeClassName():
    if request.form:
        print request.form
        classy.updateName( request.form['code'], request.form['newName'])
        return "sucess"
    else:
        return "error"

@app.route("/createAssignment", methods=['GET', 'POST'])
def createAnAssignment():
    if 'user' in session:
        if session['status'] != 'teacher':
            session.pop('user')
            session.pop('status')
            session.pop('verified')
            return redirect( url_for( "root", message = "Please Sign in as a Teacher to Access the Assignment Creation Feature" ) )
        if request.form:
            if 'assignmentName'and'classCode' and 'dueDate' and 'details' in request.form:
                returnVal = assign.createAssignment( request.form['assignmentName'], request.form['classCode'], request.form['uploadDate'], request.form['reviewDate'], True if 'groupsAllowed' in request.form else False, request.form['details'] )
                if returnVal != True:
                    return render_template("createAssignment.html", status=session['status'], verified=session['verified'], classCode=request.form['classCode'], message = "", errorMessage = returnVal, minDate = "%s-%s-%s"%(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
                return redirect( url_for( "viewClass", classCode=request.form['classCode'], message = "Assignment Created"))
        elif request.args:
            message = ""
            if message in request.args:
                message = request.args['message']
            return render_template("createAssignment.html", status=session['status'], verified=session['verified'], classCode=request.args['classCode'], message = message, minDate = "%s-%s-%s"%(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day))
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))

@app.route("/class/<code>/createGroup", methods=['GET', 'POST'])
def createaGroup(code):
    if 'user' in session:
        if request.form:
            if 'groupName' in request.form:
                groups.createGroups( session['user'], '', request.form['groupName'], '5') # we need a way to get group limit
                return redirect( url_for( 'groups', message = "Group Creation Successful", code=code ))
        elif request.args:
            if 'message' in request.args:
                return render_template( "createGroup.html", message = request.args['message'], code=code)
            else:
                print request.args
        else:
            return render_template( "createGroup.html", status = session['status'], verified=session['verified'], code=code )
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))



@app.route("/settings", methods=["GET", "POST"])
def profile():
    if request.method=="POST":
        message = ""
        if request.form['submit']=="Submit FirstName":
            accounts.updateField(session['user'], 'profile', request.form["fname"], 'firstName', session['status'])
        elif request.form['submit']=="Submit LastName":
            accounts.updateField(session['user'], 'profile', request.form["lname"],'lastName', session['status'])
        elif request.form['submit'] == "Submit Password":
            accounts.updateField(session['user'], 'password', request.form["new_password"], request.form["confirm_password"], session['status'])
            message = "Password updated."
        #inviting a new teacher
        elif request.form['submit'] == "Send Invitation Email" and session['status'] == "teacher":
            if "email" in request.form:
                registerTeacher(session['user'], request.form["email"])
                message = "Invitation sent."
            else:
                message = "Please enter an email!"
        return render_template("profile.html", status = session['status'], verified=session['verified'], errorMessage = message )
    return render_template("profile.html", status = session['status'], verified=session['verified'] )

#just a placeholder, there's no groups.html rn
@app.route("/groups", methods=["POST", "GET"])
def groups():
    if 'user' in session:
        if session['status'] == 'student':
            pass
            #your_groups = groupy.getStudentGroups( session['user'] )
        elif session['status'] == 'teacher':
            pass
            #your_groups = groupy.getTeacherGroups( session['user'] )
        return render_template( "base.html" , status = session['status'], verified = session['verified'] )
        #return render_template("class.html", status = session['status'], verified=True)
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))

@app.route("/assignment/<assignmentID>/<studentEmail>", methods=["GET", "POST"])
def assignmentStudent(assignmentID, studentEmail):
    if 'user' in session:
        if session['status'] == 'teacher':
            assignmentName = assign.getAssignmentsByID(assignmentID)[0]['assignmentName']
            response = assign.teacherGetResponse(studentEmail, assignmentID)
            assignedTo = assign.getAssignedTo(assignmentID, studentEmail)
            return render_template("assignmentInner.html", status = session['status'], verified=session['verified'], studentName=response[0], submissionDate=response[1], assignmentName=assignmentName, response= response[2], link=False, comments = assign.getComments(studentEmail, assignmentID, session['status']), assignedTo = assignedTo )
        else:
            return redirect( url_for( "root", message = "You aren't allowed here." ))
    else:
        return redirect( url_for( "root", message = "Please Sign In First", code=classCode ))

@app.route("/deleteAssignment/<assignmentID>")
def deleteAssignment(assignmentID):
    if 'user' in session:
        if session['status'] == 'teacher':
            assign.deleteAssignment(assignmentID)
    return redirect(url_for("classes"))

@app.route("/assignment/<assignmentID>", methods=["GET", "POST"])
def assignment(assignmentID):
    if 'user' in session:
        if session['status'] == 'teacher':
            assignments = assign.getAssignmentsByID(assignmentID)
            responses = assign.teacherGetAssignments(assignments, assignmentID, 0, '')
            reviews = assign.teacherGetReviews(assignmentID)
            return render_template("assignment.html", status = session['status'], verified=session['verified'], assignments=assignments, ID=assignmentID, onTime=responses['onTime'], late=responses['late'], link=True, codeReview = assign.getCodeReviewStatus(assignmentID), reviewed = reviews['reviewed'], unreviewed = reviews['unreviewed'] )
        else:
            if request.method=="POST":
                upload_file(assignmentID)
            assignments= '' #assign.getAssignmentsByID(assignmentID)
            try: prevFiles = assign.getAssignmentSubmission(session['user'], assignmentID)
            except: prevFiles = ''
            return render_template("assignment.html", status = session['status'], verified=session['verified'], assignments=assignments, link=prevFiles, comments = assign.getComments(session['user'], assignmentID, session['status']))
    else:
        return redirect( url_for( "root", message = "Please Sign In First", code=classCode ))

@app.route("/enableReviews/<assignmentID>", methods = ["GET", "POST"])
def enableReviews(assignmentID):
    assign.enableReviews(assignmentID, 2)
    assign.assignRandomReviews(assignmentID, 2)
    return redirect(url_for("assignment", assignmentID = assignmentID))

@app.route("/reviews")
def viewStudentClasses():
    return render_template("reviews.html", status = session['status'], verified = session['verified'], classes = classy.getStudentClasses(session['user']))

@app.route("/reviews/class/<classCode>")
def viewStudentClass(classCode):
    if 'user' in session:
        codetemp = classCode.split("-")
        code = codetemp[0]
        pd = codetemp[1]
        theClass = classy.getClass(code)
        peepsInfo = classy.getStudentsInYourClass(code, pd)
        #print peepsInfo
        peeps = peepsInfo['students']
        return render_template("reviews.html", status = session['status'], verified = session['verified'], className = theClass['className'], assignments = assign.getAssignments(code))
    else:
        return redirect( url_for( "root", message = "Please Sign In First"))

@app.route("/reviews/assignment/<assignmentID>", methods=["GET", "POST"])
def getAssignmentToReview(assignmentID):
    if 'user' in session:
        #here is the comments for the code
        if request.form:
            if "comments" in request.form:
                assign.submitComment(request.form['comments'], request.form['owner'], session['user'], assignmentID)
                return render_template("reviews.html", errorMessage = "Your comment has been submitted.", status = session['status'], verified = session['verified'], classes = classy.getStudentClasses(session['user']))

        assignedCodes = assign.getAssignedCodes(session['user'], assignmentID)
        if (assignedCodes != []):
            return render_template("reviews.html", status = session['status'], verified = session['verified'], codeToReview = assignedCodes, codeSource = "Random Person's", assignment = assign.getAssignmentsByID(assignmentID)[0])
        else:
            return render_template("reviews.html", status = session['status'], verified = session['verified'], message = "You haven't been assigned any code to review for this assignment yet.")
    else:
        return redirect( url_for( "root", message = "Please Sign In First"))

#This is used by the until now not in use file upload functionallity
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#This is used by the until now not in use file upload functionallity
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
def upload_file(ID):
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        buffer = []
        buffer.append("Content-type: %s" % file.content_type)
        buffer.append("File content: %s" % file.stream.read())
        upload = '|'.join(buffer)
        fileID = files.uploadFile(upload, session['user'], ID)
        accounts.addStudentFile(session['user'], ID, fileID)
        assign.submitAssignment(session['user'], ID)
        return redirect(url_for('assignment', assignmentID=ID))
    else:
        return "Not accepted file"


if __name__ == "__main__":
    app.debug = True
    app.run()
