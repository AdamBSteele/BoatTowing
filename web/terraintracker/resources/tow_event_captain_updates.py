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

    decorators = [log_request, ]

    def put(self):
        """
        .. :quickref: Tow Event; Complete/cancel a tow event
        :<json string tow_event_id: UUID of this specific Tow Event

        :>json string status: [success, failure]
        :>json string message: In case of failure, human readable message
        """
        args = request.get_json()
        tow_event_id = args['tow_event_id']
        lat = args['lat']
        lon = args['lon']

        logger.info("TowEvent:{}, Captain pos: ({},{})".format(tow_event_id, lat, lon))

        te = TowEvent.query.get(tow_event_id)
        if not te:
            return bad_request("Tow Event not found")

        user = User.query.get(te.requestee_id)
        user.update_position(lat, lon)

        return {'status': 'success'}
