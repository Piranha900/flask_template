from flask import make_response, jsonify


# @app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# @app.errorhandler(400)
def abort(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


# @app.errorhandler(409)
def already_exists(error):
    return make_response(jsonify({'error': 'Resource already Exists'}), 409)
