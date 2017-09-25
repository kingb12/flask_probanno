import uuid

from flask import request, abort, send_from_directory, render_template, jsonify, Response
from redis import Redis
from rq import Queue
import traceback
import probanno
import session_management
import data.database as db
import utils
import json
import exceptions
from job import Job, job_status_page, PROBANNO_COMPLETE_URL, get_job, COMPLETE

# TODO: (PW-10) Make this relative reference cleaner with a config file
# These correspond to the drop down menu items in the view
GRAM_NEGATIVE = 'GramNegative'
GRAM_POSITIVE = 'GramPositive'
MICORBIAL = 'Microbial'
DEFAULT_TEMPLATE = GRAM_NEGATIVE
TEMPLATE_FILES = {GRAM_NEGATIVE: 'GramNegative.json', GRAM_POSITIVE: 'GramPositive.json', MICORBIAL: 'Micorbial.json'}
FASTA_ID = 'fasta_id'
FASTA = 'fasta'
TEMPLATE = 'template'
GET = 'GET'
POST = 'POST'
PUT = 'PUT'
CALCULATE_PROBANNO_JOB = 'calculate_probanno'


probanno_queue = Queue(connection=Redis())


def get_reaction_probabilities(app, fasta_id=None, fasta_file=None):
    session = session_management.get_session_id()
    if session is None:
        abort(400)
    template = None
    if request.method == GET:
        fasta_id = request.args[FASTA_ID] if fasta_id is None else fasta_id
        # check cache
        if fasta_id is not None and fasta_id != '':
            likelihoods = db.find_probanno(fasta_id)
            if likelihoods is not None:
                job = Job(session, CALCULATE_PROBANNO_JOB, fasta_id, dummy=True)
                db.insert_probanno_record(fasta_id, session, likelihoods[2])
                job.status = COMPLETE
                return jsonify(job.to_dict_dto())
        # download fasta file from Uniprot and continue
        try:
            fasta_file = get_fasta_by_id(app, fasta_id) if fasta_file is None else fasta_file
        except probanno.FastaNotFoundError:
            return abort(404)
        template = request.args[TEMPLATE] if TEMPLATE in request.args else DEFAULT_TEMPLATE
    if request.method == PUT:
        fasta_id = request.form[FASTA_ID] if fasta_id is None else fasta_id
        if fasta_id is None:
            abort(400)
        if FASTA in request.files:
            fasta_file = app.config['UPLOAD_FOLDER'] + utils.upload_file(app, request.files[FASTA])
        else:
            abort(400)
        template = request.form[TEMPLATE] if TEMPLATE in request.form else DEFAULT_TEMPLATE
    template_file = TEMPLATE_FILES[template] if template in TEMPLATE_FILES else TEMPLATE_FILES[DEFAULT_TEMPLATE]
    gen_id = request.args[FASTA_ID] if FASTA_ID in request.args and request.args[FASTA_ID] is not None else fasta_file
    fasta_name = get_name_from_fasta(fasta_file)
    template_model_file = app.config['MODEL_TEMPLATES'] + template_file
    job = Job(session, CALCULATE_PROBANNO_JOB, fasta_id)
    probanno_queue.enqueue(_async_get_reaction_probabilities,
                           job, fasta_id, fasta_name, session, fasta_file, template_model_file, gen_id,
                           job_id=job.id, timeout=600)
    return jsonify(get_job(job.id).to_dict_dto())


def _async_get_reaction_probabilities(job, fasta_id, fasta_name, session, file_name, template_model_file, genome_id):
    # seperation needed so that DB insertion an happen as job completes
    try:
        job.start()
        likelihoods = probanno.generate_reaction_probabilities(file_name,
                                                               template_model_file=template_model_file,
                                                               genome_id=genome_id)
        if fasta_id is not None and fasta_id != '':
            db.insert_probanno(fasta_id, fasta_name, session, str(uuid.uuid4()), likelihoods.to_json())
        job.complete()
        return likelihoods.to_json()
    except BaseException as e:
        print(e.message)
        traceback.print_exc()
        job.fail()
    finally:
        print('Job ' + job.id + ' has terminated.')


def get_fasta_by_id(app, fasta_id):
    """
    NOTE: the life-time of a FASTA file is not guaranteed to be any longer than the life-time of a request.
    :param app:
    :return:
    """
    return probanno.get_fasta_by_id(fasta_id, app.config['UPLOAD_FOLDER'] + str(fasta_id) + '.fasta')


def list_probannos():
    session = session_management.get_session_id()
    if session is None:
        abort(400)
    probs = [{'fasta_id': p[0], 'name': p[1]} for p in db.list_probannos(session)]
    return jsonify(probs)


def download_probanno(app):
    fasta_id = request.args[FASTA_ID] if FASTA_ID in request.args else (request.form[FASTA_ID] if FASTA_ID in request.form else None)
    if fasta_id is None:
        abort(400)
    probanno = retrieve_probanno(fasta_id)
    if probanno is None:
        abort(404)
    filename = str(fasta_id) + '.json'
    with open(app.config['UPLOAD_FOLDER'] + filename, 'w') as f:
        f.write(json.dumps(probanno))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


def probanno_complete_view(fasta_id=None):
    if fasta_id is None:
        fasta_id = request.args[FASTA_ID] if FASTA_ID in request.args else (request.form[FASTA_ID] if FASTA_ID in request.form else None)
    if fasta_id is None:
        raise exceptions.InvalidUsage()
    return render_template("probanno_complete.html", probanno_id=fasta_id)


def retrieve_probanno():
    session = session_management.get_session_id()
    if session is None:
        abort(400)
    fasta_id = request.args[FASTA_ID] if FASTA_ID in request.args else None
    if fasta_id is None or fasta_id == '':
        abort(400)
    likelihoods = db.retrieve_probanno(session, fasta_id)
    if likelihoods is None:
        abort(404)
    return Response(likelihoods[-2], mimetype='application/json')


def get_name_from_fasta(fasta_file):
    with open(fasta_file) as f:
        return f.readlines()[0].split('OS=')[-1].split('GN=')[0].strip()