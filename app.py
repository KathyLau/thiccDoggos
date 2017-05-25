from flask import Flask, render_template, request, session, redirect, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from utils import utils, accounts, classy, groupy
from threading import Thread
import os

#connect to mongo
#connection = MongoClient("localhost", 27017, connect = False)
connection = MongoClient("127.0.0.1")
db = connection['STUYCS_CODE_REVIEW']
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

def registerTeacher(referrer, email, email1):
    if email != email1:
        return False
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
                return render_template("index.html", message = "Signed up ! ")
        else:
            if 'message' in request.args:
                return render_template("index.html", message = request.args['message'])
            else:
                return render_template("index.html")

@app.route("/home")
def home():
    if 'user' in session:
        return render_template("home.html", status = session['status'], verified = True )
    else:
        return redirect( url_for("root", message = "Please Login or Sign-Up First") )

@app.route("/verify/<link>")
def verify(link):
    #print link
    #print accounts.getAccount(link)
    email = accounts.getAccount(link)[0]['email']
    accounts.updateField(email, 'verified', True, True)
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.pop("user")
    session.pop("status")
    return redirect( url_for("root", message = "Logout Successful") )

@app.route("/classes", methods=["POST", "GET"])
def classes():
    if 'user' in session:
        if session['status'] == 'student':
            if request.method=="POST":
                code = request.form["class_code"]
                classy.addToClass(code, session['user'])
            your_classes = [ ] #classy.getStudentClasses( session['user'] )
        elif session['status'] == 'teacher':
            your_classes = classy.getTeacherClasses( session['user'] )
        return render_template("classes.html", status = session['status'], verified=True, your_classes=your_classes)
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
                return redirect( url_for( "root", message = "Please Sign in as a Teacher to Access the Class Creation Feature" ) )
            return render_template( "createClass.html", status = session['status'], verified=True )
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))

@app.route("/class/<classCode>")
def viewClass(classCode):
    if 'user' in session:
        if session['status'] == 'teacher':
            #Insert Student end of Class
            return render_template("class.html", status = session['status'], verified=True, )
        else:
            return classCode
            pass
    else:
        return redirect( url_for( "root", message = "Please Sign In First", ccode=classCode ))

@app.route("/changeClassName", methods=['POST'])
def changeClassName():
    if request.form:
        
    else:
        return "error"
    
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
            return render_template( "createGroup.html", status = session['status'], verified=True, code=code )
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))



@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method=="POST":
        if request.form['submit']=="Submit Email":
            accounts.updateField(session['user'], 'email', request.form["new_email"], request.form["confirm_email"])

        else:
            accounts.updateField(session['user'], 'password', request.form["new_password"], request.form["confirm_password"])
    return render_template("profile.html", status = session['status'], verified=True)

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

        return render_template("class.html", status = session['status'], verified=True)
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))



#This is used by the until now not in use file upload functionallity
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#This is used by the until now not in use file upload functionallity
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
#used by the upload functionallity
#for hw files
@app.route('/upload/<assignmentName>', methods=['GET', 'POST'])
def upload_file(assignmentName):
    if request.method=='GET':
        return render_template('upload.html', status = session['status'],verified=True)
    else:
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename[filename.find('.'):]
            filename = session['user']+'-'+assignmentName + ext

            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return redirect(url_for('upload_file',assignmentName=assignmentName))
        else:
            return "Not accepted file"

if __name__ == "__main__":
    app.debug = True
    app.run()
