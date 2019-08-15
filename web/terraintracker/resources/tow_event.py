import logging

from flask import g, request
from flask_restful import Resource

from terraintracker.lib.ios_push_notifications import one_signal_notification_sender
from terraintracker.resources.auth import multi_auth
from terraintracker.resources.decorators import log_request
from terraintracker.models.tow_event import TowEvent, TowEventStatus, TowEventAlreadyOverError
from terraintracker.resources.response_templates import bad_request
from terraintracker.models.user import User

from terraintracker.lib.calculate_latlon_bearing import get_bearing_between_coords, get_distance_between_coords_in_feet

logger = logging.getLogger(__name__)


class TowEventResource(Resource):

    decorators = [log_request, multi_auth.login_required]

    def put(self):
        """
        .. :quickref: Tow Event; Complete/cancel a tow event
        :<json string tow_event_id: UUID of this specific Tow Event

        :>json string status: [success, failure]
        :>json string message: In case of failure, human readable message
        """
        args = request.get_json()
        action = args['action']
        tow_event_id = args['tow_event_id']

        logger.info("{} {}'ing TowEvent:{}".format(g.user, action, tow_event_id))

        te = TowEvent.query.get(tow_event_id)
        if not te:
            return bad_request("Tow Event not found")

        if g.user.id == te.requestee_id:
            other_user = User.query.get(te.requestor_id)
        elif g.user.id == te.requestor_id:
            other_user = User.query.get(te.requestee_id)
        else:
            return bad_request("This user isn't a part of that tow_event")

        if action == 'complete':
            try:
                te.complete()
                one_signal_notification_sender.sendTowEventCompleted(g.user, other_user)
            except TowEventAlreadyOverError as e:
                g.user.active_tow_event_serving = None
                other_user.active_tow_event_serving = None
                return {'status': 'failure', 'message': str(e)}
            return {'status': 'success'}, 200
        elif action == 'cancel':
            try:
                te.cancel()
                g.user.active_tow_event_serving = None
                other_user.active_tow_event_receiving = None
                one_signal_notification_sender.sendTowEventCancelled(g.user, other_user)
            except TowEventAlreadyOverError as e:
                g.user.active_tow_event_serving = None
                other_user.active_tow_event_serving = None
                return {'status': 'failure', 'message': str(e)}
            return {'status': 'success'}, 200
        else:
            return bad_request("'action' param must be one of: ['cancel', 'complete']")

    def get(self):
        """
        Get the details of the user's currently active Tow Event

        .. :quickref: Tow Event; Get the details of the user's currently active Tow Event.
        :<json string tow_event_id: UUID of this specific Tow Event



        :>json string tow_event_id: UUID of this specific Tow Event
        :>json float distance: distance between requestor and requestee
        :>json float bearing: compass bearing to the other user in the tow
        :>json float lat: other user's lat
        :>json float lon: other user's lon
        :>json string status: One of ["success", "not_found", "bad_request", "unknown_position"]
        :>json string tow_status: One of ["waiting_for_payment", "in_progress", "completed", "cancelled", "timed_out"]
        :>json string other_user_first_name: Other user's name.
        :>json float other_user_lat: Other users lat
        :>json float other_user_lon: Other users lon
        :status 200: success
        :status 404: no Tow Event found
        :status 204: Tow Event already ended (no JSON sent with 204s)
        :status 401: authorization failed

        """
        logger.debug("Get tow event. {}".format(g.user))

        try:
            tow_event_id = request.args['tow_event_id']
            tow_event = TowEvent.query.get(tow_event_id)
            if tow_event is None:
                return {'status': 'not_found'}, 404
        except Exception as e:
            logger.exception(e)
            return {'status': 'bad_request'}, 400

        if tow_event.status == TowEventStatus.cancelled.value:
            return {'status': 'success',
                    'tow_event_id': tow_event.id,
                    'tow_status': TowEventStatus.cancelled.name}, 200
        elif tow_event.status == TowEventStatus.completed.value:
            return {'status': 'success',
                    'tow_event_id': tow_event.id,
                    'tow_status': TowEventStatus.completed.name}, 200

        try:
            other_user_id = tow_event.requestee_id if tow_event.requestee_id != g.user.id else tow_event.requestor_id
            other_user = User.query.get(other_user_id)
            distance = get_distance_between_coords_in_feet(g.user.coords, other_user.coords)
            bearing = get_bearing_between_coords(g.user.coords, other_user.coords)
        except Exception:
            logger.exception("Error getting distance and bearing")
            return {'status': 'unknown_position', 'tow_event_id': tow_event.id}, 200
        return {
            'status': 'success',
            'tow_event_id': tow_event.id,
            'distance': "{0:.2f}".format(distance),
            'bearing': "{0:.2f}".format(bearing),
            'lat': other_user.last_lat_seen,
            'lon': other_user.last_long_seen,
            'tow_status': TowEventStatus(tow_event.status).name,
            'other_user_first_name': other_user.first_name,
            'other_user_lat': other_user.last_lat_seen,
            'other_user_lon': other_user.last_long_seen
        }
