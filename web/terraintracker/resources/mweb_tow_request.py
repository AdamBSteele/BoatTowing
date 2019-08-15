"""
Handles towing CRUD
"""
import logging
import random

from flask import request, g
from flask_restful import Resource

from terraintracker.app_init import db
from terraintracker.resources.decorators import log_request
from terraintracker.models.user import User, Boat
from terraintracker.models.tow_request import NoRequesteesFound


logger = logging.getLogger(__name__)


class MWebTowRequest(Resource):
    decorators = [log_request]

    def post(self):
        expected_args = ["boat_make", "boat_type", "boat_length",
                         "lat", "lon",
                         "name", "phone",
                         "service_type"]
        try:
            args = request.get_json()
            logger.info("MWeb Drift Request: {}".format(args))
            for arg in expected_args:
                if arg not in args:
                    logger.error("Missing required arg: {}".format(arg))
                    return {"status": "missing_arg"}, 400
        except Exception as e:
            logger.exception(e)

        # Make the new User object
        u = User.query.get(args['phone'])
        if u is not None:
            logger.info("Found returning user: {}".format(u))
            g.user = u
        else:
            u = User(_id=args['phone'], name=args['name'], role=User.Role.mweb_user.value)
        u.update_position(args['lat'], args['lon'])
        u.phone_number = args['phone']
        u.name = args['name']

        # Give em a boat
        try:
            b = Boat(u, args['boat_make'], args['boat_type'], args['boat_length'])
        except Exception as e:
            logger.exception(e)

        try:
            trb = u.request_tow(args["service_type"])
        except NoRequesteesFound as e:
            return {"status": "no_captains_in_area"}

        return {"status": "success"}

    def get(self):
        logger.info(request.args)
        try:
            lat = str(request.args['lat'])[:10].strip()
            lon = str(request.args['lon'])[:10].strip()
            logger.info("{}, {}".format(lat, lon))

            # This is an ugly way to test availability but for some reason
            # I have to create a user to run that Geo DB Query
            user_id = ("internal_avail_checker{}").format(random.randint(0, 10))
            u = User.query.get(user_id)
            if not u:
                u = User(_id=user_id, name=user_id)
            u.update_position(lat, lon)
            db.session.merge(u)
            requestees = u.get_possible_requestees()
        except Exception as e:
            logger.exception(e)
            db.session.rollback()
            return {'status': 'error'}
        return {"num_found": "{}".format(len(requestees))}
