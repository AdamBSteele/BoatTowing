import logging
import stripe

from flask import g, jsonify, request
from flask_restful import Resource

from terraintracker.models.tow_event import TowEvent
from terraintracker.models.user import User
from terraintracker.resources.decorators import log_request
from terraintracker.resources.auth import multi_auth
from terraintracker.config import STRIPE_API_KEY, PRICE_OF_A_TOW

from terraintracker.lib.twilio import twilio_message_sender

logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_API_KEY


class StripeCustomerResource(Resource):

    decorators = [log_request, multi_auth.login_required]

    def post(self):
        # TODO: Add args?
        key = stripe.EphemeralKey.create(customer=g.user.stripe_customer_id, api_version="2017-05-25")
        logger.debug("Created Stripe key [{}] for user [{}] customer [{}]".format(key.id,
                                                                                  g.user,
                                                                                  g.user.stripe_customer_id))
        return jsonify(key)


class StripeChargeResource(Resource):

    decorators = [log_request, multi_auth.login_required]

    def post(self):
        """
        Charges a user for Tow Event

        .. :quickref: Stripe Payment;  Charges a user for a Tow Event

        **Example request**:

        .. sourcecode:: http

          POST /stripe_charge HTTP/1.1
          Host: example.com
          Content-Type: application/json
          Accept: application/json
          Authorization: Token <facebook_access_token>

        :resheader Content-Type: application/json
        :<json string tow_event_id: The tow_event_id of the Tow Event that the user is paying for
        :status 200: Charge completed successfully
        :status 400: Missing required arg tow_event_id
        :status 401: Payment failed because their card info was bad
        :status 404: Tow Event not found for given tow_event_id
        """
        logger.debug("StripeChargeResource")
        args = request.get_json()
        try:
            tow_event_id = args['tow_event_id']
        except KeyError:
            return {'status': 'Missing required arg tow_event_id'}, 400
        tow_event = TowEvent.query.get(tow_event_id)
        if tow_event is None:
            return {'status': "tow_event_not_found"}, 404
        logger.debug(args)
        try:
            result = stripe.Charge.create(amount=PRICE_OF_A_TOW,
                                          currency="usd",
                                          customer=g.user.stripe_customer_id,
                                          description="Drift boat tow. ID: {}".format(tow_event_id))
        except Exception as e:
            logger.exception(e)
            return {'status': 'Payment failed'}, 401
        logger.info(result)
        tow_event.apply_payment(PRICE_OF_A_TOW)
        # Notify requestee that we're ready to go
        requestor = User.query.get(tow_event.requestor_id)
        requestee = User.query.get(tow_event.requestee_id)
        twilio_message_sender.tell_requestee_that_requestor_has_paid(requestor, requestee)
        return jsonify(result)
