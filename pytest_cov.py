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

try:
    from functools import reduce
except ImportError:
    pass

def pytest_addoption(parser):
    """Add options to control coverage."""

    group = parser.getgroup('coverage reporting with distributed testing support')
    group.addoption('--cov-on', action='store_true', default=False,
                    dest='cov_on',
                    help='enable coverage, only needed if not specifying any --cov options')
    group.addoption('--cov', action='append', default=[], metavar='package',
                    dest='cov_packages',
                    help='collect coverage for the specified package (multi-allowed)')
    group.addoption('--cov-no-terminal', action='store_false', default=True,
                    dest='cov_terminal',
                    help='disable printing a report on the terminal')
    group.addoption('--cov-annotate', action='store_true', default=False,
                    dest='cov_annotate',
                    help='generate an annotated source code report')
    group.addoption('--cov-html', action='store_true', default=False,
                    dest='cov_html',
                    help='generate a html report')
    group.addoption('--cov-xml', action='store_true', default=False,
                    dest='cov_xml',
                    help='generate an xml report')
    group.addoption('--cov-annotate-dir', action='store', default='coverage_annotate', metavar='dir',
                    dest='cov_annotate_dir',
                    help='directory for the annotate report, default: %default')
    group.addoption('--cov-html-dir', action='store', default=None, metavar='dir',
                    dest='cov_html_dir',
                    help='directory for the html report, default: coverage_html')
    group.addoption('--cov-xml-file', action='store', default=None, metavar='path',
                    dest='cov_xml_file',
                    help='file for the xml report, default: coverage.xml')
    group.addoption('--cov-data-file', action='store', default=None, metavar='path',
                    dest='cov_data_file',
                    help='file containing coverage data, default: .coverage')
    group.addoption('--cov-combine-each', action='store_true', default=False,
                    dest='cov_combine_each',
                    help='for dist=each mode produce a single combined report')
    group.addoption('--cov-branch', action='store_true', default=None,
                    dest='cov_branch',
                    help='enable branch coverage')
    group.addoption('--cov-pylib', action='store_true', default=None,
                    dest='cov_pylib',
                    help='enable python library coverage')
    group.addoption('--cov-timid', action='store_true', default=None,
                    dest='cov_timid',
                    help='enable slower and simpler tracing')
    group.addoption('--cov-no-missing-lines', action='store_false', default=True,
                    dest='cov_show_missing',
                    help='disable showing missing lines, only relevant to the terminal report')
    group.addoption('--cov-no-missing-files', action='store_true', default=None,
                    dest='cov_ignore_errors',
                    help='disable showing message about missing source files')
    group.addoption('--cov-omit', action='store', default=None, metavar='prefix1,prefix2,...',
                    dest='cov_omit_prefixes',
                    help='ignore files with these prefixes')
    group.addoption('--cov-no-config', action='store_false', default=True,
                    dest='cov_config',
                    help='disable coverage reading its config file')
    group.addoption('--cov-config-file', action='store', default='.coveragerc', metavar='path',
                    dest='cov_config_file',
                    help='config file for coverage, default: %default')


def pytest_configure(config):
    """Activate coverage plugin if appropriate."""

    if config.getvalue('cov_on') or config.getvalue('cov_packages'):
        config.pluginmanager.register(CovPlugin(config), '_cov')


class CovPlugin(object):
    """Use coverage package to produce code coverage reports.

    Delegates all work to a particular implementation based on whether
    this test process is centralised, a distributed master or a
    distributed slave.
    """

    def __init__(self, config):
        """Creates a coverage pytest plugin.

        We read the rc file that coverage uses so that everything in
        the rc file will be honoured.  Specifically we tell coverage
        through it's API the data file name, html dir name and xml
        file name.  So we need to know what these are in the rc file
        or env vars.

        Doing this ensures that users can rely on the coverage rc file
        and env vars to work the same under this plugin as they do
        under coverage itself.
        """

        # Our implementation is unknown at this time.
        self.cov_controller = None

        # For data file, html dir and xml file consider coverage rc
        # file, coverage env vars and our own options in priority
        # order.
        parser = configparser.RawConfigParser()
        parser.read(config.getvalue('cov_config_file'))
        for default, section, item, env_var, option in (
            ('coverage_html', 'html', 'directory', None           , 'cov_html_dir' ),
            ('coverage.xml' , 'xml' , 'output'   , None           , 'cov_xml_file' ),
            ('.coverage'    , 'run' , 'data_file', 'COVERAGE_FILE', 'cov_data_file')):

            # Lowest priority is coverage hard coded default.
            result = default

            # Override with coverage rc file.
            if parser.has_option(section, item):
                result = parser.get(section, item)

            # Override with coverage env var.
            if env_var:
                result = os.environ.get(env_var, result)

            # Override with pytest cmd line, env var or conftest file.
            value = config.getvalue(option)
            if value:
                result = value

            # Set config option for consistency and for transport to slaves.
            setattr(config.option, option, result)

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

        self.config = config
        self.covs = []
        self.failed_slaves = []

        self.cov_data_file = config.getvalue('cov_data_file')
        self.cov_branch = config.getvalue('cov_branch')
        self.cov_pylib = config.getvalue('cov_pylib')
        self.cov_timid = config.getvalue('cov_timid')
        if self.config.getvalue('cov_config'):
            self.cov_config_file = os.path.realpath(self.config.getvalue('cov_config_file'))
        else:
            self.cov_config_file = False

    def terminal_summary(self, terminalreporter):
        """Produce coverage reports."""

        # Get terminal writer and config values.
        config = terminalreporter.config
        terminalwriter = terminalreporter._tw

        cov_packages = config.getvalue('cov_packages')
        cov_terminal = config.getvalue('cov_terminal')
        cov_annotate = config.getvalue('cov_annotate')
        cov_html = config.getvalue('cov_html')
        cov_xml = config.getvalue('cov_xml')
        cov_annotate_dir = config.getvalue('cov_annotate_dir')
        cov_html_dir = config.getvalue('cov_html_dir')
        cov_xml_file = config.getvalue('cov_xml_file')
        cov_show_missing = config.getvalue('cov_show_missing')
        cov_ignore_errors = config.getvalue('cov_ignore_errors')
        cov_omit_prefixes = config.getvalue('cov_omit_prefixes')
        if cov_omit_prefixes:
            cov_omit_prefixes = cov_omit_prefixes.split(',')

        # Determine the modules or files to limit reports on.
        morfs = list(set(module.__file__
                         for name, module in sys.modules.items()
                         for package in cov_packages
                         if hasattr(module, '__file__') and
                         os.path.splitext(module.__file__)[1] in ('.py', '.pyc', '.pyo') and
                         name.startswith(package)))

        # Produce a report for each coverage object.
        for cov, node_descs in self.covs:

            # Produce terminal report if wanted.
            if cov_terminal:
                if len(node_descs) == 1:
                    terminalwriter.sep('-', 'coverage: %s' % ''.join(node_descs))
                else:
                    terminalwriter.sep('-', 'coverage')
                    for node_desc in sorted(node_descs):
                        terminalwriter.sep(' ', '%s' % node_desc)
                cov.report(morfs, cov_show_missing, cov_ignore_errors, terminalwriter, cov_omit_prefixes)

            # Only determine a suffix if we have more reports to do.
            if cov_annotate or cov_html or cov_xml:

                # Determine suffix if needed for following reports.
                suffix = None
                if len(self.covs) > 1:
                    suffix = '_'.join(node_descs)
                    replacements = [(' ', '_'), (',', ''), ('.', ''), ('-', '')]
                    suffix = reduce(lambda suffix, oldnew: suffix.replace(oldnew[0], oldnew[1]), replacements, suffix)

                # Produce annotated source code report if wanted.
                if cov_annotate:
                    if suffix:
                        dir = '%s_%s' % (cov_annotate_dir, suffix)
                    else:
                        dir = cov_annotate_dir
                    cov.annotate(morfs, dir, cov_ignore_errors, cov_omit_prefixes)

                # Produce html report if wanted.
                if cov_html:
                    if suffix:
                        dir = '%s_%s' % (cov_html_dir, suffix)
                    else:
                        dir = cov_html_dir
                    cov.html_report(morfs, dir, cov_ignore_errors, cov_omit_prefixes)

                # Produce xml report if wanted.
                if cov_xml:
                    if suffix:
                        root, ext = os.path.splitext(cov_xml_file)
                        xml_file = '%s_%s%s' % (root, suffix, ext)
                    else:
                        xml_file = cov_xml_file
                    cov.xml_report(morfs, xml_file, cov_ignore_errors, cov_omit_prefixes)

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

        self.cov = coverage.coverage(data_file=self.cov_data_file,
                                     branch=self.cov_branch,
                                     cover_pylib=self.cov_pylib,
                                     timid=self.cov_timid,
                                     config_file=self.cov_config_file)
        self.cov.erase()
        self.cov.start()

    def sessionfinish(self, session, exitstatus):
        """Stop coverage, save data to file and set the list of coverage objects to report on."""

        self.cov.stop()
        self.cov.save()
        node_desc = get_node_desc(sys.platform, sys.version_info)
        self.covs = [(self.cov, [node_desc])]

    def terminal_summary(self, terminalreporter):
        """Produce coverage reports."""

        CovController.terminal_summary(self, terminalreporter)


class DistMaster(CovController):
    """Implementation for distributed master."""

    def sessionstart(self, session):
        """Ensure coverage rc file rsynced if appropriate."""

        self.data_files = {}
        if self.cov_config_file and os.path.exists(self.cov_config_file):
            self.config.option.rsyncdir.append(self.cov_config_file)

    def configure_node(self, node):
        """Slaves need to know if they are collocated and what files have moved."""

        node.slaveinput['cov_master_host'] = socket.gethostname()
        node.slaveinput['cov_master_topdir'] = self.config.topdir
        node.slaveinput['cov_master_rsync_roots'] = node.nodemanager.roots

    def testnodedown(self, node, error):
        """Collect data file name from slave.  Also save data to file if slave not collocated."""

        # If slave doesn't return any data then it is likely that this
        # plugin didn't get activated on the slave side.
        if not (hasattr(node, 'slaveoutput') and
                'cov_slave_data_file' in node.slaveoutput):
            self.failed_slaves.append(node)
            return

        # If slave is not collocated then we must save the data file
        # that it returns to us.
        if 'cov_slave_data_suffix' in node.slaveoutput:
            cov = coverage.coverage(data_file=node.slaveoutput['cov_slave_data_file'],
                                    data_suffix=node.slaveoutput['cov_slave_data_suffix'],
                                    branch=self.cov_branch,
                                    cover_pylib=self.cov_pylib,
                                    timid=self.cov_timid,
                                    config_file=self.cov_config_file)
            cov.start()
            cov.stop()
            cov.data.lines = node.slaveoutput['cov_slave_lines']
            cov.data.arcs = node.slaveoutput['cov_slave_arcs']
            cov.save()

        # For each data file record the set of slave types that contribute.
        rinfo = node.gateway._rinfo()
        node_desc = get_node_desc(rinfo.platform, rinfo.version_info)
        node_descs = self.data_files.setdefault(node.slaveoutput['cov_slave_data_file'], set())
        node_descs.add(node_desc)

    def sessionfinish(self, session, exitstatus):
        """Combines coverage data and sets the list of coverage objects to report on."""

        # Fn that combines all appropriate suffix files into a data file.
        def combine(data_file):
            cov = coverage.coverage(data_file=data_file,
                                    branch=self.cov_branch,
                                    cover_pylib=self.cov_pylib,
                                    timid=self.cov_timid,
                                    config_file=self.cov_config_file)
            cov.erase()
            cov.combine()
            cov.save()
            return cov

        # For each data file combine all its suffix files and record
        # the contributing node types.
        self.covs = [(combine(data_file), node_descs) for data_file, node_descs in sorted(self.data_files.items())]

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

        # Determine what data file to contribute to.
        if session.config.option.dist == 'each' and not session.config.getvalue('cov_combine_each'):
            # Contribute to data file specific to this node type,
            # typically --dist=each and we are the only contributing
            # slave.
            node_desc = 'platform_%s_python_%s' % (sys.platform, '%s%s%s%s%s' % sys.version_info[:5])
            self.data_file = '%s_%s' % (session.config.getvalue('cov_data_file'), node_desc)
        else:
            # Contribute to data file which typically is --dist=load
            # and has all slaves contributing to it.
            self.data_file = session.config.getvalue('cov_data_file')

        # Our suffix makes us unique from all other slaves, master
        # will combine our data later.
        self.data_suffix = session.nodeid

        # Erase any previous data and start coverage.
        self.cov = coverage.coverage(data_file=self.data_file,
                                     data_suffix=self.data_suffix,
                                     branch=self.cov_branch,
                                     cover_pylib=self.cov_pylib,
                                     timid=self.cov_timid,
                                     config_file=self.cov_config_file)
        self.cov.erase()
        self.cov.start()

    def sessionfinish(self, session, exitstatus):
        """Stop coverage and send relevant info back to the master."""

        self.cov.stop()

        if self.is_collocated:
            # If we are collocated then save the file ourselves and
            # inform the master of the data file we are contributing
            # to.
            self.cov.save()
            session.config.slaveoutput['cov_slave_data_file'] = self.data_file
        else:
            # If we are not collocated then rewrite the filenames from
            # the slave location to the master location.
            slave_topdir = session.config.topdir
            path_rewrites = [(str(slave_topdir.join(rsync_root.basename)), str(rsync_root))
                             for rsync_root in session.config.slaveinput['cov_master_rsync_roots']]
            path_rewrites.append((str(session.config.topdir), str(session.config.slaveinput['cov_master_topdir'])))

            def rewrite_path(filename):
                return reduce(lambda filename, slavemaster: filename.replace(slavemaster[0], slavemaster[1]),
                              path_rewrites,
                              filename)
            lines = dict((rewrite_path(filename), data) for filename, data in self.cov.data.lines.items())
            arcs = dict((rewrite_path(filename), data) for filename, data in self.cov.data.arcs.items())

            # Send all the data to the master over the channel.
            session.config.slaveoutput['cov_slave_data_file'] = self.data_file
            session.config.slaveoutput['cov_slave_data_suffix'] = self.data_suffix
            session.config.slaveoutput['cov_slave_lines'] = lines
            session.config.slaveoutput['cov_slave_arcs'] = arcs

    def terminal_summary(self, terminalreporter):
        """Only the master reports so do nothing."""

        pass


def get_node_desc(platform, version_info):
    """Return a description of this node."""

    return 'platform %s, python %s' % (platform, '%s.%s.%s-%s-%s' % version_info[:5])
