"""produce code coverage reports using the 'coverage' package, including support for distributed testing.

This plugin produces coverage reports using the coverage package.  It
supports centralised testing and distributed testing in both load and
each modes.

All features offered by the coverage package should be available,
either through this plugin or through coverage's own config file.


Installation
------------

This plugin depends on features just added to py and pytest-xdist.
Until py 1.2.2 and pytest-xdist 1.2 are released you will need to
install the 'tip' development versions from:

http://bitbucket.org/hpk42/py-trunk/downloads/

http://bitbucket.org/hpk42/pytest-xdist/downloads/


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

Distributed testing with dist mode set to load and branch coverage
enabled::

    py.test -n 2 --cov myproj --cov-branch tests/

The results from the slaves will be combined like so::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec Branch BrExec  Cover   Missing
    ----------------------------------------------------------------
    myproj/__init__          2      2      0      0   100%
    myproj/myproj          257    244     56     50    93%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87     18     13    89%   183-188, 197
    ----------------------------------------------------------------
    TOTAL                  353    333     74     63    92%


Distributed testing in each mode::

    py.test --cov myproj --dist=each
            --tx=popen//python=/usr/local/python264/bin/python
            --tx=popen//python=/usr/local/python265/bin/python
            tests/

Will produce a report for each slave::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%
    -------------------- coverage: platform linux2, python 2.6.5-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


If desired distributed testing in each mode can instead produce a single combined report::

    py.test --cov myproj --cov-combine-each --dist=each
            --tx=popen//python=/usr/local/python264/bin/python
            --tx=popen//python=/usr/local/python265/bin/python
            tests/

Which looks like::

    ---------------------------------------- coverage ----------------------------------------
                              platform linux2, python 2.6.4-final-0
                              platform linux2, python 2.6.5-final-0
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


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

try:
    from functools import reduce
except ImportError:
    pass
import sys
import os

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
    """Use coverage module to produce code coverage reports.

    Delegates all work to a particular implementation based on whether
    this test process is centralised, a distributed master or a
    distributed slave.
    """

    def __init__(self, config):
        self.config = config
        self.cov_controller = None

        # Maintain same behaviour as coverage for some of our options.
        # This ensures that users can rely on coverage rc file and env
        # vars.
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser

        parser = configparser.RawConfigParser()
        parser.read(self.config.getvalue('cov_config_file'))
        for default, section, item, env_var, option in (
            ('coverage_html', 'html', 'directory', None           , 'cov_html_dir' ),
            ('coverage.xml' , 'xml' , 'output'   , None           , 'cov_xml_file' ),
            ('.coverage'    , 'run' , 'data_file', 'COVERAGE_FILE', 'cov_data_file')):

            # Lowest priority is hard coded default.
            result = default

            # Override with coverage rc file.
            if parser.has_option(section, item):
                result = parser.get(section, item)

            # Override with env var.
            if env_var:
                result = os.environ.get(env_var, result)

            # Override with conftest file or cmd line.
            value = self.config.getvalue(option)
            if value:
                result = value

            # Set config option for consistency and for transport.
            setattr(self.config.option, option, result)

    def pytest_sessionstart(self, session):
        self.cov_controller = CovController.create_from_session(session)
        self.cov_controller.sessionstart(session)

    def pytest_configure_node(self, node):
        self.cov_controller.configure_node(node)

    def pytest_testnodedown(self, node, error):
        self.cov_controller.testnodedown(node, error)

    def pytest_sessionfinish(self, session, exitstatus):
        self.cov_controller.sessionfinish(session, exitstatus)

    def pytest_terminal_summary(self, terminalreporter):
        self.cov_controller.terminal_summary(terminalreporter)


class CovController(object):
    """Base class for different plugin implementations.

    Responsible for creating appropriate implementation based on type
    of session.

    Responsible for final outputting of coverage reports.
    """

    @staticmethod
    def create_from_session(session):
        name_to_cls = dict(Session=Central,
                           DSession=DistMaster,
                           SlaveSession=DistSlave)
        session_name = session.__class__.__name__
        controller_cls = name_to_cls.get(session_name, Central)
        return controller_cls()

    def terminal_summary(self, terminalreporter):
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

        morfs = list(set(module.__file__
                         for name, module in sys.modules.items()
                         for package in cov_packages
                         if hasattr(module, '__file__') and
                         os.path.splitext(module.__file__)[1] in ('.py', '.pyc', '.pyo') and
                         name.startswith(package)))

        for cov, node_descs in self.covs:

            if cov_terminal:
                if len(node_descs) == 1:
                    terminalwriter.sep('-', 'coverage: %s' % ''.join(node_descs))
                else:
                    terminalwriter.sep('-', 'coverage')
                    for node_desc in sorted(node_descs):
                        terminalwriter.sep(' ', '%s' % node_desc)
                cov.report(morfs, cov_show_missing, cov_ignore_errors, terminalwriter, cov_omit_prefixes)

            if cov_annotate or cov_html or cov_xml:

                suffix = None
                if len(self.covs) > 1:
                    suffix = '_'.join(node_descs)
                    replacements = [(' ', '_'), (',', ''), ('.', ''), ('-', '')]
                    suffix = reduce(lambda suffix, oldnew: suffix.replace(oldnew[0], oldnew[1]), replacements, suffix)

                if cov_annotate:
                    if suffix:
                        dir = '%s_%s' % (cov_annotate_dir, suffix)
                    else:
                        dir = cov_annotate_dir
                    cov.annotate(morfs, dir, cov_ignore_errors, cov_omit_prefixes)

                if cov_html:
                    if suffix:
                        dir = '%s_%s' % (cov_html_dir, suffix)
                    else:
                        dir = cov_html_dir
                    cov.html_report(morfs, dir, cov_ignore_errors, cov_omit_prefixes)

                if cov_xml:
                    if suffix:
                        root, ext = os.path.splitext(cov_xml_file)
                        xml_file = '%s_%s%s' % (root, suffix, ext)
                    else:
                        xml_file = cov_xml_file
                    cov.xml_report(morfs, xml_file, cov_ignore_errors, cov_omit_prefixes)

        if self.failed_slaves:
            terminalwriter.sep('-', 'coverage: failed slaves')
            terminalwriter.write('The following slaves failed to return coverage data, '
                                 'ensure that pytest-cov is installed on these slaves.\n')
            for node in self.failed_slaves:
                terminalwriter.write('%s\n' % node.gateway.id)


class Central(CovController):
    """Implementation for centralised operation."""

    def sessionstart(self, session):
        import coverage
        self.failed_slaves = []
        if session.config.getvalue('cov_config'):
            config_file = session.config.getvalue('cov_config_file')
        else:
            config_file = False
        self.cov = coverage.coverage(data_file=session.config.getvalue('cov_data_file'),
                                     branch=session.config.getvalue('cov_branch'),
                                     cover_pylib=session.config.getvalue('cov_pylib'),
                                     timid=session.config.getvalue('cov_timid'),
                                     config_file=config_file)
        self.cov.erase()
        self.cov.start()

    def sessionfinish(self, session, exitstatus):
        node_desc = 'platform %s, python %s' % (sys.platform, '%s.%s.%s-%s-%s' % sys.version_info[:5])
        self.cov.stop()
        self.cov.save()
        self.covs = [(self.cov, [node_desc])]

    def terminal_summary(self, terminalreporter):
        CovController.terminal_summary(self, terminalreporter)


class DistMaster(CovController):
    """Implementation for distributed master."""

    def sessionstart(self, session):
        self.config = session.config
        self.data_files = {}
        self.failed_slaves = []

        if session.config.getvalue('cov_config'):
            config_file = os.path.realpath(session.config.getvalue('cov_config_file'))
            if os.path.exists(config_file):
                self.config.option.rsyncdir.append(config_file)

    def configure_node(self, node):
        import socket
        node.slaveinput['cov_master_host'] = socket.gethostname()
        node.slaveinput['cov_master_topdir'] = self.config.topdir
        node.slaveinput['cov_master_rsync_roots'] = node.nodemanager.roots

    def testnodedown(self, node, error):
        if not (hasattr(node, 'slaveoutput') and
                'cov_slave_data_file' in node.slaveoutput):
            self.failed_slaves.append(node)
            return

        if 'cov_slave_data_suffix' in node.slaveoutput:
            import coverage
            if self.config.getvalue('cov_config'):
                config_file = self.config.getvalue('cov_config_file')
            else:
                config_file = False
            cov = coverage.coverage(data_file=node.slaveoutput['cov_slave_data_file'],
                                    data_suffix=node.slaveoutput['cov_slave_data_suffix'],
                                    branch=self.config.getvalue('cov_branch'),
                                    cover_pylib=self.config.getvalue('cov_pylib'),
                                    timid=self.config.getvalue('cov_timid'),
                                    config_file=config_file)
            cov.start()
            cov.stop()
            cov.data.lines = node.slaveoutput['cov_slave_lines']
            cov.data.arcs = node.slaveoutput['cov_slave_arcs']
            cov.save()

        rinfo = node.gateway._rinfo()
        node_desc = 'platform %s, python %s' % (rinfo.platform, '%s.%s.%s-%s-%s' % rinfo.version_info)
        node_descs = self.data_files.setdefault(node.slaveoutput['cov_slave_data_file'], set())
        node_descs.add(node_desc)

    def sessionfinish(self, session, exitstatus):
        import coverage
        def combine(data_file):
            if self.config.getvalue('cov_config'):
                config_file = self.config.getvalue('cov_config_file')
            else:
                config_file = False
            cov = coverage.coverage(data_file=data_file,
                                    branch=self.config.getvalue('cov_branch'),
                                    cover_pylib=self.config.getvalue('cov_pylib'),
                                    timid=self.config.getvalue('cov_timid'),
                                    config_file=config_file)
            cov.erase()
            cov.combine()
            cov.save()
            return cov

        self.covs = [(combine(data_file), node_descs) for data_file, node_descs in sorted(self.data_files.items())]

    def terminal_summary(self, terminalreporter):
        CovController.terminal_summary(self, terminalreporter)


class DistSlave(CovController):
    """Implementation for distributed slaves."""

    def sessionstart(self, session):
        import socket
        import coverage

        self.is_collocated = bool(socket.gethostname() == session.config.slaveinput['cov_master_host'] and
                                  session.config.topdir == session.config.slaveinput['cov_master_topdir'])

        if session.config.option.dist == 'each' and not session.config.getvalue('cov_combine_each'):
            node_desc = 'platform_%s_python_%s' % (sys.platform, '%s%s%s%s%s' % sys.version_info[:5])
            self.data_file = '%s_%s' % (session.config.getvalue('cov_data_file'), node_desc)
        else:
            self.data_file = session.config.getvalue('cov_data_file')

        self.data_suffix = session.nodeid

        if session.config.getvalue('cov_config'):
            config_file = session.config.getvalue('cov_config_file')
        else:
            config_file = False
        self.cov = coverage.coverage(data_file=self.data_file,
                                     data_suffix=self.data_suffix,
                                     branch=session.config.getvalue('cov_branch'),
                                     cover_pylib=session.config.getvalue('cov_pylib'),
                                     timid=session.config.getvalue('cov_timid'),
                                     config_file=config_file)
        self.cov.start()

    def sessionfinish(self, session, exitstatus):
        self.cov.stop()

        if self.is_collocated:
            self.cov.save()
            session.config.slaveoutput['cov_slave_data_file'] = self.data_file
        else:
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

            session.config.slaveoutput['cov_slave_data_file'] = self.data_file
            session.config.slaveoutput['cov_slave_data_suffix'] = self.data_suffix
            session.config.slaveoutput['cov_slave_lines'] = lines
            session.config.slaveoutput['cov_slave_arcs'] = arcs

    def terminal_summary(self, terminalreporter):
        pass
