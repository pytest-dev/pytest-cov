"""Tests for pytest-cov.

Known issues:

- If py 2 then can have tx for any py 2, but problems if tx for py 3.

- If py 3.0 then can have tx for py 3.0 / 3.1, but problems if tx for py 2.

- If py 3.1 then can have tx for py 3.1, but problems if tx for py 2 or py 3.0.

- For py 3.0 coverage seems to give incorrect results, it reports all
  covered except the one line which it should have actualy covered.
"""

import py
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
        pass
    if version == (2, 5):
        pass
    if version == (2, 6):
        pass
    if version == (2, 7):
        pass
    if version == (3, 0):
        pass
    if version == (3, 1):
        pass
'''

SCRIPT_CMATH = '''
import cmath

def test_foo():
    pass
'''

@py.test.mark.xfail('sys.version_info[:2] == (3, 0)')
def test_central(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename)
    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_central * 18 * 5 * 72% *',
            '*10 passed*'
            ])
    assert result.ret == 0

def test_module_selection(testdir):
    script = testdir.makepyfile(SCRIPT_CMATH)
    result = testdir.runpytest(script,
                               '--cov=cmath',
                               '--cov=%s' % script.purebasename)
    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_module_selection * 3 * 0 * 100% *',
            '*1 passed*'
            ])
    assert result.ret == 0
    matching_lines = [line for line in result.outlines if 'TokenError' in line]
    assert not matching_lines

@py.test.mark.xfail('sys.version_info[:2] == (3, 0)')
def test_dist_load_collocated(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--dist=load',
                               '--tx=2*popen')
    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_dist_load_collocated * 18 * 5 * 72% *',
            '*10 passed*'
            ])
    assert result.ret == 0

@py.test.mark.xfail('sys.version_info[:2] == (3, 0)')
def test_dist_load_not_collocated(testdir):
    script = testdir.makepyfile(SCRIPT)
    dir1 = testdir.mkdir('dir1')
    dir2 = testdir.mkdir('dir2')
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--dist=load',
                               '--tx=popen//chdir=%s' % dir1,
                               '--tx=popen//chdir=%s' % dir2,
                               '--rsyncdir=%s' % script.basename)
    result.stdout.fnmatch_lines([
            '*- coverage: platform *, python * -*',
            'test_dist_load_not_collocated * 18 * 5 * 72% *',
            '*10 passed*'
            ])
    assert result.ret == 0

@py.test.mark.skipif('sys.version_info[:2] >= (3, 0)')
def test_dist_each_many_reports_py2(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--dist=each',
                               '--tx=popen//python=/usr/local/python246/bin/python',
                               '--tx=popen//python=/usr/local/python255/bin/python',
                               '--tx=popen//python=/usr/local/python265/bin/python',
                               '--tx=popen//python=/usr/local/python27b1/bin/python')
    result.stdout.fnmatch_lines([
           '*- coverage: platform *, python 2.4.6-final-0 -*',
           'test_dist_each_many_reports_py2 * 18 * 5 * 72% *',
           '*- coverage: platform *, python 2.5.5-final-0 -*',
           'test_dist_each_many_reports_py2 * 18 * 5 * 72% *',
            '*- coverage: platform *, python 2.6.5-final-0 -*',
           'test_dist_each_many_reports_py2 * 18 * 5 * 72% *',
            '*- coverage: platform *, python 2.7.0-beta-1 -*',
           'test_dist_each_many_reports_py2 * 18 * 5 * 72% *',
            '*40 passed*'
            ])
    assert result.ret == 0

@py.test.mark.skipif('sys.version_info[:2] < (3, 0)')
@py.test.mark.xfail('sys.version_info[:2] == (3, 1)')
def test_dist_each_many_reports_py3(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--dist=each',
                               '--tx=popen//python=/usr/local/python301/bin/python3.0',
                               '--tx=popen//python=/usr/local/python312/bin/python3.1')
    result.stdout.fnmatch_lines([
            # coverage under python 3.0 seems to produce incorrect
            # results but ignore for this test as we want to see
            # multiple reports regardless of results.
            '*- coverage: platform *, python 3.0.1-final-0 -*',
            'test_dist_each_many_reports_py3 * 18 * 1 * 94% *',
            '*- coverage: platform *, python 3.1.2-final-0 -*',
            'test_dist_each_many_reports_py3 * 18 * 5 * 72% *',
            '*20 passed*'
            ])
    assert result.ret == 0

@py.test.mark.skipif('sys.version_info[:2] >= (3, 0)')
def test_dist_each_one_report_py2(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--cov-combine-each',
                               '--dist=each',
                               '--tx=popen//python=/usr/local/python246/bin/python',
                               '--tx=popen//python=/usr/local/python255/bin/python',
                               '--tx=popen//python=/usr/local/python265/bin/python',
                               '--tx=popen//python=/usr/local/python27b1/bin/python')
    result.stdout.fnmatch_lines([
            '*- coverage -*',
            '* platform *, python 2.4.6-final-0 *',
            '* platform *, python 2.5.5-final-0 *',
            '* platform *, python 2.6.5-final-0 *',
            '* platform *, python 2.7.0-beta-1 *',
            'test_dist_each_one_report_py2 * 18 * 2 * 88% *',
            '*40 passed*'
            ])
    assert result.ret == 0

@py.test.mark.skipif('sys.version_info[:2] < (3, 0)')
@py.test.mark.xfail('sys.version_info[:2] == (3, 1)')
def test_dist_each_one_report_py3(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--cov-combine-each',
                               '--dist=each',
                               '--tx=popen//python=/usr/local/python301/bin/python3.0',
                               '--tx=popen//python=/usr/local/python312/bin/python3.1')
    result.stdout.fnmatch_lines([
            # coverage under python 3.0 seems to produce incorrect
            # results but ignore for this test as we want to see
            # multiple reports regardless of results.
            '*- coverage -*',
            '* platform *, python 3.0.1-final-0 *',
            '* platform *, python 3.1.2-final-0 *',
            'test_dist_each_one_report_py3 * 18 * 1 * 94% *',
            '*20 passed*'
            ])
    assert result.ret == 0

@py.test.mark.skipif('sys.version_info[:2] >= (3, 0)')
def test_dist_missing_data(testdir):
    script = testdir.makepyfile(SCRIPT)
    result = testdir.runpytest(script,
                               '--cov=%s' % script.purebasename,
                               '--dist=load',
                               '--tx=popen//python=/usr/local/env255empty/bin/python')
    result.stdout.fnmatch_lines([
            '*- coverage: failed slaves -*'
            ])
    assert result.ret == 0
