import logging

from flask import g, request
from flask_restful import Resource

from terraintracker.app_init import db
from terraintracker.resources.auth import multi_auth
from terraintracker.models.location import Location
from terraintracker.models.location_history import LocationHistory
from terraintracker.resources.response_templates import bad_request

logger = logging.getLogger(__name__)


class IsWater(Resource):

    decorators = [multi_auth.login_required]

    def get(self):
        user_id = g.user.id

        lat = request.args.get('lat', None)
        lon = request.args.get('lon', None)
        if lon is None or lat is None:
            return bad_request("Missing required 'lat' and/or 'lon' arguments")
        try:
            loc = Location(float(lat), float(lon))
        except ValueError:
            return bad_request("Lat and lon must be floats")
        is_water = loc.isWater()
        db.session.merge(loc)

        lh = LocationHistory(user_id=user_id, location_id=loc.id)
        db.session.merge(lh)

        db.session.commit()
        data = {
            'lat': lat,
            'lon': lon,
            'is_water': is_water,
        }

        return data, 200
