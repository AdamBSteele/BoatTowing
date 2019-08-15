# pylint: skip-file

"""
CustomTestCase uses mocks to patch anything we want.
All our testCases inherit from this.
If you want to patch an external service in your tests, follow the patterns here.patterns here:
 - Add the patches in _patch_on
 - Remove the patches in _patch_off

"""
import base64
import json
import logging

from datetime import datetime
from flask_testing import TestCase
from unittest import mock

from terraintracker.app_init import db
from terraintracker.models.user import User
from terraintracker.tests.data.user_test_data import TEST_USER_PASSWORD

logger = logging.getLogger(__name__)

# This replaces live_config wherever it's used
mock_live_config = mock.MagicMock(
    modification_time=datetime.utcnow(),
    modification_user='TEST_DEVELOPER',
    tow_radius=16093,  # 16093m == 10 miles
)


class CustomTestCase(TestCase):

    def _patch_on(self):
        print("\t-patching-\n")
        # These three lines patch twilio calls in lib.twilio
        self.patch_twilio = mock.patch('terraintracker.lib.twilio.twilio_message_sender.request_tow', mock.MagicMock())
        self.mock_twilio = self.patch_twilio.start()
        self.mock_twilio.return_value = "TEST_USER"

        # These two lines patch live_config in models.user
        self.patch_live_config = mock.patch('terraintracker.models.user.live_config', mock_live_config)
        self.mock_live_config = self.patch_live_config.start()

        # These two lines patch stripe
        self.patch_stripe = mock.patch('terraintracker.lib.stripe_integration.initialize_stripe_customer',
                                       mock.MagicMock())
        self.mock_stripe = self.patch_stripe.start()
        self.mock_stripe.return_value = "TEST_USER"

        # iOS notification patching
        self.patch_sendTowRequest = mock.patch('terraintracker.lib.ios_push_notifications.one_signal_notification_sender.sendTowRequest',
                                               mock.MagicMock())
        self.mock_sendTowRequest = self.patch_sendTowRequest.start()
        self.mock_sendTowRequest.return_value = ("TEST_USER")

        # iOS notification patching
        self.patch_acceptTowRequest = mock.patch('terraintracker.lib.ios_push_notifications.one_signal_notification_sender.sentTowRequestAccepted',
                                                mock.MagicMock())
        self.mock_acceptTowRequest = self.patch_acceptTowRequest.start()
        self.mock_acceptTowRequest.return_value = ("TEST_USER")

        # iOS notification patching
        self.patch_snc = mock.patch('terraintracker.lib.ios_push_notifications.one_signal_notification_sender.sendNoOneIsComingBecauseYouGotRejected',
                                    mock.MagicMock())
        self.mock_snc = self.patch_snc.start()
        self.mock_snc.return_value = ("TEST_USER")

    def _patch_off(self):
        self.patch_twilio.stop()
        self.patch_live_config.stop()
        self.patch_stripe.stop()
        self.patch_sendTowRequest.stop()
        self.patch_acceptTowRequest.stop()
        self.patch_snc.stop()

    def run(self, *args, **kwargs):
        self.addCleanup(self.remove_test_data)

        # Patch, run tests, and unpatch
        self._patch_on()
        super().run(*args, **kwargs)
        self._patch_off()

    def create_app(self):
        from terraintracker.app import app
        self.client = app.test_client()
        return app

    def remove_test_data(self):
        try:
            test_users = User.query.filter_by(_is_test_user=True).all()
            for u in test_users:
                db.session.delete(u)
            db.session.commit()
        except Exception:
            pass

    def make_authorization_header(self, user):
        auth_string = 'Basic ' + base64.b64encode(bytes(user.id + ":" + TEST_USER_PASSWORD, 'ascii')).decode('ascii')
        return {'Authorization': auth_string}

    def make_api_post_request(self, endpoint, user, data={}):
        return self.client.post(endpoint,
                                content_type='application/json',
                                data=json.dumps(data),
                                headers=self.make_authorization_header(user))

    def make_api_put_request(self, endpoint, user, data={}):
        return self.client.put(endpoint,
                               content_type='application/json',
                               data=json.dumps(data),
                               headers=self.make_authorization_header(user))

    def make_api_get_request(self, endpoint, user, data={}):
        if data:
            url_args = '&'.join(["{}={}".format(k, data[k]) for k in data.keys()])
            endpoint = "{}?{}".format(endpoint, url_args)
            print(endpoint)
        return self.client.get(endpoint,
                               content_type='application/json',
                               headers=self.make_authorization_header(user))
