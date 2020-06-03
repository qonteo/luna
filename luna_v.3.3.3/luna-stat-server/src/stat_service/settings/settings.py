class ServiceSettings(object):
    """
    `ServiceSettings` loads service configuration from the file or from the loadable module and merges it with defaults.
     Refer to `defaults.py` to know allowed parameters, also see module docs to know appropriate values.
     Note, keys, which are used to load from modules are UPPER.
    """

    def __init__(self, object_sources=None):
        from . import defaults
        self._sources = []

        self._add_object_source(defaults, True)
        self._default_source_getter = self._sources[0]

        if object_sources is not None:
            for source, keys_upper in object_sources:
                self._add_object_source(source, keys_upper)

    def _add_object_source(self, source, upper=False):
        def n(name):
            try:
                return source[{False: name, True: name.upper()}[upper]]
            except TypeError:
                return getattr(source, {False: name, True: name.upper()}[upper], None)

        self._sources.append(n)

    def _add_dict_source(self, source):
        self._sources.append(
            lambda name: source[name]
        )

    def __getattr__(self, item):
        if item.startswith('_'):
            return object.__getattribute__(self, item)

        seen_default = None
        for getter in reversed(self._sources):
            try:
                res = getter(item)

                if res is None:
                    continue
                elif res == self._default_source_getter(item):
                    seen_default = res
                    continue
                else:
                    return res
            except (KeyError, AttributeError):
                continue

        if seen_default is not None:
            return seen_default

        raise KeyError(f'Cant find options for {item}')
