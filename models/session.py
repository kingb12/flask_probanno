import uuid
import data.database as db


END_OF_TIME = 99999999999


def create_new_session(log_out_time=END_OF_TIME):
    """
    Creates a new session and returns it's ID
    :param log_out_time:
    :return:
    """
    session_id = uuid.uuid4()
    while session_exists(session_id):
        session_id = uuid.uuid4()
        print 'WOWZA'  # this should never print, odds of UUID conflict
    db.insert_session(str(session_id), log_out_time)
    # print "session id: ", str(session_id)
    return str(session_id)


def session_exists(session_id):
    return db.find_by_id(db.SESSION, str(session_id)) is not None


def get_session(session_id):
    return db.find_by_id(db.SESSION, str(session_id))




