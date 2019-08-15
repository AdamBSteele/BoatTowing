from flask import jsonify


def bad_request(message=None):
    resp = jsonify({
        'status': 'Bad Request',
        'message': message if message else 'Invalid request',
    })
    resp.status_code = 403
    return resp


def unauthorized():
    resp = jsonify({
        'status': 'Unauthorized',
        'message': 'You are not authorized to view/edit this resource',
    })
    resp.status_code = 403
    return resp


def resp404(obj_they_wanted_to_see="The object you're looking for"):
    resp = jsonify({
        'status': 'Not Found',
        'message': '{} was not found or does not exist'.format(obj_they_wanted_to_see),
    })
    resp.status_code = 404
    return resp
