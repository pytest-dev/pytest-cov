pytest-cov
==========

This plugin supports pytest's distributed testing feature in both load
and each modes.  Of course it also support centralised testing.

It supports pretty much all features offered by the coverage package.

Each test run with coverage activated may produce any combination of
the four report types.  There is the terminal report output by pytest,
annotated source code, HTML and XML reports.


Installation
------------

This plugin depends on features just added to py and pytest-xdist.
Until py 1.2.2 and pytest-xdist 1.2 are released you will need to
install the 'tip' development versions from:

http://bitbucket.org/hpk42/py-trunk/downloads/

http://bitbucket.org/hpk42/pytest-xdist/downloads/


Usage
-----

Running centralised testing::

    py.test --cov myproj tests/

Shows a terminal report::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Distributed testing with dist mode set to load and branch coverage
enabled::

    py.test -n 2 --cov myproj --cov-branch tests/

The results from the slaves will be combined like so::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec Branch BrExec  Cover   Missing
    ----------------------------------------------------------------
    myproj/__init__          2      2      0      0   100%
    myproj/myproj          257    244     56     50    93%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87     18     13    89%   183-188, 197
    ----------------------------------------------------------------
    TOTAL                  353    333     74     63    92%


Distributed testing in each mode::

    py.test --cov myproj --dist=each
            --tx=popen//python=/usr/local/python264/bin/python
            --tx=popen//python=/usr/local/python265/bin/python
            tests/

Will produce a report for each slave::

    -------------------- coverage: platform linux2, python 2.6.4-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%
    -------------------- coverage: platform linux2, python 2.6.5-final-0 ---------------------
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


If desired distributed testing in each mode can instead produce a single combined report::

    py.test --cov myproj --cov-combine-each --dist=each
            --tx=popen//python=/usr/local/python264/bin/python
            --tx=popen//python=/usr/local/python265/bin/python
            tests/

Which looks like::

    ---------------------------------------- coverage ----------------------------------------
                              platform linux2, python 2.6.4-final-0
                              platform linux2, python 2.6.5-final-0
    Name                 Stmts   Exec  Cover   Missing
    --------------------------------------------------
    myproj/__init__          2      2   100%
    myproj/myproj          257    244    94%   24-26, 99, 149, 233-236, 297-298, 369-370
    myproj/feature4286      94     87    92%   183-188, 197
    --------------------------------------------------
    TOTAL                  353    333    94%


Limitations
-----------

Currently for distributed testing the python used by slaves must have
pytest-cov installed in order to operate.  This is because the
plugin must be registered through setuptools / distribute for pytest
to start the plugin on the slave.  Hopefully this will change in the
not to distant future, such that just like pytest-xdist only python
and nothing else is required on the slave side.

Currently the coverage rc file is not rsynced to slaves which can
result in different behaviour on the slaves.  Use command line options
for the time being.

This is an initial release developed on python 2.6 and support for
other python versions needs to be checked and fixed.  Hence for the
time being distributed testing in each mode may be a bit limited in
usefulness.


Acknowledgements
----------------

Holger Krekel for pytest with its distributed testing support.

Ned Batchelder for coverage and its ability to combine the coverage
results of parallel runs.

Whilst this plugin has been built fresh from the ground up to support
distributed testing it has been influenced by the work done on
pytest-coverage (Ross Lawley, James Mills, Holger Krekel) and
nose-cover (Jason Pellerin) which are other coverage plugins for
pytest and nose respectively.

No doubt others have contributed to these tools as well.
