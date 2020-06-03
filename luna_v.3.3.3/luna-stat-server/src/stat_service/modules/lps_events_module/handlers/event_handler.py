import ujson as json
from datetime import datetime
from logging import getLogger
import redis.exceptions

from common.api_tools import ClassHandler, NotValidJson, InfluxError, RedisError
from common.flattenizer import FlattenizerModel, NestedList
from stat_service.settings.defaults import TAGS_TO_ROUND


log = getLogger('ss.lps_module.handlers')


class EventsHandler(ClassHandler):
    def __init__(self):
        self.redis_client = None
        self.influx_client = None

    def initialize(self, redis_client, influx_client, **kwargs):
        self.redis_client = redis_client
        self.influx_client = influx_client

    async def post(self, request):
        """
        .. http:post:: /internal/lps_event/

            The LPS events processor, broadcasts event messages among ED services and makes InfluxDB records for future processing and providing it for end-point users via StatService.

            .. sourcecode:: http

                POST /internal/lps_event HTTP/1.1
                Accept: application/json

                {
                   "timestamp":"1490281006.88603",
                   "account_id":"e182bf55-5384-4f7a-a2c6-8e6fda993a1f",
                   "event_type":"match",
                   "auth_type":"basic",
                   "result": {
                       "canditates": [
                          {
                            "id": "141d2706-8baf-433b-82eb-8c7fada847da",
                            "descriptor_id": "151d2706-8baf-433b-82eb-8c7fada847da",
                            "similarity": 0.5
                          },
                          {
                            "id": "c51f1644-a6d9-419b-ba50-322a8ca4d413",
                            "descriptor_id": "151d2706-8baf-433b-82eb-8c7fada847da",
                            "similarity": 0.5
                          }
                        ],
                   },
                   "template": {
                     "person_id": "e182bf55-5384-4f7a-a2c6-8e6fda993a1f",
                     "descriptor_id": "e182bf55-5384-4f7a-a2c6-8e6fda993a1f"
                   },
                   "candidate": {
                     "list_id": "b0e35ae7-6b9c-4d59-80d8-919cba64d7da",
                     "list_data": "some info",
                     "list_type": 0
                   }
                }

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

            :statuscode 201: Event processed
            :statuscode 400: Empty or invalid request body
            :statuscode 500: Unexpected internal error
        """
        try:
            request_body = request.body.decode()
            payload = json.loads(request_body)
        except (ValueError, AttributeError):
            raise NotValidJson(json=request.body or '')

        log.debug('New event body: {}'.format(request_body))

        if len(request_body) == 0 or len(payload) == 0:
            return request.Response(code=400)

        request_timestamp = payload.get('timestamp') or request.headers.get('Timestamp')
        if request_timestamp is None:
            request_timestamp = datetime.utcnow().timestamp()
            if 'timestamp' not in payload:
                payload['timestamp'] = request_timestamp
        timestamp = datetime.fromtimestamp(request_timestamp).isoformat()

        event_type = payload.get('event_type')
        if event_type not in EVENT_TYPE_TO_FLATTENIZER:
            raise NotValidJson(json='- wrong "event_type"')
        measurement, flattenizer = EVENT_TYPE_TO_FLATTENIZER[event_type]

        message = flattenizer(payload)
        if message.error_code is not None:
            account_id = message.account_id
            error_code = message.error_code
            try:
                await self._write_points(
                    'error_series',
                    timestamp,
                    {
                        'error_code': error_code,
                        'account_id': account_id
                    },
                    {
                        'error_code': error_code
                    }
                )
            except OSError:
                raise InfluxError(description='No connection to influx')
        else:
            client_id = message.account_id

            key = f'event:{event_type}:{client_id}:{request_timestamp}'
            try:
                self.redis_client.publish(
                    key, json.dumps(payload)
                )
            except redis.exceptions.ConnectionError:
                raise RedisError(description='No connection to redis')

            tags = message.extract(exclude=['faces'])
            values = ValuesModel(tags).extract()
            try:
                if event_type == 'match':
                    await self._write_points(
                        measurement, timestamp, tags, values
                    )
                elif event_type == 'extract':
                    await self._write_points(
                        measurement, timestamp,
                        points=((
                            dict(**f, **tags), ValuesModel(f).extract())
                            for f in (
                                f.extract() for f in message.faces
                            )
                        ))
            except OSError:
                raise InfluxError(description='No connection to influx')

        return request.Response(code=201)

    @staticmethod
    def round_tags(tags):
        return {
            tag: tags[tag] if type(tags[tag]) is not float else
            round(tags[tag], TAGS_TO_ROUND[tag])
            for tag in tags
            if tag not in TAGS_TO_ROUND or TAGS_TO_ROUND[tag] is not None
        }

    async def _write_points(self, measurement, timestamp, tags=None, fields=None, points=None):
        if points is not None:
            points = [
                {
                    'measurement': measurement,
                    'tags': self.round_tags(tag),
                    'timestamp': timestamp,
                    'fields': field
                }
                for tag, field in points
            ]
        else:
            points = [
                {
                    'measurement': measurement,
                    'tags': self.round_tags(tags),
                    'timestamp': timestamp,
                    'fields': fields
                }
            ]

        log.debug(f'Write points: {points}')

        await self.influx_client.write_points(points)


def maxf(*args, **kwargs):
    """
    Float function to agregate maximum similarity from the LPS event
    :param args:
    :param kwargs:
    :return:
    """
    return float(max(*args, **kwargs))


def make_auth(auth):
    """
    Function to parse response with either basic auth or token
    :param auth:
    :return:
    """
    if isinstance(auth, dict):
        return auth['token_id']
    return auth


class BaseLunaMessageModel(FlattenizerModel):
    """
    All events' models parser
    """
    event_type = 'event_type'
    account_id = 'account_id'
    authorization = (make_auth, 'authorization')
    source = 'source'
    error_code = 'result.error_code'
    list = 'candidate.list_id'


class MatchLunaMessageModel(BaseLunaMessageModel):
    """
    Matcher events' model parser
    """
    similarity = (maxf, 'result.candidates.*.similarity')
    face_score = (float, 'result.face.score')
    age = (float, 'result.face.attributes.age')
    gender = (float, 'result.face.attributes.gender')
    skin_color = (float, 'result.face.attributes.naturalSkinColor')
    over_exposed = (float, 'result.face.attributes.overExposed')
    glasses = (float, 'result.face.attributes.eyeglasses')


class FaceModel(FlattenizerModel):
    """
    Face model parser (used in extractor and search)
    """
    face_score = (float, 'score', 1.0)
    age = (float, 'attributes.age')
    gender = (float, 'attributes.gender')
    skin_color = (float, 'attributes.naturalSkinColor')
    over_exposed = (float, 'attributes.overExposed')
    glasses = (float, 'attributes.eyeglasses')


class ExtractLunaMessageModel(BaseLunaMessageModel):
    """
    Extractor events' model parser
    """
    faces = (NestedList(FaceModel), 'result.faces')


class ValuesModel(FlattenizerModel):
    """
    Estimate attributes' model parser
    """
    age = 'age'
    gender = 'gender'
    face_score = 'face_score'
    over_exposed = 'over_exposed'
    similarity = 'similarity'
    skin_color = 'skin_color'
    glasses = 'glasses'


EVENT_TYPE_TO_FLATTENIZER = {
    'match': ('match_series', MatchLunaMessageModel),
    'extract': ('extract_series', ExtractLunaMessageModel)
}
