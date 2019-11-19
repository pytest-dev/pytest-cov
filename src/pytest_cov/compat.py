import warnings

import pytest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

StringIO  # pyflakes, this is for re-export

PYTEST_VERSION = tuple(int(v) for v in pytest.__version__.split('.')[:3])

if hasattr(pytest, 'hookimpl'):
    hookwrapper = pytest.hookimpl(hookwrapper=True)
else:
    hookwrapper = pytest.mark.hookwrapper


class SessionWrapper(object):
    def __init__(self, session):
        self._session = session
        if hasattr(session, 'testsfailed'):
            self._attr = 'testsfailed'
        else:
            self._attr = '_testsfailed'

    @property
    def testsfailed(self):
        return getattr(self._session, self._attr)

    @testsfailed.setter
    def testsfailed(self, value):
        setattr(self._session, self._attr, value)


if PYTEST_VERSION >= (3, 8):
    def warn(config, message, category, stacklevel=1):
        return warnings.warn(
            message=message,
            category=category,
            stacklevel=stacklevel+1,
        )
else:
    def warn(config, message, category, stacklevel=1):
        return config.warn(
            code=category.code,
            message=message,
        )


def _attrgetter(attr):
    """
    Return a callable object that fetches attr from its operand.

    Unlike operator.attrgetter, the returned callable supports an extra two
    arg form for a default.
    """
    def fn(obj, *args):
        return getattr(obj, attr, *args)

    return fn

worker = 'slave'  # for compatability with pytest-xdist<=1.22.0
workerid = worker + 'id'
workerinput = _attrgetter(worker + 'input')
workeroutput = _attrgetter(worker + 'output')
