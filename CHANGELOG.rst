Changelog
=========

2.0.0 (2015-06-29)
------------------

* Renamed ``--cov-min`` to ``--cov-fail-under`` to be consistent with the new ``fail_under`` option in `coverage-4.0`.
* Changed ``--cov-report=term`` to automatically upgrade to ``--cov-report=term-missing`` if there's ``[run] show_missing = True`` in
  ``.coveragerc``.
* Changed ``--cov-fail-under`` to be automatically activated if there's a ``[report] fail_under = ...`` in ``.coveragerc``.

1.0.0 (2015-06-05)
------------------

* Fixed `.pth` installation to work in all cases (install, easy_install, wheels, develop etc).
* Fixed `.pth` uninstallation to work for wheel installs.
* Reverted the unreleased ``--cov=path`` deprecation.
* Removed the unreleased addition of ``--cov-source=path``.

-----

* Forked from the `2.0` branch of https://github.com/schlamar/pytest-cov/ - fixes include:

  * No need to specify the source anymore via ``--cov``. The source settings from
    ``.coveragerc`` will be used instead.
  * Support for ``--cov-min``.



