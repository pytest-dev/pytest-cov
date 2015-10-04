Changelog
=========

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
