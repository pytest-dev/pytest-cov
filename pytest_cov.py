"""Coverage plugin for pytest."""


def pytest_addoption(parser):
    """Add options to control coverage."""

    group = parser.getgroup('coverage reporting with distributed testing '
                            'support')
    group.addoption('--cov', action='append', default=[], metavar='path',
                    dest='cov_source',
                    help='measure coverage for filesystem path '
                    '(multi-allowed)')
    group.addoption('--cov-report', action='append', default=[],
                    metavar='type', dest='cov_report',
                    choices=['term', 'term-missing', 'annotate', 'html',
                             'xml'],
                    help='type of report to generate: term, term-missing, '
                    'annotate, html, xml (multi-allowed)')
    group.addoption('--cov-config', action='store', default='.coveragerc',
                    metavar='path', dest='cov_config',
                    help='config file for coverage, default: .coveragerc')
    group.addoption('--no-cov-on-fail', action='store_true', default=False,
                    dest='no_cov_on_fail',
                    help='do not report coverage if test run fails, '
                         'default: False')


def pytest_load_initial_conftests(args, early_config, parser):
    """Activate coverage plugin if appropriate."""
    exists = getattr(early_config, "known_args_namespace", None) is not None
    if not exists: # pragma: no cover
        # this if is a hacky thing for versions of pytest that do not include
        # commit 083d8d0b. once that commit is in latest pytest, this hack can
        # be removed.
        early_config.known_args_namespace = parser.parse_known_args(args)
    ns = early_config.known_args_namespace

    is_dist = getattr(ns, "dist", "no") != "no"

    if ns.cov_source:
        plugin = CovPlugin(dist=is_dist)
        if not is_dist:
            plugin.nondist_start(ns)
        early_config.pluginmanager.register(plugin, '_cov')


class CovPlugin(object):
    """Use coverage package to produce code coverage reports.

    Delegates all work to a particular implementation based on whether
    this test process is centralised, a distributed master or a
    distributed slave.
    """

    def __init__(self, dist):
        """Creates a coverage pytest plugin.

        We read the rc file that coverage uses to get the data file
        name.  This is needed since we give coverage through it's API
        the data file name.
        """

        # Our implementation is unknown at this time.
        self.cov_controller = None
        self.no_cov_on_fail = None
        self.failed = False
        self.dist = dist

    def pytest_sessionstart(self, session):
        """At session start determine our implementation and delegate to it."""
        # coverage will not be measured on conftests correctly when in
        # distributed testing. to fix this, xdist needs to provide us with a
        # reliable way of determining if we're in it and whether we're master
        # or slave, and said reliable way must be available in
        # pytest_load_initial_conftests.

        if not self.dist:
            return

        import cov_core

        session_name = session.__class__.__name__
        is_master = (session.config.pluginmanager.hasplugin('dsession') or
                     session_name == 'DSession')
        is_slave = (hasattr(session.config, 'slaveinput') or
                    session_name == 'SlaveSession')
        nodeid = None

        if is_master:
            controller_cls = cov_core.DistMaster
        else:
            assert is_slave
            controller_cls = cov_core.DistSlave
            nodeid = session.config.slaveinput.get('slaveid',
                                                   getattr(session, 'nodeid'))

        self.start(
            session.config.options,
            controller_cls,
            session.config,
            nodeid
        )

    def nondist_start(self, options):
        import cov_core
        self.start(options, cov_core.Central)

    def start(self, options, controller_cls, config=None, nodeid=None):
        self.no_cov_on_fail = options.no_cov_on_fail
        self.cov_controller = controller_cls(
            options.cov_source,
            options.cov_report or ['term'],
            options.cov_config,
            config,
            nodeid
        )

        self.cov_controller.start()

    def pytest_configure_node(self, node):
        """Delegate to our implementation.

        Mark this hook as optional in case xdist is not installed.
        """

        self.cov_controller.configure_node(node)
    pytest_configure_node.optionalhook = True

    def pytest_testnodedown(self, node, error):
        """Delegate to our implementation.

        Mark this hook as optional in case xdist is not installed.
        """

        self.cov_controller.testnodedown(node, error)
    pytest_testnodedown.optionalhook = True

    def pytest_sessionfinish(self, session, exitstatus):
        """Delegate to our implementation."""
        self.failed = exitstatus != 0
        self.cov_controller.finish()

    def pytest_terminal_summary(self, terminalreporter):
        """Delegate to our implementation."""
        if not (self.failed and self.no_cov_on_fail):
            self.cov_controller.summary(terminalreporter._tw)


def pytest_funcarg__cov(request):
    """A pytest funcarg that provides access to the underlying coverage
    object.
    """

    # Check with hasplugin to avoid getplugin exception in older pytest.
    if request.config.pluginmanager.hasplugin('_cov'):
        plugin = request.config.pluginmanager.getplugin('_cov')
        if plugin.cov_controller:
            return plugin.cov_controller.cov
    return None
