import logging
import traceback

from datetime import datetime
from functools import wraps
from flask import request, g


from terraintracker.models.user import User
from terraintracker.models.request_log import RequestLog
from terraintracker.app_init import db

logger = logging.getLogger(__name__)


def is_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'user'):
            return "You're not logged in at all"
        print(g.user, g.user.role, User.Role.admin.value, g.user.role != User.Role.admin.value)
        if g.user.role != User.Role.admin.value:
            return "You're not an admin"
        response = f(*args, **kwargs)
        return response
    return wrapper


def log_request(f):
    """
    Decorator to log requests including responses

    Should get applied after the `multi_auth.login_required` decorator to capture
    the request's user, but before any other decorators to capture responses
    that may result from a bad/unauthorized request.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger.debug("Not loggging request")
        response = f(*args, **kwargs)
        return response
        # return
        user_id = g.user.id if hasattr(g, 'user') and hasattr(g.user, 'id') else None
        request_log = RequestLog(request_url=request.url,
                                 request_method=request.method,
                                 request_query=str(request.query_string) if len(str(request.query_string)) > 4 else '',
                                 request_body=str(request.data)[:1990] if len(str(request.data)) > 4 else '',
                                 request_user=user_id,
                                 remote_ip=request.remote_addr,
                                 timestamp=datetime.utcnow())
        try:
            response = f(*args, **kwargs)
            return response
        except Exception:
            request_log.response_body = traceback.format_exc()
            db.session.add(request_log)
            db.session.commit()
            raise
        else:
            if isinstance(response, dict):
                request_log.response_body = response
            else:
                try:
                    response_len = len(response)
                except TypeError:
                    # In case of "TypeError: object of type 'Foo' has no len()"
                    response_len = 1
                try:
                    if response_len == 2:
                        # resource function returns (body, status)
                        request_log.response_body = str(response[0])[:1990]
                        request_log.response_code = response[1]
                    elif response_len == 1 and hasattr(response, 'status_code') and \
                            hasattr(response, 'data'):
                        # resource function returns jsonify'd Response object
                        request_log.response_body = str(response.data)[:1990]
                        request_log.response_code = response.status_code
                    elif response_len == 1 and isinstance(response, (str, bytes, dict)):
                        # resource function returns just raw string/dict
                        request_log.response_body = str(response)[:1990]
                        request_log.response_code = 200
                    else:
                        request_log.response_body = str(response)[:1990]
                    db.session.add(request_log)
                    db.session.commit()
                except Exception:
                    # Don't ruin a perfectly good request
                    logger.exception("Failed to write RequestAudit")
            return response

    return wrapper
