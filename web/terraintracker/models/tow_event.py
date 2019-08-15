"""
Holds details about a single tow event (accepted TowRequest)
"""
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum


from sqlalchemy import Column, DateTime, String, Integer

from terraintracker.app_init import db
from terraintracker.constants import TOW_EVENT_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)


class TowEventStatus(Enum):
    """ All the possible statuses of TowEvent"""
    waiting_for_payment = 0
    in_progress = 1
    completed = 2
    cancelled = 3
    timed_out = 4


class TowEventAlreadyOverError(Exception):
    pass


class TowEventCompleteError(Exception):
    pass


class TowEvent(db.Model):
    """ Holds details about a specific TowEvent"""
    __tablename__ = 'tow_event'
    id = Column(String(length=32), primary_key=True)

    # Time the tow event confirmed by the requestor
    accepted_time = Column(DateTime)
    completed_time = Column(DateTime)
    cancelled_time = Column(DateTime)

    # [Deprecated] Time the tow event was sent to the requestor be confirmed
    time_sent = Column(DateTime)

    requestor_id = Column(String(length=32))
    requestee_id = Column(String(length=32))

    tow_request_batch_id = Column(String(length=32))

    amount_paid = Column(Integer)

    # Requstor:TowEvent == 1:1. relationship(arg1: child model, arg2: 1:1, arg3: field in child model)
    # requestor = relationship("User", foreign_keys=[requestor_id], back_populates="active_tow_event_receiving",uselist=False)
    # requestee = relationship("User", foreign_keys=[requestee_id], back_populates="active_tow_event_serving",uselist=False)

    _status = Column(Integer, name="status", default=TowEventStatus.waiting_for_payment.value)

    @property
    def status(self):
        # Check timeout if status is in progress or waiting for confirmation
        if (self._status == TowEventStatus.in_progress.value) or \
           (self._status == TowEventStatus.waiting_for_payment.value):
            if self.time_sent + timedelta(minutes=TOW_EVENT_TIMEOUT_MINUTES) < datetime.now():
                self.time_out()
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def status_string(self):
        return TowEventStatus(self.status).name

    def cancel(self):
        if self.status == TowEventStatus.in_progress.value or self.status == TowEventStatus.waiting_for_payment.value:
            self._status = TowEventStatus.cancelled.value
            self.cancelled_time = datetime.now()
            logger.debug("Cancelled tow_event [{}]".format(self))
        else:
            raise TowEventAlreadyOverError("You can't cancel a tow that is: ".format(self.status))

    def complete(self):
        if self.status == TowEventStatus.in_progress.value:
            self._status = TowEventStatus.completed.value
            self.completed_time = datetime.now()
        else:
            raise TowEventAlreadyOverError("You can't complete a tow that is: ".format(self.status))

    def time_out(self):
        self._status = TowEventStatus.timed_out.value

    def apply_payment(self, amount_paid):
        self.amount_paid = amount_paid
        self._status = TowEventStatus.in_progress.value

    def __init__(self, args=None):
        super(db.Model, self).__init__()
        self.id = uuid.uuid4().hex
        self.time_sent = datetime.now()

        if args is not None:
            for key in args:
                setattr(self, key, args[key])

    def __repr__(self):
        return self.id
