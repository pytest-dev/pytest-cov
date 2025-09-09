Reporting
=========

It is possible to generate any combination of the reports for a single test run.

The available reports are terminal (with or without missing line numbers shown), HTML, XML, JSON, Markdown (either in 'write' or 'append'
mode to file), LCOV and annotated source code.

The default is terminal report without line numbers::

    pytest --cov=myproj tests/

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%


The terminal report with line numbers::

    pytest --cov-report=term-missing --cov=myproj tests/

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      0   100%
    myproj/myproj          257     13    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94      7    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353     20    94%

The terminal report with skip covered::

    pytest --cov-report term:skip-covered --cov=myproj tests/

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Miss  Cover
    ----------------------------------------
    myproj/myproj          257     13    94%
    myproj/feature4286      94      7    92%
    ----------------------------------------
    TOTAL                  353     20    94%

    1 files skipped due to complete coverage.

You can use ``skip-covered`` with ``term-missing`` as well. e.g. ``--cov-report term-missing:skip-covered``

If any reporting options are used then the default (``--cov-report=term`` is not added automatically). For example this would not show any
terminal output:

.. code-block:: bash

    pytest --cov-report html
           --cov-report xml
           --cov-report json
           --cov-report markdown
           --cov-report markdown-append:cov-append.md
           --cov-report lcov
           --cov-report annotate
           --cov=myproj tests/

You can specify output paths for reports. The output location for the XML, JSON, Markdown and LCOV
report is a file. Where as the output location for the HTML and annotated source code reports are
directories:

.. code-block:: bash

    pytest --cov-report html:cov_html
           --cov-report xml:cov.xml
           --cov-report json:cov.json
           --cov-report markdown:cov.md
           --cov-report markdown-append:cov-append.md
           --cov-report lcov:cov.info
           --cov-report annotate:cov_annotate
           --cov=myproj tests/

Example for GitHub Actions with ``markdown-append``:

.. code-block:: bash

    pytest --cov-report=markdown-append:${GITHUB_STEP_SUMMARY}.
           --cov=myproj tests/

To disable the default ``term`` report provide an empty report:

.. code-block:: bash

    pytest --cov-report= --cov=myproj tests/

This mode can be especially useful on continuous integration servers, where a coverage file
is needed for subsequent processing, but no local report needs to be viewed. For example,
tests run on GitHub Actions could produce a .coverage file for use with Coveralls.
