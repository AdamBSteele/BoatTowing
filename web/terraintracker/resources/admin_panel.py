import logging

from flask import render_template
from sqlalchemy import desc

from terraintracker.resources.decorators import is_admin, log_request
from terraintracker.models.user import User
from terraintracker.models.live_configuration import live_config
from terraintracker.models.request_log import RequestLog
from terraintracker.models.tow_request import TowRequestBatch
from terraintracker.models.tow_event import TowEvent
from terraintracker.resources.auth import multi_auth


logger = logging.getLogger(__name__)


class AdminPanel():

    @multi_auth.login_required
    @is_admin
    def render_admin_panel(self):
        logger.debug("rendering admin_panel")
        users = User.query.all()
        trbs = TowRequestBatch.query.order_by(TowRequestBatch.last_update.desc()).limit(10).all()
        requests = RequestLog.query.order_by(RequestLog.timestamp.desc()).limit(100).all()
        return render_template('admin_panel.html', requests=requests, users=users, trbs=trbs, counts_dict={})

    @multi_auth.login_required
    @is_admin
    def render_trb_details_page(self, trb_id):
        logger.debug("rendering trb_details_page")
        trb = TowRequestBatch.query.get(trb_id)
        return render_template('trb_details.html', trb=trb, tow_requests=trb.tow_requests)

    @multi_auth.login_required
    @is_admin
    def render_tow_events(self):
        logger.debug("rendering tow_events page")
        tow_events = TowEvent.query.order_by(desc(TowEvent.time_sent)).all()
        return render_template('tow_events.html', tow_events=tow_events)

    @multi_auth.login_required
    @is_admin
    def render_tow_request_batches(self):
        logger.debug("rendering tow request batches page")
        tow_request_batches = TowRequestBatch.query.order_by(desc(TowRequestBatch.time_sent)).all()
        return render_template('tow_request_batches.html', tow_request_batches=tow_request_batches)

    @multi_auth.login_required
    @is_admin
    def render_users(self):
        logger.debug("rendering users page")
        users = User.query.all()
        return render_template('users.html', users=users)

    @multi_auth.login_required
    @is_admin
    def render_towers(self):
        logger.debug("rendering towers page")
        towers = User.towers()
        return render_template('towers.html', towers=towers)

    @multi_auth.login_required
    @is_admin
    def render_user_detail(self, user_id):
        logger.debug("rendering user detail page for user {}".format(user_id))
        user = User.query.get(user_id)
        user_dict = user.__dict__ if user else {"id": "user not found. Is this a test user?"}
        return render_template('user_detail.html', user=user, user_dict=user_dict)

    @multi_auth.login_required
    @is_admin
    def render_login(self, trb_id):
        logger.debug("rendering login")
        return render_template('login.html')

    @multi_auth.login_required
    @is_admin
    @is_admin
    def render_live_configuration(self):
        logger.debug("rendering login")
        return render_template('live_configuration.html',
                               live_config=live_config,
                               live_config_dict=live_config.to_dict())


admin_panel_renderer = AdminPanel()
