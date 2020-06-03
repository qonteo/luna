from .builder import SFBuilder


def setup(app):
    app.add_builder(SFBuilder)
