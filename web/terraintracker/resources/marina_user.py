import logging

from flask import render_template
from terraintracker.resources.decorators import log_request
from terraintracker.config import GOOGLE_MAPS_KEY


logger = logging.getLogger(__name__)


class MarinaUserRenderer():

    @log_request
    def render_live_map(self):
        logger.debug("rendering marina_user_live_map, {}".format(GOOGLE_MAPS_KEY))
        return render_template('marina_user_live_map.html', GOOGLE_MAPS_KEY=GOOGLE_MAPS_KEY)


marina_user_renderer = MarinaUserRenderer()
