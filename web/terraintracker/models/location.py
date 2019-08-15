"""
Holds details about a specific location
"""
from datetime import datetime

from terraintracker.app_init import db
from terraintracker.lib.google_maps import get_color_and_isWater
from geoalchemy2 import Geometry
import uuid


class Location(db.Model):
    """ Holds details about a specific location"""
    id = db.Column(db.String(length=64), primary_key=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    is_water = db.Column(db.Boolean)
    color_google = db.Column(db.String(length=36))
    last_seen = db.Column(db.Date)
    geom = db.Column(Geometry('POLYGON'))

    def __init__(self, lat, lon):
        #self.id = '{},{}'.format(lat, lon)
        self.id = str(uuid.uuid1())
        self.lat = lat
        self.lon = lon
        self.last_seen = datetime.now()
        self.is_water = None

    def __repr__(self):
        return '<Location {}, {}>'.format(self.lat, self.lon)

    def isWater(self):
        if self.is_water is None:
            self._getIsWaterFromGoogle()
        return self.is_water

    def _getIsWaterFromGoogle(self):
        color_google, is_water = get_color_and_isWater(self.lat, self.lon)
        self.color_google = str(color_google)
        self.is_water = is_water

    def getNearbyUsers(self):
        pass
