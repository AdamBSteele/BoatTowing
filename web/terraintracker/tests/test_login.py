import base64
import logging

from terraintracker.app import api

from terraintracker.resources.auth import LoginResource
from terraintracker.tests.data.user_test_data import LONELY_USER, create_test_user
from terraintracker.tests.custom_test_case import CustomTestCase

logger = logging.getLogger(__name__)


class TestAuth(CustomTestCase):

    def setUp(self):
        self.lonely_user = create_test_user(LONELY_USER)

    def test_verify_password_fails(self):
        # Test with an existing user's id but bad password
        auth_string = 'Basic ' + base64.b64encode(bytes(self.lonely_user.id + ":" + 'trash', 'ascii')).decode('ascii')
        res = self.client.post(api.url_for(LoginResource),
                               content_type='application/json',
                               headers={'Authorization': auth_string})
        self.assert401(res)

        # Test with garbage
        auth_string = 'Basic ' + base64.b64encode(bytes('garbage' + ":" + 'trash', 'ascii')).decode('ascii')
        res = self.client.post(api.url_for(LoginResource),
                               content_type='application/json',
                               headers={'Authorization': auth_string})
        self.assert401(res)


class TestLogin(CustomTestCase):

    def setUp(self):
        self.lonely_user = create_test_user(LONELY_USER)

    def test_post_login_no_args(self):
        res = self.make_api_post_request(api.url_for(LoginResource), self.lonely_user, {})
        self.assert400(res)


if __name__ == '__main__':
    print("Check the README for how to run this test.")
    pass
