import logging

from flask import render_template
from terraintracker.resources.decorators import log_request


logger = logging.getLogger(__name__)


class UserPanel():

    @log_request
    def render_new_tow_request_form(self):
        logger.debug("rendering new_user_form")
        return render_template('material_design_tow_request.html')


user_panel_renderer = UserPanel()
