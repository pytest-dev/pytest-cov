"""produce code coverage reports using the 'coverage' package, including support for distributed testing.

This plugin produces coverage reports using the coverage package.  It
supports centralised testing and distributed testing in both load and
each modes.

All features offered by the coverage package should be available,
either through this plugin or through coverage's own config file.


Installation
------------

The `pytest-cov pypi`_ package may be installed / uninstalled with pip::

    pip install pytest-cov
    pip uninstall pytest-cov

Alternatively easy_install can be used::

    easy_install pytest-cov

.. _`pytest-cov pypi`: http://pypi.python.org/pypi/pytest-cov/


Usage
-----

Centralised Testing
~~~~~~~~~~~~~~~~~~~

Running centralised testing::

    py.test --cov myproj tests/

Shows a terminal report::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Distributed Testing
~~~~~~~~~~~~~~~~~~~

Distributed testing with dist mode set to load::

    py.test --cov myproj -n 2 tests/

The results from the slaves will be combined like so::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Distributed testing in each mode::

    py.test --cov myproj --dist=each
            --tx=popen//python=/usr/local/python265/bin/python
            --tx=popen//python=/usr/local/python27b1/bin/python
            tests/

Will produce a report for each slave::

    -------------------- coverage: platform linux2, python 2.6.5-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%
    --------------------- coverage: platform linux2, python 2.7.0-beta-1 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Distributed testing in each mode can also produce a single combined
report.  This is useful to get coverage information spanning things
such as all python versions::

    py.test --cov myproj --cov-combine-each --dist=each
            --tx=popen//python=/usr/local/python265/bin/python
            --tx=popen//python=/usr/local/python27b1/bin/python
            tests/

Which looks like::

    ---------------------------------------- coverage ----------------------------------------
                              platform linux2, python 2.6.5-final-0
                               platform linux2, python 2.7.0-beta-1
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Reporting
---------

By default a terminal report is output.  This report can be disabled
if desired, such as when results are going to a continuous integration
system and the terminal output won't be seen.

In addition and without rerunning tests it is possible to generate
annotated source code, a html report and an xml report.

The directories for annotated source code and html reports can be
specified as can the file name for the xml report.

Since testing often takes a non trivial amount of time at the end of
testing any / all of the reports may be generated.


Coverage Data File
------------------

During testing there may be many data files with coverage data.  These
will have unique suffixes and will be combined at the end of testing.

Upon completion, for --dist=load (and also for --dist=each when the
--cov-combine-each option is used) there will only be one data file.

For --dist=each there may be many data files where each one will have
the platform / python version info appended to the name.

These data files are left at the end of testing so that it is possible
to use normal coverage tools to examine them.

At the beginning of testing any data files that are about to be used
will first be erased so ensure the data is clean for each test run.

It is possible to set the name of the data file.  If needed the
platform / python version will be appended automatically to this name.


Coverage Config File
--------------------

Coverage by default will read its own config file.  An alternative
file name may be specified or reading config can be disabled entirely.

Care has been taken to ensure that the coverage env vars and config
file options work the same under this plugin as they do under coverage
itself.

Since options may be specified in different ways the order of
precedence between pytest-cov and coverage from highest to lowest is:

1. pytest command line
2. pytest env var
3. pytest conftest
4. coverage env var
5. coverage config file
6. coverage default


Limitations
-----------

For distributed testing the slaves must have the pytest-cov package
installed.  This is needed since the plugin must be registered through
setuptools / distribute for pytest to start the plugin on the slave.


Acknowledgements
----------------

Holger Krekel for pytest with its distributed testing support.

Ned Batchelder for coverage and its ability to combine the coverage
results of parallel runs.

Whilst this plugin has been built fresh from the ground up to support
distributed testing it has been influenced by the work done on
pytest-coverage (Ross Lawley, James Mills, Holger Krekel) and
nose-cover (Jason Pellerin) which are other coverage plugins for
pytest and nose respectively.

No doubt others have contributed to these tools as well.
"""

import cov_core

def pytest_addoption(parser):
    """Add options to control coverage."""

    group = parser.getgroup('coverage reporting with distributed testing support')
    group.addoption('--cov', action='append', default=[], metavar='path',
                    dest='cov_source',
                    help='measure coverage for path (multi-allowed)')
    group.addoption('--cov-report', action='append', default=[], metavar='type',
                    choices=['term', 'term-missing', 'annotate', 'html', 'xml'],
                    dest='cov_report',
                    help='type of report to generate: term, term-missing, annotate, html, xml (multi-allowed)')
    group.addoption('--cov-config', action='store', default='.coveragerc', metavar='path',
                    dest='cov_config',
                    help='config file for coverage, default: .coveragerc')


def pytest_configure(config):
    """Activate coverage plugin if appropriate."""

    if config.getvalue('cov_source'):
        config.pluginmanager.register(CovPlugin(config), '_cov')


class CovPlugin(object):
    """Use coverage package to produce code coverage reports.

    Delegates all work to a particular implementation based on whether
    this test process is centralised, a distributed master or a
    distributed slave.
    """

    def __init__(self, config):
        """Creates a coverage pytest plugin.

        We read the rc file that coverage uses to get the data file
        name.  This is needed since we give coverage through it's API
        the data file name.
        """

        # Our implementation is unknown at this time.
        self.cov_controller = None

    def pytest_sessionstart(self, session):
        """At session start determine our implementation and delegate to it."""

        cov_source = session.config.getvalue('cov_source')
        cov_report = session.config.getvalue('cov_report') or ['term']
        cov_config = session.config.getvalue('cov_config')

        name_to_cls = dict(Session=cov_core.Central,
                           DSession=cov_core.DistMaster,
                           SlaveSession=cov_core.DistSlave)
        session_name = session.__class__.__name__
        controller_cls = name_to_cls.get(session_name, cov_core.Central)
        self.cov_controller = controller_cls(cov_source,
                                             cov_report,
                                             cov_config,
                                             session.config,
                                             getattr(session, 'nodeid', None))

        self.cov_controller.start()

    def pytest_configure_node(self, node):
        """Delegate to our implementation."""

        self.cov_controller.configure_node(node)

    def pytest_testnodedown(self, node, error):
        """Delegate to our implementation."""

        self.cov_controller.testnodedown(node, error)

    def pytest_sessionfinish(self, session, exitstatus):
        """Delegate to our implementation."""

        self.cov_controller.finish()

    def pytest_terminal_summary(self, terminalreporter):
        """Delegate to our implementation."""

        self.cov_controller.summary(terminalreporter._tw)

    def pytest_funcarg__cov(self, request):
        """A pytest funcarg that provide access to the underlying coverage object."""

        return self.cov_controller.cov if self.cov_controller else None
