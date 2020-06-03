import re
from logging import getLogger
from asyncio.locks import Lock
import ujson as json

import aioredis

redis_subscribe_lock = Lock()

log = getLogger('ss.stat_module.service.eds')


def get_attributes(attr, message):
    if message['source'] == 'descriptors':
        return [face['attributes'][attr] for face in message['result']['faces'] if 'attributes' in face]
    elif message['source'] == 'search' and 'attributes' in message['result']['face']:
        return [message['result']['face']['attributes'][attr]]
    else:
        return []


def between(elements, bounds):
    return any(bounds[0] <= elem <= bounds[1] for elem in elements)


def similarity_filter(filters, subscriber):
    min_similarity = filters.get('min_similarity', 0)

    async def _filter(client_id, event_type, timestamp, message):
        if event_type != 'match':
            return
        message['result']['candidates'] = [
            c for c in message['result']['candidates'] if c['similarity'] > min_similarity
        ]
        if len(message['result']['candidates']) == 0:
            return
        return await subscriber(client_id, event_type, timestamp, message)

    return _filter


def list_filter(filters, subscriber):
    list_id = filters.get('match_list', None)

    async def _filter(client_id, event_type, timestamp, message):
        if event_type != 'match':
            return
        if 'list_id' not in message['candidate']:
            return
        if message['candidate']['list_id'] != list_id:
            return
        return await subscriber(client_id, event_type, timestamp, message)

    return _filter


def event_type_filter(filters, subscriber):
    d_event_type = filters.get('event_type', None)

    async def _filter(client_id, event_type, timestamp, message):
        if event_type != d_event_type:
            return
        return await subscriber(client_id, event_type, timestamp, message)

    return _filter


def observe_filter(filters, subscriber):
    observe = filters.get('observe', None)
    if observe:
        observe = observe.split(',')

    async def _filter(client_id, event_type, timestamp, message):
        if 'authorization' not in message:
            return
        if isinstance(message['authorization'], str):
            if message['authorization'] not in observe:
                return
        elif isinstance(message['authorization'], dict):
            if message['authorization']['token_id'] not in observe:
                return
        else:
            raise ValueError('Wrong "authorization" format ' + str(type(message['authorization'])))
        return await subscriber(client_id, event_type, timestamp, message)

    return _filter


def gender_filter(filters, subscriber):
    gender = filters.get('gender', None)

    async def _filter(client_id, event_type, timestamp, message):
        genders = get_attributes('gender', message)

        if gender == 'male':
            if between(genders, (0.5, 1)):
                return await subscriber(client_id, event_type, timestamp, message)
        elif gender == 'female':
            if between(genders, (0, 0.5)):
                return await subscriber(client_id, event_type, timestamp, message)
        return

    return _filter


def age_filter(filters, subscriber):
    min_age = filters.get('min_age', 0)
    max_age = filters.get('max_age', 9999)

    async def _filter(client_id, event_type, timestamp, message):
        if between(get_attributes('age', message), (min_age, max_age)):
            return await subscriber(client_id, event_type, timestamp, message)
        return

    return _filter


def glasses_filter(filters, subscriber):
    min_glasses = filters.get('min_glasses', 0)
    max_glasses = filters.get('max_glasses', 1)

    async def _filter(client_id, event_type, timestamp, message):
        if between(get_attributes('eyeglasses', message), (min_glasses, max_glasses)):
            return await subscriber(client_id, event_type, timestamp, message)
        return

    return _filter


def wrap_in_filter_chain(filters, subscriber):
    """
    The function writes the subscriber callback in the filter chain, built on filters values

    :param filters:
    :param subscriber: subscriber or _filter(..._filter(subscriber)) ~ so as decorators chain
    :return: subscriber callback, which is wrapped in the filter chain
    """
    filter_map = {
        'min_similarity': lambda: similarity_filter(filters, subscriber),
        'match_list': lambda: list_filter(filters, subscriber),
        'event_type': lambda: event_type_filter(filters, subscriber),
        'observe': lambda: observe_filter(filters, subscriber),
        'gender': lambda: gender_filter(filters, subscriber),
        'min_age': lambda: age_filter(filters, subscriber),
        'max_age': lambda: age_filter(filters, subscriber),
        'min_glasses': lambda: glasses_filter(filters, subscriber),
        'max_glasses': lambda: glasses_filter(filters, subscriber),
    }

    for filter_name in filters:
        if filter_name not in filter_map:
            raise ValueError('Can\'t apply given filters: "{}"'.format(', '.join(filters.keys())))
        _filter = filter_map[filter_name]()
        filters.pop(filter_name)
        # small speedup
        if filter_name.find('min_') == 0:
            filters.pop('max_' + filter_name[4:], None)
        return wrap_in_filter_chain(filters, _filter)
    else:
        return subscriber


class AsyncSubscriptionContextManager(object):
    """
    Context manager for WebSocket subscription
    """

    def __init__(self, unsubscribe):
        self.unsubscribe = unsubscribe

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.unsubscribe()


class EventDeliveryService(object):
    """
    Subscribe on Redis events channel and deliver them to appropriate subscribers, also collects subscribers' statistics.
    """

    CHANNEL_NAME_PARSER = re.compile(
        r'event:([\w]+):([\d\w]{8}-[\d\w]{4}-[4][\d\w]{3}-[89AB][\d\w]{3}-[\d\w]{12}):([\d.]+)',
        re.IGNORECASE
    )

    def __init__(self, redis_sub, loop=None):
        self._total_subscription = 0
        self._max_subscription = 0

        self._redis_sub = redis_sub
        self._subscribers = {}

        self._notified_messages_count = 0
        self._redis_messages_count = 0

        self._receiver = aioredis.pubsub.Receiver(loop=loop)

        self._processed_messages = 0

    async def subscribe(self, account_id, subscriber, filters=None):
        """
        Subscribe on events for account_id by given filters

        :param account_id: user account id
        :param subscriber: `Subscriber` subclass
        :param filters: filters dictionary
        :return: subscription context manager
        """
        with (await redis_subscribe_lock):
            if len(self._subscribers) == 0:
                await self._wide_subscribe()

        if filters is not None or len(filters) == 0:
            subscriber = wrap_in_filter_chain(filters, subscriber.notify)
        else:
            subscriber = subscriber.notify

        if account_id not in self._subscribers:
            self._subscribers[account_id] = [subscriber]
        else:
            self._subscribers[account_id].append(subscriber)

        self._total_subscription += 1
        if self._total_subscription > self._max_subscription:
            self._max_subscription = self._total_subscription
        log.debug(f'{account_id} subscribed! Total subscribers count {self._total_subscription}.')

        async def unsubscribe():
            await self.unsubscribe(account_id, subscriber)

        return AsyncSubscriptionContextManager(unsubscribe)

    async def unsubscribe(self, account_id, subscriber):
        account_subscribers = self._subscribers.get(account_id)
        account_subscribers.remove(subscriber)
        if len(account_subscribers) == 0:
            self._subscribers.pop(account_id)

        self._total_subscription -= 1
        log.debug(f'{account_id} unsubscribed! Total subscribers count {self._total_subscription}.')

        with (await redis_subscribe_lock):
            if len(self._subscribers) == 0:
                await self._wide_unsubscribe()

    async def start(self):
        """
        This coroutine should be ran in the main event loop
        """
        while await self._receiver.wait_message():
            sender, (channel, message) = await self._receiver.get()
            self._redis_messages_count += 1
            await self._handle_message(channel, message)

    async def _handle_message(self, chanel, message):
        """
        Redis message handler
        :param chanel: chanel number
        :param message: message to share
        :return:
        """
        log.debug('Redis message {}'.format(message))

        event_type, client_id, timestamp = EventDeliveryService.CHANNEL_NAME_PARSER.search(
            chanel.decode()
        ).groups()
        message = json.loads(message.decode())

        handlers = self._subscribers.get(client_id, [])

        for h in handlers:
            await h(client_id, event_type, timestamp, message)
            self._notified_messages_count += 1

        self._processed_messages += 1

    async def _wide_subscribe(self):
        """
        Coroutine subscribes on Redis channel
        :return:
        """
        log.debug('Wide subscribe')
        await self._redis_sub.psubscribe(self._receiver.pattern(f'event:*'))

    async def _wide_unsubscribe(self):
        log.debug('Wide unsubscribe')

        await self._redis_sub.punsubscribe(f'event:*')

        log.info(
            f'Messages: \n'
            f'\tnotified: {self._notified_messages_count}, '
            f'\tredis: {self._redis_messages_count}, '
            f'\tmax subscriptions {self._max_subscription}'
        )
        self._notified_messages_count = 0
        self._redis_messages_count = 0
        self._max_subscription = 0
