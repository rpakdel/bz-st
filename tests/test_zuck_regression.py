import networkx as nx
from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file
from models.bz_controller import BZController


def load_zuck_objects(n_blocks=1000):
    base = "data/minelib/zuck_small"
    bm = parse_blocks_file(f"{base}/zuck_small.blocks")
    pm = parse_precedence_file(f"{base}/zuck_small.prec")
    om = parse_optimization_file(f"{base}/zuck_small.upit")

    subset = list(range(min(n_blocks, len(bm.blocks))))
    Gfull = pm.to_networkx()
    G = nx.DiGraph()
    G.add_nodes_from(subset)
    for u, v in Gfull.edges():
        if u in subset and v in subset:
            G.add_edge(u, v)

    profits = {i: om.objective.get(i, [0.0])[0] for i in subset}
    return bm, pm, om, G, profits


def test_zuck_large_subset_run():
    bm, pm, om, G, profits = load_zuck_objects(n_blocks=1000)
    controller = BZController(n_blocks=1000, precedence_graph=G, profits=profits, max_iters=30, max_columns=500)
    controller.seed_with_singletons(topk=50)
    res = controller.run()

    assert res["status"] in ("converged", "max_iters", "max_columns_reached")
    diag = controller.get_diagnostics()
    # Make sure diagnostics exist and best_objective is non-negative
    assert "best_objective" in diag
    assert diag["best_objective"] >= 0
