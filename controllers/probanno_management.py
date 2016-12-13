from flask import request
import probanno.probanno as probanno
import session_management
import data.database as db

# TODO: (PW-10) Make this relative reference cleaner with a config file
DEFAULT_TEMPLATE = 'GramNegative.json'
FASTA_ID = 'fasta_id'


def get_reaction_probabilities(app, fasta_id=None):
    if fasta_id is None:
        fasta_id = request.args[FASTA_ID]
    session = session_management.get_session_id()
    print session
    print type(session)
    # we will permit sessions that are None to save reaction probabilities
    likelihoods = db.find_by_id(db.PROBANNO, fasta_id)
    if likelihoods is not None:
        likelihoods = likelihoods[-1]
    if likelihoods is not None:
        return likelihoods
    fasta_file = get_fasta_by_id(app)
    likelihoods = probanno.generate_reaction_probabilities(fasta_file,
                                                           template_model_file=app.config['MODEL_TEMPLATES'] +
                                                           DEFAULT_TEMPLATE,
                                                           genome_id=request.args[FASTA_ID])
    db.insert_probanno(fasta_id, session, likelihoods.to_json())
    return likelihoods.to_json()


def get_fasta_by_id(app):
    """
    NOTE: the life-time of a FASTA file is not guaranteed to be any longer than the life-time of a request.
    :param app:
    :return:
    """
    fasta_id = request.args[FASTA_ID]
    return probanno.get_fasta_by_id(fasta_id, app.config['UPLOAD_FOLDER'] + str(fasta_id) + '.fasta')

