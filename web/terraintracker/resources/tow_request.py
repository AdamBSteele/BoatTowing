"""
Handles towing CRUD
"""
import logging

from flask import request, g
from flask_restful import Resource

from terraintracker.resources.auth import multi_auth
from terraintracker.resources.decorators import log_request
from terraintracker.models.user import TowRequestNotFoundError
from terraintracker.models.tow_request import (TowRequestAlreadyAcceptedError,
                                               TowRequestCancelledError,
                                               TowRequestTimedOutError)


logger = logging.getLogger(__name__)


class TowRequestResource(Resource):
    """
    TowRequest CRUD
    """

    decorators = [log_request, multi_auth.login_required]

    def put(self):
        """
        Accept or reject the latest tow request this user has received.
        Updates TowRequest object for a given requestee
        Creates TowEvent object if the TowRequest is successfully accepted

        .. :quickref: Tow Request; Used by requestee to accept or reject an incoming tow request.

        :<json string action: one of ['accept', 'reject']
        :<json string tow_request_id: the specific tow request we're accepting/rejecting
        :<json float lon: user's current longitude
        :<json float lat: user's current latitude

        *If action is accept and the accept is successful (201 status code), creates new TowEvent and returns:*

        :>json string tow_event_id: UUID of the newly created TowEvent
        :>json string: tow_request_batch_id: ID of TowRequestBatch
        :>json string: tow_request: ID for TowRequest object that was accepted

        *Else returns a simple status string and one of the following codes:*

        :>json string: status: One of ["not_found", "already_accepted", "timed_out", "success"]

        _

        :status 200: Action accepted. `status` one of: ["already_accepted", "timed_out", "success"]
        :status 201: Tow Event was created
        :status 400: Bad request (probably due to invalid "action" param)
        :status 403: authorization failed
        :status 404: Tow Request not found. `status: "not_found"`
        """
        required_args = ['action', 'tow_request_id']

        try:
            args = request.get_json()
        except Exception as e:
            logger.exception(e)

        for arg in required_args:
            if arg not in args:
                logger.warning("TowRequest PUT missing required args")
                return {'status': 'The endpoint requires action + id args {}'.format(required_args)}, 400

        try:
            g.user.update_position(args['lat'], args['lon'])
        except Exception:
            pass

        tow_request_id = args.get('tow_request_id')
        action = args.get('action')

        if action == "accept":
            try:
                logger.debug("{} accepting tow request {}".format(g.user, tow_request_id))
                requestor, tow_request, tow_request_batch, tow_event = g.user.accept_tow_request(tow_request_id)
                return {'tow_request_batch_id': tow_request_batch.id,
                        'tow_request': tow_request.id,
                        'tow_event_id': tow_event.id}, 201
            except TowRequestNotFoundError:
                logger.warning("{} TowRequestNotFoundError".format(tow_request_id))
                return {'status': 'not_found'}, 404
            except TowRequestAlreadyAcceptedError:
                logger.warning("{} TowRequestAlreadyAcceptedError".format(tow_request_id))
                return {'status': 'already_accepted'}, 200
            except TowRequestTimedOutError:
                logger.warning("{} TowRequestTimedOutError".format(tow_request_id))
                return {'status': 'timed_out'}, 200
            except TowRequestCancelledError:
                logger.warning("{} TowRequestCancelledError".format(tow_request_id))
                return {'status': 'cancelled'}, 200

        elif action == "reject":
            try:
                logger.debug("{} rejecting tow request {}".format(g.user, tow_request_id))
                g.user.reject_tow(tow_request_id)
                return {'status': 'success'}, 200
            except TowRequestNotFoundError:
                logger.warning("{} TowRequestNotFoundError".format(tow_request_id))
                return {'status': 'not_found'}, 404
            except TowRequestTimedOutError:
                logger.warning("{} TowRequestTimedOutError".format(tow_request_id))
                return {'status': 'timed_out'}, 200
            except TowRequestCancelledError:
                logger.warning("{} TowRequestCancelledError".format(tow_request_id))
                return {'status': 'cancelled'}, 200
        else:
            return {'status': 'invalid_command'}, 400
