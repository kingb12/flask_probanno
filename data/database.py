import sqlite3

__database = None


SESSION = 'Session'
SESSION_SCHEMA = '(sid, logout)'
MODEL = 'Model'
MODEL_SCHEMA = '(sid, mid, model)'
PROBANNO = 'Probanno'
JOB = 'Jobs'
TABLES = {SESSION: 'sid', MODEL: 'mid', PROBANNO: 'fasta_id', JOB: 'jid'}

FIND_BY_ID_QUERY = 'SELECT * FROM {0} WHERE {1} = ?'
INSERT_INTO_SESSION_QUERY = 'INSERT INTO ' + SESSION + SESSION_SCHEMA + ' VALUES (?, ?)'
INSERT_INTO_MODEL_QUERY = 'INSERT INTO ' + MODEL + MODEL_SCHEMA + ' VALUES (?, ?, ?)'


def set_db(filename):
    global __database
    """
    Sets the sqlite3 DB to the given file
    :param filename: path to DB file
    :return: None
    """
    print filename
    __database = sqlite3.connect(filename)


def find_by_id(table, obj_id):
    if table not in TABLES:
        return None
    curs = __database.cursor()
    cmd = FIND_BY_ID_QUERY.format(table, TABLES[table])
    # print obj_id
    curs.execute(cmd, [obj_id])
    return curs.fetchone()


def insert_session(session_id, log_out_time):
    curs = __database.cursor()
    # print session_id, log_out_time
    curs.execute(INSERT_INTO_SESSION_QUERY, [session_id, log_out_time])
    __database.commit()


def insert_model(sid, mid, model):
    curs = __database.cursor()
    curs.execute(INSERT_INTO_SESSION_QUERY, [sid, mid, model])
    __database.commit()
