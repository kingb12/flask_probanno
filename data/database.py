from flask_sqlalchemy import SQLAlchemy

__database = None


SESSION = 'Session'
SESSION_SCHEMA = '(sid, logout)'
MODEL = 'Model'
MODEL_SCHEMA = '(sid, mid, model)'
PROBANNO = 'Probanno'
PROBANNO_SCHEMA = '(fasta_id, sid, probs_id)'
PROBS = 'Probs'
PROBS_SCHEMA = '(id, probs, name)'
JOB = 'Jobs'
JOB_SCHEMA = '(jid, sid, job, target, status)'
UPDATE_JOB_SCHEMA = 'sid = ?, job = ?, target = ?, status = ?'  # for use in update queries, make sure agrees with JOB_SCHEMA
TABLES = {SESSION: 'sid', MODEL: 'mid', PROBANNO: 'fasta_id', JOB: 'jid'}

FIND_BY_ID_QUERY = 'SELECT * FROM {0} WHERE {1} = ?'
FIND_MODEL_QUERY = 'SELECT * FROM ' + MODEL + ' WHERE sid = ? AND mid = ?'
FIND_PROBANNO_QUERY = 'SELECT * FROM ' + PROBANNO + ' pr, ' + PROBS + \
                      ' pb WHERE pr.probs_id = pb.id AND pr.fasta_id = ?'
RETRIEVE_PROBANNO_QUERY = 'SELECT * FROM ' + PROBANNO + ' pr, ' + PROBS + \
                          ' pb WHERE pr.probs_id = pb.id AND pr.sid = ? AND pr.fasta_id = ?'
INSERT_INTO_SESSION_QUERY = 'INSERT INTO ' + SESSION + SESSION_SCHEMA + ' VALUES (?, ?)'
INSERT_INTO_MODEL_QUERY = 'INSERT INTO ' + MODEL + MODEL_SCHEMA + ' VALUES (?, ?, ?)'
INSERT_INTO_PROBANNO_QUERY = 'INSERT INTO ' + PROBANNO + PROBANNO_SCHEMA + ' VALUES (?, ?, ?)'
INSERT_INTO_PROBS_QUERY = 'INSERT INTO ' + PROBS + PROBS_SCHEMA + ' VALUES (?, ?, ?)'
INSERT_INTO_JOBS_QUERY = 'INSERT INTO ' + JOB + JOB_SCHEMA + ' VALUES (?, ?, ?, ?, ?)'
LIST_MODELS_QUERY = 'SELECT mid FROM ' + MODEL + ' WHERE sid = ?'
UPDATE_IN_JOBS_QUERY = 'UPDATE ' + JOB + ' SET ' + UPDATE_JOB_SCHEMA + ' WHERE jid = ?'
LIST_PROBANNOS_QUERY = 'SELECT pr.fasta_id as fasta_id, pb.name as name, pr.probs_id as probs_id FROM ' + \
                       PROBANNO + ' pr, ' + PROBS + ' pb WHERE pr.sid=? AND pr.probs_id = pb.id'
COUNT_ALL_PROBS = 'SELECT probs_id, count(*) as count FROM ' + PROBANNO + ' GROUP BY probs_id'
LIST_JOBS_QUERY = 'SELECT * FROM ' + JOB + '  WHERE sid = ?'
CLEAR_SESSION_QUERY = 'DELETE FROM {0} WHERE sid = ?'
CLEAR_PROBS_QUERY = 'DELETE FROM ' + PROBS + ' WHERE id in ("{0}")'
CLEAR_PROBANNO_QUERY = 'DELETE FROM ' + PROBANNO + ' WHERE fasta_id= ?'


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


def insert_probanno(fasta_id, name, sid, probs_id, likelihoods):
    # context manager handles transaction, commit and roll-back cases
    with __database.engine.begin() as connection:
        connection.execute(INSERT_INTO_PROBANNO_QUERY, [fasta_id, sid, probs_id])
        connection.execute(INSERT_INTO_PROBS_QUERY, [probs_id, likelihoods, name])


def list_models(session_id):
    curs = __database.engine
    result = curs.execute(LIST_MODELS_QUERY, [session_id]).fetchall()
    return None if result is None else [r[0] for r in result]


def list_probannos(session_id):
    curs = __database.engine
    result = curs.execute(LIST_PROBANNOS_QUERY, [session_id]).fetchall()
    return None if result is None else [list(r) for r in result]


def list_jobs(session_id):
    curs = __database.engine
    result = curs.execute(LIST_JOBS_QUERY, [session_id]).fetchall()
    return None if result is None else [list(r) for r in result]


def update_job(jid, session, job, target, status):
    curs = __database.engine
    # jid must go last to set parameter in where clause
    curs.execute(UPDATE_IN_JOBS_QUERY, [session, job, target, status, jid])


def insert_job(jid, session, job, target, status):
    curs = __database.engine
    curs.execute(INSERT_INTO_JOBS_QUERY, [jid, session, job, target, status])


def clear_session_values(sid, clear_session=False):
    curs = __database.engine
    probs_dict = dict([tuple(v) for v in curs.execute(COUNT_ALL_PROBS)])
    probs = curs.execute(LIST_PROBANNOS_QUERY, [sid])
    probs = '", "'.join([str(v[2]) for v in probs if probs_dict[str(v[2])] == 1])
    if probs != '':
        curs.execute(CLEAR_PROBS_QUERY.format(probs))
    curs.execute(CLEAR_SESSION_QUERY.format(PROBANNO), [sid])
    curs.execute(CLEAR_SESSION_QUERY.format(JOB), [sid])
    curs.execute(CLEAR_SESSION_QUERY.format(MODEL), [sid])
    if clear_session:
        curs.execute(CLEAR_SESSION_QUERY.format(SESSION), [sid])


def clear_probanno(fasta_id):
    curs = __database.engine
    curs.execute(CLEAR_PROBANNO_QUERY, [fasta_id])


# Use this with in-process lookups like /api/probanno/calculate GET, for cache checking
def find_probanno(fasta_id):
    curs = __database.engine
    result = curs.execute(FIND_PROBANNO_QUERY, [fasta_id]).fetchone()
    return None if result is None else result.values()


def insert_probanno_record(fasta_id, session_id, probs_id):
    curs = __database.engine
    curs.execute(INSERT_INTO_PROBANNO_QUERY, [fasta_id, session_id, probs_id])


# Use this with out-bound fetches like /api/probanno GET
def retrieve_probanno(session_id, fasta_id):
    curs = __database.engine
    result = curs.execute(RETRIEVE_PROBANNO_QUERY, [session_id, fasta_id]).fetchone()
    return None if result is None else result.values()