import logging
import stripe

from terraintracker.config import STRIPE_API_KEY

logger = logging.getLogger(__name__)


# class StripeDriftHelper():
def initialize_stripe_customer(description):
    logger.debug("Adding stripe info")
    stripe.api_key = STRIPE_API_KEY
    stripe_customer_object = stripe.Customer.create(
        description=description
    )
    return stripe_customer_object.id

    # def charge_for_a_tow(token):
    #     logger.info("Charging for a tow!")
    #     stripe.api_key = STRIPE_API_KEY
    #     charge = stripe.Charge.create(
    #         amount=100,  # TODO: Change this from $1.00 to $100.00
    #         currency='usd',
    #         description='Example charge',
    #         source=token,
    #         statement_descriptor='Custom descriptor',
    #     )
    #     logger.info(charge.outcome)
    #     if charge.outcome.type != 'authorized':
    #         logger.warning(charge)

    #     return charge.outcome.type
