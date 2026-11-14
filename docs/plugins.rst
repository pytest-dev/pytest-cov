===============
Plugin coverage
===============

Getting coverage on pytest plugins is a very particular situation. Because of how pytest implements plugins (using setuptools
entrypoints) it doesn't allow controlling the order in which the plugins load.
See `pytest/issues/935 <https://github.com/pytest-dev/pytest/issues/935#issuecomment-245107960>`_ for technical details.

**Currently there is no way to measure your pytest plugin if you use pytest-cov**.
You should change your test invocations to use ``coverage run -m pytest ...`` instead.

Warning filters can import code before coverage starts
-----------------------------------------------------

Pytest resolves warning classes in ``-W`` options and ``filterwarnings``
settings during startup. If a filter names a warning class from the package
being measured, pytest imports that package before pytest-cov starts tracing.
For example::

    python -m pytest --cov=mypackage -W error::mypackage.MyWarning tests/

Code executed when ``mypackage`` is first imported is not measured, even if
the tests pass. The coverage report may therefore mark import-time statements
as missing. Moving the filter into ``pytest.ini`` or ``pyproject.toml``
does not avoid the early import.

To start measurement before pytest processes its warning filters, use
coverage.py to run pytest instead::

    coverage run -m pytest -W error::mypackage.MyWarning tests/
    coverage report

Do not pass pytest-cov's ``--cov`` options in this invocation: the
``coverage`` command handles starting measurement and producing the report.
