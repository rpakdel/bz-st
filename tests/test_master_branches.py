import pytest
import pulp

from models.master_problem import MasterProblem, BlockPattern, MasterSolution


def test_export_no_variables_returns_status_no_variables():
    mp = MasterProblem(n_blocks=3)
    res = mp.export_solution()
    assert isinstance(res, dict)
    assert res["status"] == "no_variables"


def test_get_block_dual_when_constraint_missing_returns_zero():
    mp = MasterProblem(n_blocks=5)
    # No variables added -> no block constraints
    val = mp.get_block_dual(2)
    assert val == 0.0


def test_duals_presence_and_absence_after_solve():
    mp = MasterProblem(n_blocks=4)

    # Add a pattern that covers block 1 and 2
    p1 = BlockPattern(id=0, blocks=[1, 2], profit=100.0)
    mp.add_column(p1)

    # Add a pattern that covers block 3 only
    p2 = BlockPattern(id=1, blocks=[3], profit=10.0)
    mp.add_column(p2)

    sol = mp.solve()

    # convexity dual should exist (since we had variables)
    assert sol.convexity_dual is not None

    # duals should include keys for blocks that have constraints (1,2,3)
    assert 1 in sol.duals
    assert 2 in sol.duals
    assert 3 in sol.duals

    # block 0 had no covering pattern, so it should not be in duals
    assert 0 not in sol.duals


def test_export_solution_handles_infeasible_problem_gracefully(monkeypatch):
    mp = MasterProblem(n_blocks=2)

    # Add a pattern but then corrupt model to make solver return infeasible
    p = BlockPattern(id=0, blocks=[0], profit=1.0)
    mp.add_column(p)

    # Simulate solve raising an error to exercise export_solution error handling
    def fake_solve():
        raise ValueError("simulated solver failure")

    monkeypatch.setattr(mp, "solve", fake_solve)

    res = mp.export_solution()
    assert res["status"] == "error"
    assert "simulated solver failure" in res["message"]
