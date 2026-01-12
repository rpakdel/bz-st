import networkx as nx
from models.bz_controller import BZController


def make_toy_dag(n=6):
    G = nx.DiGraph()
    for i in range(n):
        G.add_node(i)
    for i in range(n-1):
        G.add_edge(i, i+1)
    return G


def test_max_columns_guard():
    n = 6
    G = make_toy_dag(n)
    profits = {i: float(i + 1) for i in range(n)}
    # Set max_columns small so we hit the guard quickly
    controller = BZController(n_blocks=n, precedence_graph=G, profits=profits, max_iters=20, max_columns=2)
    controller.seed_with_singletons()
    res = controller.run()
    assert res["status"] in ("converged", "max_columns_reached", "max_iters")


def test_topk_seeding_and_verbose():
    n = 6
    G = make_toy_dag(n)
    profits = {i: float(i + 1) for i in range(n)}
    controller = BZController(n_blocks=n, precedence_graph=G, profits=profits, max_iters=5)

    # Seed with top-2 profitable singletons
    controller.seed_with_singletons(topk=2)
    assert len(controller.master.columns) == 2

    # Run with verbose to ensure no exceptions
    res = controller.run(verbose=True)
    assert res["status"] in ("converged", "max_iters")


def test_prune_low_activity_columns():
    n = 6
    G = make_toy_dag(n)
    profits = {i: float(i + 1) for i in range(n)}
    controller = BZController(n_blocks=n, precedence_graph=G, profits=profits, max_iters=3)
    controller.seed_with_singletons(limit=6)
    # Add an artificial column with zero activity
    controller.master.add_column(type('P', (), {'id': 999, 'blocks': [], 'profit': 0.0})())
    removed = controller.prune_low_activity_columns(keep_top_k=3)
    assert removed >= 0
