from random import randint

import logging

from datetime import datetime, timedelta

from terraintracker.app import api
from terraintracker.app_init import db

from terraintracker.models.tow_request import TowRequest, TowRequestBatch
from terraintracker.models.tow_event import TowEvent, TowEventStatus
from terraintracker.models.user import User
from terraintracker.resources.tow_request import TowRequestResource
from terraintracker.resources.tow_request_batch import TowRequestBatchResource
from terraintracker.resources.tow_event import TowEventResource
from terraintracker.tests.data.user_test_data import (ELIGIBLE_USERS,
                                                      EXPECTED_REQUESTEE_IDS_BY_REQUESTOR,
                                                      LONELY_USER,
                                                      create_test_user)
from terraintracker.tests.custom_test_case import CustomTestCase

logger = logging.getLogger(__name__)


class TestTowEvent(CustomTestCase):

    # In pytest... when you make a function named 'setUp' it auto-runs before every test
    def setUp(self):
        # Create all the ELIGIBLE USERS from user_test_data
        self.eligible_users = [create_test_user(u) for u in ELIGIBLE_USERS]

    def test_active_tow_event_cancel_properly(self):
        # Requestor is a random eligible user
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        # Make a tow request batch. (via API POST)
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        # 201 means it worked
        self.assertEqual(res.status_code, 201)

        # Get the tow request batch you just created
        trb = TowRequestBatch.query.get(res.json['tow_request_batch_id'])
        # Grab a random tow request
        random_request = trb.tow_requests[randint(0, trb.num_requests - 1)]
        # Get the requestee from that random tow request
        requestee = User.query.get(random_request.requestee_id)

        # Requestee accepts tow request
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 201)
        tow_event_id = res.json['tow_event_id']
        requestee = User.query.get(requestee.id)
        requestor = User.query.get(requestor.id)
        self.assertEqual(tow_event_id, requestee.active_tow_event_serving_id)
        self.assertEqual(tow_event_id, requestor.active_tow_event_receiving_id)

        # Requestee cancels tow request
        res = self.make_api_put_request(api.url_for(TowEventResource),
                                        requestee,
                                        {'action': 'cancel', 'tow_event_id': tow_event_id},)
        requestee = User.query.get(requestee.id)
        requestor = User.query.get(requestor.id)
        towevent = TowEvent.query.get(tow_event_id)
        self.assertEqual(None, requestor.active_tow_event_serving_id)
        self.assertEqual(None, requestee.active_tow_event_receiving_id)
        self.assertEqual(TowEventStatus.cancelled.value, towevent.status)

    def test_active_tow_event_complete_properly(self):
        # Requestor is a random eligible user
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        # Make a tow request batch. (via API POST)
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        # 201 means it worked
        self.assertEqual(res.status_code, 201)

        # Get the tow request batch you just created
        trb = TowRequestBatch.query.get(res.json['tow_request_batch_id'])
        # Grab a random tow request
        random_request = trb.tow_requests[randint(0, trb.num_requests - 1)]
        # Get the requestee from that random tow request
        requestee = User.query.get(random_request.requestee_id)

        # Requestee accepts tow request
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 201)
        tow_event_id = res.json['tow_event_id']
        requestee = User.query.get(requestee.id)
        requestor = User.query.get(requestor.id)
        self.assertEqual(tow_event_id, requestee.active_tow_event_serving_id)
        self.assertEqual(tow_event_id, requestor.active_tow_event_receiving_id)

        # TODO: Actually make API calls to simulate payment
        tow_event = TowEvent.query.get(tow_event_id)
        tow_event.status = TowEventStatus.in_progress.value
        db.session.merge(tow_event)
        db.session.commit()

        # Requestee completes tow request
        res = self.make_api_put_request(api.url_for(TowEventResource),
                                        requestee,
                                        {'action': 'complete', 'tow_event_id': tow_event_id},)
        requestee = User.query.get(requestee.id)
        requestor = User.query.get(requestor.id)
        tow_event = TowEvent.query.get(tow_event_id)
        self.assertEqual(None, requestor.active_tow_event_serving_id)
        self.assertEqual(None, requestee.active_tow_event_receiving_id)
        self.assertEqual(TowEventStatus.completed.value, tow_event.status)

    def test_active_tow_event_in_user_model_gets_set_properly(self):
        # Requestor is a random eligible user
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        # Make a tow request batch. (via API POST)
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        # 201 means it worked
        self.assertEqual(res.status_code, 201)

        # Get the tow request batch you just created
        trb = TowRequestBatch.query.get(res.json['tow_request_batch_id'])
        # Grab a random tow request
        random_request = trb.tow_requests[randint(0, trb.num_requests - 1)]
        # Get the requestee from that random tow request
        requestee = User.query.get(random_request.requestee_id)

        # Requestee accepts tow request
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 201)
        tow_event_id = res.json['tow_event_id']
        requestee = User.query.get(requestee.id)
        requestor = User.query.get(requestor.id)
        tow_event = TowEvent.query.get(tow_event_id)
        self.assertEqual(tow_event_id, requestee.active_tow_event_serving_id)
        self.assertEqual(tow_event_id, requestor.active_tow_event_receiving_id)
        self.assertEqual(res.json['tow_request_batch_id'], tow_event.tow_request_batch_id)
        self.assertEqual(None, requestee.active_tow_request_batch)
        self.assertEqual(res.json['tow_request_batch_id'], requestor.active_tow_request_batch_id)


if __name__ == '__main__':
    print("Check the README for how to run this test.")
    pass
