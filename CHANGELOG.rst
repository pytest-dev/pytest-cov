Changelog
=========

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
* Changed ``--cov`` so it can be used with no path argument (in wich case the source
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
