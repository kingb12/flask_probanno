import os

from flask import Flask, request, redirect, make_response, render_template, jsonify
from flask import flash
import utils

import data.database as db
from controllers import session_management, model_management, probanno_management, job

import ConfigParser

PUT = 'PUT'
POST = 'POST'
GET = 'GET'

DATABASE = '/data/db/probannoweb.db'
UPLOAD_FOLDER = '/tmp/'
MODEL_TEMPLATES_FOLDER = '/../probanno_standalone/templates/'
UNIVERSAL_MODELS_FOLDER = '/data/universal/'
ALLOWED_EXTENSIONS = {'json', 'fasta', 'fa'}
SOLVER = 'gurobi'

# Set up on first run
app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read(os.path.realpath(__file__) + '/deploy.cfg')
app.config['MODEL_TEMPLATES'] = os.path.dirname(os.path.realpath(__file__)) + MODEL_TEMPLATES_FOLDER if not config.has_option('flask_probanno', 'model_templates_folder') else config.get('flask_probanno', 'model_templates_folder')
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__)) + UPLOAD_FOLDER
app.config['UNIVERSAL_MODELS'] = os.path.dirname(os.path.realpath(__file__)) + UNIVERSAL_MODELS_FOLDER
app.config['SOLVER'] = SOLVER
db.set_db(app, os.path.dirname(os.path.realpath(__file__)) + DATABASE)


@app.route('/')
def home_page():
    resp = make_response(render_template("index.html"))
    if session_management.has_session():
        session = session_management.get_session_id()
    else:
        session_id = session_management.prepare_new_session()
        resp.set_cookie(session_management.SESSION_ID, session_id)
    return resp

@app.route('/gapfillmodel')
def gapfill_view():
    return make_response(render_template("gapfill.html"))

@app.route('/api/session', methods=[GET])
def get_session():
    return jsonify(session_management.prepare_new_session())

@app.route('/api/io/uploadmodel', methods=[GET, POST])
def upload_model():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        filename = utils.upload_file(app, file, ALLOWED_EXTENSIONS)
        model_management.load_model(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect('/')
    return '''
    <!doctype html>
    <title>Upload new Model (JSON format)</title>
    <h1>Upload new Model (JSON  format)</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
    # TODO: Replace this with something nicer. Models View page, hiding the 'get' aspect of this API?


@app.route('/api/probanno/calculate', methods=[GET, PUT])
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


@app.route('/api/list/model')
def list_models():
    return model_management.list_models()


@app.route('/api/list/probanno')
def list_probannos():
    return probanno_management.list_probannos()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/api/io/downloadprobanno')
def download_probanno():
    return probanno_management.download_probanno(app)

@app.route('/api/io/downloadmodel')
def download_model():
    return model_management.download_model(app)

@app.route('/api/job/checkjob')
def check_job():
    return job.check_job()

@app.route('/api/list/job')
def list_jobs():
    return job.list_jobs()


@app.route('/view/probanno/complete')
def probanno_complete():
    return probanno_management.probanno_complete_view()

@app.route('/view/model/complete')
def model_complete():
    return model_management.model_complete_view()

@app.route('/aboutProbAnno.html')
def about():
    return render_template("aboutProbAnno.html")

@app.route('/view/job/status')
def job_status():
    return job.view_status()

if __name__ == '__main__':
    app.run()

