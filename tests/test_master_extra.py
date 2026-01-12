import pytest
from models.master_problem import MasterProblem, BlockPattern


def test_export_solution_error_path(monkeypatch):
    mp = MasterProblem(n_blocks=2)
    # Add a dummy column so export_solution will call solve()
    mp.add_column(BlockPattern(id=0, blocks=[0], profit=1.0))
    # monkeypatch solve to raise ValueError
    def fake_solve():
        raise ValueError('fake error')
    monkeypatch.setattr(mp, 'solve', fake_solve)

    res = mp.export_solution()
    assert res['status'] == 'error'
    assert 'fake error' in res['message']


def test_get_duals_empty_constraints():
    mp = MasterProblem(n_blocks=3)
    # No columns added; get_duals should return an empty dict
    d = mp.get_duals()
    assert isinstance(d, dict)
    assert d == {}
