"""
Handles towing CRUD
"""
import logging

from flask import request, g
from flask_restful import Resource

from terraintracker.resources.auth import multi_auth
from terraintracker.resources.decorators import log_request
from terraintracker.models.tow_event import TowEvent
from terraintracker.models.tow_request import NoRequesteesFound, TowRequestBatch
from terraintracker.lib.ios_push_notifications import one_signal_notification_sender


logger = logging.getLogger(__name__)


class TowRequestBatchResource(Resource):
    """
    TowRequestBatch CRUD
    """

    decorators = [log_request, multi_auth.login_required]

    def post(self):
        """
        Creates 1 TowRequestBatch object and 1+ TowRequest objects. Returns TowRequestBatch object.
        Sends requests to requestees.

        .. :quickref: Tow Request Batch; Creates TowRequestBatch object & sends requests to requestees.

        **Example request**:

        .. sourcecode:: http

          POST /tow_request HTTP/1.1
          Host: example.com
          Content-Type: application/json
          Accept: application/json
          Authorization: Token <facebook_access_token>

        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 201 OK
          Vary: Accept
          Content-Type: application/json

          {
            'tow_request_batch_id': "asdf1234jkl",
            'num_requests': 5
          }

        :query id: User ID
        :resheader Content-Type: application/json
        :<json float lat: user's current latitude
        :<json float lon: user's current longitude
        :<json float phone_number: user's current phone number
        :>json string tow_request_batch_id: UUID of this specific TowRequestBatch
        :>json string: num_requests: number of users that have received the tow request
        :status 201: Tow Requests sent successfully. return `tow_request_batch_id` and `num_requests`
        :status 204: No one was available to tow this user
        :status 401: authorization failed
        """
        # Get requestor
        requestor = g.user
        logger.info("{} requesting tow".format(requestor))

        # Update requestor's position
        try:
            args = request.get_json()
        except Exception:
            logger.info("No args provided")
            args = {}

        try:
            requestor.update_position(args['lat'], args['lon'])
        except KeyError:
            logger.info("Did not receive lat/lon")
        except Exception as e:
            logger.warning("Received none/invalid args (not fatal):{}\n{}".format(args, e))

        try:
            requestor.phone_number = args['phone_number']
            logger.info("Got phone number: {}".format(requestor.phone_number))
        except KeyError:
            logger.info("Did not receive phone_number")
        except Exception as e:
            logger.warning("Received none/invalid phone arg (not fatal):{}\n{}".format(args, e))

        # Create tow requests
        try:
            logger.info("Creating tow_request_batch")
            tow_request_batch = requestor.request_tow()
        except NoRequesteesFound:
            logger.info("No requestees found")
            return {}, 204
        except Exception as e:
            logger.exception(e)
            return {'error': str(e)}, 500

        logger.info("User {} [{},{}] requests a tow to {} users".format(
            requestor.id, requestor.last_lat_seen, requestor.last_long_seen, tow_request_batch.num_requests)
        )

        # Return response
        return {
            'tow_request_batch_id': tow_request_batch.id,
            'num_requests': str(tow_request_batch.num_requests)
        }, 201

    def put(self):
        """
        Updates TowRequestBatch object.
        Currently just used to cancel a TowRequestBatch

        .. :quickref: Tow Request Batch; Used by requestee to cancel an outgoing Tow Request Batch.

        :<json string action: one of ['cancel', ]
        :<json string tow_request_batch_id: the specific tow request batch we're acting on
        :<json float lon: user's current longitude
        :<json float lat: user's current latitude

        :>json string: status: One of ["not_found", "already_accepted", "timed_out", "success"]

        _
        :status 200: Action accepted. `status` one of: ["not_allowed", "invalid_command", "success"]
        :status 400: Bad request (probably due to invalid "action" param)
        :status 403: authorization failed
        :status 404: Tow Request not found `status: "not_found"`
        """
        required_args = ['action', 'tow_request_batch_id']

        try:
            args = request.get_json()
            action = args['action']
            tow_request_batch_id = args.get('tow_request_batch_id')
            if not tow_request_batch_id:
                raise KeyError
        except Exception as e:
            logger.exception(e)
            return {'status': 'The endpoint requires action + id args {}'.format(required_args)}, 400

        try:
            g.user.update_position(args['lat'], args['lon'])
        except Exception:
            pass

        if action == "cancel":
            logger.debug("{} cancelling tow request {}".format(g.user, tow_request_batch_id))
            trb = TowRequestBatch.query.get(tow_request_batch_id)
            if trb.requestor_id != g.user.id:
                return {'status': 'not_allowed'}, 403
            trb.cancel()
            return {'status': 'success'}, 200
        else:
            return {'status': 'invalid_command'}, 400

    def get(self):
        """
        Current user gets the status of their outgoing Tow Request Batch
        If tow_event_id is populated should push user to Tow Event Screen

        .. :quickref: Tow Request Batch; Current user gets the status of their outgoing Tow Request Batch

        :<json string tow_request_batch_id: UUID of the TowRequestBatch they want the status of

        :>json string num_requests: number of users that have received the tow request
        :>json string num_rejections: number of users that have rejected the tow request
        :>json string last_update: last time someone actioned this tow request
        :>json string status: status of the Tow Request Batch. One of: [timed_out, rejected, active, accepted]
        :>json string tow_event_id: [optional] ID of a tow_event that resulted
                                    from this batch if batch status is accepted

        :status 200: Success
        :status 400: Bad request - probably due to missing *tow_request_batch_id* param
        :status 401: authorization failed
        :status 403: Tried to get a TowRequestBatch you're not allowed to look at
        :status 404: TowRequestBatch not found
        """
        try:
            tow_request_batch_id = request.args['tow_request_batch_id']
        except Exception as e:
            logger.exception(e)
            return {'status': 'missing required arg tow_request_batch_id'}, 400

        logger.debug("Getting trb [{}] for user {}".format(tow_request_batch_id, g.user))

        trb = TowRequestBatch.query.get(str(tow_request_batch_id))

        if trb is None:
            logger.warning("Couldn't find a TowRequestBatch for {}".format(g.user))
            return {'status': 'no tow request found with id {}'.format(tow_request_batch_id)}, 404

        if trb.requestor_id != g.user.id:
            logger.warning("User tried to access someone elses tow request")
            return {'status': "can't get someone else's tow request batch"}, 403

        trb.update_status()
        tow_event_id = None
        try:
            tow_event = TowEvent.query.filter_by(tow_request_batch_id=tow_request_batch_id).first()
            tow_event_id = tow_event.id if tow_event else None
        except Exception as e:
            logger.exception(e)
        res = {
            'num_requests': trb.num_requests,
            'num_rejections': trb.num_rejections,
            'last_update': str(trb.last_update),
            'status': trb.status_string,
            'tow_event_id': tow_event_id
        }
        logger.debug(res)

        return res, 200
