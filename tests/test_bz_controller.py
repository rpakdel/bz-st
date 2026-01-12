import networkx as nx
from models.bz_controller import BZController


def make_toy_dag(n=5):
    G = nx.DiGraph()
    for i in range(n):
        G.add_node(i)
    # simple chain 0->1->2->3->4
    for i in range(n-1):
        G.add_edge(i, i+1)
    return G


def test_bz_controller_basic_run():
    n = 5
    G = make_toy_dag(n)

    # profits: later nodes more profitable but require predecessors
    profits = {i: float(i + 1) for i in range(n)}

    controller = BZController(n_blocks=n, precedence_graph=G, profits=profits, eps=1e-6, max_iters=10)

    # seed with singletons to give initial feasible columns
    controller.seed_with_singletons()

    res = controller.run()

    assert res["status"] in ("converged", "max_iters")
    # final objective should be non-negative
    assert res["objective"] >= 0.0
    # history should have at least one entry
    assert len(res["history"]) >= 1
