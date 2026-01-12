from parsers.optimization import parse_optimization_file
from parsers.precedence import parse_precedence_file
from parsers.block_model import parse_blocks_file
from models.bz_controller import BZController
import networkx as nx


def load_sol_selected_ids(sol_path):
    ids = []
    with open(sol_path) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                bid = int(parts[0])
                ids.append(bid)
            except ValueError:
                continue
    return set(ids)


def test_controller_vs_cpit_sol_subset():
    base = "data/minelib/zuck_small"
    bm = parse_blocks_file(f"{base}/zuck_small.blocks")
    pm = parse_precedence_file(f"{base}/zuck_small.prec")
    om = parse_optimization_file(f"{base}/zuck_small.upit")

    sol_ids = load_sol_selected_ids(f"{base}/zuck_small_cpit_gmunoz120723.sol")

    # Choose subset size
    n = 1000
    subset = list(range(min(n, len(bm.blocks))))

    # Compute objective implied by solution restricted to subset
    sol_subset_ids = [i for i in subset if i in sol_ids]
    sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)

    # Build precedence subgraph for subset
    Gfull = pm.to_networkx()
    G = nx.DiGraph()
    G.add_nodes_from(subset)
    for u, v in Gfull.edges():
        if u in subset and v in subset:
            G.add_edge(u, v)

    profits = {i: om.objective.get(i, [0.0])[0] for i in subset}

    # Run controller with larger limits to approach good solution
    controller = BZController(n_blocks=n, precedence_graph=G, profits=profits, max_iters=50, max_columns=2000)
    controller.seed_with_singletons(topk=100)
    res = controller.run()
    controller_obj = res["objective"]

    # Compare controller objective to solution objective on the subset
    # Allow relative tolerance because controller runs with limited columns. Set to 12% for now.
    tol = 0.12
    if sol_obj == 0:
        assert controller_obj == 0
    else:
        rel_err = abs(controller_obj - sol_obj) / max(abs(sol_obj), 1.0)
        if rel_err > tol:
            # Provide diagnostic information to help tune controller
            diag = controller.get_diagnostics()
            raise AssertionError(
                f"Relative error too large: {rel_err:.3f} > {tol:.3f} (controller {controller_obj} vs sol {sol_obj}).\n"
                f"Status: {res['status']}. Diagnostics: {diag}"
            )
