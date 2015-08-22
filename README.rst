===============================
pytest-cov
===============================

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
    * - package
      - |version| |downloads|

.. |docs| image:: https://readthedocs.org/projects/pytest-cov/badge/?style=flat
    :target: https://readthedocs.org/projects/pytest-cov
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/pytest-dev/pytest-cov.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/pytest-dev/pytest-cov

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/pytest-dev/pytest-cov?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/pytestbot/pytest-cov

.. |coveralls| image:: https://img.shields.io/coveralls/pytest-dev/pytest-cov/master.svg?style=flat&label=Coveralls
    :alt: Coverage Status
    :target: https://coveralls.io/r/pytest-dev/pytest-cov

.. |codecov| image:: https://img.shields.io/codecov/c/github/pytest-dev/pytest-cov/master.svg?style=flat&label=Codecov
    :alt: Coverage Status
    :target: https://codecov.io/github/pytest-dev/pytest-cov

.. |requires| image:: https://requires.io/github/pytest-dev/pytest-cov/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/pytest-dev/pytest-cov/requirements/?branch=master

.. |landscape| image:: https://landscape.io/github/pytest-dev/pytest-cov/master/landscape.svg?style=flat
    :target: https://landscape.io/github/pytest-dev/pytest-cov/master
    :alt: Code Quality Status

.. |version| image:: https://img.shields.io/pypi/v/pytest-cov.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pytest-cov

.. |downloads| image:: https://img.shields.io/pypi/dm/pytest-cov.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/pytest-cov

.. |wheel| image:: https://pypip.in/wheel/pytest-cov/badge.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/pytest-cov

.. |supported-versions| image:: https://pypip.in/py_versions/pytest-cov/badge.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pytest-cov

.. |supported-implementations| image:: https://pypip.in/implementation/pytest-cov/badge.svg?style=flat
    :alt: Supported imlementations
    :target: https://pypi.python.org/pypi/pytest-cov

.. |scrutinizer| image:: https://img.shields.io/scrutinizer/g/pytest-dev/pytest-cov/master.svg?style=flat
    :alt: Scrutinizer Status
    :target: https://scrutinizer-ci.com/g/pytest-dev/pytest-cov/

Pytest plugin for measuring coverage.

* Free software: MIT license

This plugin produces coverage reports.  It supports centralised testing and distributed testing in
both load and each modes.  It also supports coverage of subprocesses.

All features offered by the coverage package should be available, either through pytest-cov or
through coverage's config file.


Installation
============

Install with pip::

    pip install pytest-cov

For distributed testing support install pytest-xdist::

    pip install pytest-xdist

Upgrade
=======

`pytest-cov 2.0` is using a new ``.pth`` file (``pytest-cov.pth``). You may want to manually remove the older
``init_cov_core.pth`` from site-packages as it's not automatically removed.

Uninstallation
==============

Uninstall with pip::

    pip uninstall pytest-cov

Under certain scenarios a stray ``.pth`` file may be left around in site-packages.

* `pytest-cov 2.0` may leave a ``pytest-cov.pth`` if you installed without wheels
  (``easy_install``, ``setup.py install`` etc).
* `pytest-cov 1.8 or older` will leave a ``init_cov_core.pth``.

Usage
=====

Centralised Testing
-------------------

Centralised testing will report on the combined coverage of the main process and all of it's
subprocesses.

Running centralised testing::

    py.test --cov=myproj tests/

Shows a terminal report::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%


Distributed Testing: Load
-------------------------

Distributed testing with dist mode set to load will report on the combined coverage of all slaves.
The slaves may be spread out over any number of hosts and each slave may be located anywhere on the
file system.  Each slave will have it's subprocesses measured.

Running distributed testing with dist mode set to load::

    py.test --cov=myproj -n 2 tests/

Shows a terminal report::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%


Again but spread over different hosts and different directories::

    py.test --cov=myproj --dist load
            --tx ssh=memedough@host1//chdir=testenv1
            --tx ssh=memedough@host2//chdir=/tmp/testenv2//python=/tmp/env1/bin/python
            --rsyncdir myproj --rsyncdir tests --rsync examples
            tests/

Shows a terminal report::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%


Distributed Testing: Each
-------------------------

Distributed testing with dist mode set to each will report on the combined coverage of all slaves.
Since each slave is running all tests this allows generating a combined coverage report for multiple
environments.

Running distributed testing with dist mode set to each::

    py.test --cov=myproj --dist each
            --tx popen//chdir=/tmp/testenv3//python=/usr/local/python27/bin/python
            --tx ssh=memedough@host2//chdir=/tmp/testenv4//python=/tmp/env2/bin/python
            --rsyncdir myproj --rsyncdir tests --rsync examples
            tests/

Shows a terminal report::

    ---------------------------------------- coverage ----------------------------------------
                              platform linux2, python 2.6.5-final-0
                              platform linux2, python 2.7.0-final-0
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%


Reporting
=========

It is possible to generate any combination of the reports for a single test run.

The available reports are terminal (with or without missing line numbers shown), HTML, XML and
annotated source code.

The terminal report without line numbers (default)::

    py.test --cov-report term --cov=myproj tests/

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%


The terminal report with line numbers::

    py.test --cov-report term-missing --cov=myproj tests/

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94      7    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353     20    94%


These three report options output to files without showing anything on the terminal::

    py.test --cov-report html
            --cov-report xml
            --cov-report annotate
            --cov=myproj tests/

The final report option can also suppress printing to the terminal::

    py.test --cov-report= --cov=myproj tests/

This mode can be especially useful on continuous integration servers, where a coverage file
is needed for subsequent processing, but no local report needs to be viewed. For example,
tests run on Travis-CI could produce a .coverage file for use with Coveralls.

Coverage Data File
==================

The data file is erased at the beginning of testing to ensure clean data for each test run. If you
need to combine the overage of several test runs you can use the ``--cov-append`` option to append
this coverage data to coverage data from previous test runs.

The data file is left at the end of testing so that it is possible to use normal coverage tools to
examine it.


Coverage Config File
====================

This plugin provides a clean minimal set of command line options that are added to pytest.  For
further control of coverage use a coverage config file.

For example if tests are contained within the directory tree being measured the tests may be
excluded if desired by using a .coveragerc file with the omit option set::

    py.test --cov-config .coveragerc
            --cov=myproj
            myproj/tests/

Where the .coveragerc file contains file globs::

    [run]
    omit = tests/*

For full details refer to the `coverage config file`_ documentation.

.. _`coverage config file`: http://nedbatchelder.com/code/coverage/config.html

Note that this plugin controls some options and setting the option in the config file will have no
effect.  These include specifying source to be measured (source option) and all data file handling
(data_file and parallel options).

Limitations
===========

For distributed testing the slaves must have the pytest-cov package installed.  This is needed since
the plugin must be registered through setuptools for pytest to start the plugin on the
slave.

For subprocess measurement environment variables must make it from the main process to the
subprocess.  The python used by the subprocess must have pytest-cov installed.  The subprocess must
do normal site initialisation so that the environment variables can be detected and coverage
started.

Acknowledgements
================

Whilst this plugin has been built fresh from the ground up it has been influenced by the work done
on pytest-coverage (Ross Lawley, James Mills, Holger Krekel) and nose-cover (Jason Pellerin) which are
other coverage plugins.

Ned Batchelder for coverage and its ability to combine the coverage results of parallel runs.

Holger Krekel for pytest with its distributed testing support.

Jason Pellerin for nose.

Michael Foord for unittest2.

No doubt others have contributed to these tools as well.
