from flask import request
from models import session


SESSION_ID = 'session_id'


def has_session():
    """
    Returns True if a session cookie was supplied in the request, False otherwise
    :return: (Boolean) True if a session cookie was supplied in the request, False otherwise
    """
    return request.cookies.get(SESSION_ID) is not None


def get_session_id():
    # print "get session cookie: ", request.cookies.get(SESSION_ID)
    return session.get_session(request.cookies.get(SESSION_ID))[0] if has_session() else None


def prepare_new_session():
    """
    Prepares a new session for managing a user's interactions.
    :return: Session ID as a string
    """
    return session.create_new_session()



