from flask_sqlalchemy import SQLAlchemy

__database = None


SESSION = 'Session'
SESSION_SCHEMA = '(sid, logout)'
MODEL = 'Model'
MODEL_SCHEMA = '(sid, mid, model)'
PROBANNO = 'Probanno'
PROBANNO_SCHEMA = '(fasta_id, sid, probs)'
JOB = 'Jobs'
TABLES = {SESSION: 'sid', MODEL: 'mid', PROBANNO: 'fasta_id', JOB: 'jid'}

FIND_BY_ID_QUERY = 'SELECT * FROM {0} WHERE {1} = ?'
FIND_MODEL_QUERY = 'SELECT * FROM ' + MODEL + ' WHERE sid = ? AND mid = ?'
INSERT_INTO_SESSION_QUERY = 'INSERT INTO ' + SESSION + SESSION_SCHEMA + ' VALUES (?, ?)'
INSERT_INTO_MODEL_QUERY = 'INSERT INTO ' + MODEL + MODEL_SCHEMA + ' VALUES (?, ?, ?)'
INSERT_INTO_PROBANNO_QUERY = 'INSERT INTO ' + PROBANNO + PROBANNO_SCHEMA + ' VALUES (?, ?, ?)'
LIST_MODELS_QUERY = 'SELECT mid FROM ' + MODEL + ' WHERE sid = ?'

def set_db(app, filename):
    global __database
    """
    Sets the sqlite3 DB to the given file
    :param filename: path to DB file
    :return: None
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + filename
    __database = SQLAlchemy(app)


def find_by_id(table, obj_id):
    if table not in TABLES:
        return None
    curs = __database.engine
    cmd = FIND_BY_ID_QUERY.format(table, TABLES[table])
    # print obj_id
    result = curs.execute(cmd, [obj_id]).fetchone()
    return tuple(result.values()) if result is not None else None


def find_model(session_id, model_id):
    curs = __database.engine
    result = curs.execute(FIND_MODEL_QUERY, [session_id, model_id]).fetchone()
    return None if result is None else result.values()


def insert_session(session_id, log_out_time):
    curs = __database.engine
    curs.execute(INSERT_INTO_SESSION_QUERY, [session_id, log_out_time])


def insert_model(sid, mid, model):
    curs = __database.engine
    curs.execute(INSERT_INTO_MODEL_QUERY, [sid, mid, model])


def insert_probanno(fasta_id, sid, likelihoods):
    curs = __database.engine
    curs.execute(INSERT_INTO_PROBANNO_QUERY, [fasta_id, sid, likelihoods])


def list_models(session_id):
    curs = __database.engine
    result = curs.execute(LIST_MODELS_QUERY, [session_id]).fetchall()
    return None if result is None else [r[0] for r in result]