import os
import requests
import subprocess

from app.common_objects import logger
from configs import config
from common.elasticsearch.index import indexes
from analytics.classes import reporter


def assertOneDictInAnother(one, another, path=''):
    assert type(one) is type(another), path + ' types: {} {}'.format(type(one), type(another))
    if type(one) is dict:
        for key, value in one.items():
            if (key, value) == ('type', 'object'):
                continue
            assert key in another, path + '.' + key + ' not in `another`'
            assertOneDictInAnother(value, another[key], path + '.' + key)
    else:
        assert one == another, path + ' values: {} {}'.format(one, another)


def checkLunaAPI():
    """
    Check luna existence and auth.

    :raises: RuntimeError
    :return: None
    """
    try:
        reply = requests.get(
            '{}:{}/{}/login'.format(config.LUNA_API_HOST, config.LUNA_API_PORT, config.LUNA_API_API_VERSION),
            headers={"X-Auth-Token": config.LUNA_API_TOKEN}
        )
        if reply.status_code == 404:
            raise RuntimeError("Wrong LUNA_API_API_VERSION config")
        elif reply.status_code == 401:
            raise RuntimeError("Wrong LUNA_API_TOKEN config")
        elif reply.status_code != 200:
            raise RuntimeError("Luna API /login reply: {} {}".format(reply.status_code, reply.text))
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Wrong LUNA_API_HOST or LUNA_API_PORT config")
    except requests.exceptions.MissingSchema:
        raise RuntimeError("Wrong network schema in LUNA_API_HOST config")


def checkES():
    """
    Check Elasticsearch existence, auth and indexes.

    :raises: RuntimeError
    :return: None
    """
    try:
        for name, structure in indexes:
            reply = requests.get("{}{}".format(config.ELASTICSEARCH_URL, name))
            assertOneDictInAnother(structure, reply.json()[name[1:]], name[1:])
    except AssertionError as e:
        raise RuntimeError("Wrong index detected in path {}, run 'python make_index.py'".format(e.args[0]))
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Wrong ELASTICSEARCH_HOST or ELASTICSEARCH_PORT config")
    except requests.exceptions.MissingSchema:
        raise RuntimeError("Wrong network schema in ELASTICSEARCH_HOST config")


def checkLaTeX():
    """
    Check latex existence and generate test pdf.

    :raises: RuntimeError
    :return: None
    """
    text = reporter.TEX_DOC_START + reporter.TEX_DOC_CELL_SEP + reporter.TEX_DOC_ROW_END + \
           reporter.TEX_DOC_PAGE_SEP + reporter.TEX_DOC_END
    texFile = os.path.join(reporter.resultFolder, 'test.tex')
    with open(texFile, 'w') as _:
        _.write(text)
    try:
        r = subprocess.call([
            'pdflatex',
            '-interaction=nonstopmode',
            '-output-directory={}'.format(reporter.resultFolder),
            texFile,
        ], stdout=subprocess.DEVNULL)
        if r:
            raise RuntimeError("Some LaTeX libraries are not installed correctly")
    except FileNotFoundError:
        raise RuntimeError("LaTeX is not installed correctly")
    almostFile = texFile[:-4]
    subprocess.call(['rm'] + [almostFile + suffix for suffix in reporter.filesToRemove + ['.pdf']])


def checkEnvironment():
    """
    Checks environment.

    :raises: RuntimeError
    :return: None
    """
    logger.debug('Luna API check...')
    checkLunaAPI()
    logger.debug('Luna API check succeed.')
    logger.debug('Elasticsearch check...')
    checkES()
    logger.debug('Elasticsearch check succeed.')
    if config.USE_LATEX:
        logger.debug('LaTeX check...')
        checkLaTeX()
        logger.debug('LaTeX check succeed.')
