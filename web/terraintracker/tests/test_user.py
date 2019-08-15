"""
"""
from random import randint
import logging
import unittest

from datetime import datetime
from unittest import mock

from terraintracker.models.user import User
from terraintracker.models.tow_request import TowRequestBatch
from terraintracker.tests.custom_test_case import CustomTestCase
from terraintracker.tests.data.user_test_data import (ALL_USERS,
                                                      ELIGIBLE_USERS,
                                                      EXPECTED_REQUESTEE_IDS_BY_REQUESTOR,
                                                      create_test_user)

logger = logging.getLogger(__name__)


class UserTest(CustomTestCase):
    def setUp(self):
        self.ELIGIBLE_USERS = [create_test_user(u) for u in ELIGIBLE_USERS]

    def test_get_possible_requestees(self):
        """
        Tests that each user's tow request is sent to the appropriate other ppl.
        """
        for u in self.ELIGIBLE_USERS:
            # Have to fetch user from db first or PostGIS will freak out
            logger.debug("Trying {}".format(u.id))
            requestor = User.query.get(u.id)

            # Get the possible requestees
            requestees = requestor.get_possible_requestees()

            # Create a set of ids for easy comparison
            actual_requestee_ids = set([r.id for r in requestees])

            # Grab expected ids set from dict
            expected_requestee_ids = EXPECTED_REQUESTEE_IDS_BY_REQUESTOR[requestor.id]

            self.assertEqual(expected_requestee_ids, actual_requestee_ids,
                             "Requestor {} grabbed incorrect basket of users\nExpected:{}\nActual:  {}".format(
                                 requestor.id, expected_requestee_ids, actual_requestee_ids))

    # Mock db.session, not all of db (since User object depends on db.Model)
    @mock.patch('terraintracker.models.user.db.session')
    def test_update_position(self, mock_db_sesh):
        # Mock db so we don't actually create location objects
        mock_db_sesh.add.return_value = None
        mock_db_sesh.commit.return_value = None

        u = self.ELIGIBLE_USERS[0]
        TEST_LAT, TEST_LON = 0.0, 0.0
        new_loc = u.update_position(TEST_LAT, TEST_LON)
        self.assertEqual(new_loc.lat, TEST_LAT)
        self.assertEqual(new_loc.lon, TEST_LON)

        self.assertTrue(type(u.last_time_seen), type(datetime.now()))
        self.assertEqual(u.last_lat_seen, str(TEST_LAT))
        self.assertEqual(u.last_long_seen, str(TEST_LON))
        self.assertEqual(u.last_geo_point_seen, 'POINT({} {})'.format(TEST_LAT, TEST_LON))

    @mock.patch('terraintracker.models.user.TowRequestBatch')
    @mock.patch('terraintracker.models.user.db.session')
    def test_request_tow(self, mock_db_sesh, mock_tow_request_batch):
        # Mock out TowRequestBatch since we're not testing that
        class FakeTowRequestBatch(TowRequestBatch):
            def fire(self):
                pass
        mock_tow_request_batch = FakeTowRequestBatch  # NOQA

        # Mock DB so we don't save anything extra
        mock_db_sesh.add.return_value = None
        mock_db_sesh.commit.return_value = None

        # Request a tow on a random user. Assert a tow request batch was created.
        u = self.ELIGIBLE_USERS[randint(0, len(self.ELIGIBLE_USERS) - 1)]
        trb = u.request_tow()
        self.assertIsNotNone(trb)
        self.assertTrue(trb.fire.called, True)  # NOQA


if __name__ == '__main__':
    unittest.main()
