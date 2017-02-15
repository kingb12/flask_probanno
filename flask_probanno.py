import os

from flask import Flask, request, redirect, make_response, render_template
from flask import flash
from werkzeug.utils import secure_filename

import data.database as db
from controllers import session_management, model_management, probanno_management

import ConfigParser

PUT = 'PUT'
POST = 'POST'
GET = 'GET'

DATABASE = '/data/db/probannoweb.db'
UPLOAD_FOLDER = '/tmp/'
MODEL_TEMPLATES_FOLDER = '/probannoenv/src/probanno/templates/'
ALLOWED_EXTENSIONS = {'json'}

# Set up on first run
app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read(os.path.realpath(__file__) + '/deploy.cfg')
app.config['MODEL_TEMPLATES'] = os.path.dirname(os.path.realpath(__file__)) + MODEL_TEMPLATES_FOLDER if not config.has_option('flask_probanno', 'model_templates_folder') else config.get('flask_probanno', 'model_templates_folder')
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__)) + UPLOAD_FOLDER
db.set_db(app, os.path.dirname(os.path.realpath(__file__)) + DATABASE)


@app.route('/')
def home_page():
    if session_management.has_session():
        session = session_management.get_session_id()
    else:
        session_id = session_management.prepare_new_session()
        resp = make_response("Hello Stranger")
        resp.set_cookie(session_management.SESSION_ID, session_id)
    return render_template('index.html')

@app.route('/api/io/uploadmodel', methods=[GET, POST])
def upload_model():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            model_management.load_model(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'Saved!'
    return '''
    <!doctype html>
    <title>Upload new Model (JSON format)</title>
    <h1>Upload new Model (JSON  format)</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''  # TODO: Replace this with something nicer. Models View page, hiding the 'get' aspect of this API?


@app.route('/api/probanno/calculate', methods=[GET])
def get_reaction_probabilities():
    return probanno_management.get_reaction_probabilities(app)


@app.route('/api/model/gapfill')
def gapfill():
    return model_management.gapfill_model(app)


@app.route('/api/model/runfba')
def run_fba():
    return model_management.run_fba()


@app.route('/api/model/addreactions')
def add_reactions():
    return "Not Implemented"

@app.route('/hello')
def hello():
    return 'hello'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run()

