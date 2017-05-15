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

'''
used by the upload functionallity
for hw files
'''
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
