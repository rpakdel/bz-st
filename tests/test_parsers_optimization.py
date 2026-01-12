from parsers.optimization import parse_optimization_file
import os


def test_parse_upit_basic():
    fp = os.path.join('data', 'minelib', 'zuck_small', 'zuck_small.upit')
    om = parse_optimization_file(fp)
    assert om.name.lower().startswith('zuck')
    assert om.type == 'UPIT'
    assert om.n_blocks == 9400
    # Check some objective entries
    assert 0 in om.objective
    assert isinstance(om.objective[0][0], float)


def test_parse_cpit_basic():
    fp = os.path.join('data', 'minelib', 'zuck_small', 'zuck_small.cpit')
    om = parse_optimization_file(fp)
    assert om.type == 'CPIT'
    assert om.n_periods == 20
    # Resource limits should be present
    assert len(om.resource_limits) > 0
    # Check discount rate
    assert om.discount_rate == 0.1
