# ruff: noqa
import collections
import glob
import os
import platform
import re
import subprocess
import sys
from io import StringIO
from itertools import chain

import coverage
import py
import pytest
import virtualenv
import xdist
from fields import Namespace
from process_tests import TestProcess as _TestProcess
from process_tests import dump_on_error
from process_tests import wait_for_strings

import pytest_cov.plugin

coverage, platform  # required for skipif mark on test_cov_min_from_coveragerc

max_worker_restart_0 = '--max-worker-restart=0'

SCRIPT = """
import sys, helper

def pytest_generate_tests(metafunc):
    for i in [10]:
        metafunc.parametrize('p', range(i))

def test_foo(p):
    x = True
    helper.do_stuff()  # get some coverage in some other completely different location
    if sys.version_info[0] > 5:
        assert False
"""

SCRIPT2 = """
#

def test_bar():
    x = True
    assert x

"""

COVERAGERC_SOURCE = """\
[run]
source = .
"""

SCRIPT_CHILD = """
import sys

idx = int(sys.argv[1])

if idx == 0:
    foo = "a"  # previously there was a "pass" here but Python 3.5 optimizes it away.
if idx == 1:
    foo = "b"  # previously there was a "pass" here but Python 3.5 optimizes it away.
"""

SCRIPT_PARENT = """
import os
import subprocess
import sys

def pytest_generate_tests(metafunc):
    for i in [2]:
        metafunc.parametrize('idx', range(i))

def test_foo(idx):
    out, err = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), 'child_script.py'), str(idx)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()

# there is a issue in coverage.py with multiline statements at
# end of file: https://bitbucket.org/ned/coveragepy/issue/293
pass
"""

SCRIPT_PARENT_CHANGE_CWD = """
import subprocess
import sys
import os

def pytest_generate_tests(metafunc):
    for i in [2]:
        metafunc.parametrize('idx', range(i))

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
"""

SCRIPT_PARENT_CHANGE_CWD_IMPORT_CHILD = """
import subprocess
import sys
import os

def pytest_generate_tests(metafunc):
    for i in [2]:
        if metafunc.function is test_foo: metafunc.parametrize('idx', range(i))

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
"""

SCRIPT_FUNCARG = """
import coverage

def test_foo(cov):
    assert isinstance(cov, coverage.Coverage)
"""

SCRIPT_FUNCARG_NOT_ACTIVE = """
def test_foo(cov):
    assert cov is None
"""

CHILD_SCRIPT_RESULT = '[56] * 100%'
PARENT_SCRIPT_RESULT = '9 * 100%'
DEST_DIR = 'cov_dest'
XML_REPORT_NAME = 'cov.xml'
JSON_REPORT_NAME = 'cov.json'
LCOV_REPORT_NAME = 'cov.info'

xdist_params = pytest.mark.parametrize(
    'opts',
    [
        '',
        pytest.param('-n 1', marks=pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')),
        pytest.param('-n 2', marks=pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')),
        pytest.param('-n 3', marks=pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')),
    ],
    ids=['nodist', '1xdist', '2xdist', '3xdist'],
)


@pytest.fixture(scope='session', autouse=True)
def adjust_sys_path():
    """Adjust PYTHONPATH during tests to make "helper" importable in SCRIPT."""
    orig_path = os.environ.get('PYTHONPATH', None)
    new_path = os.path.dirname(__file__)
    if orig_path is not None:
        new_path = os.pathsep.join([new_path, orig_path])
    os.environ['PYTHONPATH'] = new_path

    yield

    if orig_path is None:
        del os.environ['PYTHONPATH']
    else:
        os.environ['PYTHONPATH'] = orig_path


@pytest.fixture(
    params=[
        ('branch=true', '--cov-branch', '9 * 85%', '3 * 100%'),
        ('branch=true', '', '9 * 85%', '3 * 100%'),
        ('', '--cov-branch', '9 * 85%', '3 * 100%'),
        ('', '', '9 * 89%', '3 * 100%'),
    ],
    ids=['branch2x', 'branch1c', 'branch1a', 'nobranch'],
)
def prop(request):
    return Namespace(
        code=SCRIPT,
        code2=SCRIPT2,
        conf=request.param[0],
        fullconf=f'[run]\n{request.param[0]}\n',
        prefixedfullconf=f'[coverage:run]\n{request.param[0]}\n',
        args=request.param[1].split(),
        result=request.param[2],
        result2=request.param[3],
    )


def test_central(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script, *prop.args)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_central* {prop.result} *', '*10 passed*'])
    assert result.ret == 0


def test_annotate(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=annotate', script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage annotated source written next to source',
            '*10 passed*',
        ]
    )
    assert result.ret == 0


def test_annotate_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=annotate:' + DEST_DIR, script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage annotated source written to dir ' + DEST_DIR,
            '*10 passed*',
        ]
    )
    dest_dir = testdir.tmpdir.join(DEST_DIR)
    assert dest_dir.check(dir=True)
    assert dest_dir.join(script.basename + ',cover').check()
    assert result.ret == 0


def test_html(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=html', script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage HTML written to dir htmlcov',
            '*10 passed*',
        ]
    )
    dest_dir = testdir.tmpdir.join('htmlcov')
    assert dest_dir.check(dir=True)
    assert dest_dir.join('index.html').check()
    assert result.ret == 0


def test_html_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=html:' + DEST_DIR, script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage HTML written to dir ' + DEST_DIR,
            '*10 passed*',
        ]
    )
    dest_dir = testdir.tmpdir.join(DEST_DIR)
    assert dest_dir.check(dir=True)
    assert dest_dir.join('index.html').check()
    assert result.ret == 0


def test_term_report_does_not_interact_with_html_output(testdir):
    script = testdir.makepyfile(test_funcarg=SCRIPT_FUNCARG)

    result = testdir.runpytest(
        '-v', f'--cov={script.dirpath()}', '--cov-report=term-missing:skip-covered', '--cov-report=html:' + DEST_DIR, script
    )

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage HTML written to dir ' + DEST_DIR,
            '*1 passed*',
        ]
    )
    dest_dir = testdir.tmpdir.join(DEST_DIR)
    assert dest_dir.check(dir=True)
    expected = [dest_dir.join('index.html'), dest_dir.join('test_funcarg_py.html')]
    if coverage.version_info >= (7, 5):
        expected.insert(0, dest_dir.join('function_index.html'))
        expected.insert(0, dest_dir.join('class_index.html'))
    assert sorted(dest_dir.visit('**/*.html')) == expected
    assert dest_dir.join('index.html').check()
    assert result.ret == 0


def test_html_configured_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write(
        """
[html]
directory = somewhere
"""
    )
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=html', script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage HTML written to dir somewhere',
            '*10 passed*',
        ]
    )
    dest_dir = testdir.tmpdir.join('somewhere')
    assert dest_dir.check(dir=True)
    assert dest_dir.join('index.html').check()
    assert result.ret == 0


def test_xml_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=xml:' + XML_REPORT_NAME, script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage XML written to file ' + XML_REPORT_NAME,
            '*10 passed*',
        ]
    )
    assert testdir.tmpdir.join(XML_REPORT_NAME).check()
    assert result.ret == 0


def test_json_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', '--cov=%s' % script.dirpath(), '--cov-report=json:' + JSON_REPORT_NAME, script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage JSON written to file ' + JSON_REPORT_NAME,
            '*10 passed*',
        ]
    )
    assert testdir.tmpdir.join(JSON_REPORT_NAME).check()
    assert result.ret == 0


@pytest.mark.skipif('coverage.version_info < (6, 3)')
def test_lcov_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=lcov:' + LCOV_REPORT_NAME, script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Coverage LCOV written to file ' + LCOV_REPORT_NAME,
            '*10 passed*',
        ]
    )
    assert testdir.tmpdir.join(LCOV_REPORT_NAME).check()
    assert result.ret == 0


@pytest.mark.skipif('coverage.version_info >= (6, 3)')
def test_lcov_not_supported(testdir):
    script = testdir.makepyfile('a = 1')
    result = testdir.runpytest(
        '-v',
        f'--cov={script.dirpath()}',
        '--cov-report=lcov',
        script,
    )
    result.stderr.fnmatch_lines(
        [
            '*argument --cov-report: LCOV output is only supported with coverage.py >= 6.3',
        ]
    )
    assert result.ret != 0


def test_term_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term:' + DEST_DIR, script)

    result.stderr.fnmatch_lines(
        [
            f'*argument --cov-report: output specifier not supported for: "term:{DEST_DIR}"*',
        ]
    )
    assert result.ret != 0


def test_term_missing_output_dir(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing:' + DEST_DIR, script)

    result.stderr.fnmatch_lines(
        [
            '*argument --cov-report: output specifier not supported for: "term-missing:%s"*' % DEST_DIR,
        ]
    )
    assert result.ret != 0


def test_cov_min_100(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--cov-fail-under=100', script)

    assert result.ret != 0
    result.stdout.fnmatch_lines(['FAIL Required test coverage of 100% not reached. Total coverage: *%'])


def test_cov_min_100_passes_if_collectonly(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest(
        '-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--cov-fail-under=100', '--collect-only', script
    )

    assert result.ret == 0


def test_cov_min_50(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=html', '--cov-report=xml', '--cov-fail-under=50', script)

    assert result.ret == 0
    result.stdout.fnmatch_lines(['Required test coverage of 50% reached. Total coverage: *%'])


def test_cov_min_float_value(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--cov-fail-under=88.88', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['Required test coverage of 88.88% reached. Total coverage: 88.89%'])


def test_cov_min_float_value_not_reached(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write("""
[report]
precision = 3
""")
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--cov-fail-under=88.89', script)
    assert result.ret == 1
    result.stdout.fnmatch_lines(['FAIL Required test coverage of 88.89% not reached. Total coverage: 88.89%'])


def test_cov_min_float_value_not_reached_cli(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(
        '-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--cov-precision=3', '--cov-fail-under=88.89', script
    )
    assert result.ret == 1
    result.stdout.fnmatch_lines(['FAIL Required test coverage of 88.89% not reached. Total coverage: 88.89%'])


def test_cov_precision(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--cov-precision=6', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            'Name                    Stmts   Miss       Cover   Missing',
            '----------------------------------------------------------',
            'test_cov_precision.py       9      1  88.888889%   11',
            '----------------------------------------------------------',
            'TOTAL                       9      1  88.888889%',
        ]
    )


def test_cov_precision_from_config(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('pyproject.toml').write("""
[tool.coverage.report]
precision = 6""")
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            'Name                                Stmts   Miss       Cover   Missing',
            '----------------------------------------------------------------------',
            'test_cov_precision_from_config.py       9      1  88.888889%   11',
            '----------------------------------------------------------------------',
            'TOTAL                                   9      1  88.888889%',
        ]
    )


def test_cov_min_no_report(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=', '--cov-fail-under=50', script)

    assert result.ret == 0
    result.stdout.fnmatch_lines(['Required test coverage of 50% reached. Total coverage: *%'])


def test_central_nonspecific(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest('-v', '--cov', '--cov-report=term-missing', script, *prop.args)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_central_nonspecific* {prop.result} *', '*10 passed*'])

    # multi-module coverage report
    assert any(line.startswith('TOTAL ') for line in result.stdout.lines)

    assert result.ret == 0


def test_cov_min_from_coveragerc(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write(
        """
[report]
fail_under = 100
"""
    )

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    assert result.ret != 0


def test_central_coveragerc(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(COVERAGERC_SOURCE + prop.conf)

    result = testdir.runpytest('-v', '--cov', '--cov-report=term-missing', script, *prop.args)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'test_central_coveragerc* {prop.result} *',
            '*10 passed*',
        ]
    )
    assert result.ret == 0


@xdist_params
def test_central_with_path_aliasing(pytester, testdir, monkeypatch, opts, prop):
    mod1 = testdir.mkdir('src').join('mod.py')
    mod1.write(SCRIPT)
    mod2 = testdir.mkdir('aliased').join('mod.py')
    mod2.write(SCRIPT)
    script = testdir.makepyfile(
        """
from mod import *
"""
    )
    testdir.tmpdir.join('setup.cfg').write(
        f"""
[coverage:paths]
source =
    src
    aliased
[coverage:run]
source = mod
parallel = true
{prop.conf}
"""
    )

    monkeypatch.setitem(os.environ, 'PYTHONPATH', os.pathsep.join([os.environ.get('PYTHONPATH', ''), 'aliased']))
    result = testdir.runpytest('-v', '-s', '--cov', '--cov-report=term-missing', script, *opts.split() + prop.args)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'src[\\/]mod* {prop.result} *',
            '*10 passed*',
        ]
    )
    assert result.ret == 0


@xdist_params
def test_borken_cwd(pytester, testdir, monkeypatch, opts):
    testdir.makepyfile(
        mod="""
def foobar(a, b):
    return a + b
"""
    )

    script = testdir.makepyfile(
        """
import os
import tempfile
import pytest
import mod

@pytest.fixture
def bad():
    path = tempfile.mkdtemp('test_borken_cwd')
    os.chdir(path)
    yield
    try:
        os.rmdir(path)
    except OSError:
        pass

def test_foobar(bad):
    assert mod.foobar(1, 2) == 3
"""
    )
    result = testdir.runpytest('-v', '-s', '--cov=mod', '--cov-branch', script, *opts.split())

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            '*mod* 100%',
            '*1 passed*',
        ]
    )

    assert result.ret == 0


def test_subprocess_with_path_aliasing(pytester, testdir, monkeypatch):
    src = testdir.mkdir('src')
    src.join('parent_script.py').write(SCRIPT_PARENT)
    src.join('child_script.py').write(SCRIPT_CHILD)
    aliased = testdir.mkdir('aliased')
    parent_script = aliased.join('parent_script.py')
    parent_script.write(SCRIPT_PARENT)
    aliased.join('child_script.py').write(SCRIPT_CHILD)

    testdir.tmpdir.join('.coveragerc').write(
        """
[paths]
source =
    src
    aliased
[run]
source =
    parent_script
    child_script
parallel = true
"""
    )

    monkeypatch.setitem(os.environ, 'PYTHONPATH', os.pathsep.join([os.environ.get('PYTHONPATH', ''), 'aliased']))
    result = testdir.runpytest('-v', '--cov', '--cov-report=term-missing', parent_script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'src[\\/]child_script* {CHILD_SCRIPT_RESULT}*',
            f'src[\\/]parent_script* {PARENT_SCRIPT_RESULT}*',
        ]
    )
    assert result.ret == 0


def test_show_missing_coveragerc(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(
        f"""
[run]
source = .
{prop.conf}

[report]
show_missing = true
"""
    )

    result = testdir.runpytest('-v', '--cov', '--cov-report=term', script, *prop.args)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'Name * Stmts * Miss * Cover * Missing',
            f'test_show_missing_coveragerc* {prop.result} * 11*',
            '*10 passed*',
        ]
    )

    assert result.ret == 0


def test_no_cov_on_fail(testdir):
    script = testdir.makepyfile(
        """
def test_fail():
    assert False

"""
    )

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--no-cov-on-fail', script)

    assert 'coverage: platform' not in result.stdout.str()
    result.stdout.fnmatch_lines(['*1 failed*'])


def test_no_cov(pytester, testdir, monkeypatch):
    script = testdir.makepyfile(SCRIPT)
    testdir.makeini(
        """
        [pytest]
        addopts=--no-cov
    """
    )
    result = testdir.runpytest('-vvv', f'--cov={script.dirpath()}', '--cov-report=term-missing', '-rw', script)
    result.stdout.fnmatch_lines_random(
        [
            'WARNING: Coverage disabled via --no-cov switch!',
            '*Coverage disabled via --no-cov switch!',
        ]
    )


def test_cov_and_failure_report_on_fail(testdir):
    script = testdir.makepyfile(
        SCRIPT
        + """
def test_fail(p):
    assert False

"""
    )

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-fail-under=100', '--cov-report=html', script)

    result.stdout.fnmatch_lines_random(
        [
            '*10 failed*',
            '*coverage: platform*',
            '*FAIL Required test coverage of 100% not reached*',
            '*assert False*',
        ]
    )


@pytest.mark.skipif('sys.platform == "win32" or platform.python_implementation() == "PyPy"')
def test_dist_combine_racecondition(testdir):
    script = testdir.makepyfile(
        """
import pytest

@pytest.mark.parametrize("foo", range(1000))
def test_foo(foo):
"""
        + '\n'.join(
            f"""
    if foo == {i}:
        assert True
"""
            for i in range(1000)
        )
    )

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '-n', '5', '-s', script)
    result.stdout.fnmatch_lines(['test_dist_combine_racecondition* 0 * 100%*', '*1000 passed*'])

    for line in chain(result.stdout.lines, result.stderr.lines):
        assert 'The following workers failed to return coverage data' not in line
        assert 'INTERNALERROR' not in line
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_dist_collocated(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest(
        '-v',
        f'--cov={script.dirpath()}',
        '--cov-report=term-missing',
        '--dist=load',
        '--tx=2*popen',
        max_worker_restart_0,
        script,
        *prop.args,
    )

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_dist_collocated* {prop.result} *', '*10 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_dist_not_collocated(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    dir1 = testdir.mkdir('dir1')
    dir2 = testdir.mkdir('dir2')
    testdir.tmpdir.join('.coveragerc').write(
        f"""
[run]
{prop.conf}
[paths]
source =
    .
    dir1
    dir2"""
    )

    result = testdir.runpytest(
        '-v',
        f'--cov={script.dirpath()}',
        '--cov-report=term-missing',
        '--dist=load',
        f'--tx=popen//chdir={dir1}',
        f'--tx=popen//chdir={dir2}',
        f'--rsyncdir={script.basename}',
        '--rsyncdir=.coveragerc',
        max_worker_restart_0,
        '-s',
        script,
        *prop.args,
    )

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_dist_not_collocated* {prop.result} *', '*10 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_dist_not_collocated_coveragerc_source(pytester, testdir, prop):
    script = testdir.makepyfile(prop.code)
    dir1 = testdir.mkdir('dir1')
    dir2 = testdir.mkdir('dir2')
    testdir.tmpdir.join('.coveragerc').write(
        f"""
[run]
{prop.conf}
source = {script.dirpath()}
[paths]
source =
    .
    dir1
    dir2"""
    )

    result = testdir.runpytest(
        '-v',
        '--cov',
        '--cov-report=term-missing',
        '--dist=load',
        f'--tx=popen//chdir={dir1}',
        f'--tx=popen//chdir={dir2}',
        f'--rsyncdir={script.basename}',
        '--rsyncdir=.coveragerc',
        max_worker_restart_0,
        '-s',
        script,
        *prop.args,
    )

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_dist_not_collocated* {prop.result} *', '*10 passed*'])
    assert result.ret == 0


def test_central_subprocess(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest('-v', f'--cov={scripts.dirpath()}', '--cov-report=term-missing', parent_script)

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'child_script* {CHILD_SCRIPT_RESULT}*',
            f'parent_script* {PARENT_SCRIPT_RESULT}*',
        ]
    )
    assert result.ret == 0


def test_central_subprocess_change_cwd(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT_CHANGE_CWD, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')
    testdir.makefile(
        '',
        coveragerc="""
[run]
branch = true
parallel = true
""",
    )

    result = testdir.runpytest(
        '-v', '-s', f'--cov={scripts.dirpath()}', '--cov-config=coveragerc', '--cov-report=term-missing', parent_script
    )

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'*child_script* {CHILD_SCRIPT_RESULT}*',
            '*parent_script* 100%*',
        ]
    )
    assert result.ret == 0


def test_central_subprocess_change_cwd_with_pythonpath(pytester, testdir, monkeypatch):
    stuff = testdir.mkdir('stuff')
    parent_script = stuff.join('parent_script.py')
    parent_script.write(SCRIPT_PARENT_CHANGE_CWD_IMPORT_CHILD)
    stuff.join('child_script.py').write(SCRIPT_CHILD)
    testdir.makefile(
        '',
        coveragerc="""
[run]
parallel = true
""",
    )

    monkeypatch.setitem(os.environ, 'PYTHONPATH', str(stuff))
    result = testdir.runpytest(
        '-vv', '-s', '--cov=child_script', '--cov-config=coveragerc', '--cov-report=term-missing', '--cov-branch', parent_script
    )

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'*child_script* {CHILD_SCRIPT_RESULT}*',
        ]
    )
    assert result.ret == 0


def test_central_subprocess_no_subscript(testdir):
    script = testdir.makepyfile(
        """
import subprocess, sys

def test_foo():
    subprocess.check_call([sys.executable, '-c', 'print("Hello World")'])
"""
    )
    testdir.makefile(
        '',
        coveragerc="""
[run]
parallel = true
""",
    )
    result = testdir.runpytest('-v', '--cov-config=coveragerc', f'--cov={script.dirpath()}', '--cov-branch', script)
    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            'test_central_subprocess_no_subscript* * 3 * 0 * 100%*',
        ]
    )
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_dist_subprocess_collocated(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest(
        '-v', f'--cov={scripts.dirpath()}', '--cov-report=term-missing', '--dist=load', '--tx=2*popen', max_worker_restart_0, parent_script
    )

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'child_script* {CHILD_SCRIPT_RESULT}*',
            f'parent_script* {PARENT_SCRIPT_RESULT}*',
        ]
    )
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_dist_subprocess_not_collocated(pytester, testdir, tmpdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')
    child_script = scripts.dirpath().join('child_script.py')

    dir1 = tmpdir.mkdir('dir1')
    dir2 = tmpdir.mkdir('dir2')
    testdir.tmpdir.join('.coveragerc').write(
        f"""
[paths]
source =
    {scripts.dirpath()}
    */dir1
    */dir2
"""
    )
    result = testdir.runpytest(
        '-v',
        f'--cov={scripts.dirpath()}',
        '--dist=load',
        f'--tx=popen//chdir={dir1}',
        f'--tx=popen//chdir={dir2}',
        f'--rsyncdir={child_script}',
        f'--rsyncdir={parent_script}',
        '--rsyncdir=.coveragerc',
        max_worker_restart_0,
        parent_script,
    )

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'child_script* {CHILD_SCRIPT_RESULT}*',
            f'parent_script* {PARENT_SCRIPT_RESULT}*',
        ]
    )
    assert result.ret == 0


def test_invalid_coverage_source(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.makeini(
        """
        [pytest]
        console_output_style=classic
    """
    )
    result = testdir.runpytest('-v', '--cov=non_existent_module', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*10 passed*'])
    result.stderr.fnmatch_lines(['*No data was collected.*'])
    result.stdout.fnmatch_lines(
        [
            '*Failed to generate report: No data to report.',
        ]
    )
    assert result.ret == 0

    matching_lines = [line for line in result.outlines if '%' in line]
    assert not matching_lines


@pytest.mark.skipif("'dev' in pytest.__version__")
@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
@pytest.mark.skipif(
    'tuple(map(int, xdist.__version__.split("."))) >= (2, 3, 0)',
    reason='Since pytest-xdist 2.3.0 the parent sys.path is copied in the child process',
)
def test_dist_missing_data(testdir):
    """Test failure when using a worker without pytest-cov installed."""
    venv_path = os.path.join(str(testdir.tmpdir), 'venv')
    virtualenv.cli_run([venv_path])
    if sys.platform == 'win32':
        if platform.python_implementation() == 'PyPy':
            exe = os.path.join(venv_path, 'bin', 'python.exe')
        else:
            exe = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        exe = os.path.join(venv_path, 'bin', 'python')
    subprocess.check_call(
        [exe, '-mpip', 'install', f'py=={py.__version__}', f'pytest=={pytest.__version__}', f'pytest_xdist=={xdist.__version__}']
    )
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest(
        '-v',
        '--assert=plain',
        f'--cov={script.dirpath()}',
        '--cov-report=term-missing',
        '--dist=load',
        f'--tx=popen//python={exe}',
        max_worker_restart_0,
        str(script),
    )
    result.stdout.fnmatch_lines(
        ['The following workers failed to return coverage data, ensure that pytest-cov is installed on these workers.']
    )


def test_funcarg(testdir):
    script = testdir.makepyfile(SCRIPT_FUNCARG)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', 'test_funcarg* 3 * 100%*', '*1 passed*'])
    assert result.ret == 0


def test_funcarg_not_active(testdir):
    script = testdir.makepyfile(SCRIPT_FUNCARG_NOT_ACTIVE)

    result = testdir.runpytest('-v', script)

    result.stdout.fnmatch_lines(['*1 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32"', reason="SIGTERM isn't really supported on Windows")
@pytest.mark.xfail('platform.python_implementation() == "PyPy"', reason='Interpreter seems buggy')
def test_cleanup_on_sigterm(testdir):
    script = testdir.makepyfile(
        '''
import os, signal, subprocess, sys, time

def cleanup(num, frame):
    print("num == signal.SIGTERM => %s" % (num == signal.SIGTERM))
    raise Exception()

def test_run():
    proc = subprocess.Popen([sys.executable, __file__], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)
    proc.terminate()
    stdout, stderr = proc.communicate()
    assert not stderr
    assert stdout == b"""num == signal.SIGTERM => True
captured Exception()
"""
    assert proc.returncode == 0

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, cleanup)

    from pytest_cov.embed import cleanup_on_sigterm
    cleanup_on_sigterm()

    try:
        time.sleep(10)
    except BaseException as exc:
        print("captured %r" % exc)
'''
    )

    result = testdir.runpytest('-vv', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', 'test_cleanup_on_sigterm* 26-27', '*1 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform != "win32"')
@pytest.mark.parametrize(
    'setup',
    [
        ('signal.signal(signal.SIGBREAK, signal.SIG_DFL); cleanup_on_signal(signal.SIGBREAK)', '87%   21-22'),
        ('cleanup_on_signal(signal.SIGBREAK)', '87%   21-22'),
        ('cleanup()', '73%   19-22'),
    ],
)
def test_cleanup_on_sigterm_sig_break(pytester, testdir, setup):
    # worth a read: https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/
    script = testdir.makepyfile(
        """
import os, signal, subprocess, sys, time

def test_run():
    proc = subprocess.Popen(
        [sys.executable, __file__],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, shell=True
    )
    time.sleep(1)
    proc.send_signal(signal.CTRL_BREAK_EVENT)
    stdout, stderr = proc.communicate()
    assert not stderr
    assert stdout in [b"^C", b"", b"captured IOError(4, 'Interrupted function call')\\n"]

if __name__ == "__main__":
    from pytest_cov.embed import cleanup_on_signal, cleanup
    """
        + setup[0]
        + """

    try:
        time.sleep(10)
    except BaseException as exc:
        print("captured %r" % exc)
"""
    )

    result = testdir.runpytest('-vv', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_cleanup_on_sigterm* {setup[1]}', '*1 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32"', reason="SIGTERM isn't really supported on Windows")
@pytest.mark.xfail('sys.platform == "darwin"', reason='Something weird going on Macs...')
@pytest.mark.xfail('platform.python_implementation() == "PyPy"', reason='Interpreter seems buggy')
@pytest.mark.parametrize(
    'setup',
    [
        ('signal.signal(signal.SIGTERM, signal.SIG_DFL); cleanup_on_sigterm()', '88%   18-19'),
        ('cleanup_on_sigterm()', '88%   18-19'),
        ('cleanup()', '75%   16-19'),
    ],
)
def test_cleanup_on_sigterm_sig_dfl(pytester, testdir, setup):
    script = testdir.makepyfile(
        """
import os, signal, subprocess, sys, time

def test_run():
    proc = subprocess.Popen([sys.executable, __file__], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)
    proc.terminate()
    stdout, stderr = proc.communicate()
    assert not stderr
    assert stdout == b""
    assert proc.returncode in [128 + signal.SIGTERM, -signal.SIGTERM]

if __name__ == "__main__":
    from pytest_cov.embed import cleanup_on_sigterm, cleanup
    """
        + setup[0]
        + """

    try:
        time.sleep(10)
    except BaseException as exc:
        print("captured %r" % exc)
"""
    )

    result = testdir.runpytest('-vv', '--assert=plain', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_cleanup_on_sigterm* {setup[1]}', '*1 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32"', reason='SIGINT is subtly broken on Windows')
@pytest.mark.xfail('sys.platform == "darwin"', reason='Something weird going on Macs...')
@pytest.mark.xfail('platform.python_implementation() == "PyPy"', reason='Interpreter seems buggy')
def test_cleanup_on_sigterm_sig_dfl_sigint(testdir):
    script = testdir.makepyfile(
        '''
import os, signal, subprocess, sys, time

def test_run():
    proc = subprocess.Popen([sys.executable, __file__], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)
    proc.send_signal(signal.SIGINT)
    stdout, stderr = proc.communicate()
    assert not stderr
    assert stdout == b"""captured KeyboardInterrupt()
"""
    assert proc.returncode == 0

if __name__ == "__main__":
    from pytest_cov.embed import cleanup_on_signal
    cleanup_on_signal(signal.SIGINT)

    try:
        time.sleep(10)
    except BaseException as exc:
        print("captured %r" % exc)
'''
    )

    result = testdir.runpytest('-vv', '--assert=plain', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', 'test_cleanup_on_sigterm* 88%   19-20', '*1 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32"', reason='fork not available on Windows')
@pytest.mark.xfail('platform.python_implementation() == "PyPy"', reason='Interpreter seems buggy')
def test_cleanup_on_sigterm_sig_ign(testdir):
    script = testdir.makepyfile(
        """
import os, signal, subprocess, sys, time

def test_run():
    proc = subprocess.Popen([sys.executable, __file__], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)
    proc.send_signal(signal.SIGINT)
    time.sleep(1)
    proc.terminate()
    stdout, stderr = proc.communicate()
    assert not stderr
    assert stdout == b""
    assert proc.returncode in [128 + signal.SIGTERM, -signal.SIGTERM]

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    from pytest_cov.embed import cleanup_on_signal
    cleanup_on_signal(signal.SIGINT)

    try:
        time.sleep(10)
    except BaseException as exc:
        print("captured %r" % exc)
    """
    )

    result = testdir.runpytest('-vv', '--assert=plain', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', 'test_cleanup_on_sigterm* 89%   22-23', '*1 passed*'])
    assert result.ret == 0


MODULE = """
def func():
    return 1

"""

CONFTEST = """

import mod
mod.func()

"""

BASIC_TEST = """

def test_basic():
    x = True
    assert x

"""

CONF_RESULT = 'mod* 2 * 100%*'


def test_cover_conftest(testdir):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([CONF_RESULT])


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_cover_looponfail(testdir, monkeypatch):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)

    def mock_run(*args, **kwargs):
        return _TestProcess(*map(str, args))

    monkeypatch.setattr(testdir, 'run', mock_run)
    assert testdir.run is mock_run
    if hasattr(testdir, '_pytester'):
        monkeypatch.setattr(testdir._pytester, 'run', mock_run)
        assert testdir._pytester.run is mock_run
    with testdir.runpytest('-v', f'--cov={script.dirpath()}', '--looponfail', script) as process:
        with dump_on_error(process.read):
            wait_for_strings(process.read, 30, 'Stmts   Miss  Cover')  # 30 seconds


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_cover_conftest_dist(testdir):
    testdir.makepyfile(mod=MODULE)
    testdir.makeconftest(CONFTEST)
    script = testdir.makepyfile(BASIC_TEST)
    result = testdir.runpytest(
        '-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', '--dist=load', '--tx=2*popen', max_worker_restart_0, script
    )
    assert result.ret == 0
    result.stdout.fnmatch_lines([CONF_RESULT])


def test_no_cover_marker(testdir):
    testdir.makepyfile(mod=MODULE)
    script = testdir.makepyfile(
        """
import pytest
import mod
import subprocess
import sys

@pytest.mark.no_cover
def test_basic():
    mod.func()
    subprocess.check_call([sys.executable, '-c', 'from mod import func; func()'])
"""
    )
    result = testdir.runpytest('-v', '-ra', '--strict', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['mod* 2 * 1 * 50% * 2'])


def test_no_cover_fixture(testdir):
    testdir.makepyfile(mod=MODULE)
    script = testdir.makepyfile(
        """
import mod
import subprocess
import sys

def test_basic(no_cover):
    mod.func()
    subprocess.check_call([sys.executable, '-c', 'from mod import func; func()'])
"""
    )
    result = testdir.runpytest('-v', '-ra', '--strict', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines(['mod* 2 * 1 * 50% * 2'])


COVERAGERC = """
[report]
# Regexes for lines to exclude from consideration
exclude_lines =
    raise NotImplementedError
"""
PYPROJECTTOML = """
[tool.coverage.report]
# Regexes for lines to exclude from consideration
exclude_lines = [
    'raise NotImplementedError',
]
"""

EXCLUDED_TEST = """

def func():
    raise NotImplementedError

def test_basic():
    x = True
    assert x

"""

EXCLUDED_RESULT = '4 * 100%*'


def test_coveragerc(testdir):
    testdir.makefile('', coveragerc=COVERAGERC)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest('-v', '--cov-config=coveragerc', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([f'test_coveragerc* {EXCLUDED_RESULT}'])


def test_pyproject_toml(testdir):
    testdir.makefile('.toml', pyproject=PYPROJECTTOML)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([f'test_pyproject_toml* {EXCLUDED_RESULT}'])


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_coveragerc_dist(testdir):
    testdir.makefile('', coveragerc=COVERAGERC)
    script = testdir.makepyfile(EXCLUDED_TEST)
    result = testdir.runpytest(
        '-v', '--cov-config=coveragerc', f'--cov={script.dirpath()}', '--cov-report=term-missing', '-n', '2', max_worker_restart_0, script
    )
    assert result.ret == 0
    result.stdout.fnmatch_lines([f'test_coveragerc_dist* {EXCLUDED_RESULT}'])


SKIP_COVERED_COVERAGERC = """
[report]
skip_covered = True

"""

SKIP_COVERED_TEST = """

def func():
    return "full coverage"

def test_basic():
    assert func() == "full coverage"

"""

SKIP_COVERED_RESULT = '1 file skipped due to complete coverage.'


@pytest.mark.parametrize('report_option', ['term-missing:skip-covered', 'term:skip-covered'])
def test_skip_covered_cli(pytester, testdir, report_option):
    testdir.makefile('', coveragerc=SKIP_COVERED_COVERAGERC)
    script = testdir.makepyfile(SKIP_COVERED_TEST)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', f'--cov-report={report_option}', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([SKIP_COVERED_RESULT])


def test_skip_covered_coveragerc_config(testdir):
    testdir.makefile('', coveragerc=SKIP_COVERED_COVERAGERC)
    script = testdir.makepyfile(SKIP_COVERED_TEST)
    result = testdir.runpytest('-v', '--cov-config=coveragerc', f'--cov={script.dirpath()}', script)
    assert result.ret == 0
    result.stdout.fnmatch_lines([SKIP_COVERED_RESULT])


CLEAR_ENVIRON_TEST = """

import os

def test_basic():
    os.environ.clear()

"""


def test_clear_environ(testdir):
    script = testdir.makepyfile(CLEAR_ENVIRON_TEST)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=term-missing', script)
    assert result.ret == 0


SCRIPT_SIMPLE = """

def test_foo():
    assert 1 == 1
    x = True
    assert x

"""

SCRIPT_SIMPLE_RESULT = '4 * 100%'


@pytest.mark.skipif('tuple(map(int, xdist.__version__.split("."))) >= (3, 0, 2)', reason='--boxed option was removed in version 3.0.2')
@pytest.mark.skipif('sys.platform == "win32"')
def test_dist_boxed(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)

    result = testdir.runpytest('-v', '--assert=plain', f'--cov={script.dirpath()}', '--boxed', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_dist_boxed* {SCRIPT_SIMPLE_RESULT}*', '*1 passed*'])
    assert result.ret == 0


@pytest.mark.skipif('sys.platform == "win32"')
@pytest.mark.skipif('platform.python_implementation() == "PyPy"', reason='strange optimization on PyPy3')
def test_dist_bare_cov(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)

    result = testdir.runpytest('-v', '--cov', '-n', '1', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_dist_bare_cov* {SCRIPT_SIMPLE_RESULT}*', '*1 passed*'])
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

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script)

    result.stdout.fnmatch_lines(['*coverage*'])
    assert result.ret == 0


def test_disabled_output(testdir):
    script = testdir.makepyfile(SCRIPT)

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-report=', script)

    stdout = result.stdout.str()
    # We don't want the path to the executable to fail the test if we happen
    # to put the project in a directory with "coverage" in it.
    stdout = stdout.replace(sys.executable, '<SYS.EXECUTABLE>')
    assert 'coverage' not in stdout
    assert result.ret == 0


def test_coverage_file(testdir):
    script = testdir.makepyfile(SCRIPT)
    data_file_name = 'covdata'
    os.environ['COVERAGE_FILE'] = data_file_name
    try:
        result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script)
        assert result.ret == 0
        data_file = testdir.tmpdir.join(data_file_name)
        assert data_file.check()
    finally:
        os.environ.pop('COVERAGE_FILE')


def test_external_data_file(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write(
        """
[run]
data_file = %s
"""
        % testdir.tmpdir.join('some/special/place/coverage-data').ensure()
    )

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script)
    assert result.ret == 0
    assert glob.glob(str(testdir.tmpdir.join('some/special/place/coverage-data*')))


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_external_data_file_xdist(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write(
        """
[run]
parallel = true
data_file = %s
"""
        % testdir.tmpdir.join('some/special/place/coverage-data').ensure()
    )

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '-n', '1', max_worker_restart_0, script)
    assert result.ret == 0
    assert glob.glob(str(testdir.tmpdir.join('some/special/place/coverage-data*')))


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_xdist_no_data_collected(testdir):
    testdir.makepyfile(target='x = 123')
    script = testdir.makepyfile(
        """
import target
def test_foobar():
    assert target.x == 123
"""
    )
    result = testdir.runpytest('-v', '--cov=target', '-n', '1', script)
    assert 'no-data-collected' not in result.stderr.str()
    assert 'no-data-collected' not in result.stdout.str()
    assert 'module-not-imported' not in result.stderr.str()
    assert 'module-not-imported' not in result.stdout.str()
    assert result.ret == 0


def test_external_data_file_negative(testdir):
    script = testdir.makepyfile(SCRIPT)
    testdir.tmpdir.join('.coveragerc').write('')

    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script)
    assert result.ret == 0
    assert glob.glob(str(testdir.tmpdir.join('.coverage*')))


@xdist_params
def test_append_coverage(pytester, testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script, *opts.split() + prop.args)
    result.stdout.fnmatch_lines(
        [
            f'test_1* {prop.result}*',
        ]
    )
    script2 = testdir.makepyfile(test_2=prop.code2)
    result = testdir.runpytest('-v', '--cov-append', f'--cov={script2.dirpath()}', script2, *opts.split() + prop.args)
    result.stdout.fnmatch_lines(
        [
            f'test_1* {prop.result}*',
            f'test_2* {prop.result2}*',
        ]
    )


@xdist_params
def test_coverage_plugin(pytester, testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.makepyfile(
        coverageplugin="""
import coverage

class ExamplePlugin(coverage.CoveragePlugin):
    pass

def coverage_init(reg, options):
    reg.add_file_tracer(ExamplePlugin())
"""
    )
    testdir.makepyprojecttoml(f"""
[tool.coverage.run]
plugins = ["coverageplugin"]
concurrency = ["thread", "multiprocessing"]
{prop.conf}
""")
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script, *opts.split() + prop.args)
    result.stdout.fnmatch_lines(
        [
            f'test_1* {prop.result}*',
        ]
    )


@xdist_params
def test_dynamic_context(pytester, testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.makepyprojecttoml(f"""
[tool.coverage.run]
dynamic_context = "test_function"
parallel = true
{prop.conf}
""")
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script, *opts.split() + prop.args)
    if opts:
        result.stderr.fnmatch_lines(['pytest_cov.DistCovError: Detected dynamic_context=test_function*'])
    else:
        result.stdout.fnmatch_lines(
            [
                '* CentralCovContextWarning: Detected dynamic_context=test_function*',
                f'test_1* {prop.result}*',
            ]
        )


@xdist_params
def test_simple(pytester, testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.makepyprojecttoml(f"""
[tool.coverage.run]
parallel = true
{prop.conf}
""")
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script, *opts.split() + prop.args)
    result.stdout.fnmatch_lines(
        [
            f'test_1* {prop.result}*',
        ]
    )


@xdist_params
def test_do_not_append_coverage(pytester, testdir, opts, prop):
    script = testdir.makepyfile(test_1=prop.code)
    testdir.tmpdir.join('.coveragerc').write(prop.fullconf)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', script, *opts.split() + prop.args)
    result.stdout.fnmatch_lines(
        [
            f'test_1* {prop.result}*',
        ]
    )
    script2 = testdir.makepyfile(test_2=prop.code2)
    result = testdir.runpytest('-v', f'--cov={script2.dirpath()}', script2, *opts.split() + prop.args)
    result.stdout.fnmatch_lines(
        [
            'test_1* 0%',
            f'test_2* {prop.result2}*',
        ]
    )


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_append_coverage_subprocess(testdir):
    scripts = testdir.makepyfile(parent_script=SCRIPT_PARENT, child_script=SCRIPT_CHILD)
    parent_script = scripts.dirpath().join('parent_script.py')

    result = testdir.runpytest(
        '-v',
        f'--cov={scripts.dirpath()}',
        '--cov-append',
        '--cov-report=term-missing',
        '--dist=load',
        '--tx=2*popen',
        max_worker_restart_0,
        parent_script,
    )

    result.stdout.fnmatch_lines(
        [
            '*_ coverage: platform *, python * _*',
            f'child_script* {CHILD_SCRIPT_RESULT}*',
            f'parent_script* {PARENT_SCRIPT_RESULT}*',
        ]
    )
    assert result.ret == 0


def test_pth_failure(monkeypatch):
    with open('src/pytest-cov.pth') as fh:
        payload = fh.read()

    class SpecificError(Exception):
        pass

    def bad_init():
        raise SpecificError

    buff = StringIO()

    from pytest_cov import embed

    monkeypatch.setattr(embed, 'init', bad_init)
    monkeypatch.setattr(sys, 'stderr', buff)
    monkeypatch.setitem(os.environ, 'COV_CORE_SOURCE', 'foobar')
    exec(payload)
    expected = "pytest-cov: Failed to setup subprocess coverage. Environ: {'COV_CORE_SOURCE': 'foobar'} Exception: SpecificError()\n"
    assert buff.getvalue() == expected


def test_double_cov(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v', '--assert=plain', '--cov', f'--cov={script.dirpath()}', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_double_cov* {SCRIPT_SIMPLE_RESULT}*', '*1 passed*'])
    assert result.ret == 0


def test_double_cov2(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v', '--assert=plain', '--cov', '--cov', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_double_cov2* {SCRIPT_SIMPLE_RESULT}*', '*1 passed*'])
    assert result.ret == 0


def test_cov_reset(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v', '--assert=plain', f'--cov={script.dirpath()}', '--cov-reset', script)

    assert 'coverage: platform' not in result.stdout.str()


def test_cov_reset_then_set(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v', '--assert=plain', f'--cov={script.dirpath()}', '--cov-reset', f'--cov={script.dirpath()}', script)

    result.stdout.fnmatch_lines(['*_ coverage: platform *, python * _*', f'test_cov_reset_then_set* {SCRIPT_SIMPLE_RESULT}*', '*1 passed*'])


@pytest.mark.skipif('sys.platform == "win32" and platform.python_implementation() == "PyPy"')
def test_cov_and_no_cov(testdir):
    script = testdir.makepyfile(SCRIPT_SIMPLE)
    result = testdir.runpytest('-v', '--cov', '--no-cov', '-n', '1', '-s', script)
    assert 'Coverage disabled via --no-cov switch!' not in result.stdout.str()
    assert 'Coverage disabled via --no-cov switch!' not in result.stderr.str()
    assert result.ret == 0


def find_labels(text, pattern):
    all_labels = collections.defaultdict(set)
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        labels = re.findall(pattern, line)
        for label in labels:
            all_labels[label].add(lineno)
    return all_labels


# The contexts and their labels in contextful.py
EXPECTED_CONTEXTS = {
    '': 'c0',
    'test_contexts.py::test_01|run': 'r1',
    'test_contexts.py::test_02|run': 'r2',
    'test_contexts.py::OldStyleTests::test_03|setup': 's3',
    'test_contexts.py::OldStyleTests::test_03|run': 'r3',
    'test_contexts.py::OldStyleTests::test_04|run': 'r4',
    'test_contexts.py::OldStyleTests::test_04|teardown': 't4',
    'test_contexts.py::test_05|setup': 's5',
    'test_contexts.py::test_05|run': 'r5',
    'test_contexts.py::test_06|setup': 's6',
    'test_contexts.py::test_06|run': 'r6',
    'test_contexts.py::test_07|setup': 's7',
    'test_contexts.py::test_07|run': 'r7',
    'test_contexts.py::test_08|run': 'r8',
    'test_contexts.py::test_09[1]|setup': 's9-1',
    'test_contexts.py::test_09[1]|run': 'r9-1',
    'test_contexts.py::test_09[2]|setup': 's9-2',
    'test_contexts.py::test_09[2]|run': 'r9-2',
    'test_contexts.py::test_09[3]|setup': 's9-3',
    'test_contexts.py::test_09[3]|run': 'r9-3',
    'test_contexts.py::test_10|run': 'r10',
    'test_contexts.py::test_11[1-101]|run': 'r11-1',
    'test_contexts.py::test_11[2-202]|run': 'r11-2',
    'test_contexts.py::test_12[one]|run': 'r12-1',
    'test_contexts.py::test_12[two]|run': 'r12-2',
    'test_contexts.py::test_13[3-1]|run': 'r13-1',
    'test_contexts.py::test_13[3-2]|run': 'r13-2',
    'test_contexts.py::test_13[4-1]|run': 'r13-3',
    'test_contexts.py::test_13[4-2]|run': 'r13-4',
}


@pytest.mark.skipif('coverage.version_info < (5, 0)')
@pytest.mark.skipif('coverage.version_info > (6, 4)')
@xdist_params
def test_contexts(pytester, testdir, opts):
    with open(os.path.join(os.path.dirname(__file__), 'contextful.py')) as f:
        contextful_tests = f.read()
    script = testdir.makepyfile(contextful_tests)
    result = testdir.runpytest('-v', f'--cov={script.dirpath()}', '--cov-context=test', script, *opts.split())
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            'test_contexts* 100%*',
        ]
    )

    data = coverage.CoverageData('.coverage')
    data.read()
    assert data.measured_contexts() == set(EXPECTED_CONTEXTS)
    measured = data.measured_files()
    assert len(measured) == 1
    test_context_path = next(iter(measured))
    assert test_context_path.lower() == os.path.abspath('test_contexts.py').lower()

    line_data = find_labels(contextful_tests, r'[crst]\d+(?:-\d+)?')
    for context, label in EXPECTED_CONTEXTS.items():
        if context == '':
            continue
        data.set_query_context(context)
        actual = set(data.lines(test_context_path))
        assert line_data[label] == actual, f'Wrong lines for context {context!r}'


@pytest.mark.skipif('coverage.version_info >= (5, 0)')
def test_contexts_not_supported(testdir):
    script = testdir.makepyfile('a = 1')
    result = testdir.runpytest(
        '-v',
        f'--cov={script.dirpath()}',
        '--cov-context=test',
        script,
    )
    result.stderr.fnmatch_lines(
        [
            '*argument --cov-context: Contexts are only supported with coverage.py >= 5.x',
        ]
    )
    assert result.ret != 0


def test_contexts_no_cover(testdir):
    script = testdir.makepyfile("""
import pytest

def foobar():
    return 1

def test_with_coverage():
    foobar()

@pytest.mark.no_cover()
def test_without_coverage():
    foobar()
""")
    result = testdir.runpytest(
        '-v',
        '--cov-context=test',
        '--cov=test_contexts_no_cover',
        script,
    )
    result.stdout.fnmatch_lines(
        [
            'test_contexts_no_cover.py       8      1    88%',
            'TOTAL                           8      1    88%',
        ]
    )
    assert result.stderr.lines == []
    assert result.ret == 0


def test_issue_417(testdir):
    # https://github.com/pytest-dev/pytest-cov/issues/417
    whatever = testdir.maketxtfile(whatever='')
    testdir.inline_genitems(whatever)
