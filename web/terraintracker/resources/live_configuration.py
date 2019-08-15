import logging

from flask import g, request
from flask_restful import Resource

from terraintracker.app_init import db
from terraintracker.resources.auth import multi_auth
from terraintracker.resources.decorators import is_admin, log_request
from terraintracker.models.live_configuration import LiveConfiguration, live_config
from terraintracker.resources.response_templates import bad_request

logger = logging.getLogger(__name__)


class LiveConfigurationResource(Resource):

    decorators = [is_admin, multi_auth.login_required]

    def post(self):
        admin = g.user
        logger.debug("{} changing admin_panel".format(admin))

        # Update requestor's position
        try:
            args = request.get_json()
        except Exception:
            logger.info("No args provided")
            args = {}

        logger.debug(args)
        logger.debug(request.args)
        for arg in args:
            print(arg, args[arg])
        return args
