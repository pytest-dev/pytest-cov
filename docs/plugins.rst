===============
Plugin coverage
===============

Getting coverage on pytest plugins is a very particular situation. Because how pytest implements plugins (using setuptools
entrypoints) it doesn't allow controlling the order in which the plugins load.
See `pytest/issues/935 <https://github.com/pytest-dev/pytest/issues/935#issuecomment-245107960>`_ for technical details.

The current way of dealing with this problem is using the append feature and manually starting ``pytest-cov``'s engine, eg:

    COV_CORE_SOURCE=src COV_CORE_CONFIG=.coveragerc COV_CORE_DATAFILE=.coverage.eager py.test --cov=src --cov-append

Alternatively you can have this in ``tox.ini`` (if you're using `Tox <https://tox.readthedocs.io/en/latest/>`_ of course)::

    [testenv]
    setenv =
        COV_CORE_SOURCE={toxinidir}/src
        COV_CORE_CONFIG={toxinidir}/.coveragerc
        COV_CORE_DATAFILE={toxinidir}/.coverage.eager

And in ``pytest.ini`` / ``tox.ini`` / ``setup.cfg``::

    [tool:pytest]
    addopts =
        --cov-append
