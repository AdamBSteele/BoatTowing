"""
Keep Twilio initialization in one central place so we don't have to keep re-initializing
"""
import logging
import re
import urllib

from flask import url_for
from twilio.rest import TwilioRestClient

from terraintracker.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, APPLICATION_ROOT

logger = logging.getLogger(__name__)


class TwilioMessageSender():

    twilio_client = None

    def __init__(self):
        try:
            self.twilio_client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            logger.info("Initialized Twilio")
        except Exception:
            logger.warning("Twilio failed to initialize with auth info SID:[{}] TOKEN:[{}]".format(
                TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))

    def send_twilio_message(self, body, to):
        if to.phone in ['', None]:
            logger.warning("Tried to send SMS to {} but they don't have a phone number".format(to))
            return ""
        dest_phone = "+1" + str(to.phone)
        logger.debug('Sending Twilio msg FROM [{}] TO [{}]'.format(TWILIO_PHONE_NUMBER, dest_phone))
        try:
            message = self.twilio_client.messages.create(body=body,
                                                         to=dest_phone,
                                                         from_=TWILIO_PHONE_NUMBER)
        except Exception as e:
            logger.exception(e)
            return
        return message

    def send_twilio_message_with_raw_phone(self, body, to_phone):
        dest_phone = "+1" + str(to_phone)
        logger.debug('Sending Twilio msg FROM [{}] TO [{}]'.format(TWILIO_PHONE_NUMBER, dest_phone))
        try:
            message = self.twilio_client.messages.create(body=body,
                                                         to=dest_phone,
                                                         from_=TWILIO_PHONE_NUMBER)
        except Exception as e:
            logger.exception(e)
            return
        return message

    def request_tow(self, tow_request, requestor, requestee):
        msgs = []

        msgs.append(
            self.send_twilio_message(
                body="DRIFT Tow Request: {} needs {}. Reply yes to help them.".format(
                    requestor.name,
                    tow_request.service_requested.string_format_for_text_message),
                to=requestee)
        )

        msgs.append(
            self.send_twilio_message(
                body="Boat information: {}".format(requestor.boat),
                to=requestee)
        )

        msgs.append(
            self.send_twilio_message(
                body="https://www.google.com/maps/place/{},{}".format(
                    str(requestor.last_lat_seen).strip(),
                    str(requestor.last_long_seen).strip()),
                to=requestee)
        )
        logger.info("TWILIO FIRED TOW REQUEST {} -> {} ({}). Message: {}".format(
            requestor.id, requestee.id, requestee.phone, msgs))

    def tell_requestee_that_requestor_has_paid(self, requestor, requestee):
        body = ("The stranded boater ({}) has confirmed payment. "
                "Please call them at {} and let them know you're on your way!".format(requestor.name,
                                                                                      requestor.phone_number))
        message = self.send_twilio_message(body=body, to=requestee)
        logger.info("Twilio fired tell_requestee_that_requestor_has_paid. Message: {}".format(message))

    def send_one_message_to_multiple_recipients(self, recipients, message):
        for recipient in recipients:
            try:
                self.send_twilio_message(body=message, to=recipient)
            except Exception:
                logger.warning("Error sending message to {}".format(recipient))
        return

    def send_mweb_drift_request_text(self, phone):
        sanitized_phone_number = re.sub('[^0-9]', '', phone)
        logger.info("Sending mweb form to: " + sanitized_phone_number)
        self.send_twilio_message_with_raw_phone(body="Thanks for contacting Drift."
                                                " Please click this link and fill out your information"
                                                " and we will call you back shortly.",
                                                to_phone=sanitized_phone_number)
        mweb_form_url = urllib.parse.urljoin(APPLICATION_ROOT, '/user_panel/md_tow_request?phone=' + sanitized_phone_number)
        logger.info(mweb_form_url)
        self.send_twilio_message_with_raw_phone(body="{}".format(mweb_form_url),
                                                to_phone=sanitized_phone_number)


twilio_message_sender = TwilioMessageSender()
