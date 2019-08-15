import datetime
import logging

from flask import render_template, g, request
from flask_restful import Resource
from pprint import pformat

from terraintracker.lib.twilio import twilio_message_sender

from terraintracker.models.user import User
from terraintracker.models.tow_request import TowRequestBatch

from terraintracker.resources.auth import multi_auth
from terraintracker.resources.decorators import log_request


logger = logging.getLogger(__name__)


class OperatorPanel():

    @multi_auth.login_required
    def render_operator_panel(self):
        logger.debug("rendering operator_panel")
        return render_template('distressed_boaters.html')

    def render_trb_card(self, trb_id):
        try:
            trb = TowRequestBatch.query.get(trb_id)
            requestor = User.query.get(trb.requestor_id)
            res = {
                'requestor': {
                    'name': requestor.name,
                    'phone': requestor.phone_number,
                    'lat': requestor.last_lat_seen,
                    'lon': requestor.last_long_seen,
                    'google_maps_string': requestor.google_maps_string,
                },
                'trb': {
                    'id': trb.id,
                    'time_sent': trb.time_sent.isoformat(),
                    'status': trb.status_string,
                    'captains': []
                }
            }
            captains = [User.query.get(tow_request.requestee_id) for tow_request in trb.tow_requests]
            for captain in captains:
                res['trb']['captains'].append({
                    'id': captain.id,
                    'name': captain.name,
                    'phone': captain.pretty_phone,
                })
            logger.debug(pformat(res))
            return render_template('operator-trb-card.html', res=res)
        except Exception as e:
            logger.exception(e)
            return "<p>Renderfail<p>"


class OperatorPanelJSON(Resource):
    decorators = [multi_auth.login_required, ]

    def get(self):
        try:
            trb_time_window = datetime.datetime.now() - datetime.timedelta(hours=6)
            trbs = TowRequestBatch.query.filter(TowRequestBatch.time_sent > trb_time_window) \
                                        .order_by(TowRequestBatch.time_sent).all()

            res = [trb.id for trb in trbs]
            logger.debug(pformat(res))
            return res
        except Exception as e:
            logger.exception(e)
            return [], 500


class OperatorPanelSendText(Resource):
    decorators = [multi_auth.login_required, ]

    def post(self):
        try:
            args = request.get_json()
            phone = args['phone']
            logger.debug(phone)
        except Exception as e:
            logger.exception(e)
            return {'status': 'failure'}, 400
        try:
            twilio_message_sender.send_mweb_drift_request_text(phone)
        except Exception as e:
            logger.exception(e)
            return {'status': 'failure'}, 500

        return {'status': 'success'}, 200


operator_panel_renderer = OperatorPanel()
