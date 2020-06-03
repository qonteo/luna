from .lps_events_module import app as lpse_app
from .statistic_module import app as sm_app
from .lps_stub import app as lps_stub_app

APPS = {'lpse': lpse_app, 'lps_stub': lps_stub_app, 'sm': sm_app}

__all__ = ['APPS']
