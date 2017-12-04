import json
import os

from flask import Flask, request, redirect, make_response, render_template, jsonify
from flask_swagger import swagger
from flask import flash
import utils

import data.database as db
from controllers import session_management, model_management, probanno_management, job

import ConfigParser
import sys

PUT = 'PUT'
POST = 'POST'
GET = 'GET'

DATABASE = '/data/probanno.db'
UPLOAD_FOLDER = '/tmp/'
MODEL_TEMPLATES_FOLDER = '/probannoenv/src/probanno/templates/'
UNIVERSAL_MODELS_FOLDER = '/data/universal/'
ALLOWED_EXTENSIONS = {'json', 'fasta', 'fa'}
SOLVER = 'gurobi'

os.environ["GUROBI_HOME"] = "/users/bking/gurobi751/linux64"
os.environ["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"] + ":" + os.environ["GUROBI_HOME"] if "LD_LIBRARY_PATH" in os.environ else os.environ["GUROBI_HOME"]
sys.path.append(os.environ["GUROBI_HOME"] + "/bin")

# Set up on first run
app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read(os.path.realpath(__file__) + '/deploy.cfg')
app.config['MODEL_TEMPLATES'] = os.path.dirname(os.path.realpath(__file__)) + MODEL_TEMPLATES_FOLDER \
    if not config.has_option('flask_probanno', 'model_templates_folder') \
    else config.get('flask_probanno', 'model_templates_folder')
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__)) + UPLOAD_FOLDER
app.config['UNIVERSAL_MODELS'] = os.path.dirname(os.path.realpath(__file__)) + UNIVERSAL_MODELS_FOLDER
app.config['SOLVER'] = SOLVER

# Establish a database connection with our sqlite DB
db.set_db(app, os.path.dirname(os.path.realpath(__file__)) + DATABASE)

#  ROUTES: Below are definitions for what occurs when a URL is reached using one of the HTTP methods. In short, the
#  route tag calls the function whenever a request targets a particular URL. These are separated into two sections, one
#  for views and functions related to the web-site, and ones beginning with /api/, which are for the underlying web
#  web service. API documentation can be found at /swagger and is defined in swagger-yaml/swagger.yaml. Changes to APIs
#  Should be reflected in the API documentation

# ================ API ROUTES ==========================================================================================


# Session APIs
@app.route('/api/session', methods=[GET])
def get_session():
    return jsonify(session_management.prepare_new_session())


@app.route('/session/clear', methods=[GET])
def clear_session():
    return session_management.clear_session()


# Probanno APIs
@app.route('/api/probanno', methods=[GET])
def get_probanno():
    return probanno_management.get_probanno()


@app.route('/api/probanno/list')
def list_probannos():
    return probanno_management.list_probannos()


@app.route('/api/probanno/calculate', methods=[GET, PUT])
def get_reaction_probabilities():
    return probanno_management.get_reaction_probabilities(app)


@app.route('/api/probanno/download')
def download_probanno():
    return probanno_management.download_probanno(app)


# Model APIs
@app.route('/api/model', methods=[PUT, POST])
def upload_model():
    if request.method == POST or request.method == PUT:
        return model_management.load_model(app)


@app.route('/api/model', methods=[GET])
def get_model():
    if request.method == GET:
        return model_management.get_model(app)


@app.route('/api/model/gapfill')
def gapfill():
    return model_management.gapfill_model(app)


@app.route('/api/model/list')
def list_models():
    return model_management.list_models()


@app.route('/api/model/download')
def download_model():
    return model_management.download_model(app)


# Job APIs
@app.route('/api/job', methods=[GET])
def get_job():
    return job.get_job()


# Hidden/non-public APIs
@app.route('/api/model/runfba')
def run_fba():
    return model_management.run_fba()


@app.route('/hello')
def hello():
    return 'hello'


@app.route('/api/job/checkjob')
def check_job(job_id=None):
    return job.check_job(job_id)


@app.route('/api/job/list', methods=[GET])
def list_jobs():
    return job.list_jobs()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Hack for navigating from home form submit to probanno job page
@app.route('/submit/probanno/calculate', methods=[POST, GET])
def submit_probanno_calculate():
    response = get_reaction_probabilities()
    if response.status_code != 200:
        return response
    job = json.loads(response.response[0])
    return job_status(job['jid'])


# Upload a model in the home page
@app.route('/submit/model/upload', methods=[POST])
def submit_model_upload():
    response = upload_model()
    if response.status_code != 200:
        return response
    return home_page()


# Hack for navigating fromgapfill form to job status
@app.route('/submit/model/gapfill', methods=[GET])
def submit_model_gapfill():
    response = gapfill()
    if response.status_code != 200:
        return response
    job = json.loads(response.response[0])
    return job_status(job['jid'])


# ================= VIEWS ==============================================================================================
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
    return _about()


@app.route('/view/job/status')
def job_status(job_id=None):
    # Displays a page with information on a job. Has some status-checking logic, but eventually a template is rendered
    return job.view_status(job_id)


@app.route('/swagger')
def spec():
    # TODO: Renders the template indicating the API specification. Make sure the HTML file is up to date!
    return make_response(redirect("https://app.swaggerhub.com/apis/kingb12/ProbannoWeb/1.0.0"))

@app.route('/api')
def api_base():
    return spec()

@app.route('/about')
def _about():
    return render_template("aboutProbAnno.html")
if __name__ == '__main__':
    app.run()

