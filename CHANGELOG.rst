Changelog
=========

2.10.1 (2020-06-??)
-------------------

* Support for ``pytest-xdist`` 2.0, which breaks compatibility with ``pytest-xdist`` before 1.22.3 (from 2017).
  Contributed by Zac Hatfield-Dodds in `#412 <https://github.com/pytest-dev/pytest-cov/pull/412>`_.

2.10.0 (2020-06-12)
-------------------

* Improved the ``--no-cov`` warning. Now it's only shown if ``--no-cov`` is present before ``--cov``.
* Removed legacy pytest support. Changed ``setup.py`` so that ``pytest>=4.6`` is required.

2.9.0 (2020-05-22)
------------------

* Fixed ``RemovedInPytest4Warning`` when using Pytest 3.10.
  Contributed by Michael Manganiello in `#354 <https://github.com/pytest-dev/pytest-cov/pull/354>`_.
* Made pytest startup faster when plugin not active by lazy-importing.
  Contributed by Anders Hovmöller in `#339 <https://github.com/pytest-dev/pytest-cov/pull/339>`_.
* Various CI improvements.
  Contributed by Daniel Hahler in `#363 <https://github.com/pytest-dev/pytest-cov/pull/>`_ and
  `#364 <https://github.com/pytest-dev/pytest-cov/pull/364>`_.
* Various Python support updates (drop EOL 3.4, test against 3.8 final).
  Contributed by Hugo van Kemenade in
  `#336 <https://github.com/pytest-dev/pytest-cov/pull/336>`_ and
  `#367 <https://github.com/pytest-dev/pytest-cov/pull/367>`_.
* Changed ``--cov-append`` to always enable ``data_suffix`` (a coverage setting).
  Contributed by Harm Geerts in
  `#387 <https://github.com/pytest-dev/pytest-cov/pull/387>`_.
* Changed ``--cov-append`` to handle loading previous data better
  (fixes various path aliasing issues).
* Various other testing improvements, github issue templates, example updates.
* Fixed internal failures that are caused by tests that change the current working directory by
  ensuring a consistent working directory when coverage is called.
  See `#306 <https://github.com/pytest-dev/pytest-cov/issues/306>`_ and
  `coveragepy#881 <https://github.com/nedbat/coveragepy/issues/881>`_

2.8.1 (2019-10-05)
------------------

* Fixed `#348 <https://github.com/pytest-dev/pytest-cov/issues/348>`_ -
  regression when only certain reports (html or xml) are used then ``--cov-fail-under`` always fails.

2.8.0 (2019-10-04)
------------------

* Fixed ``RecursionError`` that can occur when using
  `cleanup_on_signal <https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html#if-you-got-custom-signal-handling>`__ or
  `cleanup_on_sigterm <https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html#if-you-got-custom-signal-handling>`__.
  See: `#294 <https://github.com/pytest-dev/pytest-cov/issues/294>`_.
  The 2.7.x releases of pytest-cov should be considered broken regarding aforementioned cleanup API.
* Added compatibility with future xdist release that deprecates some internals
  (match pytest-xdist master/worker terminology).
  Contributed by Thomas Grainger in `#321 <https://github.com/pytest-dev/pytest-cov/pull/321>`_
* Fixed breakage that occurs when multiple reporting options are used.
  Contributed by Thomas Grainger in `#338 <https://github.com/pytest-dev/pytest-cov/pull/338>`_.
* Changed internals to use a stub instead of ``os.devnull``.
  Contributed by Thomas Grainger in `#332 <https://github.com/pytest-dev/pytest-cov/pull/332>`_.
* Added support for Coverage 5.0.
  Contributed by Ned Batchelder in `#319 <https://github.com/pytest-dev/pytest-cov/pull/319>`_.
* Added support for float values in ``--cov-fail-under``.
  Contributed by Martín Gaitán in `#311 <https://github.com/pytest-dev/pytest-cov/pull/311>`_.
* Various documentation fixes. Contributed by
  Juanjo Bazán,
  Andrew Murray and
  Albert Tugushev in
  `#298 <https://github.com/pytest-dev/pytest-cov/pull/298>`_,
  `#299 <https://github.com/pytest-dev/pytest-cov/pull/299>`_ and
  `#307 <https://github.com/pytest-dev/pytest-cov/pull/307>`_.
* Various testing improvements. Contributed by
  Ned Batchelder,
  Daniel Hahler,
  Ionel Cristian Mărieș and
  Hugo van Kemenade in
  `#313 <https://github.com/pytest-dev/pytest-cov/pull/313>`_,
  `#314 <https://github.com/pytest-dev/pytest-cov/pull/314>`_,
  `#315 <https://github.com/pytest-dev/pytest-cov/pull/315>`_,
  `#316 <https://github.com/pytest-dev/pytest-cov/pull/316>`_,
  `#325 <https://github.com/pytest-dev/pytest-cov/pull/325>`_,
  `#326 <https://github.com/pytest-dev/pytest-cov/pull/326>`_,
  `#334 <https://github.com/pytest-dev/pytest-cov/pull/334>`_ and
  `#335 <https://github.com/pytest-dev/pytest-cov/pull/335>`_.
* Added the ``--cov-context`` CLI options that enables coverage contexts. Only works with coverage 5.0+.
  Contributed by Ned Batchelder in `#345 <https://github.com/pytest-dev/pytest-cov/pull/345>`_.

2.7.1 (2019-05-03)
------------------

* Fixed source distribution manifest so that garbage ain't included in the tarball.

2.7.0 (2019-05-03)
------------------

* Fixed ``AttributeError: 'NoneType' object has no attribute 'configure_node'`` error when ``--no-cov`` is used.
  Contributed by Alexander Shadchin in `#263 <https://github.com/pytest-dev/pytest-cov/pull/263>`_.
* Various testing and CI improvements. Contributed by Daniel Hahler in
  `#255 <https://github.com/pytest-dev/pytest-cov/pull/255>`_,
  `#266 <https://github.com/pytest-dev/pytest-cov/pull/266>`_,
  `#272 <https://github.com/pytest-dev/pytest-cov/pull/272>`_,
  `#271 <https://github.com/pytest-dev/pytest-cov/pull/271>`_ and
  `#269 <https://github.com/pytest-dev/pytest-cov/pull/269>`_.
* Improved documentation regarding subprocess and multiprocessing.
  Contributed in `#265 <https://github.com/pytest-dev/pytest-cov/pull/265>`_.
* Improved ``pytest_cov.embed.cleanup_on_sigterm`` to be reentrant (signal deliveries while signal handling is
  running won't break stuff).
* Added ``pytest_cov.embed.cleanup_on_signal`` for customized cleanup.
* Improved cleanup code and fixed various issues with leftover data files. All contributed in
  `#265 <https://github.com/pytest-dev/pytest-cov/pull/265>`_ or
  `#262 <https://github.com/pytest-dev/pytest-cov/pull/262>`_.
* Improved examples. Now there are two examples for the common project layouts, complete with working coverage
  configuration. The examples have CI testing. Contributed in
  `#267 <https://github.com/pytest-dev/pytest-cov/pull/267>`_.
* Improved help text for CLI options.

2.6.1 (2019-01-07)
------------------

* Added support for Pytest 4.1. Contributed by Daniel Hahler and Семён Марьясин in
  `#253 <https://github.com/pytest-dev/pytest-cov/pull/253>`_ and
  `#230 <https://github.com/pytest-dev/pytest-cov/pull/230>`_.
* Various test and docs fixes. Contributed by Daniel Hahler in
  `#224 <https://github.com/pytest-dev/pytest-cov/pull/224>`_ and
  `#223 <https://github.com/pytest-dev/pytest-cov/pull/223>`_.
* Fixed the "Module already imported" issue (`#211 <https://github.com/pytest-dev/pytest-cov/issues/211>`_).
  Contributed by Daniel Hahler in `#228 <https://github.com/pytest-dev/pytest-cov/pull/228>`_.

2.6.0 (2018-09-03)
------------------

* Dropped support for Python < 3.4, Pytest < 3.5 and Coverage < 4.4.
* Fixed some documentation formatting. Contributed by Jean Jordaan and Julian.
* Added an example with ``addopts`` in documentation. Contributed by Samuel Giffard in
  `#195 <https://github.com/pytest-dev/pytest-cov/pull/195>`_.
* Fixed ``TypeError: 'NoneType' object is not iterable`` in certain xdist configurations. Contributed by Jeremy Bowman in
  `#213 <https://github.com/pytest-dev/pytest-cov/pull/213>`_.
* Added a ``no_cover`` marker and fixture. Fixes
  `#78 <https://github.com/pytest-dev/pytest-cov/issues/78>`_.
* Fixed broken ``no_cover`` check when running doctests. Contributed by Terence Honles in
  `#200 <https://github.com/pytest-dev/pytest-cov/pull/200>`_.
* Fixed various issues with path normalization in reports (when combining coverage data from parallel mode). Fixes
  `#130 <https://github.com/pytest-dev/pytest-cov/issues/161>`_.
  Contributed by Ryan Hiebert & Ionel Cristian Mărieș in
  `#178 <https://github.com/pytest-dev/pytest-cov/pull/178>`_.
* Report generation failures don't raise exceptions anymore. A warning will be logged instead. Fixes
  `#161 <https://github.com/pytest-dev/pytest-cov/issues/161>`_.
* Fixed multiprocessing issue on Windows (empty env vars are not passed). Fixes
  `#165 <https://github.com/pytest-dev/pytest-cov/issues/165>`_.

2.5.1 (2017-05-11)
------------------

* Fixed xdist breakage (regression in ``2.5.0``).
  Fixes `#157 <https://github.com/pytest-dev/pytest-cov/issues/157>`_.
* Allow setting custom ``data_file`` name in ``.coveragerc``.
  Fixes `#145 <https://github.com/pytest-dev/pytest-cov/issues/145>`_.
  Contributed by Jannis Leidel & Ionel Cristian Mărieș in
  `#156 <https://github.com/pytest-dev/pytest-cov/pull/156>`_.

2.5.0 (2017-05-09)
------------------

* Always show a summary when ``--cov-fail-under`` is used. Contributed by Francis Niu in `PR#141
  <https://github.com/pytest-dev/pytest-cov/pull/141>`_.
* Added ``--cov-branch`` option. Fixes `#85 <https://github.com/pytest-dev/pytest-cov/issues/85>`_.
* Improve exception handling in subprocess setup. Fixes `#144 <https://github.com/pytest-dev/pytest-cov/issues/144>`_.
* Fixed handling when ``--cov`` is used multiple times. Fixes `#151 <https://github.com/pytest-dev/pytest-cov/issues/151>`_.

2.4.0 (2016-10-10)
------------------

* Added a "disarm" option: ``--no-cov``. It will disable coverage measurements. Contributed by Zoltan Kozma in
  `PR#135 <https://github.com/pytest-dev/pytest-cov/pull/135>`_.

  **WARNING: Do not put this in your configuration files, it's meant to be an one-off for situations where you want to
  disable coverage from command line.**
* Fixed broken exception handling on ``.pth`` file. See `#136 <https://github.com/pytest-dev/pytest-cov/issues/136>`_.

2.3.1 (2016-08-07)
------------------

* Fixed regression causing spurious errors when xdist was used. See `#124
  <https://github.com/pytest-dev/pytest-cov/issues/124>`_.
* Fixed DeprecationWarning about incorrect `addoption` use. Contributed by Florian Bruhin in `PR#127
  <https://github.com/pytest-dev/pytest-cov/pull/127>`_.
* Fixed deprecated use of funcarg fixture API. Contributed by Daniel Hahler in `PR#125
  <https://github.com/pytest-dev/pytest-cov/pull/125>`_.

2.3.0 (2016-07-05)
------------------

* Add support for specifying output location for html, xml, and annotate report.
  Contributed by Patrick Lannigan in `PR#113 <https://github.com/pytest-dev/pytest-cov/pull/113>`_.
* Fix bug hiding test failure when cov-fail-under failed.
* For coverage >= 4.0, match the default behaviour of `coverage report` and
  error if coverage fails to find the source instead of just printing a warning.
  Contributed by David Szotten in `PR#116 <https://github.com/pytest-dev/pytest-cov/pull/116>`_.
* Fixed bug occurred when bare ``--cov`` parameter was used with xdist.
  Contributed by Michael Elovskikh in `PR#120 <https://github.com/pytest-dev/pytest-cov/pull/120>`_.
* Add support for ``skip_covered`` and added ``--cov-report=term-skip-covered`` command
  line options. Contributed by Saurabh Kumar in `PR#115 <https://github.com/pytest-dev/pytest-cov/pull/115>`_.

2.2.1 (2016-01-30)
------------------

* Fixed incorrect merging of coverage data when xdist was used and coverage was ``>= 4.0``.

2.2.0 (2015-10-04)
------------------

* Added support for changing working directory in tests. Previously changing working
  directory would disable coverage measurements in suprocesses.
* Fixed broken handling for ``--cov-report=annotate``.

2.1.0 (2015-08-23)
------------------

* Added support for `coverage 4.0b2`.
* Added the ``--cov-append`` command line options. Contributed by Christian Ledermann
  in `PR#80 <https://github.com/pytest-dev/pytest-cov/pull/80>`_.

2.0.0 (2015-07-28)
------------------

* Added ``--cov-fail-under``, akin to the new ``fail_under`` option in `coverage-4.0`
  (automatically activated if there's a ``[report] fail_under = ...`` in ``.coveragerc``).
* Changed ``--cov-report=term`` to automatically upgrade to ``--cov-report=term-missing``
  if there's ``[run] show_missing = True`` in ``.coveragerc``.
* Changed ``--cov`` so it can be used with no path argument (in which case the source
  settings from ``.coveragerc`` will be used instead).
* Fixed `.pth` installation to work in all cases (install, easy_install, wheels, develop etc).
* Fixed `.pth` uninstallation to work for wheel installs.
* Support for coverage 4.0.
* Data file suffixing changed to use coverage's ``data_suffix=True`` option (instead of the
  custom suffixing).
* Avoid warning about missing coverage data (just like ``coverage.control.process_startup``).
* Fixed a race condition when running with xdist (all the workers tried to combine the files).
  It's possible that this issue is not present in `pytest-cov 1.8.X`.

1.8.2 (2014-11-06)
------------------

* N/A
