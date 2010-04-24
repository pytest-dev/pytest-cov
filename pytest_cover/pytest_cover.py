"""produce code coverage reports using the 'coverage' package.

This plugin supports pytest's distributed testing feature in both load
and each modes.  Of course it also support centralised testing.

It supports pretty much all features offered by the coverage package.

Each test run with coverage activated may produce any combination of
the four report types.  There is the terminal report output by pytest,
annotated source code, HTML and XML reports.


Installation
------------

The `pytest-cover pypi`_ package may be installed / uninstalled with pip::

    pip install pytest-cover
    pip uninstall pytest-cover

Alternatively easy_install can be used::

    easy_install pytest-cover

.. _`pytest-cover pypi`: http://pypi.python.org/pypi/pytest-cover/


Usage
-----

Running centralised testing::

    py.test --cover myproj tests/

Shows a terminal report::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Distributed testing with dist mode set to load and branch coverage
enabled::

    py.test -n 2 --cover myproj --cover-branch tests/

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

    py.test --cover myproj --dist=each
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

    py.test --cover myproj --cover-combine-each --dist=each
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

Currently for distributed testing the python used by slaves must have
pytest-cover installed in order to operate.  This is because the
plugin must be registered through setuptools / distribute for pytest
to start the plugin on the slave.  Hopefully this will change in the
not to distant future, such that just like pytest-xdist only python
and nothing else is required on the slave side.

Currently the coverage rc file is not rsynced to slaves which can
result in different behaviour on the slaves.  Use command line options
for the time being.

This is an initial release developed on python 2.6 and support for
other python versions needs to be checked and fixed.  Hence for the
time being distributed testing in each mode may be a bit limited in
usefulness.


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

    group = parser.getgroup('coverage based coverage reporting')
    group.addoption('--cover-on', action='store_true', default=False,
                    dest='cover_on',
                    help='enable coverage, only needed if not specifying any --cover options')
    group.addoption('--cover', action='append', default=[], metavar='package',
                    dest='cover_packages',
                    help='collect coverage for the specified package (multi-allowed)')
    group.addoption('--cover-no-terminal', action='store_false', default=True,
                    dest='cover_terminal',
                    help='disable printing a report on the terminal')
    group.addoption('--cover-annotate', action='store_true', default=False,
                    dest='cover_annotate',
                    help='generate an annotated source code report')
    group.addoption('--cover-html', action='store_true', default=False,
                    dest='cover_html',
                    help='generate a html report')
    group.addoption('--cover-xml', action='store_true', default=False,
                    dest='cover_xml',
                    help='generate an xml report')
    group.addoption('--cover-annotate-dir', action='store', default='coverage_annotate', metavar='dir',
                    dest='cover_annotate_dir',
                    help='directory for the annotate report, default: %default')
    group.addoption('--cover-html-dir', action='store', default=None, metavar='dir',
                    dest='cover_html_dir',
                    help='directory for the html report, default: coverage_html')
    group.addoption('--cover-xml-file', action='store', default=None, metavar='path',
                    dest='cover_xml_file',
                    help='file for the xml report, default: coverage.xml')
    group.addoption('--cover-data-file', action='store', default=None, metavar='path',
                    dest='cover_data_file',
                    help='file containing coverage data, default: .coverage')
    group.addoption('--cover-combine-each', action='store_true', default=False,
                    dest='cover_combine_each',
                    help='for dist=each mode produce a single combined report')
    group.addoption('--cover-branch', action='store_true', default=None,
                    dest='cover_branch',
                    help='enable branch coverage')
    group.addoption('--cover-pylib', action='store_true', default=None,
                    dest='cover_pylib',
                    help='enable python library coverage')
    group.addoption('--cover-timid', action='store_true', default=None,
                    dest='cover_timid',
                    help='enable slower and simpler tracing')
    group.addoption('--cover-no-missing-lines', action='store_false', default=True,
                    dest='cover_show_missing',
                    help='disable showing missing lines, only relevant to the terminal report')
    group.addoption('--cover-no-missing-files', action='store_true', default=None,
                    dest='cover_ignore_errors',
                    help='disable showing message about missing source files')
    group.addoption('--cover-omit', action='store', default=None, metavar='prefix1,prefix2,...',
                    dest='cover_omit_prefixes',
                    help='ignore files with these prefixes')
    group.addoption('--cover-no-config', action='store_false', default=True,
                    dest='cover_config',
                    help='disable coverage reading its config file')
    group.addoption('--cover-config-file', action='store', default='.coveragerc', metavar='path',
                    dest='cover_config_file',
                    help='config file for coverage, default: %default')


def pytest_configure(config):
    """Activate coverage plugin if appropriate."""

    if config.getvalue('cover_on') or config.getvalue('cover_packages'):
        config.pluginmanager.register(CoverPlugin(config), '_cover')


class CoverPlugin(object):
    """Use coverage module to produce code coverage reports.

    Delegates all work to a particular implementation based on whether
    this test process is centralised, a distributed master or a
    distributed slave.
    """

    def __init__(self, config):
        self.config = config
        self.cover_controller = None

        # Maintain same behaviour as coverage for some of our options.
        # This ensures that users can rely on coverage rc file and env
        # vars.
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser

        parser = configparser.RawConfigParser()
        parser.read(self.config.getvalue('cover_config_file'))
        for default, section, item, env_var, option in (
            ('coverage_html', 'html', 'directory', None           , 'cover_html_dir' ),
            ('coverage.xml' , 'xml' , 'output'   , None           , 'cover_xml_file' ),
            ('.coverage'    , 'run' , 'data_file', 'COVERAGE_FILE', 'cover_data_file')):

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
        self.cover_controller = CoverController.create_from_session(session)
        self.cover_controller.sessionstart(session)

    def pytest_configure_node(self, node):
        self.cover_controller.configure_node(node)

    def pytest_testnodedown(self, node, error):
        self.cover_controller.testnodedown(node, error)

    def pytest_sessionfinish(self, session, exitstatus):
        self.cover_controller.sessionfinish(session, exitstatus)

    def pytest_terminal_summary(self, terminalreporter):
        self.cover_controller.terminal_summary(terminalreporter)


class CoverController(object):
    """Base class for different plugin implementations.

    Responsible for creating appropriate implementation based on type
    of session.

    Responsible for final outputting of coverage reports.
    """

    @staticmethod
    def create_from_session(session):
        name_to_cls = dict(Session=Central,
                           DSession=DistMaster,
                           SlaveNode=DistSlave)
        session_name = session.__class__.__name__
        controller_cls = name_to_cls.get(session_name, Central)
        return controller_cls()

    def terminal_summary(self, terminalreporter):
        config = terminalreporter.config

        cover_packages = config.getvalue('cover_packages')
        cover_terminal = config.getvalue('cover_terminal')
        cover_annotate = config.getvalue('cover_annotate')
        cover_html = config.getvalue('cover_html')
        cover_xml = config.getvalue('cover_xml')
        cover_annotate_dir = config.getvalue('cover_annotate_dir')
        cover_html_dir = config.getvalue('cover_html_dir')
        cover_xml_file = config.getvalue('cover_xml_file')
        cover_show_missing = config.getvalue('cover_show_missing')
        cover_ignore_errors = config.getvalue('cover_ignore_errors')
        cover_omit_prefixes = config.getvalue('cover_omit_prefixes')
        if cover_omit_prefixes:
            cover_omit_prefixes = cover_omit_prefixes.split(',')

        morfs = list(set(module.__file__
                         for name, module in sys.modules.items()
                         for package in cover_packages
                         if hasattr(module, '__file__') and name.startswith(package)))

        for cover, node_descs in self.covers:

            if cover_terminal:
                terminalwriter = terminalreporter._tw
                if len(node_descs) == 1:
                    terminalwriter.sep('-', 'coverage: %s' % ''.join(node_descs))
                else:
                    terminalwriter.sep('-', 'coverage')
                    for node_desc in node_descs:
                        terminalwriter.sep(' ', '%s' % node_desc)
                cover.report(morfs, cover_show_missing, cover_ignore_errors, terminalwriter, cover_omit_prefixes)

            if cover_annotate or cover_html or cover_xml:

                suffix = None
                if len(self.covers) > 1:
                    suffix = '_'.join(node_descs)
                    replacements = [(' ', '_'), (',', ''), ('.', ''), ('-', '')]
                    suffix = reduce(lambda suffix, oldnew: suffix.replace(oldnew[0], oldnew[1]), replacements, suffix)

                if cover_annotate:
                    dir = '%s_%s' % (cover_annotate_dir, suffix) if suffix else cover_annotate_dir
                    cover.annotate(morfs, dir, cover_ignore_errors, cover_omit_prefixes)

                if cover_html:
                    dir = '%s_%s' % (cover_html_dir, suffix) if suffix else cover_html_dir
                    cover.html_report(morfs, dir, cover_ignore_errors, cover_omit_prefixes)

                if cover_xml:
                    root, ext = os.path.splitext(cover_xml_file)
                    xml_file = '%s_%s%s' % (root, suffix, ext) if suffix else cover_xml_file
                    cover.xml_report(morfs, xml_file, cover_ignore_errors, cover_omit_prefixes)


class Central(CoverController):
    """Implementation for centralised operation."""

    def sessionstart(self, session):
        import coverage
        config_file = session.config.getvalue('cover_config_file') if session.config.getvalue('cover_config') else False
        self.cover = coverage.coverage(data_file=session.config.getvalue('cover_data_file'),
                                       branch=session.config.getvalue('cover_branch'),
                                       cover_pylib=session.config.getvalue('cover_pylib'),
                                       timid=session.config.getvalue('cover_timid'),
                                       config_file=config_file)
        self.cover.erase()
        self.cover.start()

    def sessionfinish(self, session, exitstatus):
        node_desc = 'platform %s, python %s' % (sys.platform, '%s.%s.%s-%s-%s' % sys.version_info)
        self.cover.stop()
        self.cover.save()
        self.covers = [(self.cover, [node_desc])]

    def terminal_summary(self, terminalreporter):
        CoverController.terminal_summary(self, terminalreporter)


class DistMaster(CoverController):
    """Implementation for distributed master."""

    def sessionstart(self, session):
        self.config = session.config
        self.data_files = {}

    def configure_node(self, node):
        import socket
        node.slaveinput['coverage_master_host'] = socket.gethostname()
        node.slaveinput['coverage_master_topdir'] = self.config.topdir
        node.slaveinput['coverage_master_rsync_roots'] = node.nodemanager.roots

    def testnodedown(self, node, error):
        if 'coverage_data_suffix' in node.slaveoutput:
            import coverage
            config_file = self.config.getvalue('cover_config_file') if self.config.getvalue('cover_config') else False
            cover = coverage.coverage(data_file=node.slaveoutput['coverage_data_file'],
                                      data_suffix=node.slaveoutput['coverage_data_suffix'],
                                      branch=self.config.getvalue('cover_branch'),
                                      cover_pylib=self.config.getvalue('cover_pylib'),
                                      timid=self.config.getvalue('cover_timid'),
                                      config_file=config_file)
            cover.start()
            cover.stop()
            cover.data.lines = node.slaveoutput['coverage_lines']
            cover.data.arcs = node.slaveoutput['coverage_arcs']
            cover.save()

        rinfo = node.gateway._rinfo()
        node_desc = 'platform %s, python %s' % (rinfo.platform, '%s.%s.%s-%s-%s' % rinfo.version_info)
        node_descs = self.data_files.setdefault(node.slaveoutput['coverage_data_file'], set())
        node_descs.add(node_desc)

    def sessionfinish(self, session, exitstatus):
        import coverage
        def combine(data_file):
            config_file = self.config.getvalue('cover_config_file') if self.config.getvalue('cover_config') else False
            cover = coverage.coverage(data_file=data_file,
                                      branch=self.config.getvalue('cover_branch'),
                                      cover_pylib=self.config.getvalue('cover_pylib'),
                                      timid=self.config.getvalue('cover_timid'),
                                      config_file=config_file)
            cover.erase()
            cover.combine()
            cover.save()
            return cover

        self.covers = [(combine(data_file), node_descs) for data_file, node_descs in sorted(self.data_files.items())]

    def terminal_summary(self, terminalreporter):
        CoverController.terminal_summary(self, terminalreporter)


class DistSlave(CoverController):
    """Implementation for distributed slaves."""

    def sessionstart(self, session):
        import uuid
        import socket
        import coverage

        self.is_collocated = bool(socket.gethostname() == session.config.slaveinput['coverage_master_host'] and
                                  session.config.topdir == session.config.slaveinput['coverage_master_topdir'])

        if session.config.option.dist == 'each' and not session.config.getvalue('cover_combine_each'):
            node_desc = 'platform_%s_python_%s' % (sys.platform, '%s%s%s%s%s' % sys.version_info)
            self.data_file = '%s_%s' % (session.config.getvalue('cover_data_file'), node_desc)
        else:
            self.data_file = session.config.getvalue('cover_data_file')

        self.data_suffix = uuid.uuid1().hex

        config_file = session.config.getvalue('cover_config_file') if session.config.getvalue('cover_config') else False
        self.cover = coverage.coverage(data_file=self.data_file,
                                       data_suffix=self.data_suffix,
                                       branch=session.config.getvalue('cover_branch'),
                                       cover_pylib=session.config.getvalue('cover_pylib'),
                                       timid=session.config.getvalue('cover_timid'),
                                       config_file=config_file)
        self.cover.start()

    def sessionfinish(self, session, exitstatus):
        self.cover.stop()

        if self.is_collocated:
            self.cover.save()
            session.config.slaveoutput['coverage_data_file'] = self.data_file
        else:
            slave_topdir = session.config.topdir
            path_rewrites = [(str(slave_topdir.join(rsync_root.basename)), str(rsync_root))
                             for rsync_root in session.config.slaveinput['coverage_master_rsync_roots']]
            path_rewrites.append((str(session.config.topdir), str(session.config.slaveinput['coverage_master_topdir'])))

            def rewrite_path(filename):
                return reduce(lambda filename, slavemaster: filename.replace(slavemaster[0], slavemaster[1]),
                              path_rewrites,
                              filename)
            lines = dict((rewrite_path(filename), data) for filename, data in self.cover.data.lines.items())
            arcs = dict((rewrite_path(filename), data) for filename, data in self.cover.data.arcs.items())

            session.config.slaveoutput['coverage_data_file'] = self.data_file
            session.config.slaveoutput['coverage_data_suffix'] = self.data_suffix
            session.config.slaveoutput['coverage_lines'] = lines
            session.config.slaveoutput['coverage_arcs'] = arcs

    def terminal_summary(self, terminalreporter):
        pass
