import logging
import sys

import pyroutes

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

real_stderr = sys.stderr
fake_stderr = StringIO()
real_loghandlers = pyroutes.LOGGER.handlers
fake_loghandlers = [logging.StreamHandler(fake_stderr)]

logging.basicConfig(level=logging.DEBUG)

def redirect_stderr():
    sys.stderr = fake_stderr
    pyroutes.LOGGER.handlers = fake_loghandlers

def revert_stderr():
    sys.stderr = real_stderr
    pyroutes.LOGGER.handlers = real_loghandlers

def get_stderr_data():
    fake_stderr.seek(0)
    data = fake_stderr.read()
    fake_stderr.truncate(0)
    return data
