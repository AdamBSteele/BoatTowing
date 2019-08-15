"""
Keeps track of where users have been
"""
from sqlalchemy import Column, DateTime, String

from terraintracker.app_init import db


class LocationHistory(db.Model):
    """ Keeps track of where users have been """
    id = db.Column(db.Integer, primary_key=True)
    location_id = Column(String(length=64))
    user_id = Column(String(length=32))
    timestamp = Column(DateTime)
