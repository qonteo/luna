import sys
import os
from argparse import ArgumentParser
from subprocess import Popen


def get_version():
    sys.path.insert(0, '.')
    import versioneer
    return versioneer.get_version()

parser = ArgumentParser()
parser.add_argument('output')
parser.add_argument('--raml2html', default='raml2html', help='Path to the raml2html executable')
parser.add_argument('--api-root', default=os.path.join('raml', 'StatServiceApi'))


def main():
    args = parser.parse_args(sys.argv[1:])

    with open(os.path.join(args.api_root, 'version.txt'), 'w') as f:
        f.write(get_version())

    with open(os.path.join(args.output), 'w') as f:
        sp = Popen(
            [args.raml2html, os.path.join(args.api_root, 'api.raml')],
            stdout=f, stderr=sys.stderr
        )
        sp.wait()


if __name__ == '__main__':
    main()
