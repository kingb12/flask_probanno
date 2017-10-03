import os

from flask import Flask, request, redirect, make_response, render_template, jsonify
from flask_swagger import swagger
from flask import flash
import utils

import data.database as db
from controllers import session_management, model_management, probanno_management, job

import ConfigParser

PUT = 'PUT'
POST = 'POST'
GET = 'GET'

DATABASE = '/data/probanno.db'
UPLOAD_FOLDER = '/tmp/'
MODEL_TEMPLATES_FOLDER = '/probannoenv/src/probanno/templates/'
UNIVERSAL_MODELS_FOLDER = '/data/universal/'
ALLOWED_EXTENSIONS = {'json', 'fasta', 'fa'}
SOLVER = 'cplex'

# Set up on first run
app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read(os.path.realpath(__file__) + '/deploy.cfg')
app.config['MODEL_TEMPLATES'] = os.path.dirname(os.path.realpath(__file__)) + MODEL_TEMPLATES_FOLDER if not config.has_option('flask_probanno', 'model_templates_folder') else config.get('flask_probanno', 'model_templates_folder')
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__)) + UPLOAD_FOLDER
app.config['UNIVERSAL_MODELS'] = os.path.dirname(os.path.realpath(__file__)) + UNIVERSAL_MODELS_FOLDER
app.config['SOLVER'] = SOLVER
db.set_db(app, os.path.dirname(os.path.realpath(__file__)) + DATABASE)

#  ROUTES: Below are definitions for what occurs when a URL is reached using one of the HTTP methods. In short, the
#  route tag calls the function whenever a request targets a particular URL. These are separated into two sections, one
#  for views and functions related to the web-site, and ones beginning with /api/, which are for the underlying web
#  web service.

#  VIEW ROUTES

@app.route('/')
def home_page():
    # Displays the users home page
    resp = make_response(render_template("index.html"))
    if session_management.has_session():
        session = session_management.get_session_id()
    else:
        session_id = session_management.prepare_new_session()
        resp.set_cookie(session_management.SESSION_ID, session_id)
    return resp

@app.route('/gapfillmodel')
def gapfill_view():
    # Displays a page for submission of gap-filling jobs
    return make_response(render_template("gapfill.html"))


@app.route('/view/probanno/complete')
def probanno_complete():
    # Displays a page indicating a probanno job has completed, and provides a download link
    return probanno_management.probanno_complete_view()


@app.route('/view/model/complete')
def model_complete():
    # Displays a page indicating a gapfill job has completed, and provides a download link
    return model_management.model_complete_view()

@app.route('/aboutProbAnno.html')
def about():
    # Displays an about page
    return render_template("aboutProbAnno.html")

@app.route('/view/job/status')
def job_status():
    # Displays a page with information on a job. Has some status-checking logic, but eventually a template is rendered
    return job.view_status()


# API ROUTES

@app.route('/api/session', methods=[GET])
def get_session():
    return jsonify(session_management.prepare_new_session())


@app.route('/api/model', methods=[PUT, POST])
def upload_model():
    if request.method == POST or request.method == PUT:
        return model_management.load_model(app)


@app.route('/api/model', methods=[GET])
def get_model():
    if request.method == GET:
        return model_management.get_model(app)


@app.route('/api/probanno/calculate', methods=[GET, PUT])
def get_reaction_probabilities():
    return probanno_management.get_reaction_probabilities(app)


@app.route('/api/probanno', methods=[GET])
def get_probanno():
    return probanno_management.get_probanno()


@app.route('/api/model/gapfill')
def gapfill():
    return model_management.gapfill_model(app)


@app.route('/api/model/runfba')
def run_fba():
    return model_management.run_fba()


@app.route('/hello')
def hello():
    return 'hello'


@app.route('/api/model/list')
def list_models():
    return model_management.list_models()


@app.route('/api/probanno/list')
def list_probannos():
    return probanno_management.list_probannos()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/api/probanno/download')
def download_probanno():
    return probanno_management.download_probanno(app)


@app.route('/api/model/download')
def download_model():
    return model_management.download_model(app)


@app.route('/api/job/checkjob')
def check_job():
    return job.check_job()


@app.route('/api/job/list', methods=[GET])
def list_jobs():
    return job.list_jobs()


@app.route('/spec')
def spec():
    # Renders the template indicating the API specification. Make sure the file is up to date!
    # Basic workflow I follow
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Probanno API"
    return jsonify(swag)


@app.route('/api/job', methods=[GET])
def get_job():
    return job.get_job()


if __name__ == '__main__':
    app.run()

