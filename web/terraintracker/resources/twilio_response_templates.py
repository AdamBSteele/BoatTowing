from flask import Response
from twilio import twiml

from . import constants


def invalid_phone(phone):
    resp = twiml.Response()
    resp.message("Received invalid phone number: {}".format(phone))
    return Response(str(resp), content_type='text/xml')


def invalid_args():
    resp = twiml.Response()
    resp.message('{}{}'.format(constants.TWILIO_INVALID_COMMAND_MSG, constants.TWILIO_VALID_ARGS))
    return Response(str(resp), content_type='text/xml')


def error500(e):
    resp = twiml.Response()
    resp.message(str(e))
    return Response(str(resp), content_type='text/xml')


def user_not_found(phone):
    resp = twiml.Response()
    resp.message('{} [{}]'.format(constants.TWILIO_PHONE_NOT_FOUND_MSG, phone))
    return Response(str(resp), content_type='text/xml')


def successful_trb_creation(tow_request_batch):
    strmessage = """
    Great News! {} requests have been made. Sit tight and we will let you know when somone responds.
    Your tow request ID is: {}
    """.format(tow_request_batch.num_requests, tow_request_batch.id)
    resp = twiml.Response()
    resp.message(strmessage)
    return Response(str(resp), content_type='text/xml')


def no_requestees_found(phone):
    resp = twiml.Response()
    resp.message("Sit tight we are dispatching help for you. A drifter will call you within 5 minutes at {}".format(
        phone))
    return Response(str(resp), content_type='text/xml')


def no_outstanding_requests():
    resp = twiml.Response()
    resp.message("There are no requests outstanding for you to accept")
    return Response(str(resp), content_type='text/xml')


def already_accepted():
    resp = twiml.Response()
    resp.message("Sorry, they've already accepted another offer. Better luck next time")
    return Response(str(resp), content_type='text/xml')


def already_rejected():
    resp = twiml.Response()
    resp.message("You've already rejected this request.")
    return Response(str(resp), content_type='text/xml')


def successful_accept_tr(requestor, tow_event):
    msg = ("Cool. Please get ready to tow. We will message you once the user has confirmed payment. "
           "Event ID: {} "
           "http://maps.google.com/?saddr=My+Location&daddr={},{}").format(tow_event.id,
                                                                           requestor.last_lat_seen,
                                                                           requestor.last_long_seen)
    resp = twiml.Response()
    resp.message(msg)
    return Response(str(resp), content_type='text/xml')


def already_cancelled():
    resp = twiml.Response()
    resp.message("Thanks for responding!  The Drifter has cancelled this request. Have a Nice Day.")
    return Response(str(resp), content_type='text/xml')


def successful_reject_tr():
    resp = twiml.Response()
    resp.message("No Problem, maybe next time. Have a nice day")
    return Response(str(resp), content_type='text/xml')


def slipped_through_the_cracks(twilio_command):
    resp = twiml.Response()
    resp.message("This should've never happened. Twilio Command: [{}]".format(twilio_command))
    return Response(str(resp), content_type='text/xml')


def marina_assist_missing_phone_number():
    resp = twiml.Response()
    resp.message("What is the member's 10-digit phone number?")
    return Response(str(resp), content_type='text/xml')


def you_should_call_the_marina():
    resp = twiml.Response()
    resp.message("Please call the marina for more help.")
    return Response(str(resp), content_type='text/xml')


def invalid_marina_flow():
    resp = twiml.Response()
    resp.message('Please send a message in the form: "name, phone". Example: adam, 1234567890')
    return Response(str(resp), content_type='text/xml')


def marina_flow_started(name, phone):
    resp = twiml.Response()
    resp.message('Sending live map to {} at phone number: {}'.format(name, phone))
    return Response(str(resp), content_type='text/xml')
