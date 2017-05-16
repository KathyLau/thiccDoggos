from flask import Flask, render_template, request, session, redirect, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from utils import utils, accounts

#connect to mongo
connection = MongoClient("localhost", 27017, connect = False)
db = connection['database']
students = db['students']
teachers = db['teachers']
classes = db['classes']

#get secret data
secrets = utils.getSecretData()

app = Flask(__name__)
mail = Mail(app)
app.secret_key = secrets['app-secret-key']

UPLOAD_FOLDER = './static/images/'
ALLOWED_EXTENSIONS = set(['java', 'py', 'rkt', 'nlogo'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#mail configs
app.config['MAIL_SERVER'] ='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = secrets['email']
app.config['MAIL_PASSWORD'] = secrets['email-password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#registers student and adds to database, stills requires email verif.
#sends verification email
#returns false if not registered
def registerStudent(email, email2, firstname, lastname, password1, password2):
    #check if email/password + confirm email/password are same
    if email1 != email2:
        return False
    if password1 != password2:
        return False

    #create verification link/profile link
    verificationLink = utils.getVerificationLink()
    
    #list of people with the same email
    alreadyRegistered = list(db.students.find( { 'email': email } ))
    #checks if above is empty
    if not(alreadyRegistered):
        #send email here
        message = Message()
        message.recipients = [ email1 ]
        message.subject = "Confirm Your StuyCS Code Review Account"
        message.html = '''
        <center>
        <h1 style="font-weight: 500 ; font-family: Arial">StuyCS Code Review</h1>
        <p style="font-weight: 500 ; font-family: Arial">Thanks for signing up for StuyCS Code Review! Please press the button below to verify your account.</p>
        <br>
        <a href="%s" style="padding: 5% ; text-decoration: none ; border: 1px solid black ; text-transform: uppercase ; font-weight: 500 ; font-family: Arial ; padding-left: 10% ; padding-right: 10%">Verify Email</a>
        </center>
        ''' % ("127.0.0.1:5000/verify/" + verificationLink)
        mail.send(message)
        
        
        #add to db here, only password is hashed
        db.students.insert_one(
            {
                'email': email1,
                'password': hash(password1),
                'verified': False,
                'verificationLink': verificationLink,
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

@app.route("/")
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
        return render_template("index.html")

@app.route("/home")
def home( **kargs ):
    if 'user' in session:
        return render_template("home.html", status = session['status'], verified =  kargs['verified'] )
    else:
        return redirect( url_for("root", message = "Please Login or Sign-Up First") )



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
            info = idek(filename)
            os.remove(UPLOAD_FOLDER + filename) # remove file after parsing imge
            return redirect(url_for('main'))
        else:
            return "Not accepted file"

if __name__ == "__main__":
    app.debug = True
    app.run()
