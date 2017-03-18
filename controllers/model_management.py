import models.cobra_modeling as cobra_modeling
import probanno_management
from flask import request, send_from_directory, render_template, abort
import data.database as db
import session_management
import json
from job import Job, job_status_page
from rq import Queue
from redis import Redis
from session_management import SESSION_ID
import exceptions

MICROBIAL = 'Microbial'
GAPFILL_MODEL_JOB = 'gapfill_model'
GAPFILL_COMPLETE_URL = '/view/model/complete'
MODEL_ID = 'model_id'
model_queue = Queue(connection=Redis())


def load_model(filename):
    # load model w/ cobra
    model = cobra_modeling.from_json_file(filename)
    session = session_management.get_session_id()
    model_id = request.form['upload_model_id'] if request.form['upload_model_id'] is not None else (
    model.id if model.id is not None else str(request.date))
    print request.form['upload_model_id']
    if session is not None and db.find_model(session, model_id) is None:
        print("hello")
        db.insert_model(session, model_id, cobra_modeling.model_to_json(model))
    else:
        # TODO: Make this a 400
        if session is None:
            return "Session-less state"
        else:
            return "model already uploaded"


def run_fba():
    model_id = request.args['model_id']
    session_id = session_management.get_session_id()
    model = _retrieve_model(session_id, model_id)
    result = cobra_modeling.solution_to_json(cobra_modeling.run_fba(model))
    return result


def gapfill_model(app):
    model_id = request.args['model_id']
    session_id = session_management.get_session_id()
    fasta_id = request.args['fasta_id']
    likelihoods = probanno_management.get_reaction_probabilities(app, fasta_id)
    addReactions = request.args['add_reactions'] if 'add_reactions' in request.args else True
    model = _retrieve_model(session_id, model_id)
    template = request.args['template'] if 'template' in request.args else MICROBIAL
    universal_model_file = app.config['MODEL_TEMPLATES'] + template + '.json'
    job = Job(session_id, GAPFILL_MODEL_JOB, fasta_id)
    model_queue.enqueue(_async_gapfill_model, job, model_id, session_id, model, universal_model_file, likelihoods,
                        addReactions)
    return job_status_page(job.id, GAPFILL_COMPLETE_URL + '?fasta_id=' + fasta_id)


def _async_gapfill_model(job, model_id, session_id, model, universal_model_file, likelihoods, addReactions):
    job.start()
    try:
        universal_model = cobra_modeling.build_universal_model(universal_model_file)
        reactions = cobra_modeling.gapfill_model(model, universal_model, likelihoods)[0]
        print reactions
        if addReactions:
            model.add_reactions([universal_model.reactions.get_by_id(r.id) for r in reactions if
                                 universal_model.reactions.has_id(r.id) and not model.reactions.has_id(
                                     r.id)])
        print model.optimize().f
        new_model_id = model_id + '_gapfilled' if 'new_name' not in request.args else request.args['new_name']
        if db.find_model(session_id, new_model_id) is None:
            save_model(model_id + '_gapfilled', session_id, model)
        job.complete()
        return cobra_modeling.model_to_json(model)
    except BaseException as e:
        print(e)
        job.fail()


def save_model(model_id, session_id, model):
    if session_id is not None and model_id is not None and db.find_model(session_id, model_id) is None:
        db.insert_model(session_id, model_id, cobra_modeling.model_to_json(model))


def list_models():
    # session_id = request.args['sid']
    session_id = session_management.get_session_id()
    return json.dumps(db.list_models(session_id))


def _retrieve_model(session_id, model_id):
    return cobra_modeling.from_json(db.find_model(session_id, model_id)[-1])


def model_complete_view(model_id=None):
    if model_id is None:
        model_id = request.args[model_id] if model_id in request.args else (
        request.form[model_id] if model_id in request.form else None)
    if model_id is None:
        raise exceptions.InvalidUsage()
    return render_template("model_complete.html", model_id=model_id)


def download_model(app):
    model_id = request.args[MODEL_ID] if MODEL_ID in request.args else (
        request.form[MODEL_ID] if MODEL_ID in request.form else None)
    session_id = request.cookies.get(SESSION_ID)
    if model_id is None:
        abort(400)
    probanno = db.find_model(session_id, model_id)
    if probanno is None:
        abort(404)
    filename = str(model_id) + '.json'
    with open(app.config['UPLOAD_FOLDER'] + filename, 'w') as f:
        f.write(json.dumps(probanno))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
