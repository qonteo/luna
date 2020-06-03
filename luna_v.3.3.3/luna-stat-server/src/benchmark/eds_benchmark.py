import asyncio
import datetime
import os
import pickle
import ujson as json
from itertools import chain
from multiprocessing import Pool

import websockets
from tornado import options
from tornado.options import define, options

from benchmark.utils import DelayedKeyboardInterrupt, sigterm_as_callback, load_report


def np_mean(iterable):
    """
    Count math mean
    :param iterable: numeric iter to count mean from
    :return:
    """
    n = summ = 0
    for elem in iterable:
        if type(elem) in [int, float]:
            summ += elem
            n += 1
        elif type(elem) in [list, set, tuple]:
            summ += sum(elem)
            n += len(elem)
        else:
            raise ValueError('Wrong type')
    if not n:
        return n
    return summ / n


def distance(l1: iter, l2: iter):
    l1, l2 = map(list, (l1, l2))
    assert len(l1) == len(l2), 'Cannot find distance in different vector dimensions'
    return (sum((l1[i] - l2[i]) ** 2 for i in range(len(l1)))) ** 1 / 2


def np_std(iter):
    """
    Count math standard deviation
    :param iter: numeric iter to count mean from
    :return:
    """
    l = list(iter)
    if not len(l):
        return 0
    mean = np_mean(l)
    if type(l[0]) is list:
        return (sum(sum((x - mean) ** 2 for x in e) for e in l) / len(l) / len(l[0])) ** (1 / 2) if mean else mean
    return (sum((x - mean) ** 2 for x in l) / len(l)) ** (1 / 2) if mean else mean


async def connect_ws(url, walk_through_times, times_arrival):
    """
    Coroutine to work with WebSockets
    :param url: url to connect
    :param walk_through_times: list object to print result transport time delta
    :param times_arrival: list object to print result timestamp
    :return:
    """
    while True:
        try:
            async with websockets.connect(url) as ws:
                while ws.open:
                    msg = await ws.recv()
                    m = json.loads(msg)
                    ts = m.get('timestamp')
                    if ts:
                        now = datetime.datetime.utcnow()
                        times_arrival += [now.timestamp()]
                        walk_through_times.append(
                            (
                                now - datetime.datetime.fromtimestamp(float(ts))
                            ).total_seconds()
                        )
            print('Connection was closed')
        except Exception:
            from traceback import print_exc
            print_exc()


def process(args):
    """
    Function to work inside subprocess worker
    :param args: object to make pool.map comfortable
    :return:
    """
    connections_batch, report_filename, port = args

    print(f'Worker filename {report_filename}, connections count {len(connections_batch)}')

    walk_through_times = {}
    times_arrival = []

    wss = []
    for client_token, client_url in connections_batch:
        url = client_url.format(port=port)

        ta = []
        if client_token not in walk_through_times:
            walk_through_times[client_token] = []
            times_arrival += [ta]

        fut = asyncio.ensure_future(connect_ws(
            url, walk_through_times[client_token], ta
        ))
        wss += [fut]

    print(f'Sock connected: {len(wss)}')

    def close_connections():
        """
        Kill WbeSocket clients from outside
        :return:
        """
        print('close_connections')
        asyncio.get_event_loop().close()

        with DelayedKeyboardInterrupt():
            with open(report_filename, 'wb') as f:
                pickle.dump(
                    {
                        'wk': walk_through_times,
                        'ta': times_arrival
                    },
                    f, pickle.HIGHEST_PROTOCOL
                )
                print(f'Worker report save finished to {report_filename}')

        os.system('kill %d' % os.getpid())

    try:
        with sigterm_as_callback(close_connections):
            asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        close_connections()


def _get_report_filenames(cpus):
    """
    Names from subprocess count
    :param cpus: count of subprocesses
    :return:
    """
    return [
        'report_per_cpu_{}'.format(cpu) for cpu in range(cpus)
    ]


def bench(
        client_tokens, remote, start_port, cpus,
        desired_connections_per_client=None, range_ports=False, query_filter=None
):
    """
    Main function to start benchmark test
    :param client_tokens: list of client tokens
    :param remote: url to connect at
    :param start_port: first port to connect at (the only if range_ports is False)
    :param cpus: number of subprocesses to raise
    :param desired_connections_per_client:
    :param range_ports: for several workers
    :param query_filter: custom filter query filter for subscription
    :return:
    """
    remote_base = 'ws://{}:{port}/api/subscribe?auth_token={id}'.format(
        remote, port='{port}', id='{id}'
    )
    if query_filter is not None:
        remote_base += f'{query_filter}'

    client_urls = [
        remote_base.format(id=client_token, port='{port}') for client_token in client_tokens
    ]

    total_connections = len(client_tokens) * desired_connections_per_client

    total_connections = total_connections - total_connections % cpus

    client_params = list(zip(client_tokens, client_urls))

    batch = list(chain.from_iterable([param] * desired_connections_per_client for param in client_params))

    count_in_batch = int(total_connections / cpus)
    connection_batches = []
    for i in range(cpus):
        connection_batches.append(
            batch[i * count_in_batch:(i + 1) * count_in_batch]
        )
    if range_ports:
        ports = [
            str(start_port + i) for i in range(cpus)
        ]
    else:
        ports = [start_port] * cpus

    report_filenames = _get_report_filenames(cpus)

    print('Start measuring ...')
    pool = Pool(cpus)

    try:
        pool.map(
            process,
            (
                (
                    batch, report_filename, port
                )
                for batch, port, report_filename in zip(
                    connection_batches, ports, report_filenames
                )
            )
        )
    except KeyboardInterrupt:
        # from traceback import print_last
        # print_last()

        pool.terminate()
        pool.join()

        with DelayedKeyboardInterrupt():
            print('Recover report due to keyboard Interrupt')

            def load_report(filename):
                with open(filename, 'rb') as f:
                    return pickle.load(f)

            measures = [
                load_report(report) for report in report_filenames
            ]

            compute(measures)


def accumulate_only(iterable, func):
    """
    Yield func call for every pair in iterable
    :param iterable:
    :param func:
    :return:
    """
    iterator = iter(iterable)

    try:
        prev_val = next(iterator)
        while True:
            next_val = next(iterator)
            yield func(prev_val, next_val)
            prev_val = next_val
    except StopIteration:
        pass


def compute(measures):
    print('Measures completed, calculating ...')

    # merge measures
    measures_merged = measures[0]['wk']
    times_arrival = measures[0]['ta']
    for m in measures[1:]:
        for i, v in m['wk'].items():
            if i not in measures_merged:
                measures_merged[i] = v
            else:
                measures_merged[i].extend(v)
        for v in m['ta']:
            times_arrival += [v]

    mps_per_connection = []
    for conn in times_arrival:
        accumulated = list(accumulate_only(conn, lambda c, n: n - c))
        mean = np_mean(
            accumulated
        )
        if mean is None:
            print(accumulated)
            continue
        mps_per_connection += [mean]

    mps_general_avg = np_mean(
        mps_per_connection
    )
    mps_general_std = np_std(
        mps_per_connection
    )

    general_avg = np_mean(measures_merged.values())
    general_std = np_std(measures_merged.values())
    avg_per_client = {
        client_token: np_mean(measures)
        for client_token, measures in measures_merged.items()
    }
    std_per_client = {
        client_token: np_std(measures)
        for client_token, measures in measures_merged.items()
    }

    print(
        f'Average among all clients: {general_avg:.3f} msec, std: {general_std:.3f}, '
        f'total event count: {sum(len(m) for m in measures_merged.values())}\n'
        f'Average SPM: {mps_general_avg:.4f}, std: {mps_general_std}\n'
        f'Average MPS: {1/mps_general_avg:.4f}, std: {mps_general_std/mps_general_avg**2}'
    )
    print(
        'Stat per client:\n{}'.format(
            ''.join(
                '\t#{}: avg walk through {:.3f} msec, std {:.3f} msec, event counts: {:.3f}\n'
                ''.format(
                    client_token, average, std, len(measures_merged[client_token])
                )
                for client_token, average, std in zip(
                    avg_per_client.keys(), avg_per_client.values(), std_per_client.values()
                )
            )
        )
    )


define('load_cids', type=str, help='load client ids from file (each client id on new line)')
define('cids', type=str, multiple=True, help='client ids array')
define('remote', 'localhost', type=str)
define('sp', 5008, type=int, help='start port')
define('cfr', type=bool, help='compute from report files (need actual workers parameter)')
define('workers', type=int, default=4)
define('cpc', type=int, help='connections per client', default=100)
define('rp', type=bool, default=False)
define('filter', type=str, default=None)


def main():
    options.parse_command_line()

    if options.cfr:
        measures = [
            load_report(f) for f in _get_report_filenames(options.workers)
        ]
        compute(measures)
    else:
        if len(options.cids) > 0:
            client_ids = options.cids
        elif options.load_cids is None:
            with open('cids.txt', 'r') as f:
                client_ids = [id.strip() for id in f.readlines()]
        elif len(options.load_cids) > 0:
            with open(options.load_cids, 'r') as f:
                client_ids = [id.strip() for id in f.readlines()]
        else:
            exit('Either load_cids or cids must be defined')
            return
        bench(client_ids, options.remote, options.sp, options.workers, options.cpc, options.rp, options.filter)


if __name__ == '__main__':
    main()
