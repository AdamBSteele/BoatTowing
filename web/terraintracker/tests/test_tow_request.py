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


class TowRequestBatchTest(CustomTestCase):

    def setUp(self):
        self.eligible_users = [create_test_user(u) for u in ELIGIBLE_USERS]

    def test_post_tow_request_batch(self):
        for requestor in self.eligible_users:
            res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
            self.assertEqual(res.status_code, 201, "{} couldn't request ppl".format(requestor))

            # Get new tow_request_batch contains all tows we expected
            tow_request_batch_id = res.json['tow_request_batch_id']
            actual_ids = set([x.requestee_id for x in TowRequest.get_tow_requests_in_batch(tow_request_batch_id)])
            expected_ids = EXPECTED_REQUESTEE_IDS_BY_REQUESTOR[requestor.id]
            self.assertEqual(expected_ids, actual_ids,
                             "\nTest:{}\nexpected:{}\nactual:{}".format(requestor.id, expected_ids, actual_ids))

            # Check num_requests
            self.assertEqual(len(expected_ids), int(res.json['num_requests']))

    def test_get_tow_request_batch(self):
        # Post a TowRequestBatch
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        self.assertEqual(res.status_code, 201, "{} couldn't request ppl".format(requestor))
        tow_request_batch_id = res.json['tow_request_batch_id']

        # Get a TowRequestBatch
        trb = TowRequestBatch.query.get(tow_request_batch_id)
        res = self.make_api_get_request(api.url_for(TowRequestBatchResource),
                                        requestor,
                                        {'tow_request_batch_id': tow_request_batch_id})
        self.assertEqual(res.status_code, 200, "{} couldn't get tow request batch".format(requestor))
        self.assertEqual(res.json['num_rejections'], 0)

        # Time out the TowRequestBatch
        trb.time_sent = datetime.now() - timedelta(minutes=60)
        db.session.merge(trb)

        # Get it, make sure it's timed out
        res = self.make_api_get_request(api.url_for(TowRequestBatchResource),
                                        requestor,
                                        {'tow_request_batch_id': tow_request_batch_id})
        self.assertEqual(res.status_code, 200, "{} couldn't get tow request batch".format(requestor))
        self.assertEqual(res.json['status'], TowRequestBatch.Status.timed_out.name)

        # Dude with no acess tries to get it but it's timed out
        dude_with_no_access = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        res = self.make_api_get_request(api.url_for(TowRequestBatchResource),
                                        dude_with_no_access,
                                        {'tow_request_batch_id': tow_request_batch_id})
        self.assertEqual(res.status_code, 403, "{} couldn't get tow request batch".format(requestor))

    def tearDown(self):
        self.remove_test_data()


class TowRequestTest(CustomTestCase):
    def setUp(self):
        self.eligible_users = [create_test_user(u) for u in ELIGIBLE_USERS]
        self.lonely_user = create_test_user(LONELY_USER)

    def test_rejections(self):
        logger.debug("Creating tow requests")
        for requestor in self.eligible_users:
            res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
            self.assertEqual(res.status_code, 201, "res is {}".format(res.__dict__))

            # Get new tow_request_batch contains all tows we expected
            tow_request_batch_id = res.json['tow_request_batch_id']
            tow_batch = TowRequestBatch.query.get(tow_request_batch_id)

            # Grab all requests from batch
            tow_requests = TowRequest.get_tow_requests_in_batch(tow_batch.id)
            actual_ids = set([r.requestee_id for r in tow_requests])
            expected_ids = EXPECTED_REQUESTEE_IDS_BY_REQUESTOR[requestor.id]
            self.assertEqual(expected_ids, set(actual_ids),
                             "\nTest:{}\nexpected:{}\nactual:{}".format(requestor.id, expected_ids, set(actual_ids)))

            # Check num_requests
            num_requests = int(res.json['num_requests'])
            num_expected = len(expected_ids)
            # Assert num_requests looks good in response
            self.assertEqual(num_expected, num_requests, "expected:{}\nactual:{}".format(num_expected, num_requests))
            # Assert num_requests looks good in db
            self.assertEqual(num_expected, tow_batch.num_requests,
                             "expected:{}\nactual:{}".format(num_expected, num_requests))

            # Reject each request from this batch
            current_rejection_count = 0
            self.assertEqual(tow_batch.num_rejections, current_rejection_count)
            for tow_request in tow_requests:
                requestee = User.query.get(tow_request.requestee_id)
                res = self.make_api_put_request(api.url_for(TowRequestResource),
                                                requestee,
                                                {'action': 'reject', 'tow_request_id': tow_request.id})
                self.assert200(res)
                current_rejection_count += 1
                tow_batch = TowRequestBatch.query.get(tow_request_batch_id)
                self.assertEqual(current_rejection_count, tow_batch.num_rejections,
                                 "Tow Batch [{}] rejections\nExpected:{}\nActual:{}".format(tow_request_batch_id,
                                                                                            tow_batch.num_rejections,
                                                                                            current_rejection_count))

            self.assertEqual(tow_batch.status, TowRequestBatch.Status.all_rejected.value)

    def test_two_people_try_to_accept_the_same_tow_request_batch(self):
        # Post TowRequestBatch
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        self.assertEqual(res.status_code, 201)
        tow_request_batch_id = res.json['tow_request_batch_id']
        trb = TowRequestBatch.query.get(tow_request_batch_id)

        # Accept a random requestee
        i = randint(0, trb.num_requests - 1)
        random_request = trb.tow_requests[i]
        requestee = User.query.get(random_request.requestee_id)
        logger.debug("Requestee {} rejects tow request".format(requestee))
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 201)
        tow_event_id = res.json['tow_event_id']

        requestor = User.query.get(requestor.id)
        self.assertEqual(requestor.active_tow_event_receiving.id, tow_event_id)

        requestee = User.query.get(requestee.id)
        self.assertEqual(requestee.active_tow_event_serving.id, tow_event_id)

        # Accept a different random request
        i += 1
        i = i % len(trb.tow_requests) - 1
        random_request = trb.tow_requests[i]
        requestee = User.query.get(random_request.requestee_id)
        logger.debug("Requestee {} accepts tow request".format(requestee))
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['status'], 'already_accepted')

        # TODO ADD STUFF

    def test_action_on_timed_out_tow_request(self):
        # Post TowRequestBatch
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        self.assertEqual(res.status_code, 201)

        # Time out the TowRequestBatch
        tow_request_batch_id = res.json['tow_request_batch_id']
        trb = TowRequestBatch.query.get(tow_request_batch_id)
        trb.time_sent = datetime.now() - timedelta(minutes=60)
        db.session.merge(trb)

        # Reject a random request
        i = randint(0, trb.num_requests - 1)
        random_request = trb.tow_requests[i]
        requestee = User.query.get(random_request.requestee_id)
        logger.debug("Requestee {} rejects tow request".format(requestee))
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'reject', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "timed_out")

        # Accept a different random request
        i += 1
        i = i % len(trb.tow_requests) - 1
        random_request = trb.tow_requests[i]
        requestee = User.query.get(random_request.requestee_id)
        logger.debug("Requestee {} accepts tow request".format(requestee))
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "timed_out")

    def test_acceptance_success(self):
        requestor = self.eligible_users.pop(randint(0, len(self.eligible_users) - 1))
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        self.assertEqual(res.status_code, 201)

        logger.debug("Grab arbitrary request from the TowRequestBatch that was created")
        trb = TowRequestBatch.query.get(res.json['tow_request_batch_id'])
        random_request = trb.tow_requests[randint(0, trb.num_requests - 1)]
        requestee = User.query.get(random_request.requestee_id)

        logger.debug("Requestee {} accepts tow request".format(requestee))
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestee,
                                        {'action': 'accept', 'tow_request_id': random_request.id},)
        self.assertEqual(res.status_code, 201)
        tow_event_id = res.json['tow_event_id']
        tow_event = TowEvent.query.get(tow_event_id)
        self.assertEqual(tow_event.status, TowEventStatus.waiting_for_payment.value)

        # TODO: Make requestor actually pay
        tow_event.status = TowEventStatus.in_progress.value
        db.session.merge(tow_event)
        db.session.commit()

        logger.debug("Requestee gets distance / bearing")
        res = self.make_api_get_request(api.url_for(TowEventResource), requestee, data={'tow_event_id': tow_event_id})
        self.assertEqual(res.status_code, 200, "Bad status code. JSON: {}".format(res.json))
        self.assertEqual(res.json['tow_event_id'], tow_event_id)
        self.assertTrue(0.0 <= float(res.json['bearing']) <= 360.0)
        self.assertTrue(0.0 <= float(res.json['distance']) <= 52800)

    def test_no_requestees_found(self):
        requestor = self.lonely_user
        res = self.make_api_post_request(api.url_for(TowRequestBatchResource), requestor)
        self.assertEqual(res.status_code, 204)

    def test_respond_to_non_existant_tow_request(self):
        requestor = self.lonely_user
        for command in ['accept', 'reject']:
            res = self.make_api_put_request(api.url_for(TowRequestResource),
                                            requestor,
                                            {'action': command, 'tow_request_id': 'TRASHGARBAGE'})
            self.assertEqual(res.status_code, 404)

    def test_invalid_command(self):
        requestor = self.lonely_user
        res = self.make_api_put_request(api.url_for(TowRequestResource),
                                        requestor,
                                        {'action': 'TRASHGARBAGE', 'tow_request_id': 'TRASHGARBAGE'})
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    print("Check the README for how to run this test.")
    pass
