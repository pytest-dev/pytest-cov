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

import coverage
import socket
import sys
import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from pytest_cov_init import UNIQUE_SEP


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

        # For data file name consider coverage rc file, coverage env
        # vars in priority order.
        parser = configparser.RawConfigParser()
        parser.read(config.getvalue('cov_config'))
        for default, section, item, env_var, option in [
            ('.coverage', 'run', 'data_file', 'COVERAGE_FILE', 'cov_data_file')]:

            # Lowest priority is coverage hard coded default.
            result = default

            # Override with coverage rc file.
            if parser.has_option(section, item):
                result = parser.get(section, item)

            # Override with coverage env var.
            if env_var:
                result = os.environ.get(env_var, result)

            # Set config option for consistency and for transport to slaves.
            setattr(config.option, option, result)

    def pytest_funcarg__cov(self, request):
        """A pytest funcarg that provide access to the underlying coverage object."""

        return self.cov_controller.cov

    def pytest_sessionstart(self, session):
        """At session start determine our implementation and delegate to it."""

        self.cov_controller = CovController.create_from_session(session)
        self.cov_controller.sessionstart(session)

    def pytest_configure_node(self, node):
        """Delegate to our implementation."""

        self.cov_controller.configure_node(node)

    def pytest_testnodedown(self, node, error):
        """Delegate to our implementation."""

        self.cov_controller.testnodedown(node, error)

    def pytest_sessionfinish(self, session, exitstatus):
        """Delegate to our implementation."""

        self.cov_controller.sessionfinish(session, exitstatus)

    def pytest_terminal_summary(self, terminalreporter):
        """Delegate to our implementation."""

        self.cov_controller.terminal_summary(terminalreporter)


class CovController(object):
    """Base class for different plugin implementations."""

    @staticmethod
    def create_from_session(session):
        """Create the appropriate implementation based on the type of session."""

        name_to_cls = dict(Session=Central,
                           DSession=DistMaster,
                           SlaveSession=DistSlave)
        session_name = session.__class__.__name__
        controller_cls = name_to_cls.get(session_name, Central)
        return controller_cls(session.config)

    def __init__(self, config):
        """Get some common config used by multiple derived classes."""

        self.cov = None
        self.node_descs = set()
        self.failed_slaves = []
        self.config = config
        self.cov_source = self.config.getvalue('cov_source')
        self.cov_data_file = self.config.getvalue('cov_data_file')
        self.cov_config = self.config.getvalue('cov_config')

    def set_env(self):
        """Put info about coverage into the env so that subprocesses can activate coverage."""

        os.environ['PYTEST_COV_SOURCE'] = UNIQUE_SEP.join(self.cov_source)
        os.environ['PYTEST_COV_DATA_FILE'] = self.cov_data_file
        os.environ['PYTEST_COV_CONFIG'] = self.cov_config

    @staticmethod
    def unset_env():
        """Remove coverage info from env."""

        del os.environ['PYTEST_COV_SOURCE']
        del os.environ['PYTEST_COV_DATA_FILE']
        del os.environ['PYTEST_COV_CONFIG']

    @staticmethod
    def get_node_desc(platform, version_info):
        """Return a description of this node."""

        return 'platform %s, python %s' % (platform, '%s.%s.%s-%s-%s' % version_info[:5])

    def terminal_summary(self, terminalreporter):
        """Produce coverage reports."""

        # Get terminal writer and config values.
        terminalwriter = terminalreporter._tw
        cov_report = self.config.getvalue('cov_report') or ['term']

        # Produce terminal report if wanted.
        if 'term' in cov_report or 'term-missing' in cov_report:
            if len(self.node_descs) == 1:
                terminalwriter.sep('-', 'coverage: %s' % ''.join(self.node_descs))
            else:
                terminalwriter.sep('-', 'coverage')
                for node_desc in sorted(self.node_descs):
                    terminalwriter.sep(' ', '%s' % node_desc)
            show_missing = 'term-missing' in cov_report
            self.cov.report(show_missing=show_missing, ignore_errors=True, file=terminalwriter)

        # Produce annotated source code report if wanted.
        if 'annotate' in cov_report:
            self.cov.annotate(ignore_errors=True)

        # Produce html report if wanted.
        if 'html' in cov_report:
            self.cov.html_report(ignore_errors=True)

        # Produce xml report if wanted.
        if 'xml' in cov_report:
            self.cov.xml_report(ignore_errors=True)

        # Report on any failed slaves.
        if self.failed_slaves:
            terminalwriter.sep('-', 'coverage: failed slaves')
            terminalwriter.write('The following slaves failed to return coverage data, '
                                 'ensure that pytest-cov is installed on these slaves.\n')
            for node in self.failed_slaves:
                terminalwriter.write('%s\n' % node.gateway.id)


class Central(CovController):
    """Implementation for centralised operation."""

    def sessionstart(self, session):
        """Erase any previous coverage data and start coverage."""

        self.cov = coverage.coverage(source=self.cov_source,
                                     data_file=self.cov_data_file,
                                     config_file=self.cov_config)
        self.cov.erase()
        self.cov.start()
        self.set_env()

    def sessionfinish(self, session, exitstatus):
        """Stop coverage, save data to file and set the list of coverage objects to report on."""

        self.unset_env()
        self.cov.stop()
        self.cov.combine()
        self.cov.save()
        node_desc = self.get_node_desc(sys.platform, sys.version_info)
        self.node_descs.add(node_desc)

    def terminal_summary(self, terminalreporter):
        """Produce coverage reports."""

        CovController.terminal_summary(self, terminalreporter)


class DistMaster(CovController):
    """Implementation for distributed master."""

    def sessionstart(self, session):
        """Ensure coverage rc file rsynced if appropriate."""

        if self.cov_config and os.path.exists(self.cov_config):
            self.config.option.rsyncdir.append(self.cov_config)

    def configure_node(self, node):
        """Slaves need to know if they are collocated and what files have moved."""

        node.slaveinput['cov_master_host'] = socket.gethostname()
        node.slaveinput['cov_master_topdir'] = self.config.topdir
        node.slaveinput['cov_master_rsync_roots'] = node.nodemanager.roots

    def testnodedown(self, node, error):
        """Collect data file name from slave.  Also save data to file if slave not collocated."""

        # If slave doesn't return any data then it is likely that this
        # plugin didn't get activated on the slave side.
        if not (hasattr(node, 'slaveoutput') and 'cov_slave_node_id' in node.slaveoutput):
            self.failed_slaves.append(node)
            return

        # If slave is not collocated then we must save the data file
        # that it returns to us.
        if 'cov_slave_lines' in node.slaveoutput:
            cov = coverage.coverage(source=self.cov_source,
                                    data_file=self.cov_data_file,
                                    data_suffix=node.slaveoutput['cov_slave_node_id'],
                                    config_file=self.cov_config)
            cov.start()
            cov.data.lines = node.slaveoutput['cov_slave_lines']
            cov.data.arcs = node.slaveoutput['cov_slave_arcs']
            cov.stop()
            cov.save()

        # Record the slave types that contribute to the data file.
        rinfo = node.gateway._rinfo()
        node_desc = self.get_node_desc(rinfo.platform, rinfo.version_info)
        self.node_descs.add(node_desc)

    def sessionfinish(self, session, exitstatus):
        """Combines coverage data and sets the list of coverage objects to report on."""

        # Combine all the suffix files into the data file.
        self.cov = coverage.coverage(source=self.cov_source,
                                     data_file=self.cov_data_file,
                                     config_file=self.cov_config)
        self.cov.erase()
        self.cov.combine()
        self.cov.save()

    def terminal_summary(self, terminalreporter):
        """Produce coverage reports."""

        CovController.terminal_summary(self, terminalreporter)


class DistSlave(CovController):
    """Implementation for distributed slaves."""

    def sessionstart(self, session):
        """Determine what data file and suffix to contribute to and start coverage."""

        # Determine whether we are collocated with master.
        self.is_collocated = bool(socket.gethostname() == session.config.slaveinput['cov_master_host'] and
                                  session.config.topdir == session.config.slaveinput['cov_master_topdir'])

        # If we are not collocated then rewrite master paths to slave paths.
        if not self.is_collocated:
            master_topdir = str(session.config.slaveinput['cov_master_topdir'])
            slave_topdir = str(session.config.topdir)
            self.cov_source = [source.replace(master_topdir, slave_topdir) for source in self.cov_source]
            self.cov_data_file = self.cov_data_file.replace(master_topdir, slave_topdir)
            self.cov_config = self.cov_config.replace(master_topdir, slave_topdir)

        # Our slave node id makes us unique from all other slaves so
        # adjust the data file that we contribute to and the master
        # will combine our data with other slaves later.
        self.cov_data_file += '.%s' % session.nodeid

        # Erase any previous data and start coverage.
        self.cov = coverage.coverage(source=self.cov_source,
                                     data_file=self.cov_data_file,
                                     config_file=self.cov_config)
        self.cov.erase()
        self.cov.start()
        self.set_env()

    def sessionfinish(self, session, exitstatus):
        """Stop coverage and send relevant info back to the master."""

        self.unset_env()
        self.cov.stop()
        self.cov.combine()
        self.cov.save()

        if self.is_collocated:
            # If we are collocated then just inform the master of our
            # data file to indicate that we have finished.
            session.config.slaveoutput['cov_slave_node_id'] = session.nodeid
        else:
            # If we are not collocated then rewrite the filenames from
            # the slave location to the master location.
            slave_topdir = session.config.topdir
            path_rewrites = [(str(slave_topdir.join(rsync_root.basename)), str(rsync_root))
                             for rsync_root in session.config.slaveinput['cov_master_rsync_roots']]
            path_rewrites.append((str(session.config.topdir), str(session.config.slaveinput['cov_master_topdir'])))

            def rewrite_path(filename):
                for slave_path, master_path in path_rewrites:
                    filename = filename.replace(slave_path, master_path)
                return filename

            lines = dict((rewrite_path(filename), data) for filename, data in self.cov.data.lines.items())
            arcs = dict((rewrite_path(filename), data) for filename, data in self.cov.data.arcs.items())

            # Send all the data to the master over the channel.
            session.config.slaveoutput['cov_slave_node_id'] = session.nodeid
            session.config.slaveoutput['cov_slave_lines'] = lines
            session.config.slaveoutput['cov_slave_arcs'] = arcs

    def terminal_summary(self, terminalreporter):
        """Only the master reports so do nothing."""

        pass
