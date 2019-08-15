"""
Reads .ini file and sets config vals from it and/or environment variables
Looks for .ini files in CONFIG_LOCATIONS, and selects first one it finds
"""
import configparser
from copy import copy
import datetime
import logging
import logging.config

import os

DEBUG = os.getenv("DEBUG", False)
PRESERVE_CONTEXT_ON_EXCEPTION = True


REPO_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

CONFIG_LOCATIONS = [
    '/etc/terraintracker.ini',
    'terraintracker.local.ini',
    '../terraintracker.local.ini',
    '../../terraintracker.local.ini',
    'terraintracker/terraintracker.local.ini',
    'terraintracker.default.ini',
    '../terraintracker.default.ini',
    'terraintracker/terraintracker.default.ini',
]

# Find config .ini...
_config = configparser.ConfigParser()
for location in CONFIG_LOCATIONS:
    if os.path.isfile(os.path.abspath(location)):
        config_path = location
        break
else:
    raise RuntimeError('Could not find config file at any of:\n - {}'.format('\n - '.join(CONFIG_LOCATIONS)))

# Read config .ini
config_path = os.path.abspath(config_path)
print("Pulling config from: " + config_path)
_config.read(config_path)
REQUIRED_CONFIG_SECTIONS = [ ]
# Make sure required sections are there
for required_conf_sect in REQUIRED_CONFIG_SECTIONS:
    if required_conf_sect not in _config.sections():
        raise RuntimeError('Missing required section [{}] in .ini file [{}]'.format(required_conf_sect, config_path))

# === SystemRuntime ===
FALLBACK_SECRET_KEY = "TrashGarbageDefaultSECRET_KEY*#*6184"
SECRET_KEY = _config.get('SystemRuntime', 'secret_key', fallback=os.getenv("FALLBACK_SECRET_KEY",
                                                                           "TrashGarbageDefaultSECRET_KEY*#*6184"))
if SECRET_KEY == FALLBACK_SECRET_KEY:
    print("Using default secret key. Consider setting the OS Env var $FALLBACK_SECRET_KEY")

PRICE_OF_A_TOW = _config.get('SystemRuntime', 'price_of_a_tow', fallback=20000)
APPLICATION_ROOT = _config.get('SystemRuntime', 'application_root', fallback=os.getenv('DRIFT_URL', None))
if not APPLICATION_ROOT:
    print("Missing required config value application_root! Add it in your .ini file!")


# === iOS Push Notifications ===
ONE_SIGNAL_API_KEY = _config.get('OneSignal', 'api_key', fallback=os.getenv('ONE_SIGNAL_API_KEY', ''))
ONE_SIGNAL_APP_ID = _config.get('OneSignal', 'app_id', fallback=os.getenv('ONE_SIGNAL_APP_ID', None))

# === Stripe ===
STRIPE_API_KEY = _config.get('Stripe', 'api_key', fallback=os.getenv('STRIPE_API_KEY',
                                                                     'sk_test_9OiCgAQZhAA0xyEWSW9efNIx'))
if STRIPE_API_KEY == 'sk_test_9OiCgAQZhAA0xyEWSW9efNIx':
    print("Using default stripe key")


# === Twilio ===
TWILIO_ACCOUNT_SID = _config.get('Twilio', 'account_sid', fallback=os.getenv('TWILIO_ACCOUNT_SID', None))
TWILIO_AUTH_TOKEN = _config.get('Twilio', 'auth_token', fallback=os.getenv('TWILIO_AUTH_TOKEN', None))
TWILIO_PHONE_NUMBER = _config.get('Twilio', 'phone_number', fallback=os.getenv('TWILIO_PHONE_NUMBER', '5619269231'))

# === GoogleMaps ===
GOOGLE_MAPS_KEY = _config.get('GoogleMaps', 'key', fallback=os.getenv('GOOGLE_MAPS_API_KEY', ''))


# === Database ===
# Postgresql
try:
    postgresql_host = _config.get('Database', 'postgresql_host', fallback='postgres')
    postgresql_user = _config.get('Database', 'postgresql_user', fallback='postgres')
    postgresql_pass = _config.get('Database', 'postgresql_pass', fallback=None)
    postgresql_pass_str = ':' + postgresql_pass if postgresql_pass else ''
    postgresql_port = _config.get('Database', 'postgresql_port', fallback=5432)
    postgresql_database_name = _config.get('Database', 'postgresql_dbname', fallback='postgres')
    SQLALCHEMY_DATABASE_URI = "postgresql+pypostgresql://{}{}@{}:{}/{}".format(postgresql_user,
                                                                               postgresql_pass_str,
                                                                               postgresql_host,
                                                                               postgresql_port,
                                                                               postgresql_database_name)
except configparser.NoOptionError:
    raise RuntimeError('{} is missing one of [host, user, pass] in [Postgresql] section'.format(config_path))

# I don't think we ever want to do this, and we get a warning in stderr if we don't explicity opt out:
SQLALCHEMY_TRACK_MODIFICATIONS = False

# === Logs ===
LOG_DIRECTORY = '/tmp'

# We aren't really using this right now since docker just expects stdout
defaultlog_level = _config.get('Logs', 'main_level', fallback='DEBUG')
postgresqllog_level = _config.get('Logs', 'postgressql_level', fallback='DEBUG')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s %(asctime)-15s %(module)s:%(funcName)s:%(lineno)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S %Z',
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': defaultlog_level,
            'stream': 'ext://sys.stdout',
        },
        'postgresql': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': postgresqllog_level,
            'stream': 'ext://sys.stdout',
        },
        'pil': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'WARNING',
            'stream': 'ext://sys.stdout',
        },
        'stripe': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO',
            'stream': 'ext://sys.stdout',
        },
        'filehandler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': '/tmp/terraintracker.log',
            'maxBytes': 102400,
            'backupCount': 3
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'filehandler'],
            'level': defaultlog_level,
            'propagate': True,
        },
        'requests': {
            'handlers': ['default', 'filehandler'],
            'level': _config.get('SystemRuntime', 'logLevelThirdParty', fallback='WARNING'),
            'propagate': False,
        },
        'postgresql': {
            'handlers': ['postgresql', 'filehandler'],
            'level': _config.get('SystemRuntime', 'logLevelThirdParty', fallback='WARNING'),
            'propagate': False,
        },
        'PIL.PngImagePlugin': {
            'handlers': ['pil', 'filehandler'],
            'level': _config.get('SystemRuntime', 'logLevelThirdParty', fallback='WARNING'),
            'propagate': False,
        },
        'stripe': {
            'handlers': ['stripe', 'filehandler'],
            'level': _config.get('SystemRuntime', 'logLevelThirdParty', fallback='INFO'),
            'propagate': False,
        }
    },
})


class ColoredFormatter(logging.Formatter):
    def __init__(self, pattern):
        logging.Formatter.__init__(self, pattern)

    def format(self, record):
        COLOR_MAPPING = {
            'DEBUG': 37,  # white
            'INFO': 36,  # cyan
            'WARNING': 33,  # yellow
            'ERROR': 31,  # red
            'CRITICAL': 41,  # white on red bg
        }

        LABEL_MAPPING = {
            'DEBUG': 'DEBUG',
            'INFO': 'INFO ',
            'WARNING': 'WARN ',
            'ERROR': ' ERR ',
            'CRITICAL': 'CRIT!'
        }

        PREFIX = '\033['
        SUFFIX = '\033[0m'
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = COLOR_MAPPING.get(levelname, 37)  # default white
        label = LABEL_MAPPING.get(levelname, "?lvl?")
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format(PREFIX, seq, label, SUFFIX)
        colored_record.levelname = colored_levelname
        return logging.Formatter.format(self, colored_record)


cf = ColoredFormatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d  %(message)s")
root = logging.getLogger('')
hdlr = root.handlers[0]
hdlr.setFormatter(cf)

logger = logging.getLogger(__name__)
print("<>==<> CONFIGURATION LOADED  {} {} <>==<>".format(datetime.datetime.utcnow().isoformat(), config_path))
