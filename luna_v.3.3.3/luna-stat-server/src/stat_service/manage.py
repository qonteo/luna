import sys
from argparse import ArgumentParser
from logging.config import dictConfig

from stat_service.modules import APPS
from stat_service.settings import ServiceSettings


parser = ArgumentParser('stat_service')
parser.add_argument(
    'module', help='run specified module (one of the [{}])'.format(', '.join(APPS))
)
parser.add_argument(
    '--port', action='store', type=int,
    help='run on the given port', required=True
)
parser.add_argument(
    '--run-demo', type=bool,
    help='Run demo page available at /demo resource. Warning: never use it in production.'
)


def main():
    """
    Initialize one of modules named in params
    :return:
    """
    args = parser.parse_args(sys.argv[1:])

    module = args.module
    assert module in APPS.keys()

    settings = ServiceSettings(
        object_sources=[(args, False)]
    )

    if settings.logging is not None:
        dictConfig(settings.logging)

    ss = APPS[module]
    ss.main(settings)


if __name__ == '__main__':
    main()
