=============
Configuration
=============

This plugin provides a clean minimal set of command line options that are added to pytest.  For
further control of coverage use a coverage config file.

For example if tests are contained within the directory tree being measured the tests may be
excluded if desired by using a .coveragerc file with the omit option set::

    pytest --cov-config=.coveragerc
           --cov=myproj
           myproj/tests/

Where the .coveragerc file contains file globs::

    [run]
    omit = tests/*

For full details refer to the `coverage config file`_ documentation.

.. _`coverage config file`: https://coverage.readthedocs.io/en/latest/config.html

Note that this plugin controls some options and setting the option in the config file will have no
effect.  These include specifying source to be measured (source option) and all data file handling
(data_file and parallel options).

If you wish to always add pytest-cov with pytest, you can use ``addopts`` under ``pytest`` or ``tool:pytest`` section.
For example: ::

    [tool:pytest]
    addopts = --cov=<project-name> --cov-report html

Caveats
=======

A unfortunate consequence of coverage.py's history is that ``.coveragerc`` is a magic name: it's the default file but it also
means "try to also lookup coverage configuration in ``tox.ini`` or ``setup.cfg``".

In practical terms this means that if you have your coverage configuration in ``tox.ini`` or ``setup.cfg`` it is paramount
that you also use ``--cov-config=tox.ini`` or ``--cov-config=setup.cfg``.

You might not be affected but it's unlikely that you won't ever use ``chdir`` in a test.

Reference
=========

The complete list of command line options is:

  --cov=PATH            Measure coverage for filesystem path. (multi-allowed)
  --cov-report=type     Type of report to generate: term, term-missing,
                        annotate, html, xml (multi-allowed). term, term-
                        missing may be followed by ":skip-covered". annotate,
                        html and xml may be followed by ":DEST" where DEST
                        specifies the output location. Use --cov-report= to
                        not generate any output.
  --cov-config=path     Config file for coverage. Default: .coveragerc
  --no-cov-on-fail      Do not report coverage if test run fails. Default:
                        False
  --no-cov              Disable coverage report completely (useful for
                        debuggers). Default: False
  --cov-fail-under=MIN  Fail if the total coverage is less than MIN.
  --cov-append          Do not delete coverage but append to current. Default:
                        False
  --cov-branch          Enable branch coverage.
  --cov-context         Choose the method for setting the dynamic context.
