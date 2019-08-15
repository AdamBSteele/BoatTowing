"""
Holds details about a single TowRequest (if accepted, spawns TowEvent)
"""
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime, String, ForeignKey, Integer

from terraintracker.app_init import db
from terraintracker.constants import TOW_REQUEST_BATCH_TIMEOUT_MINUTES
from terraintracker.models.tow_event import TowEvent
from terraintracker.lib.ios_push_notifications import one_signal_notification_sender
from terraintracker.lib.twilio import twilio_message_sender


logger = logging.getLogger(__name__)


class NoRequesteesFound(Exception):
    pass


class TowRequestAlreadyAcceptedError(Exception):
    pass


class TowRequestTimedOutError(Exception):
    pass


class TowRequestCancelledError(Exception):
    pass


class TowServiceTypes(Enum):
    tow = 0
    tow_grounded = 1
    fuel = 2
    battery = 3
    entanglement = 4

    @property
    def string_format_for_text_message(self):
        human_readable = {'tow': 'a tow (ungrounded)',
                          'tow_grounded': 'a tow (grounded)',
                          'fuel': 'a fuel refill',
                          'battery': 'a battery jump',
                          'entanglement': 'their entanglement straightened out'}
        return human_readable[self.name]


class TowRequestBatch(db.Model):
    __tablename__ = 'tow_request_batch'
    """ Holds details about a TowRequest"""
    id = Column(String(length=32), primary_key=True)
    requestor_id = Column(String(length=32))
    requestor_name = Column(String(length=81))

    time_sent = Column(DateTime)

    # 1:M relationship w/ TowRequest
    tow_requests = relationship("TowRequest", back_populates="tow_request_batch")

    num_requests = Column(Integer, default=0)
    num_rejections = Column(Integer, default=0)
    last_update = Column(DateTime)

    _service_requested = Column(Integer, default=TowServiceTypes.tow.value)

    @property
    def service_requested(self):
        return TowServiceTypes(self._service_requested)

    @service_requested.setter
    def service_requested(self, service):
        if type(service) == int:
            self.service_requested = service
        elif type(service) == str:
            self._service_requested = TowServiceTypes[service].value
        elif type(service) == TowServiceTypes:
            self._service_requested = service.value
        else:
            logger.warning("invalid service_requested setter: {}".format(service))

    class Status(Enum):
        """ All the possible statuses of TowRequest"""
        active = 0
        accepted = 1
        all_rejected = 2
        timed_out = 3
        cancelled = 4

    _status = Column(Integer, default=Status.active.value)

    @property
    def status(self):
        # Check timeout if status is in progress or waiting for confirmation
        self.update_status()
        return self._status

    @property
    def status_string(self):
        return TowRequestBatch.Status(self._status).name

    def update_status(self):
        # Timeout if needed
        if self._status == TowRequestBatch.Status.active.value:
            logger.debug("active")
            if self.time_sent + timedelta(minutes=TOW_REQUEST_BATCH_TIMEOUT_MINUTES) < datetime.now():
                logger.debug("timed out")
                self._status = TowRequestBatch.Status.timed_out.value
        self.last_update = datetime.now()

    def get_responses(self):
        # Get responses from all TowRequests
        return None

    def __init__(self, requestor, service_requested=None):
        super(db.Model, self).__init__()
        self.id = uuid.uuid4().hex
        self.time_sent = datetime.now()
        self.last_update = datetime.now()
        self.requestor_id = requestor.id
        self.requestor_name = requestor.name
        if service_requested:
            self.service_requested = service_requested
        self._status = TowRequestBatch.Status.active.value
        logger.debug("Created TowRequestBatch {}, [{}->{}]".format(self.id, self.requestor_id, self.requestor_name))

    def fire(self, requestor):
        requestees = requestor.get_possible_requestees()

        self.num_requests = len(requestees)

        # Make requests
        for requestee in requestees:
            try:
                tr = TowRequest(self, requestee, requestor, self.service_requested)
                logger.info("New TowRequest[{}]: [{}]->[{}]".format(tr.id, requestor, requestee))
                tr.fire(requestor, requestee)
                db.session.add(tr)
                requestee.requestee_tow_request_id = tr.id
                db.session.merge(requestee)
            except Exception as e:
                logger.exception(e)

        db.session.commit()

        if len(requestees) == 0:
            logger.info("No requests found for requestor: [{}]".format(requestor.id))
            try:
                one_signal_notification_sender.sendNoDriftTowersInYourArea(requestor.one_signal_player_id)
            except Exception:
                logger.warning("Tried to send one_signal 'no requestees found' but user didn't have onesignal")
            raise NoRequesteesFound

        logger.info("New TowRequestBatch {}. {} requestees".format(self.id, self.num_requests))

    def handle_rejection(self, requestor):
        # Add rejections to tow_request_batch and set status
        self.update_status()
        if self._status == TowRequestBatch.Status.timed_out.value:
            logger.info("TowRequestBatch [{}] is too old to be accepted".format(self.id))
            raise TowRequestTimedOutError

        self.num_rejections = self.num_rejections + 1
        if self.num_rejections == self.num_requests:
            self._status = TowRequestBatch.Status.all_rejected.value
            logger.info("TowRequestBatch [{}] has been rejected by all {} users".format(self.id, self.num_requests))
            one_signal_notification_sender.sendNoOneIsComingBecauseYouGotRejected(requestor.one_signal_player_id)
        else:
            logger.info("Rejected TowRequestBatch")
        self.last_update = datetime.now()
        db.session.commit()
        logger.info("TowBatch {} is at {}/{} rejections".format(self.id, self.num_rejections, self.num_requests))

    def handle_acceptance(self, requestor, requestee):
        self.update_status()

        if self._status == TowRequestBatch.Status.cancelled.value:
            logger.info("TowRequestBatch [{}] was already cancelled".format(self.id))
            raise TowRequestCancelledError

        if self._status == TowRequestBatch.Status.accepted.value:
            logger.info("TowRequestBatch [{}] was already accepted".format(self.id))
            raise TowRequestAlreadyAcceptedError

        if self._status == TowRequestBatch.Status.timed_out.value:
            logger.info("TowRequestBatch [{}] is too old to be accepted".format(self.id))
            raise TowRequestTimedOutError

        self._status = TowRequestBatch.Status.accepted.value
        self.last_update = datetime.now()
        db.session.commit()
        logger.info("TowRequestBatch [{}] has been accepted".format(self.id))

        te = TowEvent({'requestor_id': requestor.id,
                       'requestee_id': requestee.id,
                       'tow_request_batch_id': self.id})
        one_signal_notification_sender.sentTowRequestAccepted(requestor,
                                                              requestee, te.id)
        db.session.add(te)
        db.session.commit()
        return te

    def cancel(self):
        self._status = TowRequestBatch.Status.cancelled.value
        db.session.commit()


class TowRequest(db.Model):
    __tablename__ = 'tow_request'
    """ Holds details about a TowRequest"""
    id = Column(String(length=32), primary_key=True)

    # What batch was this a part of:  (TowRequestBatch:TowRequests 1:M)
    tow_request_batch_id = Column(String(length=32), ForeignKey('tow_request_batch.id'))
    tow_request_batch = relationship("TowRequestBatch", back_populates="tow_requests")

    # Other stuff
    requestor_location = Column(String(length=32))
    requestor_id = Column(String(length=32))
    requestor_name = Column(String(length=81))
    requestee_id = Column(String(length=32))
    requestee_name = Column(String(length=81))
    requestee_location = Column(String(length=32))
    time_sent = Column(DateTime)
    rejection_time = Column(DateTime)
    cancelled_time = Column(DateTime)
    tow_event_id = Column(String(length=32))

    class Status(Enum):
        """ All the possible statuses of TowRequest"""
        active = 0
        accepted = 1
        rejected = 2
        timed_out = 3
        confirmed = 4
        cancelled = 5

    status = Column(Integer, default=Status.active.value)

    @property
    def status_string(self):
        return TowRequest.Status(self.status).name

    _service_requested = Column(Integer, default=TowServiceTypes.tow.value)

    @property
    def service_requested(self):
        return TowServiceTypes(self._service_requested)

    @service_requested.setter
    def service_requested(self, service):
        if type(service) == int:
            self.service_requested = service
        elif type(service) == str:
            self._service_requested = TowServiceTypes[service].value
        elif type(service) == TowServiceTypes:
            self._service_requested = service.value
        else:
            logger.warning("invalid service_requested setter: {}".format(service))

    def __init__(self, tow_request_batch, requestee, requestor, service_requested):
        super(db.Model, self).__init__()
        self.id = uuid.uuid4().hex
        self.time_sent = datetime.now()
        self.tow_request_batch_id = tow_request_batch.id
        self.requestor_id = requestor.id
        self.requestor_name = requestor.name
        self.requestee_id = requestee.id
        self.requestee_name = requestee.name
        self.requestor_location = requestor.readable_location
        self.requestee_location = requestee.readable_location
        self.status = TowRequest.Status.active.value
        self.service_requested = service_requested

    def __repr__(self):
        return "<{} from {}>".format(self.id[:4], self.requestor_id)

    def fire(self, requestor, requestee):
        """
        Send a Tow Request to the requestee
        """
        logger.debug("Firing")
        if requestee.is_android:
            twilio_message_sender.request_tow(self, requestor, requestee)
        else:
            one_signal_notification_sender.sendTowRequest(requestee, requestor, self.id)

    def get_batch(self):
        """ Return the tow request batch """
        return TowRequestBatch.query.get(self.tow_request_batch)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_tow_requests_in_batch(cls, batch_id):
        return cls.query.filter_by(tow_request_batch_id=batch_id)

    def reject(self):
        self.status = TowRequest.Status.rejected.value
        self.rejection_time = datetime.now()

    def accept(self):
        self.status = TowRequest.Status.accepted.value

    def cancel(self):
        self.status = TowRequest.Status.cancelled.value
