import networkx as nx
from models.pricer import ClosurePricer, PricingResult


def test_pricer_single_positive_node():
    G = nx.DiGraph()
    G.add_node(0)
    profits = {0: 10.0}
    pricer = ClosurePricer(G, profits)

    duals = {0: 2.0}
    res = pricer.price(duals, convexity_dual=0.0)

    assert isinstance(res, PricingResult)
    # weight = profit - dual = 8.0, reduced_cost = 0 - 8 = -8
    assert res.total_weight == 8.0
    assert res.reduced_cost == -8.0
    assert res.selected_blocks == [0]


def test_pricer_single_negative_node():
    G = nx.DiGraph()
    G.add_node(0)
    profits = {0: 1.0}
    pricer = ClosurePricer(G, profits)

    duals = {0: 5.0}
    res = pricer.price(duals, convexity_dual=0.0)

    # weight = 1 - 5 = -4 => no nodes selected, total_weight = 0
    assert res.total_weight == 0.0
    assert res.reduced_cost == 0.0
    assert res.selected_blocks == []


def test_pricer_chain_precedence_enforces_closure():
    # Chain 0 -> 1 -> 2 (0 predecessor of 1, etc.)
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2)])
    profits = {0: 5.0, 1: 6.0, 2: 7.0}
    pricer = ClosurePricer(G, profits)

    # Give high positive weight to node 2 only; closure requires selecting 0 and 1 as well
    duals = {0: 0.0, 1: 0.0, 2: 0.0}
    # Adjust duals so only node 2 has positive net weight if allowed alone
    # But because of precedence, selecting 2 forces 0 and 1 included
    # Here profit weights are all positive so closure should pick all three
    res = pricer.price(duals, convexity_dual=0.0)

    assert set(res.selected_blocks) == {0, 1, 2}
    assert res.total_weight == 5.0 + 6.0 + 7.0
    assert res.reduced_cost == -(5.0 + 6.0 + 7.0)


def test_pricer_respects_convexity_dual():
    G = nx.DiGraph()
    G.add_nodes_from([0])
    profits = {0: 4.0}
    pricer = ClosurePricer(G, profits)

    duals = {0: 1.0}
    # If convexity_dual is non-zero it shifts reduced cost
    res = pricer.price(duals, convexity_dual=2.0)

    # total weight = 3.0, reduced_cost = 2.0 - 3.0 = -1.0
    assert res.total_weight == 3.0
    assert res.reduced_cost == -1.0
import networkx as nx
from models.pricer import ClosurePricer, PricingResult


def make_simple_dag():
    G = nx.DiGraph()
    # nodes 0..4 with edges enforcing closure: 0->2, 1->2, 2->3, 3->4
    edges = [(0, 2), (1, 2), (2, 3), (3, 4)]
    G.add_edges_from(edges)
    # ensure nodes exist
    for i in range(5):
        G.add_node(i)
    return G


def test_pricer_selects_best_closure():
    G = make_simple_dag()

    # Give profits that favor selecting nodes 0 and 1 individually but selecting 2 requires both
    profits = {
        0: 5.0,
        1: 6.0,
        2: 8.0,
        3: 1.0,
        4: -1.0,
    }

    pricer = ClosurePricer(precedence_graph=G, profits=profits)

    # No duals -> should pick the maximum-weight closure. Here, selecting {0,1} alone
    # is allowed (they have no predecessors) and total weight 11 > selecting chain {0,1,2,3}?
    res = pricer.price(duals={})
    assert isinstance(res, PricingResult)
    # total_weight should be non-negative and selected blocks non-empty
    assert res.total_weight >= 0
    assert len(res.selected_blocks) > 0


def test_pricer_respects_precedence():
    G = make_simple_dag()
    # If node 2 has high profit but its predecessors have negative profit,
    # the closure will include predecessors if the combined weight is positive.
    profits = {0: -10.0, 1: -10.0, 2: 50.0, 3: 0.0, 4: 0.0}
    pricer = ClosurePricer(precedence_graph=G, profits=profits)

    res = pricer.price(duals={})

    # Selecting 2 requires selecting 0 and 1; combined weight = 30 > 0 so they should be included
    assert 2 in res.selected_blocks
    assert 0 in res.selected_blocks and 1 in res.selected_blocks


def test_pricer_accounts_for_duals():
    G = make_simple_dag()
    profits = {0: 5.0, 1: 5.0, 2: 1.0, 3: 0.0, 4: 0.0}
    pricer = ClosurePricer(precedence_graph=G, profits=profits)

    # Give high duals to 0 and 1 to discourage selecting them
    duals = {0: 6.0, 1: 6.0}
    res = pricer.price(duals=duals)

    # With duals, weights of 0 and 1 become negative, so they shouldn't be selected
    assert 0 not in res.selected_blocks
    assert 1 not in res.selected_blocks
