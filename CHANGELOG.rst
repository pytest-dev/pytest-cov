Changelog
=========

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



