import models.cobra_modeling as cobra_modeling
import probanno_management
from flask import request, make_response
import data.database as db
import session_management
import json

MICROBIAL = 'Microbial'

def load_model(filename):
    # load model w/ cobra
    model = cobra_modeling.from_json_file(filename)
    session = session_management.get_session_id()
    print(request.form)
    model_id = request.form['upload_model_id'] if request.form['upload_model_id'] is not None else (model.id if model.id is not None else str(request.date))
    print request.form['upload_model_id']
    if session is not None and db.find_model(session, model_id) is None:
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
    universal_model = cobra_modeling.build_universal_model(app.config['MODEL_TEMPLATES'] + template + '.json')
    reactions = cobra_modeling.gapfill_model(model, universal_model, likelihoods)[0]
    print reactions
    model.add_reactions([universal_model.reactions.get_by_id(r.id) for r in reactions if
                                     universal_model.reactions.has_id(r.id) and not model.reactions.has_id(
                                         r.id)])
    print model.optimize().f
    new_model_id = model_id + '_gapfilled' if 'new_name' not in request.args else request.args['new_name']
    if db.find_model(session_id, new_model_id) is None:
        save_model(model_id + '_gapfilled', session_id, model)
    return cobra_modeling.model_to_json(model)


def save_model(model_id, session_id, model):
    if session_id is not None and model_id is not None and db.find_model(session_id, model_id) is None:
        db.insert_model(session_id, model_id, cobra_modeling.model_to_json(model))

def list_models():
    # session_id = request.args['sid']
    session_id = session_management.get_session_id()
    return json.dumps(db.list_models(session_id))

def _retrieve_model(session_id, model_id):
    return cobra_modeling.from_json(db.find_model(session_id, model_id)[-1])
