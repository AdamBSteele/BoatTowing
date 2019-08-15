"""
Handles initialization of the app
"""
import logging
import os

from apns3 import APNs
from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy


# Init app & load config
app = Flask(__name__)
app.config.from_object('terraintracker.config')
logger = logging.getLogger('app')
logger.info("Starting app...")
logger.info("static_folder: {}".format(app.static_folder))
logger.info("static_url_path: {}".format(app.static_url_path))

logger.info("Initializing DB connection")
db = SQLAlchemy(app)  # pylint: disable=invalid-name
logger.info("DB connection initialized")

# Production APNS only works for apps on the app store
USE_PRODUCTION_APNS = str(os.getenv("USE_PRODUCTION_APNS")).lower() == 'true'
logger.info("Initializing Apple Push Notification Service connection. [Sanbox={}]".format(not USE_PRODUCTION_APNS))
apns = APNs(use_sandbox=not USE_PRODUCTION_APNS,
            cert_file='/usr/src/app/terraintracker/apns_certs/HarmeetCertificate.pem',
            key_file='/usr/src/app/terraintracker/apns_certs/HarmeetKey.pem',
            enhanced=True)  # pylint: disable=invalid-name
apns.gateway_server.register_response_listener(lambda x: logger.warning("APNS got error-response: " + str(x)))
logger.info("Apple Push Notification Service connection initialized")


@app.teardown_request
def show_teardown(exception):
    logger.debug('Request Finished | {} "{}" | User: "{}"'.format(request.method, request.path, g.get("user")))
    pass


# Make sure app closes db session
@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:
        logger.warning("Shut down with exception:\n{}".format(exception))
        db.session.expunge_all()  # noqa pylint: disable=no-member
    db.session.commit()
    db.session.remove()
