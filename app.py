from flask import Flask, render_template, request, session, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'dogs'

UPLOAD_FOLDER = './static/images/'
ALLOWED_EXTENSIONS = set(['java', 'py', 'rkt', 'nlogo'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#This is used by the until now not in use file upload functionallity
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#This is used by the until now not in use file upload functionallity
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
                               
@app.route("/")
def root():
    if user in session:
        return redirect(url_for('studentHome')) if session['status'] == 'student' else redirect(url_for('teacherHome'))
    else:
        return render_template("index.html")

@app.route("/studentHome")
def studentHome():
    pass

@app.route("/teacherHome")
def teacherHome():
    pass

    
if __name__ == "__main__":
    app.debug = True
    app.run()
