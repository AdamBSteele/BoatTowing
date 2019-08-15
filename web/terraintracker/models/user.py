"""
User model
"""
import logging
import uuid

from datetime import datetime
from enum import Enum
from geoalchemy2 import func, Geography
from haversine import haversine
from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash

from terraintracker.app_init import db
from terraintracker.models.live_configuration import live_config
from terraintracker.models.location import Location
from terraintracker.models.location_history import LocationHistory
from terraintracker.models.tow_event import TowEventStatus
from terraintracker.models.tow_request import TowRequestBatch, TowRequest
from terraintracker.lib.calculate_latlon_bearing import get_bearing_between_coords
from terraintracker.lib.stripe_integration import initialize_stripe_customer
from terraintracker.lib.twilio import twilio_message_sender


logger = logging.getLogger(__name__)


class TowRequestNotFoundError(Exception):
    pass


class TowRequestAlreadyAcceptedError(Exception):
    pass


class TowEventNotFoundError(Exception):
    pass


class User(db.Model):
    """ User model """
    __tablename__ = 'terraintracker_user'

    id = Column(String(length=32), primary_key=True)
    active = Column(Boolean, default=True)

    class Role(Enum):
        admin = 0
        user = 1
        tower = 2
        mweb_user = 3
    role = Column(Integer, default=Role.user.value)

    @property
    def is_admin(self):
        return self.role == User.Role.admin.value

    time_created = Column(DateTime)

    @property
    def role_string(self):
        return User.Role(self.role).name

    phone = Column(String(length=10), unique=True)  # Strip non-digits, no 1 in front

    @property
    def pretty_phone(self):
        return '({}) {}-{}'.format(self.phone[:3], self.phone[3
            :6], self.phone[6:])


    _phone_string = Column(String(length=20))  # Less strict phone field for non-twilio users

    @property
    def phone_number(self):
        return self._phone_string

    @phone_number.setter
    def phone_number(self, phone_number):
        try:
            self._phone_string = phone_number
            db.session.commit()
        except Exception as e:
            logger.error(e)
            print("Error setting phone")
            self._phone_string = ''

    email = Column(String(length=255))
    first_name = Column(String(length=40))
    last_name = Column(String(length=40))

    @property
    def name(self):
        try:
            return ' '.join([self.first_name, self.last_name])
        except Exception:
            return str(self.first_name)

    @name.setter
    def name(self, name):
        try:
            setattr(self, 'first_name', name.split()[0])
            setattr(self, 'last_name', name.split()[1])
        except Exception:
            setattr(self, 'first_name', str(name))

    # Geo stuff
    last_geo_point_seen = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    last_lat_seen = Column(String(length=255))
    last_long_seen = Column(String(length=255))

    @property
    def coords(self):
        return (float(self.last_lat_seen), float(self.last_long_seen))

    last_time_seen = Column(DateTime, default=datetime.now())

    @property
    def readable_location(self):
        try:
            return "({},{})".format(self.last_lat_seen[:9], self.last_long_seen[:9])
        except Exception:
            logger.warning("last_lat_lon_seen had unexpected value")
            return "({},{})".format(self.last_lat_seen, self.last_long_seen)

    over_water = Column(Boolean)
    requestee_tow_request_id = Column(String(length=255))

    # User:Boat == 1:1. relationship(arg1: child model, arg2: 1:1, arg3: field (*relationship?) in child model)
    boat = relationship("Boat", uselist=False, back_populates="user")

    active_tow_event_serving_id = Column(String(length=32), ForeignKey('tow_event.id'))
    active_tow_event_receiving_id = Column(String(length=32), ForeignKey('tow_event.id'))

    active_tow_event_serving = relationship("TowEvent", foreign_keys=[active_tow_event_serving_id])
    active_tow_event_receiving = relationship("TowEvent", foreign_keys=[active_tow_event_receiving_id])

    active_tow_request_batch_id = Column(String(length=32), ForeignKey('tow_request_batch.id'))
    active_tow_request_batch = relationship("TowRequestBatch", foreign_keys=[active_tow_request_batch_id])

    # Token Auth
    stored_token = Column(String(length=256))

    # Apple Push Notification System token [DEPRECATED]
    apns_token = Column(String(length=255))

    # OneSingle ID, which is what we actually use for Push Notifications
    one_signal_player_id = Column(String(length=255))

    # stripe customer id
    stripe_customer_id = Column(String(length=32))

    # Android User

    is_android = Column(Boolean, default=False)
    # Unused stuff
    honorific = Column(String(length=10))
    gender = Column(String(length=1))
    address1 = Column(String(length=255))
    address2 = Column(String(length=255))
    city = Column(String(length=40))
    state = Column(String(length=2))
    zipcode = Column(String(length=10))
    country = Column(String(length=40))
    nationality = Column(String(length=255))
    notes = Column(String(length=255))
    middle_name = Column(String(length=40))
    birth_date = Column(String(length=10))  # YYYY-MM-DD
    uses_parent_account = Column(Boolean)
    parent_id = Column(String(length=32))
    id_card_number = Column(String(length=255))
    id_card_expiration_date = Column(String(length=10))  # YYYY-MM-DD
    _password = Column(String(length=255))
    company = Column(String(length=255))
    ip_address = Column(String(length=45))

    _is_test_user = Column(Boolean, default=False)

    @property
    def google_maps_string(self):
        return "https://www.google.com/maps/place/{},{}".format(self.last_lat_seen,
                                                                self.last_long_seen)

    @property
    def is_test_user(self):
        return self._is_test_user

    def __repr__(self):
        try:
            return "User<" + ','.join([self.name,
                                       self.id,
                                       self.readable_location,
                                       ]) + ">"
        except Exception:
            return "User<self.id>"

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, v):
        self._password = generate_password_hash(v)

    def __init__(self, _id=None, name=None, role=None, _is_test_user=False):
        """ init is expecting a dictionary of arguments """
        if not _is_test_user:
            logger.debug("Creating new user")
        super(db.Model, self).__init__()

        self.id = _id if _id else uuid.uuid4().hex
        self.name = name if name else self.id
        self._is_test_user = _is_test_user
        self.time_created = datetime.now()

        try:
            if not _is_test_user:
                self.stripe_customer_id = initialize_stripe_customer(str(self))
        except Exception as e:
            logger.warning("{} failed to initialize Stripe customer".format(self))
            logger.exception(e)

        db.session.merge(self)
        db.session.commit()
        logger.info("Created new user: {}".format(self))

    @staticmethod
    def get_requestees_in_geo(lat, lon):
        return User.query.filter(
            func.ST_DWithin(
                User.last_geo_point_seen,
                'POINT({} {})'.format(str(lat), str(lon)),
                live_config.tow_radius,
                False)
        ).filter_by(active=True).filter_by(role=User.Role.tower.value).all()

    def get_possible_requestees(self):
        # Need to add time_seen to this
        possible_requestees = User.query.filter(
            func.ST_DWithin(User.last_geo_point_seen, self.last_geo_point_seen, live_config.tow_radius, False)
        ).filter_by(active=True).filter_by(role=self.Role.tower.value).all()

        # Grab everybody but self
        requestees = [r for r in possible_requestees if r.id != self.id]

        logger.debug("Found {} requestees".format(len(requestees)))

        # TODO: Find a way to send alerts to admins for each tow request fired
        # User.send_admin_text("{} sending tow requests to: {}".format(self, requestees))
        return requestees

    def update_position(self, lat, lon):
        try:
            logger.debug("{}->[{:.9f},{:.9f}]".format(self.id, float(lat), float(lon)))
        except Exception:
            logger.warning("update_position got insane data: '{}' '{}'".format(lat, lon))

        loc = Location(float(lat), float(lon))
        db.session.merge(loc)

        lh = LocationHistory(user_id=self.id, location_id=loc.id)
        db.session.add(lh)

        self.last_time_seen = datetime.now()
        self.last_lat_seen = str(lat)
        self.last_long_seen = str(lon)
        self.last_geo_point_seen = 'POINT({} {})'.format(lat, lon)

        db.session.merge(self)
        db.session.commit()
        return loc

    def request_tow(self, service_requested=None):
        # Generate TowRequestBatch. Fire it.
        trb = TowRequestBatch(self, service_requested)
        db.session.add(trb)
        self.active_tow_request_batch = trb
        db.session.commit()
        trb.fire(self)
        return trb

    def accept_tow_request(self, tow_request_id):
        logger.debug("{} is accepting tow_request {}".format(self.id, tow_request_id))
        tow_request = TowRequest.query.get(tow_request_id)
        if tow_request is None:
            raise TowRequestNotFoundError
        tow_request_batch = TowRequestBatch.query.get(tow_request.tow_request_batch_id)
        requestor = User.query.get(tow_request_batch.requestor_id)

        # handle_acceptance creates new tow event
        tow_event = tow_request_batch.handle_acceptance(requestor, self)
        tow_request.status = TowRequest.Status.accepted.value

        # Manage foreign key stuff
        self.active_tow_event_serving = tow_event
        self.active_tow_event_receiving = None
        requestor.active_tow_event_receiving = tow_event
        requestor.active_tow_event_serving = None
        tow_request.tow_event_id = tow_event.id

        db.session.merge(self)
        db.session.merge(requestor)
        db.session.merge(tow_request)
        db.session.commit()

        logger.debug("{} is serving tow event {}".format(self, self.active_tow_event_serving_id))
        logger.debug("{} is receiving tow event {}".format(requestor, requestor.active_tow_event_receiving_id))

        return requestor, tow_request, tow_request_batch, tow_event

    def reject_tow(self, tow_request_id):
        logger.debug("{} is rejecting tow_request {}".format(self.id, tow_request_id))
        tow_request = TowRequest.query.get(tow_request_id)
        if tow_request is None:
            raise TowRequestNotFoundError
        tow_request.status = TowRequest.Status.rejected.value
        tow_request_batch = TowRequestBatch.query.get(tow_request.tow_request_batch_id)
        requestor = User.query.get(tow_request_batch.requestor_id)
        tow_request_batch.handle_rejection(requestor)
        self.requestee_tow_request_id = None
        db.session.merge(self)
        db.session.commit()

    def get_distance_and_bearing(self, tow_event):
        requestee = User.query.get(tow_event.requestee_id)
        requestor = User.query.get(tow_event.requestor_id)
        start = (float(requestee.last_lat_seen), float(requestee.last_long_seen))
        end = (float(requestor.last_lat_seen), float(requestor.last_long_seen))
        distance = haversine(start, end)
        bearing = str(get_bearing_between_coords(start, end))
        logger.debug("User [{}]\tBearing [{}]\tDistance [{}]\ttow requestor [{}]".format(self,
                                                                                         bearing,
                                                                                         distance,
                                                                                         requestor))
        return distance, bearing

    def get_most_recent_user_by_phone(phonenumber):
        requestee = User.query.filter_by(phone=phonenumber).first()
        return requestee

    def get_active_tow_event_receiving(self):
        try:
            if self.active_tow_event_receiving:
                if self.active_tow_event_receiving.status == TowEventStatus.in_progress.value:
                    return self.active_tow_event_receiving.id
        except Exception as e:
            logger.exception(e)
        return None

    def get_active_tow_event_serving(self):
        try:
            if self.active_tow_event_serving:
                if self.active_tow_event_serving.status == TowEventStatus.in_progress.value:
                    return self.active_tow_event_serving.id
        except Exception as e:
            logger.exception(e)
        return None

    def get_active_tow_request_batch(self):
        try:
            if self.active_tow_request_batch:
                if self.active_tow_request_batch.status == TowRequestBatch.Status.active.value:
                    return self.active_tow_request_batch.id
        except Exception as e:
            logger.exception(e)
        return None

    @staticmethod
    def admins():
        return User.query.filter_by(role=User.Role.admin.value).all()

    @staticmethod
    def towers():
        return User.query.filter_by(role=User.Role.tower.value).all()

    @staticmethod
    def send_admin_text(message):
        twilio_message_sender.send_one_message_to_multiple_recipients(User.admins(), message)


class Boat(db.Model):
    __tablename__ = 'terraintracker_boat'
    id = Column(String(length=32), primary_key=True)

    # Boat:User == 1:1
    user_id = Column(String(length=32), ForeignKey('terraintracker_user.id'))
    user = relationship("User", back_populates="boat")

    model = Column(String(length=32))
    make = Column(String(length=32))
    _type = Column(String(length=32))
    length = Column(String(length=32))
    engine_hp = Column(Integer)

    def __init__(self, user, make, _type, length):
        super(db.Model, self).__init__()
        self.id = uuid.uuid4().hex
        self.user = user
        self._type = _type
        self.make = make
        self.length = length
        logger.debug("Created Boat {}".format(self))
        db.session.merge(self)
        db.session.commit()

    def __repr__(self):
        return "{} {} (Length: {})".format(self.make, self._type, self.length)
