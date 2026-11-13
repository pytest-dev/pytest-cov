"""Regression coverage for xdist master data merging (#642)."""

import coverage
import pytest

from pytest_cov.engine import _discard_unexecuted_files


@pytest.mark.parametrize('branches', [False, True])
def test_discard_empty_master_records_preserves_executed_data_and_contexts(tmp_path, branches):
    master_file = str(tmp_path / '.coverage')
    recorded_file = str(tmp_path / 'startup.py')
    unexecuted_file = str(tmp_path / 'target.py')
    data = coverage.CoverageData(basename=master_file, suffix='master')

    for context in ('setup', 'teardown'):
        data.set_context(context)
        if branches:
            data.add_arcs({recorded_file: [(-1, 1), (1, 2)]})
        else:
            data.add_lines({recorded_file: [1, 2]})

    data.touch_files([unexecuted_file])
    data.add_file_tracers({recorded_file: 'demo_plugin.Plugin'})

    assert _discard_unexecuted_files(data)
    data.write()

    saved = coverage.CoverageData(basename=master_file, suffix='master')
    saved.read()
    assert saved.measured_files() == {recorded_file}
    assert saved.file_tracer(recorded_file) == 'demo_plugin.Plugin'
    assert saved.measured_contexts() == {'setup', 'teardown'}

    for context in ('setup', 'teardown'):
        saved.set_query_context(context)
        if branches:
            assert saved.arcs(recorded_file) == [(-1, 1), (1, 2)]
        else:
            assert saved.lines(recorded_file) == [1, 2]


def test_discard_entirely_unexecuted_master_data(tmp_path):
    data = coverage.CoverageData(basename=str(tmp_path / '.coverage'), suffix='master')
    data.add_arcs({})
    data.touch_files([str(tmp_path / 'target.py')])
    data.write()

    assert not _discard_unexecuted_files(data)
    assert data.measured_files() == set()
    assert not (tmp_path / '.coverage.master').exists()
