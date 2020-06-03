import re

from urllib.parse import urlparse
import aioredis


DB_PATH_REGEXPR = re.compile('/([\w]+)')


async def create_aioredis(redis_url, loop=None):
    """
    Init async redis client
    :param redis_url: url to redis
    :param loop: loop to start client in
    :return:
    """
    parsed = urlparse(redis_url)
    assert parsed.scheme == 'redis'

    db_match = DB_PATH_REGEXPR.match(parsed.path)
    if not db_match:
        db = None
    else:
        db, = db_match.groups()
        db = int(db)

    return await aioredis.create_redis((parsed.hostname, parsed.port), db=db, loop=loop)
