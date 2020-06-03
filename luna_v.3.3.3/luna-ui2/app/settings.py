import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = 'static/build/'
STATIC_ROOT = os.path.join(BASE_DIR, STATIC_DIR)
CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')

ACCEPTED_INPUT_FILES = {
    'image/jpg', 'image/jpeg', 'image/png', 'image/bmp',
    'image/tiff', 'image/gif', 'image/x-portable-pixmap',
}

STATIC_FILES_EXTENSIONS = ['js', 'css', 'ttf', 'json', 'png', 'xml', 'ico', 'jpg', 'map']
INDEX_PAGE_PATH = os.path.join(STATIC_ROOT, 'index.html')
