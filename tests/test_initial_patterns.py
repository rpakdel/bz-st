from models.initial_patterns import generate_initial_patterns, create_trivial_pattern
from models.optimization import OptimizationModel


def make_dummy_om(n_blocks: int, profits=None):
    om = OptimizationModel(name='dummy', type='UPIT', n_blocks=n_blocks)
    if profits is None:
        profits = [float(i * 10 + 1) for i in range(n_blocks)]
    for i in range(n_blocks):
        om.objective[i] = [profits[i]]
    return om


def test_generate_initial_patterns_basic():
    om = make_dummy_om(10)
    patterns = generate_initial_patterns(om, max_patterns=5)
    assert len(patterns) == 5
    # check ids and blocks
    for idx, p in enumerate(patterns):
        assert p.id == idx
        assert p.blocks == [idx]
        assert p.profit == om.objective[idx][0]


def test_generate_initial_patterns_full():
    om = make_dummy_om(3)
    patterns = generate_initial_patterns(om, max_patterns=10)
    # should not exceed n_blocks
    assert len(patterns) == 3


def test_create_trivial_pattern():
    p = create_trivial_pattern(10)
    assert p.id == 999999
    assert p.blocks == []
    assert p.profit == 0.0
    assert p.name == 'trivial'
