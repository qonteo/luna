import pickle
import signal
import logging
from contextlib import contextmanager

from itertools import islice, count


class DelayedKeyboardInterrupt(object):
    def __init__(self):
        self.signal_received = None

    def __enter__(self):
        # self.signal_received = False
        # self.old_handler = signal.getsignal(signal.SIGINT)
        # signal.signal(signal.SIGINT, self.handler)
        self.sinit = signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.sterm = signal.signal(signal.SIGTERM, signal.SIG_IGN)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        logging.debug('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        # signal.signal(signal.SIGINT, self.old_handler)
        # if self.signal_received:
        #     self.old_handler(*self.signal_received)
        signal.signal(signal.SIGINT, self.sinit)
        signal.signal(signal.SIGTERM, self.sterm)


@contextmanager
def sigterm_as_callback(callback):
    def handler(*args):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        callback()
        raise SystemExit()

    signal.signal(signal.SIGTERM, handler)
    yield None
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def avg(sequence):
    i = count()
    s = sum(map(lambda d: d[0], zip(sequence, i)))
    c = next(i) - 1

    if c <= 0:
        return 0
    else:
        return float(s) / c


def grouper(n, iterable):
    if n == 1:
        return iter(iterable)

    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, n))
        if not chunk:
            return
        yield chunk


def load_report(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
