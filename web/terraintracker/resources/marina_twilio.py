import logging

from flask import request
from flask_restful import Resource


# from . import constants
from terraintracker.resources.decorators import log_request
from terraintracker import config
from terraintracker.lib import phone_parser
from terraintracker.lib import name_parser
from terraintracker.lib.twilio import twilio_message_sender
from terraintracker.resources import twilio_response_templates
from terraintracker.models.user import User


logger = logging.getLogger(__name__)


class MarinaTwilio(Resource):

    decorators = [log_request, ]

    def get(self):
        logger.info(request.args)

        body = request.args.get('Body', '').upper().strip()
        phone = request.args.get('From', '')[2:]
        # logger.info("Phone Number recieved is [{}]".format(phone))
        this_user = User.get_most_recent_user_by_phone(phone)
        logging.debug("{} {} {}".format(body, phone, this_user))

        # Valid bodies:
        #   "adam, (352) 414-9721"
        #   "adam 123-456-7890"

        try:
            if ',' in body:
                command_args = [x.strip() for x in body.strip().split(',')]
            else:
                command_args = [x.strip() for x in body.strip().split(' ')]
            if len(command_args) != 2:
                raise ValueError("Invalid marina command_args {}".format(command_args))

            name = name_parser.parse_name(command_args[0])
            phone = phone_parser.parse_phone(command_args[1])
        except Exception as e:
            logging.exception(e)
            return twilio_response_templates.invalid_marina_flow()

        twilio_message_sender.send_twilio_message_with_raw_phone(
            ("Captain {} from Freedom Boat Club is on their way to help you out. "
             "If you require further assistance "
             "please call Freedom Boat Club at (855) 373-3366").format(this_user.name), phone)

        twilio_message_sender.send_twilio_message_with_raw_phone(
            "To see live updates of Captain {}'s progress, please click this link: {}. ".format(
                this_user.name, config.APPLICATION_ROOT + '/marina_user/live_map'), phone)

        return twilio_response_templates.marina_flow_started(name, phone)
