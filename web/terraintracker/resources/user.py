"""
User resource docstring
"""

import logging

from flask import g, request
from flask_restful import Resource

from terraintracker.models.user import User
from terraintracker.resources.decorators import log_request
from terraintracker.resources.auth import multi_auth
from terraintracker.resources.response_templates import resp404, bad_request
from terraintracker.app_init import db

logger = logging.getLogger(__name__)


class UserResource(Resource):
    """UserResource"""

    decorators = [log_request, multi_auth.login_required]

    def get(self):
        """
        Return single user

        .. :quickref: User; Get a single user.

        **Example request**:

        .. sourcecode:: http

          GET /users?id=12345 HTTP/1.1
          Host: example.com
          Content-Type: application/json
          Accept: application/json
          Authorization: Token <facebook_access_token>


        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json

          {
            "first_name": "Jeremy",
            "id": "130056427781965"
          }

        :query id: User ID
        :resheader Content-Type: application/json
        :>json string: id
        :>json string: first_name
        :>json string: active_tow_event_serving
        :>json string: active_tow_event_receiving
        :>json string: active_tow_request_batch
        :status 200: user found
        :status 401: authorization failed
        :status 404: user not found
        :returns: :class:`terraintracker.models.user.User`
        """
        _id = request.args.get('id', None)
        if not _id:
            _id = request.args.get('phone_number', None)
        if _id:
            u = User.query.get(_id)
        else:
            u = g.user
        if not u:
            return resp404("User {}".format(_id))
        return {
            'user_id': u.id,
            'first_name': u.first_name,
            'active_tow_event_serving_id': u.get_active_tow_event_serving() if u.get_active_tow_event_serving() else '',
            'active_tow_event_receiving_id': u.get_active_tow_event_receiving() if u.get_active_tow_event_receiving() else '',
            'active_tow_request_batch_id': u.get_active_tow_request_batch() if u.get_active_tow_request_batch() else '',
            'phone_number': u.phone_number if u.phone_number else None,
        }

    def put(self):
        """
        Modify the currently logged in user - usually to update their location

        .. :quickref: User; Modify the currently logged in user.

        **Example request**:

        .. sourcecode:: http

          PUT /users HTTP/1.1
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
             "status": "success"
          }

        :resheader Content-Type: application/json
        :<json float lat: user's current latitude
        :<json float lon: user's current longitude
        :<json float one_signal_player_id: user's one_signal_player_id (optional)
        :<json float phone: user's phone number (optional)
        :>json string status: "success", if applicable
        :status 200: posts found
        :status 401: authorization failed
        """
        print("AAHHHHHH")
        logger.info("PUT")
        args = request.get_json()
        logger.info(args)

        # If we're trying to modify another user
        if args.get('id') and args.get('id') != g.user.id:
            if not g.user.is_admin:
                return {'status': 'Cant modify another user - youre not an admin'}, 401
            u = User.query.get(args['id'])
            if u is None:
                return {'status': 'Couldnt find user'}, 404
        else:
            u = g.user

        if args.get('lat') and args.get('lon'):
            try:
                lat, lon = float(args.pop('lat')), float(args.pop('lon'))
                u.update_position(lat, lon)
            except Exception as e:
                logger.exception(e)

        for optional_arg in ['name', 'phone_number', 'one_signal_player_id']:
            if args.get(optional_arg):
                logger.info("Setting" + optional_arg + "to" + args[optional_arg])
                setattr(u, optional_arg, args[optional_arg])

        return {
            'user_id': u.id,
            'first_name': u.first_name,
            'active_tow_event_serving_id': u.get_active_tow_event_serving() if u.get_active_tow_event_serving() else '',
            'active_tow_event_receiving_id': u.get_active_tow_event_receiving() if u.get_active_tow_event_receiving() else '',
            'active_tow_request_batch_id': u.get_active_tow_request_batch() if u.get_active_tow_request_batch() else '',
            'phone_number': u.phone_number if u.phone_number else None,
        }

    def post(self):
        """
        DEPRECATED: Use /login to create a new user

        .. :quickref: User; Deprecated.

        :resheader Content-Type: application/json
        :<json string phone: 10 digit phone number
        :<json string email: User's email
        :<json string name: User's name
        :<json string name: User's password
        :<json float one_signal_player_id: user's one_signal_player_id

        :>json string: status
        :>json user_id: status

        :status 200: success
        :status 400: invalid params
        :status 401: authorization failed
        """

        # DEPRECATED
        logger.warning("Makin a new tower")
        args = request.get_json()

        if not g.user.is_admin:
            return {'status': 'Cant create a user - youre not an admin'}, 401

        # You must provide these args
        required_args = ['lat', 'lon', 'name', 'phone']
        for arg in required_args:
            if arg not in args:
                logger.info("Missed required value '{}'".format(arg))
                return bad_request("Missed required value '{}'".format(arg))

        user = User(_id=args['name'], name=args['name'], _is_test_user=False)
        user.is_android = True
        user.active = True
        user.phone = args['phone']
        user.role = User.Role.tower.value
        user.update_position(args['lat'], args['lon'])
        db.session.merge(user)
        db.session.commit()

        return {
            'status': 'New user created',
            'user_id': str(user.id)
        }, 201
