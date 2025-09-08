===============
Plugin coverage
===============

Getting coverage on pytest plugins is a very particular situation. Because of how pytest implements plugins (using setuptools
entrypoints) it doesn't allow controlling the order in which the plugins load.
See `pytest/issues/935 <https://github.com/pytest-dev/pytest/issues/935#issuecomment-245107960>`_ for technical details.

**Currently there is no way to measure your pytest plugin if you use pytest-cov**.
You should change your test invocations to use ``coverage run -m pytest ...`` instead.
