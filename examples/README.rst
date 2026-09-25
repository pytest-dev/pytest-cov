Simple examples with ``tox.ini``
================================

These examples provide necessary configuration to:

* aggregate coverage from multiple interpreters
* support tox parallel mode
* run tests on installed code

The `adhoc` layout is the old and problematic layout where you can mix up the installed code
with the source code. However, these examples will provide correct configuration even for
the `adhoc` layout. Its coverage configuration uses ``source_pkgs = example`` to measure
the installed package without also measuring unrelated files in the test directory.
The ``changedir = tests`` setting is still needed to keep the source checkout out of
Python's import path, so tests exercise the installed package.

The `src` layout configuration is less complicated, have that in mind when picking a layout
for your project.
