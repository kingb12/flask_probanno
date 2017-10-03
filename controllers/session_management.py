from flask import request, abort

from controllers.error_management import bad_request
from models import session

SESSION_ID = 'session'


def has_session():
    """
    Returns True if a session cookie was supplied in the request, False otherwise
    :return: (Boolean) True if a session cookie was supplied in the request, False otherwise
    """
    # can either be a header or a cookie, default to header
    return (request.headers is not None and request.headers.get(SESSION_ID) is not None) or \
           (request.cookies is not None and request.cookies.get(SESSION_ID) is not None)


def get_session_id():
    # print "get session cookie: ", request.cookies.get(SESSION_ID)
    # can either be a header or a cookie, default to header
    sesh = ((session.get_session(request.headers.get(SESSION_ID))) or
                                 session.get_session(request.cookies.get(SESSION_ID))) if has_session() else None
    return sesh[0] if sesh is not None else None


def prepare_new_session():
    """
    Prepares a new session for managing a user's interactions.
    :return: Session ID as a string
    """
    return session.create_new_session()


def clear_session():
    sesh= get_session_id()
    if sesh is None:
        return bad_or_missing_session()
    return session.clear_session(sesh, request.args['clear_session'] if 'clear_session' in request.args else None)


def bad_or_missing_session():
    return bad_request("No session or invalid session supplied")