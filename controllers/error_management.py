from flask import jsonify


def bad_request(message):
    response = jsonify({'message': message})
    response.status_code = 400
    return response


def not_found(message):
    response = jsonify({'message': message})
    response.status_code = 404
    return response

def missing_argument(arg):
    return bad_request(message="Missing argument: " + arg)