import logging

from flask import request
from flask_restful import Resource

from . import constants
# from terraintracker.resources.decorators import log_request
from terraintracker.resources import twilio_response_templates
from terraintracker.models.user import User, TowRequestNotFoundError
from terraintracker.models.tow_request import NoRequesteesFound, TowRequestAlreadyAcceptedError, TowRequestCancelledError


logger = logging.getLogger(__name__)


class TwillioDispatcher(Resource):

    # decorators = [log_request, ]

    def get(self):
        logger.info(request.args)

        twilio_command = request.args.get('Body', '').upper().strip()
        phone = request.args.get('From', '')[2:]
        logger.warning("Phone Number recieved is [{}]".format(phone))
        this_user = User.get_most_recent_user_by_phone(phone)

        # ==== Argument Validation ==== #
        # Validate phone number
        if len(phone) != 10:
            logger.error("Invalid phone number {}".format(phone))
            return twilio_response_templates.invalid_phone(phone)

        # Validate a user exists for this phone number
        if this_user is None:
            logger.exception("User not found for phone {}".format(phone))
            return twilio_response_templates.user_not_found(phone)

        # Validate body
        if twilio_command not in constants.TWILIO_VALID_ARGS:
            logger.warning("Received invalid twilio command: [{}]".format(twilio_command))
            return twilio_response_templates.invalid_args()

        logger.info("valid Twilio request from [{}]. User: [{}]. Body: [{}]".format(phone, this_user.id, twilio_command))

        # ==== Actual Logic ==== #
        # TOW command
        if twilio_command.upper() in constants.TWILIO_HELP_ARGS:
            try:
                tow_request_batch = this_user.request_tow()
            except NoRequesteesFound:
                return twilio_response_templates.no_requestees_found(phone)
            except Exception as e:
                logger.exception(e)
                return twilio_response_templates.error500(e)

            logger.info("User {} at ({},{}) requests a tow to {} users".format(
                this_user.id, this_user.last_lat_seen, this_user.last_long_seen, tow_request_batch.num_requests)
            )
            return twilio_response_templates.successful_trb_creation(tow_request_batch)

        # YES command
        elif twilio_command.upper() == "YES":
            try:
                requestor, _, tow_request_batch, tow_event = this_user.accept_tow_request(this_user.requestee_tow_request_id)
            except TowRequestNotFoundError:
                logger.info("User {} accepted, but doesn't have any outstanding tows".format(this_user.id))
                return twilio_response_templates.no_outstanding_requests()
            except TowRequestAlreadyAcceptedError:
                logger.info("Tow {} was already accepted".format(this_user.requestee_tow_request_id))
                return twilio_response_templates.already_accepted()
            except TowRequestCancelledError:
                logger.info("Tow {} was already cancelled".format(this_user.requestee_tow_request_id))
                return twilio_response_templates.already_cancelled()
            except Exception as e:
                logger.exception(e)
                return twilio_response_templates.error500(e)

            logger.info("User {} at ({},{}) accepted user {}'s ({},{}) tow request.".format(
                this_user.id, this_user.last_lat_seen, this_user.last_long_seen,
                requestor.id, requestor.last_lat_seen, requestor.last_long_seen
            ))
            return twilio_response_templates.successful_accept_tr(requestor, tow_event)

        # NO command
        elif twilio_command.upper() == "NO":
            try:
                this_user.reject_tow(this_user.requestee_tow_request_id)
            except TowRequestNotFoundError:
                logger.info("User {} rejected, but doesn't have any outstanding tows".format(this_user.id))
                return twilio_response_templates.no_outstanding_requests()

            return twilio_response_templates.successful_reject_tr()

        logger.error("This should never happen!\n{}\n{}\n{}".format(
            twilio_command, phone, this_user.id()
        ))
        return twilio_response_templates.slipped_through_the_cracks(twilio_command)
