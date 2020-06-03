import ujson as json

import redis
import datetime
import time


def main(account_ids, frequency, messages_count):
    period = 1 / float(frequency)

    r = redis.client.StrictRedis(host='localhost')
    for i in range(messages_count // len(account_ids)):
        for accountId in account_ids:
            now = datetime.datetime.utcnow()
            before = time.time()
            r.publish(
                f'event:match:{accountId}:{now.timestamp()}', json.dumps({
                    "result": {
                        "faces": [{
                            "score": 0.9998425245,
                            "id": "e23f96bc-f38b-454b-b70a-3163f3e6ecf2",
                            "rectISO": {
                                "width": 196,
                                "height": 261,
                                "x": 27,
                                "y": 647
                            },
                            "rect": {
                                "width": 106,
                                "height": 133,
                                "x": 72,
                                "y": 713
                            }
                        }, {
                            "score": 0.9986633062,
                            "id": "4bf22f6a-ce62-4dc4-a99d-a58f3d9478ce",
                            "rectISO": {
                                "width": 408,
                                "height": 544,
                                "x": 220,
                                "y": 38
                            },
                            "rect": {
                                "width": 238,
                                "height": 277,
                                "x": 329,
                                "y": 188
                            }
                        }]
                    },
                    "account_id": accountId,
                    "event_type": "extract",
                    "source": "descriptors",
                    "auth_type": "basic",
                    "timestamp": now.timestamp()
                }

                )
            )
            elapsed = time.time() - before
            if elapsed > period:
                # print('rate {}'.format(1/elapsed))
                pass
            else:
                time.sleep(period - elapsed)


if __name__ == '__main__':
    client_ids = [
        line.rstrip() for line in open('cids.txt').readlines()
    ]
    main(client_ids, 1000, 10000)
