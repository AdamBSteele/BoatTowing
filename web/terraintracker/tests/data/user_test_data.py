"""
Dicts for each test user. A function to create them.
"""

import datetime
import logging

from terraintracker.models.user import User

logger = logging.getLogger(__name__)

TEST_USER_PASSWORD = 'Test1234'


def create_test_user(user_dict):
    u = User(_id=user_dict['id'], name=user_dict['phone'], _is_test_user=True)
    u.password = TEST_USER_PASSWORD
    u.role = User.Role.tower.value
    u.active = True
    for k in user_dict.keys():
        setattr(u, k, user_dict[k])
    u.update_position(user_dict['last_lat_seen'], user_dict['last_long_seen'])
    logger.debug("created test user: {}".format(User.query.get(u.id)))
    return u


# Eligible users is 5 users near each otherlike:
#      o
#  o   o   o
#      o
# Left and right are very far apart.

ELIGIBLE_USERS = [
    {
        'phone': '1111111111',
        'id': 'test_left',
        'last_long_seen': '-81.333583',
        'last_lat_seen': '31.252527',
    },
    {
        'phone': '222222222',
        'id': 'test_right',
        'last_long_seen': '-81.120793',
        'last_lat_seen': '31.242464',
    },
    {
        'phone': '3333333333',
        'id': 'test_top',
        'last_long_seen': '-81.206815',
        'last_lat_seen': '31.327326',
    },
    {
        'phone': '4444444444',
        'id': 'test_bottom',
        'last_long_seen': '-81.198940',
        'last_lat_seen': '31.202165',
    },
    {
        'phone': '5555555555',
        'id': 'test_middle',
        'last_long_seen': '-81.198062',
        'last_lat_seen': '31.254075',
    },
]

# For each requestor, which eligible users should they request?
EXPECTED_REQUESTEE_IDS_BY_REQUESTOR = {

    # Middle reaches everything but itself
    'test_middle': set([u['id'] for u in ELIGIBLE_USERS if u['id'] != 'test_middle']),

    # Left and right are very far apart, so they won't grab each other
    'test_left': set([u['id'] for u in ELIGIBLE_USERS if u['id'] not in ['test_left', 'test_right']]),
    'test_right': set([u['id'] for u in ELIGIBLE_USERS if u['id'] not in ['test_left', 'test_right']]),

    # Top and bottom are close to each other. Reach everything but themselves
    'test_top': set([u['id'] for u in ELIGIBLE_USERS if u['id'] != 'test_top']),
    'test_bottom': set([u['id'] for u in ELIGIBLE_USERS if u['id'] != 'test_bottom']),
    'test_not_active': set(),
}


LONELY_USER = {
    'phone': '7777777778',
    'id': 'test_far_away',
    'last_lat_seen': '-31.254075',
    'last_long_seen': ' 81.198062',
    'active': False}

INACTIVE_USER = {
    'phone': '7777777777',
    'id': 'test_not_active',
    'last_lat_seen': '31.254075',
    'last_long_seen': '-81.198062',
    'active': False}


INELIGIBLE_USERS = [LONELY_USER, INACTIVE_USER]


# === Data for test_get_most_recent_user_by_phone === #
#  The code below is deprecated:
PHONE_TEST_USER_NEWEST = {
    'id': 'phone_test_user_newest',
    'last_time_seen': datetime.datetime.now(),
    'phone': '8888888888'}

PHONE_TEST_USER_OLDEST = {
    'id': 'phone_test_user_oldest',
    'last_time_seen': datetime.datetime.now() - datetime.timedelta(days=1),
    'phone': '9999999999'}

PHONE_TEST_USER_NO_LAST_SEEN = {
    'id': 'phone_test_user_no_last_seen',
    'phone': '0000000000'}

USERS_SHARING_PHONE = [PHONE_TEST_USER_NEWEST, PHONE_TEST_USER_OLDEST, PHONE_TEST_USER_NO_LAST_SEEN]

ALL_USERS = ELIGIBLE_USERS + INELIGIBLE_USERS + USERS_SHARING_PHONE
