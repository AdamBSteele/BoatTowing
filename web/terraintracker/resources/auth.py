"""
Creates the functions needed by login_manager and auth
"""
import logging
import requests

from flask import g, request, session
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_restful import Resource
from werkzeug.security import check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


from terraintracker.app_init import db
from terraintracker.config import SECRET_KEY  # , basic_auth, token_auth, , auth
from terraintracker.models.user import User

logger = logging.getLogger(__name__)


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Token')
multi_auth = MultiAuth(basic_auth, token_auth)


@basic_auth.verify_password
def verify_password(username, password):
    logger.warning("Using password verification: [{}, {}]".format(username, password))
    try:
        # Get the user
        user = User.query.get(str(username))
        if not user:
            logger.debug("Failed to find user with id: {}".format(username))
            return False

        # Check their pw
        if check_password_hash(user.password, password):
            g.user = user
            if not g.user.is_test_user:
                logger.warning("Password login {}:{}".format(username, password))
            return True
        else:
            logger.debug("User with username: {} failed password check".format(username))
            return False

    except Exception as e:
        logger.exception(e)
        logger.error("Error checking user password for user w/ id of {}".format(username))
    return False


@token_auth.verify_token
def verify_auth_token(auth_token):
    # Try to get the user from session cookies
    try:
        if User.query.get(session['user_id']):
            g.user = User.query.get(session['user_id'])
            return True
    except Exception:
        logger.debug("Couldn't log in via session cookie")

    if not auth_token:
        logger.warning("Showed up at token_auth with no token")
        return False

    logger.info("Authtoken: {}".format(auth_token))

    # Verify token with FB
    try:
        response = requests.get('https://graph.facebook.com/me?access_token=' + auth_token)
        data = response.json()
        if data.get('error'):
            logger.warning(data.get('error'))
            logger.warning("FB token got bad response: {}".format(data))
        elif int(data.get('id'), 0) > 0:
            user_id = data.get('id')
            logger.info("Got FB ID: {}".format(user_id))
            g.user = User.query.get(user_id)
            if not g.user:
                logger.info("verify_auth_token found no user with from FB data: {}".format(data))
                user_name = data.get('name')
                try:
                    new_user = User(_id=user_id, name=user_name)
                    db.session.merge(new_user)
                    g.user = new_user
                    g.logging_in_new_user = True
                except Exception as e:
                    logger.error("Exception in verify_token")
                    logger.exception(e)
            session['user_id'] = g.user.id
            return True
    except Exception as e:
        logger.error("Exception in verify_token")
        logger.exception(e)
    return False


def generate_auth_token(user_id):
    gen_serial = Serializer(SECRET_KEY, expires_in=9999)
    data = {'id': user_id}
    res = None
    try:
        res = gen_serial.dumps(data).decode()
    except Exception as e:
        logger.exception(e)
    return res


class LoginResource(Resource):
    """ Resource to handle logins """
    decorators = [multi_auth.login_required]

    def post(self):
        """Log the user in.  Update lat/lon if sent. Create a new user if a valid Facebook token is sent
           from a Facebook account we haven't seen before.
           Will also return the IDs of the user's active tow_request_batch or tow_event.
           Should be evaluated in this order:

            - If active_tow_event_serving is populated, should move to Tow Event screen
            - If active_tow_event_receiving is populated, should move to Tow Event screen
            - If active_tow_request_batch is populated, should move to Tow Request screen

        .. :quickref: Login; Logs user in. Creates new user if applicable.

        **Example request (existing user)**:

        .. sourcecode:: http

          POST /login HTTP/1.1
          Host: example.com
          Content-Type: application/json
          Accept: application/json
          Authorization: Token <facebook_access_token>
          Data: {"lat":"40.7273949017785",
                 "lon":"-73.98767802526797"}

        **Example response**:

        .. sourcecode:: http

          HTTP/1.0 200 OK
          Vary: Accept
          Content-Type: application/json

          {
             "user_id": "1891933447491488"
          }

        **Example request (new user)**:

        .. sourcecode:: http

          POST /login HTTP/1.1
          Host: example.com
          Content-Type: application/json
          Accept: application/json
          Authorization: Token <facebook_access_token>
          Data: {"lat":"40.7273949017785",
                 "lon":"-73.98767802526797"}

        **Example response**:

        .. sourcecode:: http

          HTTP/1.0 201 OK
          Vary: Accept
          Content-Type: application/json

          {
             "user_id": "1891933447491488"
          }

        :resheader Content-Type: application/json
        :<json string one_signal_player_id: user's one_signal_player_id
        :<json float lat: user's current latitude
        :<json float lon: user's current longitude
        :>json string: user_id
        :>json string: active_tow_event_serving
        :>json string: active_tow_event_receiving
        :>json string: active_tow_request_batch
        :status 200: login succeeded (existing user)
        :status 201: login succeeded (new user)
        :status 400: invalid or missing params
        :status 401: authorization failed
        """
        if getattr(g, 'logging_in_new_user', None):
            status_code = 201
            logger.info("Created new user: {}".format(g.user))
        else:
            status_code = 200
            logger.debug("Logging in {}".format(g.user))

        required_args_list = ['one_signal_player_id', 'lat', 'lon']
        try:
            args = request.get_json()

        except Exception as e:
            logger.exception(e)
            return {'error': str(e)}, 400
        try:
            logging.debug("Posting to /login: {}".format(args))
            for arg in required_args_list:
                if not args.get(arg):
                    return {'error': "missing required arg: \'{}\'".format(arg)}, 400
            logging.debug('args verified')

            g.user.one_signal_player_id = args['one_signal_player_id']
            g.user.update_position(args['lat'], args['lon'])
        except Exception as e:
            logger.exception(e)
            return {'error': 'failed to signin with that lat/lon and one_signal_player_id'}, 500

        res = {
            'user_id': g.user.id,
            'first_name': g.user.first_name,
            'active_tow_event_serving_id': g.user.get_active_tow_event_serving() if g.user.get_active_tow_event_serving() else '',
            'active_tow_event_receiving_id': g.user.get_active_tow_event_receiving() if g.user.get_active_tow_event_receiving() else '',
            'active_tow_request_batch_id': g.user.get_active_tow_request_batch() if g.user.get_active_tow_request_batch() else '',
            'phone_number': g.user.phone_number if g.user.phone_number else None,
        }, status_code
        logger.debug(res)
        return res
