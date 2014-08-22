
import os
import sys

import virtualenv

import py
import pytest
import pytest_cov


pytest_plugins = 'pytester', 'cov'

SCRIPT = '''
import sys

def pytest_generate_tests(metafunc):
    for i in range(10):
        metafunc.addcall()

def test_foo():
    assert True
    if sys.version_info[0] > 5:
        assert False
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
    out, err = subprocess.Popen(
        [sys.executable, 'child_script.py', str(idx)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()

# there is a issue in coverage.py with multiline statements at
# end of file: https://bitbucket.org/ned/coveragepy/issue/293
pass
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


SCRIPT_FAIL = '''
def test_fail():
    assert False

'''

SCRIPT_RESULT = '8 * 88%'
CHILD_SCRIPT_RESULT = '6 * 100%'
PARENT_SCRIPT_RESULT = '8 * 100%'


def test_central(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central * %s *' % SCRIPT_RESULT,
        '*10 passed*'
        ])
    assert result.ret == 0


def test_no_cov_on_fail(testdir):
    script = testdir.makepyfile(SCRIPT_FAIL)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--no-cov-on-fail',
                               script)

    assert 'coverage: platform' not in result.stdout.str()
    result.stdout.fnmatch_lines(['*1 failed*'])


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
        'test_dist_collocated * %s *' % SCRIPT_RESULT,
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
        'test_dist_not_collocated * %s *' % SCRIPT_RESULT,
        '*10 passed*'
        ])
    assert result.ret == 0


def test_central_subprocess(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT,
                                 child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest('-v',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-report=term-missing',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'child_script * %s *' % CHILD_SCRIPT_RESULT,
        'parent_script * %s *' % PARENT_SCRIPT_RESULT,
        ])
    assert result.ret == 0


def test_dist_subprocess_collocated(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT,
                                 child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest('-v',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'child_script * %s *' % CHILD_SCRIPT_RESULT,
        'parent_script * %s *' % PARENT_SCRIPT_RESULT,
        ])
    assert result.ret == 0


def test_dist_subprocess_not_collocated(testdir, tmpdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT,
                                 child_script=SCRIPT_CHILD)
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
        'child_script * %s *' % CHILD_SCRIPT_RESULT,
        'parent_script * %s *' % PARENT_SCRIPT_RESULT,
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
    venv_path = os.path.join(str(testdir.tmpdir), 'venv')
    virtualenv.create_environment(venv_path)
    if sys.platform == 'win32':
        exe = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        exe = os.path.join(venv_path, 'bin', 'python')
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


MODULE = '''
def func():
    return 1

'''

CONFTEST = '''

import mod
mod.func()

'''

BASIC_TEST = '''

def test_basic():
    assert True

'''

CONF_RESULT = 'mod * 2 * 100% *'


def test_cover_conftest(testdir):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([CONF_RESULT])


def test_cover_conftest_dist(testdir):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([CONF_RESULT])


COVERAGERC = '''
[report]
# Regexes for lines to exclude from consideration
exclude_lines =
    raise NotImplementedError

'''

EXCLUDED_TEST = '''

def func():
    raise NotImplementedError

def test_basic():
    assert True

'''

EXCLUDED_RESULT = '3 * 100% *'


def test_coveragerc(testdir):
    testdir.makefile('', coveragerc=COVERAGERC)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['test_coveragerc * %s' % EXCLUDED_RESULT])


def test_coveragerc_dist(testdir):
    testdir.makefile('', coveragerc=COVERAGERC)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '-n', '2',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        ['test_coveragerc_dist * %s' % EXCLUDED_RESULT])


CLEAR_ENVIRON_TEST = '''

import os

def test_basic():
    os.environ.clear()

'''


def test_clear_environ(testdir):
    script = testdir.makepyfile(CLEAR_ENVIRON_TEST)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)
    assert result.ret == 0


SCRIPT_SIMPLE = '''

def test_foo():
    assert 1 == 1
    assert True

'''

SCRIPT_SIMPLE_RESULT = '3 * 100%'


@pytest.mark.skipif('sys.platform == "win32"')
def test_dist_boxed(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--boxed',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_boxed * %s*' % SCRIPT_SIMPLE_RESULT,
        '*1 passed*'
        ])
    assert result.ret == 0


def test_not_started_plugin_does_not_fail(testdir):
    plugin = pytest_cov.CovPlugin(None, None, start=False)
    plugin.pytest_sessionfinish(None, None)
    plugin.pytest_terminal_summary(None)
