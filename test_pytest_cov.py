"""Tests for pytest-cov.

Known issues:

- If py 2 then can have tx for any py 2, but problems if tx for py 3.

- If py 3.0 then can have tx for py 3.0 / 3.1, but problems if tx for py 2.

- If py 3.1 then can have tx for py 3.1, but problems if tx for py 2 or py 3.0.

- For py 3.0 coverage seems to give incorrect results, it reports all
  covered except the one line which it should have actually covered.
  Issue reported upstream, also only problem with pass statement and
  is fine with simple assignment statement.
"""

import py
import os
import sys

pytest_plugins = 'pytester', 'cov'

SCRIPT = '''
import sys

def pytest_generate_tests(metafunc):
    for i in range(10):
        metafunc.addcall()

def test_foo():
    version = sys.version_info[:2]
    if version == (2, 4):
        a = True
    if version == (2, 5):
        a = True
    if version == (2, 6):
        a = True
    if version == (2, 7):
        a = True
    if version == (3, 0):
        a = True
    if version == (3, 1):
        a = True
    if version == (3, 2):
        a = True
'''

SCRIPT_CHILD = '''
import sys

idx = int(sys.argv[1])

if idx == 0:
    pass
if idx == 1:
    pass
'''

SCRIPT_PARENT = '''
import subprocess
import sys

def pytest_generate_tests(metafunc):
    for i in range(2):
        metafunc.addcall(funcargs=dict(idx=i))

def test_foo(idx):
    out, err = subprocess.Popen([sys.executable, 'child_script.py', str(idx)], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
'''

SCRIPT_FUNCARG = '''
import coverage

def test_foo(cov):
    assert isinstance(cov, coverage.control.coverage)
'''

SCRIPT_FUNCARG_NOT_ACTIVE = '''
def test_foo(cov):
    assert cov is None
'''

MULTIPROCESSING_SCRIPT = '''
import multiprocessing

def target_fn():
    a = True
    return a

def test_run_target():
    p = multiprocessing.Process(target=target_fn)
    p.start()
    p.join()
'''


def test_central(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_central * 20 * 70%*',
            '*10 passed*'
            ])
    assert result.ret == 0


def test_dist_collocated(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_dist_collocated * 20 * 70%*',
            '*10 passed*'
            ])
    assert result.ret == 0


def test_dist_not_collocated(testdir):
    script = testdir.makepyfile(SCRIPT)
    dir1 = testdir.mkdir('dir1')
    dir2 = testdir.mkdir('dir2')

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=popen//chdir=%s' % dir1,
                               '--tx=popen//chdir=%s' % dir2,
                               '--rsyncdir=%s' % script.basename,
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_dist_not_collocated * 20 * 70%*',
            '*10 passed*'
            ])
    assert result.ret == 0


def test_central_subprocess(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest('-v',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-report=term-missing',
                               parent_script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'child_script * 6 * 100%*',
            'parent_script * 7 * 100%*',
            ])
    assert result.ret == 0


def test_dist_subprocess_collocated(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest('-v',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               parent_script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'child_script * 6 * 100%*',
            'parent_script * 7 * 100%*',
            ])
    assert result.ret == 0


def test_dist_subprocess_not_collocated(testdir, tmpdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')
    child_script = scripts.dirpath().join('child_script.py')

    dir1 = tmpdir.mkdir('dir1')
    dir2 = tmpdir.mkdir('dir2')

    result = testdir.runpytest('-v',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=popen//chdir=%s' % dir1,
                               '--tx=popen//chdir=%s' % dir2,
                               '--rsyncdir=%s' % child_script,
                               '--rsyncdir=%s' % parent_script,
                               parent_script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'child_script * 6 * 100%*',
            'parent_script * 7 * 100%*',
            ])
    assert result.ret == 0


def test_empty_report(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=non_existent_module',
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            '*10 passed*'
            ])
    assert result.ret == 0
    matching_lines = [line for line in result.outlines if '%' in line]
    assert not matching_lines


def test_dist_missing_data(testdir):
    version = sys.version_info[:2]
    if version == (2, 4):
        exe = '/usr/local/py24/bin/python'
    if version == (2, 5):
        exe = '/usr/local/py25/bin/python'
    if version == (2, 6):
        exe = '/usr/local/py26/bin/python'
    if version == (2, 7):
        exe = '/usr/local/py27/bin/python'
    if version == (3, 0):
        exe = '/usr/local/py30/bin/python3.0'
    if version == (3, 1):
        exe = '/usr/local/py31/bin/python3.1'
    if version == (3, 2):
        exe = '/usr/local/py32/bin/python3.2'

    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=popen//python=%s' % exe,
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: failed slaves -*'
            ])
    assert result.ret == 0


def test_funcarg(testdir):
    script = testdir.makepyfile(SCRIPT_FUNCARG)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_funcarg * 3 * 100%*',
            '*1 passed*'
            ])
    assert result.ret == 0


def test_funcarg_not_active(testdir):
    script = testdir.makepyfile(SCRIPT_FUNCARG_NOT_ACTIVE)

    result = testdir.runpytest('-v',
                               script)

    result.stdout.fnmatch_lines([
            '*1 passed*'
            ])
    assert result.ret == 0


def test_multiprocessing_subprocess(testdir):
    py.test.importorskip('multiprocessing.util')

    script = testdir.makepyfile(MULTIPROCESSING_SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_multiprocessing_subprocess * 8 * 100%*',
            '*1 passed*'
            ])
    assert result.ret == 0
