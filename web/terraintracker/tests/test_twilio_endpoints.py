# import unittest

# from unittest import mock

# from terraintracker.models.user import User
# from terraintracker.resources import constants
# from terraintracker.resources.tow_request_twillio import TwillioDispatcher
# from terraintracker.tests.custom_test_case import CustomTestCase


# class TwilioTest(CustomTestCase):

#     @mock.patch('terraintracker.resources.tow_request_twillio.User')
#     @mock.patch('terraintracker.resources.tow_request_twillio.request')
#     def test_bad_body(self, fake_request, fake_user):
#         # Set up mock vars
#         fake_request.args = {
#             'From': 'xx1234567890',
#             'Body': 'This is not a valid command'
#         }
#         fake_user.get_most_recent_user_by_phone.return_value = User()

#         response = TwillioDispatcher().get()
#         self.assertIn(constants.TWILIO_INVALID_COMMAND_MSG, str(response.response))
#         self.assertEqual(response.status_code, 200)

#     @mock.patch('terraintracker.resources.tow_request_twillio.User')
#     @mock.patch('terraintracker.resources.tow_request_twillio.request')
#     def test_phone_not_associated_with_any_user(self, fake_request, fake_user):
#         # Set up mock vars
#         fake_request.args = {
#             'From': 'xx1234567890',
#             'Body': 'toW'
#         }
#         fake_user.get_most_recent_user_by_phone.return_value = None

#         response = TwillioDispatcher().get()
#         self.assertIn(constants.TWILIO_PHONE_NOT_FOUND_MSG, str(response.response))

#     @mock.patch('terraintracker.resources.tow_request_twillio.User')
#     @mock.patch('terraintracker.resources.tow_request_twillio.request')
#     def test_no_requestees_found(self, fake_request, fake_user):
#         # FakeUser class gets no requestees
#         class FakeUser(User):
#             def get_possible_requestees(self):
#                 return []
#         fake_request.args = {
#             'From': 'xx1234567890',
#             'Body': 'TOW'
#         }
#         fake_user.get_most_recent_user_by_phone.return_value = FakeUser()

#         response = TwillioDispatcher().get()
#         self.assertIn('A drifter will call ', str(response.response))


# if __name__ == '__main__':
#     unittest.main()
