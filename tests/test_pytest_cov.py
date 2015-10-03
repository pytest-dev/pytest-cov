import glob
import os
import subprocess
import sys
from distutils.version import StrictVersion

import coverage
import py
import pytest
import virtualenv
from process_tests import TestProcess
from process_tests import dump_on_error
from process_tests import wait_for_strings

import pytest_cov.plugin

coverage, StrictVersion  # required for skipif mark on test_cov_min_from_coveragerc

SCRIPT = '''
import sys, helper

def pytest_generate_tests(metafunc):
    for i in range(10):
        metafunc.addcall()

def test_foo():
    x = True
    helper.do_stuff()  # get some coverage in some other completely different location
    if sys.version_info[0] > 5:
        assert False
'''

SCRIPT2 = '''
#

def test_bar():
    x = True
    assert x

'''


COVERAGERC_SOURCE = '''\
[run]
source = .
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

SCRIPT_PARENT_CHANGE_CWD = '''
import subprocess
import sys
import os

def pytest_generate_tests(metafunc):
    for i in range(2):
        metafunc.addcall(funcargs=dict(idx=i))

def test_foo(idx):
    os.mkdir("foobar")
    os.chdir("foobar")

    subprocess.check_call([
        sys.executable,
        os.path.join(os.path.dirname(__file__), 'child_script.py'),
        str(idx)
    ])

# there is a issue in coverage.py with multiline statements at
# end of file: https://bitbucket.org/ned/coveragepy/issue/293
pass
'''

SCRIPT_FUNCARG = '''
import coverage

def test_foo(cov):
    assert isinstance(cov, coverage.coverage)
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

SCRIPT_RESULT = '9 * 89%'
SCRIPT2_RESULT = '3 * 100%'
CHILD_SCRIPT_RESULT = '[56] * 100%'
PARENT_SCRIPT_RESULT = '8 * 100%'

xdist = pytest.mark.parametrize('opts', ['', '-n 1'], ids=['nodist', 'xdist'])


def test_central(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central* %s *' % SCRIPT_RESULT,
        '*10 passed*'
    ])
    assert result.ret == 0


def test_annotate(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=annotate',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'Coverage annotated source written next to source',
        '*10 passed*',
    ])
    assert result.ret == 0


def test_cov_min_100(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--cov-fail-under=100',
                               script)

    assert result.ret != 0


def test_cov_min_50(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--cov-fail-under=50',
                               script)

    assert result.ret == 0


def test_cov_min_no_report(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=',
                               '--cov-fail-under=50',
                               script)

    assert result.ret == 0


def test_central_nonspecific(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central_nonspecific* %s *' % SCRIPT_RESULT,
        '*10 passed*'
    ])

    # multi-module coverage report
    assert any(line.startswith('TOTAL ') for line in result.stdout.lines[-4:])

    assert result.ret == 0


@pytest.mark.skipif('StrictVersion(coverage.__version__) <= StrictVersion("3.8")')
def test_cov_min_from_coveragerc(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("""
[report]
fail_under = 100
""")

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    assert result.ret != 0


def test_central_coveragerc(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write(COVERAGERC_SOURCE)

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central_coveragerc* %s *' % SCRIPT_RESULT,
        '*10 passed*',
    ])

    # single-module coverage report
    assert all(not line.startswith('TOTAL ') for line in result.stdout.lines[-4:])

    assert result.ret == 0


def test_show_missing_coveragerc(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("""
[run]
source = .

[report]
show_missing = true
""")

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'Name * Stmts * Miss * Cover * Missing',
        'test_show_missing_coveragerc* %s * 11' % SCRIPT_RESULT,
        '*10 passed*',
    ])

    # single-module coverage report
    assert all(not line.startswith('TOTAL ') for line in result.stdout.lines[-4:])

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


def test_dist_combine_racecondition(testdir):
    script = testdir.makepyfile("""
import pytest

@pytest.mark.parametrize("foo", range(1000))
def test_foo(foo):
""" + "\n".join("""
    if foo == %s:
        assert True
""" % i for i in range(1000)))

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '-n', '5',
                               script)
    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_combine_racecondition* 2002 * 0 * 100% *',
        '*1000 passed*'
    ])
    for line in result.stdout.lines:
        assert 'The following slaves failed to return coverage data' not in line
    assert result.ret == 0


def test_dist_collocated(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               '--max-slave-restart=0',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_collocated* %s *' % SCRIPT_RESULT,
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
                               '--max-slave-restart=0', '-s',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_not_collocated* %s *' % SCRIPT_RESULT,
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
        'child_script* %s *' % CHILD_SCRIPT_RESULT,
        'parent_script* %s *' % PARENT_SCRIPT_RESULT,
    ])
    assert result.ret == 0


def test_central_subprocess_change_cwd(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT_CHANGE_CWD,
                                 child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')
    testdir.makefile('', coveragerc="""
[run]
branch = true
parallel = true
""")

    result = testdir.runpytest('-v', '--tb=short',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-config=coveragerc',
                               '--cov-report=term-missing',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'child_script* %s *' % CHILD_SCRIPT_RESULT,
        'parent_script* 100% *',
    ])
    assert result.ret == 0


def test_central_subprocess_no_subscript(testdir):
    script = testdir.makepyfile("""
import subprocess, sys

def test_foo():
    subprocess.check_call([sys.executable, '-c', 'print("Hello World")'])
""")
    testdir.makefile('', coveragerc="""
[run]
branch = true
parallel = true
omit =
    */__init__.py
""")
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(), script)
    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central_subprocess_no_subscript* * 3 * 0 * 100%*',
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
                               '--max-slave-restart=0',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'child_script* %s *' % CHILD_SCRIPT_RESULT,
        'parent_script* %s *' % PARENT_SCRIPT_RESULT,
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
                               '--max-slave-restart=0',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'child_script* %s *' % CHILD_SCRIPT_RESULT,
        'parent_script* %s *' % PARENT_SCRIPT_RESULT,
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
    subprocess.check_call([
        exe,
        '-mpip' if sys.version_info >= (2, 7) else '-mpip.__main__',
        'install',
        'py==%s' % py.__version__,
        'pytest==%s' % pytest.__version__
    ])
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=popen//python=%s' % exe,
                               '--max-slave-restart=0',
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
        'test_funcarg* 3 * 100%*',
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
        'test_multiprocessing_subprocess* 8 * 100%*',
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
    x = True
    assert x

'''

CONF_RESULT = 'mod* 2 * 100% *'


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


def test_cover_looponfail(testdir, monkeypatch):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)

    monkeypatch.setattr(testdir, 'run', lambda *args: TestProcess(*map(str, args)))
    with testdir.runpytest('-v',
                           '--cov=%s' % script.dirpath(),
                           '--looponfail',
                           script) as process:
        with dump_on_error(process.read):
            wait_for_strings(
                process.read,
                30,  # 30 seconds
                'Stmts   Miss  Cover'
            )


def test_cover_conftest_dist(testdir):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               '--max-slave-restart=0',
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
    x = True
    assert x

'''

EXCLUDED_RESULT = '4 * 100% *'


def test_coveragerc(testdir):
    testdir.makefile('', coveragerc=COVERAGERC)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['test_coveragerc* %s' % EXCLUDED_RESULT])


def test_coveragerc_dist(testdir):
    testdir.makefile('', coveragerc=COVERAGERC)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '-n', '2',
                               '--max-slave-restart=0',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        ['test_coveragerc_dist* %s' % EXCLUDED_RESULT])


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
    x = True
    assert x

'''

SCRIPT_SIMPLE_RESULT = '4 * 100%'


@pytest.mark.skipif('sys.platform == "win32"')
def test_dist_boxed(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--boxed',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_boxed* %s*' % SCRIPT_SIMPLE_RESULT,
        '*1 passed*'
    ])
    assert result.ret == 0


def test_not_started_plugin_does_not_fail(testdir):
    plugin = pytest_cov.plugin.CovPlugin(None, None, start=False)
    plugin.pytest_sessionfinish(None, None)
    plugin.pytest_terminal_summary(None)


def test_default_output_setting(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script)

    result.stdout.fnmatch_lines([
        '*coverage*'
    ])
    assert result.ret == 0


def test_disabled_output(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=',
                               script)

    assert 'coverage' not in result.stdout.str()
    assert result.ret == 0


def test_coverage_file(testdir):
    script = testdir.makepyfile(SCRIPT)
    data_file_name = 'covdata'
    os.environ['COVERAGE_FILE'] = data_file_name
    try:
        result = testdir.runpytest('-v', '--cov=%s' % script.dirpath(),
                                   script)
        assert result.ret == 0
        data_file = testdir.tmpdir.join(data_file_name)
        assert data_file.check()
    finally:
        os.environ.pop('COVERAGE_FILE')


def test_external_data_file(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("""
[run]
data_file = %s
""" % testdir.tmpdir.join('some/special/place/coverage-data').ensure())

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script)
    assert result.ret == 0
    assert glob.glob(str(testdir.tmpdir.join('some/special/place/coverage-data*')))


def test_external_data_file_xdist(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("""
[run]
parallel = true
data_file = %s
""" % testdir.tmpdir.join('some/special/place/coverage-data').ensure())

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '-n', '1',
                               '--max-slave-restart=0',
                               script)
    assert result.ret == 0
    assert glob.glob(str(testdir.tmpdir.join('some/special/place/coverage-data*')))


def test_external_data_file_negative(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("")

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script)
    assert result.ret == 0
    assert glob.glob(str(testdir.tmpdir.join('.coverage*')))


@xdist
def test_append_coverage(testdir, opts):
    script = testdir.makepyfile(test_1=SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("")
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script,
                               *opts.split())
    result.stdout.fnmatch_lines([
        'test_1* %s*' % SCRIPT_RESULT,
    ])
    script2 = testdir.makepyfile(test_2=SCRIPT2)
    result = testdir.runpytest('-v',
                               '--cov-append',
                               '--cov=%s' % script2.dirpath(),
                               script2,
                               *opts.split())
    result.stdout.fnmatch_lines([
        'test_1* %s*' % SCRIPT_RESULT,
        'test_2* %s*' % SCRIPT2_RESULT,
    ])


@xdist
def test_do_not_append_coverage(testdir, opts):
    script = testdir.makepyfile(test_1=SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("")
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script,
                               *opts.split())
    result.stdout.fnmatch_lines([
        'test_1* %s*' % SCRIPT_RESULT,
    ])
    script2 = testdir.makepyfile(test_2=SCRIPT2)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script2.dirpath(),
                               script2,
                               *opts.split())
    result.stdout.fnmatch_lines([
        'test_1* 0%',
        'test_2* %s*' % SCRIPT2_RESULT,
    ])

