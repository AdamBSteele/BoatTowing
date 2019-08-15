"""
Creates the API object, attaches resources to it
"""
from flask import render_template
from flask_restful import Api
from terraintracker.app_init import app

# Import resources after "app" so "app" is initialized
from terraintracker.resources.admin_panel import admin_panel_renderer
from terraintracker.resources.operator_panel import (operator_panel_renderer,
                                                     OperatorPanelJSON,
                                                     OperatorPanelSendText)
from terraintracker.resources.user_panel import user_panel_renderer
from terraintracker.resources.marina_user import marina_user_renderer
from terraintracker.resources.auth import LoginResource
from terraintracker.resources.location import IsWater  # pylint: disable=ungrouped-imports
from terraintracker.resources.live_configuration import LiveConfigurationResource
from terraintracker.resources.marina_twilio import MarinaTwilio
from terraintracker.resources.mweb_tow_request import MWebTowRequest
from terraintracker.resources.stripe_payments import StripeCustomerResource, StripeChargeResource
from terraintracker.resources.user import UserResource  # pylint: disable=ungrouped-imports
from terraintracker.resources.tow_event import TowEventResource
from terraintracker.resources.tow_request import TowRequestResource
from terraintracker.resources.tow_request_batch import TowRequestBatchResource
from terraintracker.resources.tow_request_twillio import TwillioDispatcher

# Set up API routes
api = Api(app, catch_all_404s=True)  # pylint: disable=invalid-name
api.add_resource(IsWater, '/geo/is_water')
api.add_resource(UserResource, '/users')
api.add_resource(TowRequestResource, '/tow_request')
api.add_resource(TowRequestBatchResource, '/tow_request_batch')
api.add_resource(TowEventResource, '/tow_event')
api.add_resource(TwillioDispatcher, '/twillioDispatcher')
api.add_resource(LoginResource, '/login')
api.add_resource(MarinaTwilio, '/marina_twilio')
api.add_resource(OperatorPanelSendText, '/operator_panel_send_text')
api.add_resource(StripeCustomerResource, '/stripe_customer')
api.add_resource(StripeChargeResource, '/stripe_charge')
api.add_resource(LiveConfigurationResource, '/live_configuration')
api.add_resource(MWebTowRequest, '/mweb_tow_request')
api.add_resource(OperatorPanelJSON, '/operator_panel_json')


@app.route('/')
def render_index():
    return render_template('index.html')

@app.route('/terms-and-conditions')
def render_terms_and_conditions():
    return render_template('terms-and-conditions.html')



ADMIN_PANEL_PREFIX = "/admin_panel"


@app.route(ADMIN_PANEL_PREFIX + '/home')
def render_home():
    return admin_panel_renderer.render_admin_panel()


@app.route(ADMIN_PANEL_PREFIX + '/html_login')
def render_html_login():
    return admin_panel_renderer.render_admin_panel()


@app.route(ADMIN_PANEL_PREFIX + '/tow_events')
def render_tow_events():
    return admin_panel_renderer.render_tow_events()


@app.route(ADMIN_PANEL_PREFIX + '/tow_request_batches')
def render_tow_request_batches():
    return admin_panel_renderer.render_tow_request_batches()


@app.route(ADMIN_PANEL_PREFIX + '/users')
def render_users():
    return admin_panel_renderer.render_users()


@app.route(ADMIN_PANEL_PREFIX + '/towers')
def render_towers():
    return admin_panel_renderer.render_towers()


@app.route(ADMIN_PANEL_PREFIX + '/user_detail/<user_id>')
def render_user_detail(user_id):
    return admin_panel_renderer.render_user_detail(user_id)


@app.route(ADMIN_PANEL_PREFIX + '/live_configuration')
def render_live_config():
    return admin_panel_renderer.render_live_configuration()


@app.route(ADMIN_PANEL_PREFIX + '/trb_detail/<trb_id>')
def render_trb_details_page(trb_id):
    return admin_panel_renderer.render_trb_details_page(trb_id)


OPERATOR_PANEL_PREFIX = "/operator_panel"


@app.route(OPERATOR_PANEL_PREFIX + '/home')
def render_operator_panel():
    return operator_panel_renderer.render_operator_panel()


@app.route(OPERATOR_PANEL_PREFIX + '/distressed_boaters')
def render_operator_panel_distressed_boaters():
    return operator_panel_renderer.render_operator_panel()


@app.route(OPERATOR_PANEL_PREFIX + "/render_trb_card/<trb_id>")
def render_trb_card(trb_id):
    return operator_panel_renderer.render_trb_card(trb_id)


USER_PANEL_PREFIX = "/user_panel"


@app.route(USER_PANEL_PREFIX + '/new_tow_request')
def render_new_tow_request():
    return user_panel_renderer.render_new_tow_request_form()


@app.route(USER_PANEL_PREFIX + '/md_tow_request')
def render_md_tow_request():
    return user_panel_renderer.render_new_tow_request_form()


MARINA_USER_PREFIX = "/marina_user"


@app.route(MARINA_USER_PREFIX + '/live_map')
def render_marina_user_live_map():
    return marina_user_renderer.render_live_map()
