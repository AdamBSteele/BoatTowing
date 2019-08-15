import ast
import pprint

from sqlalchemy import DateTime

from terraintracker.app_init import db


class RequestLog(db.Model):
    __tablename__ = 'terraintracker_request_log'
    id = db.Column(db.Integer, primary_key=True)
    request_url = db.Column(db.String(length=2000))
    request_method = db.Column(db.String(length=200))
    request_query = db.Column(db.String(length=2000))
    request_body = db.Column(db.String(length=2000))
    request_user = db.Column(db.String(length=32))
    remote_ip = db.Column(db.String(length=200))
    timestamp = db.Column(DateTime)
    response_body = db.Column(db.String(length=2000))
    response_code = db.Column(db.Integer())

    def __repr__(self):
        res = '[{}] {} {} {} [User:{}] {} {}'.format(
            self.response_code,
            self.timestamp,
            self.request_method,
            self.request_url,
            self.request_user,
            "[Query:{}]".format(self.request_query) if len(str(self.request_query)) > 4 else '',
            self.request_body if len(str(self.request_body)) > 4 else '')
        return res

    @property
    def pretty_response_body(self):
        try:
            return pprint.pformat(ast.literal_eval(self.response_body))
        except Exception:
            return self.response_body

    @property
    def pretty_request_body(self):
        try:
            return pprint.pformat(ast.literal_eval(self.request_body))
        except Exception:
            return self.request_body
