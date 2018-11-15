import glob
import os
import subprocess
import sys
from distutils.version import StrictVersion
from itertools import chain

import coverage
import py
import pytest
import virtualenv
from process_tests import TestProcess as _TestProcess
from process_tests import dump_on_error
from process_tests import wait_for_strings
from six import exec_
from fields import Namespace

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

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
    foo = "a"  # previously there was a "pass" here but Python 3.5 optimizes it away.
if idx == 1:
    foo = "b"  # previously there was a "pass" here but Python 3.5 optimizes it away.
'''

SCRIPT_PARENT = '''
import os
import subprocess
import sys

def pytest_generate_tests(metafunc):
    for i in range(2):
        metafunc.addcall(funcargs=dict(idx=i))

def test_foo(idx):
    out, err = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), 'child_script.py'), str(idx)],
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

SCRIPT_PARENT_CHANGE_CWD_IMPORT_CHILD = '''
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
        '-c', 'import sys; sys.argv = ["", str(%s)]; import child_script' % idx
    ])

# there is a issue in coverage.py with multiline statements at
# end of file: https://bitbucket.org/ned/coveragepy/issue/293
pass
'''

SCRIPT_FUNCARG = '''
import coverage

def test_foo(cov):
    assert isinstance(cov, coverage.Coverage)
'''

SCRIPT_FUNCARG_NOT_ACTIVE = '''
def test_foo(cov):
    assert cov is None
'''

SCRIPT_FAIL = '''
def test_fail():
    assert False

'''

CHILD_SCRIPT_RESULT = '[56] * 100%'
PARENT_SCRIPT_RESULT = '9 * 100%'
DEST_DIR = 'cov_dest'
REPORT_NAME = 'cov.xml'

xdist = pytest.mark.parametrize('opts', ['', '-n 1'], ids=['nodist', 'xdist'])


@pytest.fixture(params=[
    ('branch=true', '--cov-branch', '9 * 85%', '3 * 100%'),
    ('branch=true', '',             '9 * 85%', '3 * 100%'),
    ('',            '--cov-branch', '9 * 85%', '3 * 100%'),
    ('',            '',             '9 * 89%', '3 * 100%'),
], ids=['branch2x', 'branch1c', 'branch1a', 'nobranch'])
def prop(request):
    return Namespace(
        code=SCRIPT,
        code2=SCRIPT2,
        conf=request.param[0],
        fullconf='[run]\n%s\n' % request.param[0],
        prefixedfullconf='[coverage:run]\n%s\n' % request.param[0],
        args=request.param[1].split(),
        result=request.param[2],
        result2=request.param[3],
    )


def test_central(testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script,
                               *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central* %s *' % prop.result,
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


def test_annotate_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=annotate:' + DEST_DIR,
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'Coverage annotated source written to dir ' + DEST_DIR,
        '*10 passed*',
    ])
    dest_dir = testdir.tmpdir.join(DEST_DIR)
    assert dest_dir.check(dir=True)
    assert dest_dir.join(script.basename + ",cover").check()
    assert result.ret == 0


def test_html_output_dir(testdir, prop):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=html:' + DEST_DIR,
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'Coverage HTML written to dir ' + DEST_DIR,
        '*10 passed*',
    ])
    dest_dir = testdir.tmpdir.join(DEST_DIR)
    assert dest_dir.check(dir=True)
    assert dest_dir.join("index.html").check()
    assert result.ret == 0


def test_xml_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=xml:' + REPORT_NAME,
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'Coverage XML written to file ' + REPORT_NAME,
        '*10 passed*',
    ])
    assert testdir.tmpdir.join(REPORT_NAME).check()
    assert result.ret == 0


def test_term_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term:' + DEST_DIR,
                               script)

    result.stderr.fnmatch_lines([
        '*argument --cov-report: output specifier not supported for: "term:%s"*' % DEST_DIR,
    ])
    assert result.ret != 0


def test_term_missing_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing:' + DEST_DIR,
                               script)

    result.stderr.fnmatch_lines([
        '*argument --cov-report: output specifier not supported for: '
        '"term-missing:%s"*' % DEST_DIR,
    ])
    assert result.ret != 0


def test_cov_min_100(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--cov-fail-under=100',
                               script)

    assert result.ret != 0
    result.stdout.fnmatch_lines([
        'FAIL Required test coverage of 100% not reached. Total coverage: *%'
    ])


def test_cov_min_50(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--cov-fail-under=50',
                               script)

    assert result.ret == 0
    result.stdout.fnmatch_lines([
        'Required test coverage of 50% reached. Total coverage: *%'
    ])


def test_cov_min_no_report(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=',
                               '--cov-fail-under=50',
                               script)

    assert result.ret == 0
    result.stdout.fnmatch_lines([
        'Required test coverage of 50% reached. Total coverage: *%'
    ])


def test_central_nonspecific(testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               script, *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central_nonspecific* %s *' % prop.result,
        '*10 passed*'
    ])

    # multi-module coverage report
    assert any(line.startswith('TOTAL ') for line in result.stdout.lines)

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


def test_central_coveragerc(testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(COVERAGERC_SOURCE + prop.conf)

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               script, *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_central_coveragerc* %s *' % prop.result,
        '*10 passed*',
    ])

    # single-module coverage report
    assert all(not line.startswith('TOTAL ') for line in result.stdout.lines[-4:])

    assert result.ret == 0


@xdist
def test_central_with_path_aliasing(testdir, monkeypatch, opts, prop):
    mod1 = testdir.mkdir('src').join('mod.py')
    mod1.write(SCRIPT)
    mod2 = testdir.mkdir('aliased').join('mod.py')
    mod2.write(SCRIPT)
    script = testdir.makepyfile('''
from mod import *
''')
    testdir.tmpdir.join('setup.cfg').write("""
[coverage:paths]
source =
    src
    aliased
[coverage:run]
source = mod
parallel = true
%s
""" % prop.conf)

    monkeypatch.setitem(os.environ, 'PYTHONPATH', os.pathsep.join([os.environ.get('PYTHONPATH', ''), 'aliased']))
    result = testdir.runpytest('-v', '-s',
                               '--cov',
                               '--cov-report=term-missing',
                               script, *opts.split()+prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'src[\\/]mod* %s *' % prop.result,
        '*10 passed*',
    ])

    # single-module coverage report
    assert all(not line.startswith('TOTAL ') for line in result.stdout.lines[-4:])

    assert result.ret == 0


def test_subprocess_with_path_aliasing(testdir, monkeypatch):
    src = testdir.mkdir('src')
    src.join('parent_script.py').write(SCRIPT_PARENT)
    src.join('child_script.py').write(SCRIPT_CHILD)
    aliased = testdir.mkdir('aliased')
    parent_script = aliased.join('parent_script.py')
    parent_script.write(SCRIPT_PARENT)
    aliased.join('child_script.py').write(SCRIPT_CHILD)

    testdir.tmpdir.join('.coveragerc').write("""
[paths]
source =
    src
    aliased
[run]
source =
    parent_script
    child_script
parallel = true
""")

    monkeypatch.setitem(os.environ, 'PYTHONPATH', os.pathsep.join([os.environ.get('PYTHONPATH',''), 'aliased']))
    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'src[\\/]child_script* %s*' % CHILD_SCRIPT_RESULT,
        'src[\\/]parent_script* %s*' % PARENT_SCRIPT_RESULT,
    ])
    assert result.ret == 0


def test_show_missing_coveragerc(testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write("""
[run]
source = .
%s

[report]
show_missing = true
""" % prop.conf)

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term',
                               script, *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'Name * Stmts * Miss * Cover * Missing',
        'test_show_missing_coveragerc* %s * 11*' % prop.result,
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


def test_no_cov(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-vvv',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--no-cov',
                               '-rw',
                               script)
    result.stdout.fnmatch_lines_random([
        'WARNING: Coverage disabled via --no-cov switch!',
        '*Coverage disabled via --no-cov switch!',
    ])


def test_cov_and_failure_report_on_fail(testdir):
    script = testdir.makepyfile(SCRIPT + SCRIPT_FAIL)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-fail-under=100',
                               script)

    result.stdout.fnmatch_lines_random([
        '*10 failed*',
        '*coverage: platform*',
        '*FAIL Required test coverage of 100% not reached*',
        '*assert False*',
    ])


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
                               '-n', '5', '-s',
                               script)
    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_combine_racecondition* 2002 * 0 * 100%*',
        '*1000 passed*'
    ])

    for line in chain(result.stdout.lines, result.stderr.lines):
        assert 'The following slaves failed to return coverage data' not in line
        assert 'INTERNALERROR' not in line
    assert result.ret == 0


def test_dist_collocated(testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=2*popen',
                               '--max-slave-restart=0',
                               script, *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_collocated* %s *' % prop.result,
        '*10 passed*'
    ])
    assert result.ret == 0


def test_dist_not_collocated(testdir, prop):
    script = testdir.makepyfile(prop.code)
    dir1 = testdir.mkdir('dir1')
    dir2 = testdir.mkdir('dir2')
    testdir.tmpdir.join('.coveragerc').write('''
[run]
%s
[paths]
source =
    .
    dir1
    dir2''' % prop.conf)

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=popen//chdir=%s' % dir1,
                               '--tx=popen//chdir=%s' % dir2,
                               '--rsyncdir=%s' % script.basename,
                               '--rsyncdir=.coveragerc',
                               '--max-slave-restart=0', '-s',
                               script, *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_not_collocated* %s *' % prop.result,
        '*10 passed*'
    ])
    assert result.ret == 0


def test_dist_not_collocated_coveragerc_source(testdir, prop):
    script = testdir.makepyfile(prop.code)
    dir1 = testdir.mkdir('dir1')
    dir2 = testdir.mkdir('dir2')
    testdir.tmpdir.join('.coveragerc').write('''
[run]
%s
source = %s
[paths]
source =
    .
    dir1
    dir2''' % (prop.conf, script.dirpath()))

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               '--dist=load',
                               '--tx=popen//chdir=%s' % dir1,
                               '--tx=popen//chdir=%s' % dir2,
                               '--rsyncdir=%s' % script.basename,
                               '--rsyncdir=.coveragerc',
                               '--max-slave-restart=0', '-s',
                               script, *prop.args)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_not_collocated* %s *' % prop.result,
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
        'child_script* %s*' % CHILD_SCRIPT_RESULT,
        'parent_script* %s*' % PARENT_SCRIPT_RESULT,
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

    result = testdir.runpytest('-v', '-s',
                               '--cov=%s' % scripts.dirpath(),
                               '--cov-config=coveragerc',
                               '--cov-report=term-missing',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        '*child_script* %s*' % CHILD_SCRIPT_RESULT,
        '*parent_script* 100%*',
    ])
    assert result.ret == 0


def test_central_subprocess_change_cwd_with_pythonpath(testdir, monkeypatch):
    stuff = testdir.mkdir('stuff')
    parent_script = stuff.join('parent_script.py')
    parent_script.write(SCRIPT_PARENT_CHANGE_CWD_IMPORT_CHILD)
    stuff.join('child_script.py').write(SCRIPT_CHILD)
    testdir.makefile('', coveragerc="""
[run]
parallel = true
""")

    monkeypatch.setitem(os.environ, 'PYTHONPATH', str(stuff))
    result = testdir.runpytest('-vv', '-s',
                               '--cov=child_script',
                               '--cov-config=coveragerc',
                               '--cov-report=term-missing',
                               '--cov-branch',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        '*child_script* %s*' % CHILD_SCRIPT_RESULT,
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
parallel = true
""")
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(),
                               '--cov-branch',
                               script)
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
        'child_script* %s*' % CHILD_SCRIPT_RESULT,
        'parent_script* %s*' % PARENT_SCRIPT_RESULT,
    ])
    assert result.ret == 0


def test_dist_subprocess_not_collocated(testdir, tmpdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT,
                                 child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')
    child_script = scripts.dirpath().join('child_script.py')

    dir1 = tmpdir.mkdir('dir1')
    dir2 = tmpdir.mkdir('dir2')
    testdir.tmpdir.join('.coveragerc').write('''
[paths]
source =
    %s
    */dir1
    */dir2
''' % scripts.dirpath())
    result = testdir.runpytest('-v',
                               '--cov=%s' % scripts.dirpath(),
                               '--dist=load',
                               '--tx=popen//chdir=%s' % dir1,
                               '--tx=popen//chdir=%s' % dir2,
                               '--rsyncdir=%s' % child_script,
                               '--rsyncdir=%s' % parent_script,
                               '--rsyncdir=.coveragerc',
                               '--max-slave-restart=0',
                               parent_script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'child_script* %s*' % CHILD_SCRIPT_RESULT,
        'parent_script* %s*' % PARENT_SCRIPT_RESULT,
    ])
    assert result.ret == 0


def test_invalid_coverage_source(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.makeini("""
        [pytest]
        console_output_style=classic
    """)
    result = testdir.runpytest('-v',
                               '--cov=non_existent_module',
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*10 passed*'
    ])
    result.stderr.fnmatch_lines([
        'Coverage.py warning: No data was collected.*'
    ])
    result.stdout.fnmatch_lines([
        '*Failed to generate report: No data to report.',
    ])
    assert result.ret == 0

    matching_lines = [line for line in result.outlines if '%' in line]
    assert not matching_lines


@pytest.mark.skipif("'dev' in pytest.__version__")
def test_dist_missing_data(testdir):
    venv_path = os.path.join(str(testdir.tmpdir), 'venv')
    virtualenv.create_environment(venv_path)
    if sys.platform == 'win32':
        exe = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        exe = os.path.join(venv_path, 'bin', 'python')
    subprocess.check_call([
        exe,
        '-mpip',
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

    script = testdir.makepyfile('''
import multiprocessing

def target_fn():
    a = True
    return a

def test_run_target():
    p = multiprocessing.Process(target=target_fn)
    p.start()
    p.join()
''')

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


def test_multiprocessing_subprocess_no_source(testdir):
    py.test.importorskip('multiprocessing.util')

    script = testdir.makepyfile('''
import multiprocessing

def target_fn():
    a = True
    return a

def test_run_target():
    p = multiprocessing.Process(target=target_fn)
    p.start()
    p.join()
''')

    result = testdir.runpytest('-v',
                               '--cov',
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_multiprocessing_subprocess* 8 * 100%*',
        '*1 passed*'
    ])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32"',
                    reason="multiprocessing don't support clean process temination on Windows")
def test_multiprocessing_subprocess_with_terminate(testdir):
    py.test.importorskip('multiprocessing.util')

    script = testdir.makepyfile('''
import multiprocessing
import time
from pytest_cov.embed import cleanup_on_sigterm
cleanup_on_sigterm()

event = multiprocessing.Event()

def target_fn():
    a = True
    event.set()
    time.sleep(5)

def test_run_target():
    p = multiprocessing.Process(target=target_fn)
    p.start()
    time.sleep(0.5)
    event.wait(1)
    p.terminate()
    p.join()
''')

    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_multiprocessing_subprocess* 16 * 100%*',
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

CONF_RESULT = 'mod* 2 * 100%*'


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

    monkeypatch.setattr(testdir, 'run', lambda *args: _TestProcess(*map(str, args)))
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


def test_no_cover_marker(testdir):
    testdir.makepyfile(mod=MODULE)
    script = testdir.makepyfile('''
import pytest
import mod
import subprocess
import sys

@pytest.mark.no_cover
def test_basic():
    mod.func()
    subprocess.check_call([sys.executable, '-c', 'from mod import func; func()'])    
''')
    result = testdir.runpytest('-v', '-ra', '--strict',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['mod* 2 * 1 * 50% * 2'])


def test_no_cover_fixture(testdir):
    testdir.makepyfile(mod=MODULE)
    script = testdir.makepyfile('''
import mod
import subprocess
import sys

def test_basic(no_cover):
    mod.func()
    subprocess.check_call([sys.executable, '-c', 'from mod import func; func()'])    
''')
    result = testdir.runpytest('-v', '-ra', '--strict',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=term-missing',
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['mod* 2 * 1 * 50% * 2'])


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

EXCLUDED_RESULT = '4 * 100%*'


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


SKIP_COVERED_COVERAGERC = '''
[report]
skip_covered = True

'''

SKIP_COVERED_TEST = '''

def func():
    return "full coverage"

def test_basic():
    assert func() == "full coverage"

'''

SKIP_COVERED_RESULT = '1 file skipped due to complete coverage.'


@pytest.mark.skipif('StrictVersion(coverage.__version__) < StrictVersion("4.0")')
@pytest.mark.parametrize('report_option', [
    'term-missing:skip-covered',
    'term:skip-covered'])
def test_skip_covered_cli(testdir, report_option):
    testdir.makefile('', coveragerc=SKIP_COVERED_COVERAGERC)
    script = testdir.makepyfile(SKIP_COVERED_TEST)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               '--cov-report=%s' % report_option,
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([SKIP_COVERED_RESULT])


@pytest.mark.skipif('StrictVersion(coverage.__version__) < StrictVersion("4.0")')
def test_skip_covered_coveragerc_config(testdir):
    testdir.makefile('', coveragerc=SKIP_COVERED_COVERAGERC)
    script = testdir.makepyfile(SKIP_COVERED_TEST)
    result = testdir.runpytest('-v',
                               '--cov-config=coveragerc',
                               '--cov=%s' % script.dirpath(),
                               script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([SKIP_COVERED_RESULT])


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


@pytest.mark.skipif('sys.platform == "win32"')
def test_dist_bare_cov(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)

    result = testdir.runpytest('-v',
                               '--cov',
                               '-n', '1',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_dist_bare_cov* %s*' % SCRIPT_SIMPLE_RESULT,
        '*1 passed*'
    ])
    assert result.ret == 0


def test_not_started_plugin_does_not_fail(testdir):
    class ns:
        cov_source = [True]
        cov_report = ''
    plugin = pytest_cov.plugin.CovPlugin(ns, None, start=False)
    plugin.pytest_runtestloop(None)
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
def xtest_append_coverage(testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script,
                               *opts.split()+prop.args)
    result.stdout.fnmatch_lines([
        'test_1* %s*' % prop.result,
    ])
    script2 = testdir.makepyfile(test_2=prop.code2)
    result = testdir.runpytest('-v',
                               '--cov-append',
                               '--cov=%s' % script2.dirpath(),
                               script2,
                               *opts.split()+prop.args)
    result.stdout.fnmatch_lines([
        'test_1* %s*' % prop.result,
        'test_2* %s*' % prop.result2,
    ])


@xdist
def xtest_do_not_append_coverage(testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.tmpdir.join('.coveragerc').write("")
    result = testdir.runpytest('-v',
                               '--cov=%s' % script.dirpath(),
                               script,
                               *opts.split()+prop.args)
    result.stdout.fnmatch_lines([
        'test_1* %s*' % prop.result,
    ])
    script2 = testdir.makepyfile(test_2=prop.code2)
    result = testdir.runpytest('-v',
                               '--cov=%s' % script2.dirpath(),
                               script2,
                               *opts.split()+prop.args)
    result.stdout.fnmatch_lines([
        'test_1* 0%',
        'test_2* %s*' % prop.result2,
    ])


def test_pth_failure(monkeypatch):
    with open('src/pytest-cov.pth') as fh:
        payload = fh.read()

    class SpecificError(Exception):
        pass

    def bad_init():
        raise SpecificError()

    buff = StringIO()

    from pytest_cov import embed

    monkeypatch.setattr(embed, 'init', bad_init)
    monkeypatch.setattr(sys, 'stderr', buff)
    monkeypatch.setitem(os.environ, 'COV_CORE_SOURCE', 'foobar')
    exec_(payload)
    assert buff.getvalue() == '''pytest-cov: Failed to setup subprocess coverage. Environ: {'COV_CORE_SOURCE': 'foobar'} Exception: SpecificError()
'''


def test_double_cov(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v',
                               '--cov', '--cov=%s' % script.dirpath(),
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_double_cov* %s*' % SCRIPT_SIMPLE_RESULT,
        '*1 passed*'
    ])
    assert result.ret == 0


def test_double_cov2(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v',
                               '--cov', '--cov',
                               script)

    result.stdout.fnmatch_lines([
        '*- coverage: platform *, python * -*',
        'test_double_cov2* %s*' % SCRIPT_SIMPLE_RESULT,
        '*1 passed*'
    ])
    assert result.ret == 0
