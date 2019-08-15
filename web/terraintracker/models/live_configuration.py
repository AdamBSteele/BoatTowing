"""
This is a 'live' configuration object that's stored in the DB.
It'll allow us to change configuration of the application without having to redeploy.
e.g. If we want to set tow radius from 10mi to 3000mi, we can just change that val here in the DB
and it'll get updated without us having to redeploy.

When a line of code requests a config value from the live config object,
the live config object will do:
      if stale:
        self.refresh()
      return <requested config value>


To add new values to this config:
 - Add _value and associated property (see _application_url and _tow_radius in here for example)
 - Add name to to LIVE_PROPERTIES as well
 - Create a new migration file in web/migrations/versions using: $ python manage.py db migrate
   - Make sure the new revision is adding the correct columns (use 8d18ae4e6b58_.py as an example)
 - Run the new migration file using: $ python manage.py db upgrade
 - Patch your new value in live_config in tests/custom_test_case.py
"""
import logging
import postgresql
import pprint
import time

from datetime import datetime

from sqlalchemy import DateTime, String, desc

from terraintracker.app_init import db

logger = logging.getLogger(__name__)


class LiveConfiguration(db.Model):
    """ Live configuration object. Refreshes from DB every CONFIG_UPDATE_INTERVAL seconds """
    __tablename__ = 'live_configuration'

    # How many seconds until we call the config stale?
    CONFIG_UPDATE_INTERVAL = 60

    # When was this config last grabbed from DB?
    last_loaded = time.time()

    modification_time = db.Column(DateTime(), primary_key=True)
    modification_user = db.Column(String(length=32))

    def __init__(self, very_first_config_ever=False):
        super(db.Model, self).__init__()
        self.modification_time = datetime.now()

        # If it's the very first config ever, like in scripts/initial_live_config
        #   then we're gonna avoid looking at the database.
        if not very_first_config_ever:
            self.reload_database()

    def __repr__(self):
        return 'Config\nLast loaded: {}\n{}'.format(self.last_loaded, pprint.pformat(self.__dict__))

    def reload_database(self):
        logger.debug("Grabbing new configuration from DB")
        new_config = LiveConfiguration.get_latest_db_entry()
        if new_config is None:
            logger.warning("No config found!")
            return

        # If the new config is the same as the current one, bail
        if new_config.modification_time == self.modification_time:
            logger.debug("Modification time [{}] hasn't changed. Ignoring found config".format(self.modification_time))
            return

        # Looks like we've got a new config.  Update as needed
        changed = False
        for property_name in self.LIVE_PROPERTIES:
            curr_val = getattr(self, property_name)
            new_val = getattr(new_config, property_name)
            if curr_val != new_val:
                changed = True
                logger.debug('Config updated {} [{}->{}]'.format(property_name, curr_val, new_val))
                setattr(self, property_name, new_val)
        if changed is False:
            logger.debug("All attributes looked the same to me. Why'd you have a new config in the first place?")

        self.last_loaded = time.time()

    def reload_if_stale(self):
        is_stale = time.time() - self.last_loaded > self.CONFIG_UPDATE_INTERVAL
        if is_stale:
            logger.debug("Config is stale")
            self.reload_database()

    @classmethod
    def get_latest_db_entry(cls):
        """ Return the most up-to-date config """
        try:
            res = LiveConfiguration.query.order_by(desc(LiveConfiguration.modification_time)).limit(1).first()
            return res
        except (postgresql.exceptions.UndefinedTableError, postgresql.exceptions.UndefinedColumnError):
            logger.warning("LiveConfiguration isn't defined in your DB. Hope you're running migrations now.")
            return None
        except Exception as e:
            logger.warning(e.args)
            # logger.exception(e)
            return None

    def to_dict(self):
        my_dict = dict([(k, getattr(self, k)) for k in self.LIVE_PROPERTIES])
        return my_dict

    # Update this every time you add a new value
    LIVE_PROPERTIES = [
        '_tow_radius'
    ]

    _tow_radius = db.Column('tow_radius', db.Integer())
    _application_url = db.Column('application_url', db.String()) # deprecated

    @property
    def tow_radius(self):
        self.reload_if_stale()
        return self._tow_radius

    @tow_radius.setter
    def tow_radius(self, tow_radius):
        self.modification_time = datetime.now()
        self._tow_radius = tow_radius


try:
    live_config = LiveConfiguration()
except Exception as e:
    logger.exception(e)
    live_config = None
