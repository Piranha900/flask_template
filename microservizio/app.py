import error
import json
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import logging.handlers
from flask_oidc import OpenIDConnect
import requests
from flask import Flask, jsonify, request

people = list()
config_data = dict()
with open('config.json') as config_file: config_data.update(json.load(config_file))

sentry_sdk.init(
    dsn= config_data['sentry_dns'],
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)

app = Flask(__name__)

my_logger = logging.getLogger('rSyslogLogger')
my_logger.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address=(config_data['rsyslog_host'], config_data['rsyslog_port']), facility=19)
my_logger.addHandler(handler)

with open("client_secrets.json", "r") as secret: keycloak_uri = json.loads(secret.read())['web']['keycloak_uri']
with open("client_secrets.json", "r") as secret: keycloak_realm = json.loads(secret.read())['web']['realm']
with open("client_secrets.json", "r") as secret: client_id = json.loads(secret.read())['web']['client_id']
with open("client_secrets.json", "r") as secret: client_secret = json.loads(secret.read())['web']['client_secret']

app.config.update({
    'SECRET_KEY': client_secret,
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_OPENID_REALM': keycloak_realm,
    'OIDC-SCOPES': ['openid'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_TOKEN_TYPE_HINT': 'access_token'
})
oidc = OpenIDConnect(app)


@app.route('/token_login/', methods=['POST'])
def get_token():
    body = request.get_json()

    for field in ['username', 'password']:
        if field not in body:
            return error.abort(400)
    data = {
        'grant_type': 'password',
        'client_id': client_id,
        'client_secret': client_secret,
        'username': body['username'],
        'password': body['password']
    }

    with open("client_secrets.json", "r") as secret:
        url = json.loads(secret.read())['web']['token_uri']

    response = requests.post(url, data=data)
    if response.status_code > 200:
        return error.abort(400)
    tokens_data = response.json()

    ret = {
        'tokens': {"access_token": tokens_data['access_token'],
                   "refresh_token": tokens_data['refresh_token'], }
    }
    return jsonify(ret), 200


@app.route('/token_refresh/', methods=['POST'])
def refresh_token():
    body = request.get_json()
    for field in ['refresh_token']:
        if field not in body:
            return error.abort(400)
    data = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': body['refresh_token'],
    }
    with open("client_secrets.json", "r") as secret:
        url = json.loads(secret.read())['web']['token_uri']

    response = requests.post(url, data=data)
    if response.status_code != requests.codes.ok:
        return error.abort(400)
    data = response.json()
    ret = {
        "access_token": data['access_token'],
        "refresh_token": data['refresh_token']
    }
    return jsonify(ret), 200


@app.route('/health')
@oidc.accept_token(require_token=True)
def health():
    my_logger.debug("calling for healthcheck...")
    my_logger.debug("Alive!")
    return {'message': 'Healthy'}


@app.route('/api1', methods=['GET', 'POST'])
@oidc.accept_token(require_token=True)
def get_all():
    if request.method != 'GET':
        my_logger.debug("Trying to POST data..")
        if not request.json or not 'name' in request.json:
            my_logger.error("no data to insert!")
            return error.abort(400)
        if not request.json in people:
            people.append(request.json)
        else:
            my_logger.error("Data already exists")
            return error.already_exists(409)
        my_logger.info("Insert data successfully!")
        return jsonify({'message': "person added!"}), 201
    else:
        my_logger.info("Trying to GET data..")
        if not people:
            my_logger.error(error.not_found(404))
            return error.not_found(404)
        if not request.args.get('name'):
            my_logger.info("Found Data!")
            return jsonify({'message': people}), 200
        else:
            for element in people:
                if request.args.get('name') in element['name']:
                    return element
        my_logger.warning("Data not found!")
        my_logger.error(error.not_found(404))
        return error.not_found(404)


@app.route('/api1/<name>', methods=['DELETE'])
@oidc.accept_token(require_token=True)
def delete_person(name):
    my_logger.info("Trying to DELETE data..")
    for element in people:
        if name in element['name']:
            people.remove(element)
            my_logger.info("Delete successfully!")
            return jsonify({'message': "person removed!"}), 200
    my_logger.error("Data doesn't exists!")
    return error.not_found(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=False)
