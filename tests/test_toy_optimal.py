from models.master_problem import MasterProblem, BlockPattern


def test_toy_closed_form_optimum():
    # Simple known LP: two patterns with constraint sum lambda = 1
    # Pattern A profit 100, Pattern B profit 60 -> optimal is A with lambda_A=1
    mp = MasterProblem(n_blocks=1)
    pA = BlockPattern(id=0, blocks=[0], profit=100.0, name="A")
    pB = BlockPattern(id=1, blocks=[0], profit=60.0, name="B")
    mp.add_column(pA)
    mp.add_column(pB)

    sol = mp.solve()
    assert abs(sol.objective_value - 100.0) < 1e-6
    assert abs(sol.variable_values[0] - 1.0) < 1e-6
