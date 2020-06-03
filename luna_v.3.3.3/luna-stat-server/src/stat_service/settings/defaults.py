import os
import tornado.options
from tornado.options import define, options

define('INFLUX_LOGIN', help='Login of influxdb')
define('INFLUX_PASSWORD', help='Password of influxdb')
define('INFLUX_DATABASE', help='Database of influxdb')
define('INFLUX_URL', help='Url to influxdb in format "<IP_address>:<port (default 8086)>"')

define('REDIS_LOGIN', help='Login of REDIS')
define('REDIS_PASSWORD', help='Password of REDIS')
define('REDIS_DATABASE', help='Database of REDIS')
define('REDIS_URL', help='Url to REDIS in format "<IP_address>:<port (default 6379)>"')

define('LPS_URL', help='Url to LPS in format "<IP_address>:<port (default 5000)>"')
define('LPS_API_VERSION', type=int, help='LPS api version as integer')

define('IGNORE_AGE_TAG', type=int, help='Do not make tag age in Influx if true')
define('IGNORE_FACE_SCORE_TAG', type=int, help='Do not make tag face_score in Influx if true')
define('IGNORE_GENDER_TAG', type=int, help='Do not make tag gender in Influx if true')
define('IGNORE_GLASSES_TAG', type=int, help='Do not make tag glasses in Influx if true')
define('IGNORE_SIMILARITY_TAG', type=int, help='Do not make tag similarity in Influx if true')

define('COOKIE_SECRET', help='Some secret cookie')

tornado.options.parse_config_file('config.conf')

# host
HOST = '0.0.0.0'

INFLUX_LOGIN = options.INFLUX_LOGIN
INFLUX_PASSWORD = options.INFLUX_PASSWORD
INFLUX_DATABASE = options.INFLUX_DATABASE
INFLUX_URL = options.INFLUX_URL
INFLUX_CONNECTION_URL = 'influxdb://' + options.INFLUX_LOGIN + ':' + options.INFLUX_PASSWORD + '@' + options.INFLUX_URL + '/' + options.INFLUX_DATABASE

REDIS_CONNECTION_URL = 'redis://' + options.REDIS_LOGIN + ':' + options.REDIS_PASSWORD + '@' + options.REDIS_URL + '/' + options.REDIS_DATABASE

# LPS account handler link
LPS_URL = 'http://' + options.LPS_URL + '/' + str(options.LPS_API_VERSION)

# secret phrase to sign cookies with HMAC, refer to
# https://en.wikipedia.org/wiki/Hash-based_message_authentication_code
COOKIE_SECRET = options.COOKIE_SECRET

# dictionary "numeric tag" - "digits after dot" (supports negative ones)
# comment out numeric tags here if they are not needed in influx
TAGS_TO_ROUND = dict(
    age=0 if not options.IGNORE_AGE_TAG else None,
    face_score=2 if not options.IGNORE_FACE_SCORE_TAG else None,
    gender=2 if not options.IGNORE_GENDER_TAG else None,
    glasses=2 if not options.IGNORE_GLASSES_TAG else None,
    similarity=3 if not options.IGNORE_SIMILARITY_TAG else None,
)

# see here https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)s[%(levelname)s]: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'ss': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    },
}

# HTTP timeout
HTTP_TIMEOUT = 20

# Run demo page
RUN_DEMO = False
