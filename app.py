from flask import Flask, render_template, request, session, redirect, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from utils import utils, accounts, classy
import os

#connect to mongo
connection = MongoClient("localhost", 27017, connect = False)
db = connection['database']
students = db['students']
teachers = db['teachers']
classes = db['classes']

#get secret data
#secrets = utils.getSecretData() #Can't Do this cause no secrets.txt on heroku (gotta deploy manually LMAO)

app = Flask(__name__)
mail = Mail(app)
app.secret_key = os.environ['app-secret-key']

UPLOAD_FOLDER = './data/'
ALLOWED_EXTENSIONS = set(['java', 'py', 'rkt', 'nlogo'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#mail configs
app.config['MAIL_SERVER'] ='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ['email']
app.config['MAIL_PASSWORD'] = os.environ['email-password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

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
    alreadyRegistered = list(db.students.find( { 'email': email } ))
    #checks if above is empty
    if not(alreadyRegistered):
        #send email here
        message = Message()
        message.recipients = [ email ]
        message.subject = "Confirm Your StuyCS Code Review Account"
        message.html = '''
        <center>
        <h1 style="font-weight: 500 ; font-family: Arial">StuyCS Code Review</h1>
        <p style="font-weight: 500 ; font-family: Arial">Thanks for signing up for StuyCS Code Review! Please press the button below to verify your account.</p>
        <br>
        <a href="%s" style="padding: 5% ; text-decoration: none ; border: 1px solid black ; text-transform: uppercase ; font-weight: 500 ; font-family: Arial ; padding-left: 10% ; padding-right: 10%">Verify Email</a>
        </center>
        '''.format("127.0.0.1:5000/verify/" + verificationLink)
        mail.send(message)
        addStudent( email1, password1, firstName, lastName, verificationLink )
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
        message = Message()
        message.recipients = [ email ]
        message.subject = "Create Your StuyCS Code Review Account"
        message.html = '''
        <center>
        <h1 style="font-weight: 500 ; font-family: Arial">StuyCS Code Review</h1>
        <p style="font-weight: 500 ; font-family: Arial">%s has referred you to join StuyCS Code Review as a teacher. Please press the button below to create your teacher account.</p>
        <br>
        <a href="%s" style="padding: 5% ; text-decoration: none ; border: 1px solid black ; text-transform: uppercase ; font-weight: 500 ; font-family: Arial ; padding-left: 10% ; padding-right: 10%">Create Account</a>
        </center>
        ''' % (whoReferred['name'], "127.0.0.1:5000/verify/" + verificationLink)
        mail.send(message)

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
                return redirect( url_for( 'home', verified = student['verified'], notifications = None ) )
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
                return redirect( url_for( 'home', verified = student['verified'], notifications = None ) )
            else:
                #cant find account, prolly error so force logout and go to login page
                del session['user']
                return render_template("index.html", message = "Account error. Please try logging in again.")
    else:
        #User is Not Logged In
        # FOR STUDENTS
        if request.method=="POST":
            if request.form["submit"]=="login":
                email = request.form["email"]
                pwd = request.form["pwd"]
                #print accounts.getStudent(email)
                if accounts.confirmStudent(email, pwd): # and fxn to check pass
                    session['status'] = 'student'
                    session['user'] = email
                elif accounts.confirmTeacher( email, pwd ):
                    session['status'] = 'teacher'
                    session['user'] = email
                return redirect( url_for( 'home') )
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

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect( url_for("root", message = "Logout Successful") )

@app.route("/classes")
def classes():
    if 'user' in session:
        if session['status'] == 'student':
            your_classes = classy.getStudentClasses( session['user'] )
        elif session['status'] == 'teacher':
            your_classes = classy.getTeacherClasses( session['user'] )
        return render_template("classes.html", status = session['status'], verified=True, your_classes=your_classes)
    else:
        return redirect( url_for( "root", message = "Please Sign In First" ))

@app.route("/createClass", methods=['GET', 'POST'])
def createaClass():
    if 'user' in session:
        if request.form:
            if 'className' in request.form and 'groupLimit' in request.form:
                classy.createClass( session['user'], request.form['className'], request.form['groupLimit'])
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
                return redirect( url_for( "root", message = "Please Sign in as a Teacher to Access this Feature" ) )
            return render_template( "createClass.html", status = session['status'], verified=True )
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

@app.route("/class/<classCode>")
def viewClass(classCode):
    if 'user' in session:
        if session['status'] == 'student':
            #Insert Student end of Class
            pass
        else:
            return classCode
            pass
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
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method=='GET':
        return render_template('upload.html')
    else:
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return redirect(url_for('upload_file'))
        else:
            return "Not accepted file"

if __name__ == "__main__":
    app.debug = True
    app.run()
