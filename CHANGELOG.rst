Changelog
=========

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
