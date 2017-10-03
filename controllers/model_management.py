import os

import models.cobra_modeling as cobra_modeling
import probanno_management
from flask import request, send_from_directory, render_template, abort, Response, jsonify
import data.database as db
import session_management
import json

import utils
from controllers.error_management import missing_argument, bad_request, not_found
from job import Job, job_status_page, GAPFILL_COMPLETE_URL, retrieve_job
from rq import Queue
from redis import Redis
from session_management import SESSION_ID
import exceptions, copy
import traceback

MICROBIAL = 'Microbial'
GAPFILL_MODEL_JOB = 'gapfill_model'
MODEL_ID = 'model_id'
model_queue = Queue(connection=Redis(), default_timeout=60)
ALLOWED_EXTENSIONS = {'json', 'fasta', 'fa'}
FASTA_ID = 'fasta_id'
OUTPUT_ID = 'output_id'



def load_model(app):
    session = session_management.get_session_id()
    if session is None:
        return session_management.bad_or_missing_session()
    if 'file' not in request.files:
        return missing_argument('file')
    file = request.files['file']
    filename = utils.upload_file(app, file, ALLOWED_EXTENSIONS)
    # load model w/ cobra
    model = None
    try:
        model = cobra_modeling.from_json_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except BaseException as e:
        return bad_request("Invalid CobraPy Model. Not in proper cobra.io.json deserializable format")
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    if MODEL_ID not in request.form:
        return missing_argument(MODEL_ID)
    model_id = request.form[MODEL_ID]
    if db.find_model(session, model_id) is not None:
        db.delete_model(session, model_id)
    db.insert_model(session, model_id, cobra_modeling.model_to_json(model))
    return Response()


def run_fba():
    model_id = request.args['model_id']
    session_id = session_management.get_session_id()
    model = _retrieve_model(session_id, model_id)
    result = cobra_modeling.solution_to_json(cobra_modeling.run_fba(model))
    return result


def gapfill_model(app):
    session = session_management.get_session_id()
    if session is None:
        return session_management.bad_or_missing_session()
    if MODEL_ID not in request.args:
        return missing_argument(MODEL_ID)
    if OUTPUT_ID not in request.args:
        return missing_argument(OUTPUT_ID)
    fasta_id = request.args[FASTA_ID] if FASTA_ID in request.args else None
    if fasta_id is None or fasta_id == '':
        return missing_argument(FASTA_ID)
    model_id = request.args['model_id']
    session_id = session_management.get_session_id()
    likelihoods = db.retrieve_probanno(session, fasta_id)
    if likelihoods is None:
        return not_found(fasta_id + " not found")
    addReactions = True  # Could make an argument for more customization
    model = _retrieve_model(session_id, model_id)
    if model is None:
        return not_found(model_id + " not found")
    template = request.args['template'] if 'template' in request.args else MICROBIAL
    universal_model_file = app.config['UNIVERSAL_MODELS'] + template + '.json'
    job = Job(session_id, GAPFILL_MODEL_JOB, model_id)
    model_queue.enqueue(_async_gapfill_model, job, model_id, session_id, model, universal_model_file, likelihoods,
                        addReactions, copy.copy(request.args), timeout=600, job_id=job.id, solver=app.config['SOLVER'])
    return jsonify(retrieve_job(job.id).to_dict_dto())


def _async_gapfill_model(job, output_id, session_id, model, universal_model_file, likelihoods, addReactions, request_args, solver='glpk'):
    job.start()
    try:
        universal_model = cobra_modeling.get_universal_model(universal_model_file)
        model.solver = solver
        universal_model.solver = solver
        reactions = cobra_modeling.gapfill_model(model, universal_model, likelihoods)[0]
        if addReactions:
            model.add_reactions([universal_model.reactions.get_by_id(r.id) for r in reactions if
                                 universal_model.reactions.has_id(r.id) and not model.reactions.has_id(
                                     r.id)])
        print model.optimize().f
        save_model(output_id, session_id, model)
        job.complete()
        return cobra_modeling.model_to_json(model)
    except BaseException as e:
        print(traceback.format_exc())
        job.fail()


def save_model(model_id, session_id, model):
    if session_id is not None and model_id is not None and db.find_model(session_id, model_id) is None:
        db.insert_model(session_id, model_id, cobra_modeling.model_to_json(model))


def list_models():
    # session_id = request.args['sid']
    session_id = session_management.get_session_id()
    if session_id is None:
        return session_management.bad_or_missing_session()
    return jsonify(db.list_models(session_id))


def _retrieve_model(session_id, model_id):
    model = db.find_model(session_id, model_id)
    if model is not None:
        return cobra_modeling.from_json(model[-1])


def model_complete_view(model_id=None):
    if model_id is None:
        model_id = request.args[model_id] if model_id in request.args else (
        request.form[model_id] if model_id in request.form else None)
    if model_id is None:
        raise exceptions.InvalidUsage()
    return render_template("model_complete.html", model_id=model_id)


def download_model(app):
    session = session_management.get_session_id()
    if session is None:
        return session_management.bad_or_missing_session()
    if MODEL_ID not in request.args:
        return missing_argument(MODEL_ID)
    model_id = request.args[MODEL_ID]
    model = db.find_model(session, model_id)
    if model is None:
        return not_found(model_id + " not found")
    filename = str(model_id) + '.json'
    with open(app.config['UPLOAD_FOLDER'] + filename, 'w') as f:
        f.write(json.dumps(model[-1]))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


def get_model(app):
    session = session_management.get_session_id()
    if session is None:
        return session_management.bad_or_missing_session()
    if MODEL_ID not in request.args:
        return missing_argument(MODEL_ID)
    model = db.find_model(session, request.args[MODEL_ID])
    if model is None:
        return not_found(request.args[MODEL_ID] + " not found")
    return Response(model[-1], mimetype='application/json')