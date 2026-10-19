========
Contexts
========

Coverage.py 5.0 can record separate coverage data for `different contexts`_ during
one run of a test suite.  Pytest-cov can use this feature to record coverage
data for each test individually, with the ``--cov-context=test`` option.

This requires a coverage core that supports dynamic contexts. If the selected
core does not support them, pytest-cov reports a usage error before running
tests. For example, coverage.py's ``sysmon`` core currently does not support
dynamic contexts and is the default on Python 3.14 and newer. Select a compatible
core in ``.coveragerc``::

    [run]
    core = ctrace

Or in ``pyproject.toml``::

    [tool.coverage.run]
    core = "ctrace"

.. _different contexts: https://coverage.readthedocs.io/en/latest/contexts.html

The context name recorded in the coverage.py database is the pytest test id,
and the phase of execution, one of "setup", "run", or "teardown".  These two
are separated with a pipe symbol.  You might see contexts like::

    test_functions.py::test_addition|run
    test_fancy.py::test_parametrized[1-101]|setup
    test_oldschool.py::RegressionTests::test_error|run

Note that parameterized tests include the values of the parameters in the test
id, and each set of parameter values is recorded as a separate test.

To view contexts when using ``--cov-report=html``, add this to your ``.coveragerc``::

    [html]
    show_contexts = True

The HTML report will include an annotation on each covered line, indicating the
number of contexts that executed the line. Clicking the annotation displays a
list of the contexts.
