import pytest
from models.master_problem import MasterProblem, BlockPattern, MasterSolution
import numpy as np

def test_master_problem_basic():
    """Test basic master problem functionality"""
    mp = MasterProblem(n_blocks=3)

    # Add a pattern
    pattern = BlockPattern(id=0, blocks=[0, 1], profit=100.0)
    mp.add_column(pattern)

    # Should have one column
    assert mp.get_column_count() == 1

    # Solve
    solution = mp.solve()
    assert isinstance(solution, MasterSolution)
    assert solution.objective_value == 100.0
    assert len(solution.duals) == 2  # blocks 0 and 1
    assert solution.convexity_dual == 100.0

def test_master_problem_multiple_patterns():
    """Test with multiple patterns"""
    mp = MasterProblem(n_blocks=4)

    # Add patterns
    patterns = [
        BlockPattern(id=0, blocks=[0], profit=50.0),
        BlockPattern(id=1, blocks=[1, 2], profit=80.0),
        BlockPattern(id=2, blocks=[2, 3], profit=70.0),
    ]

    for pattern in patterns:
        mp.add_column(pattern)

    assert mp.get_column_count() == 3

    # Solve
    solution = mp.solve()
    assert solution.objective_value > 0
    # With convexity constraint, the LP should choose the best pattern
    assert abs(solution.objective_value - 80.0) < 1e-6  # Should choose pattern 1

def test_master_problem_export():
    """Test solution export"""
    mp = MasterProblem(n_blocks=2)
    pattern = BlockPattern(id=0, blocks=[0], profit=100.0)
    mp.add_column(pattern)

    solution = mp.solve()
    export = mp.export_solution()

    assert export["status"] == "optimal"
    assert export["objective"] == 100.0
    assert 0 in export["duals"]
    assert 0 in export["variables"]

def test_constraint_satisfaction():
    """Test that constraints are properly satisfied"""
    mp = MasterProblem(n_blocks=3)

    # Add patterns that use blocks
    patterns = [
        BlockPattern(id=0, blocks=[0, 1], profit=60.0),
        BlockPattern(id=1, blocks=[1, 2], profit=70.0),
    ]

    for pattern in patterns:
        mp.add_column(pattern)

    solution = mp.solve()

    # Check convexity constraint: sum lambda = 1
    total_lambda = sum(solution.variable_values.values())
    assert abs(total_lambda - 1.0) < 1e-6

    # Check objective
    expected_obj = sum(solution.variable_values[pid] * p.profit
                      for pid, p in enumerate(patterns))
    assert abs(solution.objective_value - expected_obj) < 1e-6

def test_dual_extraction():
    """Test dual value extraction"""
    mp = MasterProblem(n_blocks=2)

    # Add a pattern that uses block 0
    pattern = BlockPattern(id=0, blocks=[0], profit=100.0)
    mp.add_column(pattern)

    solution = mp.solve()

    # Block 0 should have a dual (since it's used)
    assert 0 in solution.duals
    # Block 1 may or may not have a dual (depending on if it's constrained)
    # Just check that we get some duals
    assert isinstance(solution.duals, dict)

def test_large_problem():
    """Test with a larger problem"""
    n_blocks = 100
    mp = MasterProblem(n_blocks=n_blocks)

    solution = mp.solve()
    assert solution.objective_value >= 0
    assert len(solution.duals) <= n_blocks

    # Check convexity (only if there are variables)
    if solution.variable_values:
        total_lambda = sum(solution.variable_values.values())
        assert abs(total_lambda - 1.0) < 1e-6

def test_block_dual_method():
    """Test the get_block_dual method"""
    mp = MasterProblem(n_blocks=3)
    pattern = BlockPattern(id=0, blocks=[0, 1], profit=50.0)
    mp.add_column(pattern)

    solution = mp.solve()

    # Test the method
    dual_0 = mp.get_block_dual(0)
    dual_1 = mp.get_block_dual(1)
    dual_2 = mp.get_block_dual(2)

    assert dual_0 == solution.duals.get(0, 0.0)
    assert dual_1 == solution.duals.get(1, 0.0)
    assert dual_2 == 0.0  # Block 2 not used

def test_empty_master_problem():
    """Test master problem with no columns"""
    mp = MasterProblem(n_blocks=2)
    
    # Should give objective 0 with no variables
    solution = mp.solve()
    assert solution.objective_value == 0.0
    assert len(solution.variable_values) == 0

def test_known_lp_problem():
    """Test against a known small LP problem"""
    # Simple transportation-like problem
    # maximize 3x + 2y subject to x + y <= 1, x,y >= 0
    # Optimal: x=1, y=0, objective=3

    mp = MasterProblem(n_blocks=1)  # Only one constraint (convexity)

    # Pattern 1: x=1, y=0, profit=3, uses "constraint 0"
    pattern1 = BlockPattern(id=0, blocks=[0], profit=3.0, name="x=1,y=0")

    # Pattern 2: x=0, y=1, profit=2, uses "constraint 0"
    pattern2 = BlockPattern(id=1, blocks=[0], profit=2.0, name="x=0,y=1")

    mp.add_column(pattern1)
    mp.add_column(pattern2)

    solution = mp.solve()

    # Should choose pattern 1 (x=1,y=0) with objective 3
    assert abs(solution.objective_value - 3.0) < 1e-6
    assert abs(solution.variable_values[0] - 1.0) < 1e-6  # lambda_0 = 1
    assert abs(solution.variable_values[1] - 0.0) < 1e-6  # lambda_1 = 0

if __name__ == "__main__":
    test_master_problem_basic()
    test_master_problem_multiple_patterns()
    test_master_problem_export()
    test_constraint_satisfaction()
    test_dual_extraction()
    test_empty_master_problem()
    test_large_problem()
    test_block_dual_method()
    test_known_lp_problem()
    print("✅ All master problem tests passed!")