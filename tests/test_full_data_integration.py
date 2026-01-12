"""Optional full-dataset integration tests.

These tests run the BZ controller on full Minelib instances using the complete
block, precedence, and optimization models. They are intentionally slow and are
only collected/executed when selected via the pytest marker.

Run manually with:
    pytest -m full_data -v
"""

from typing import Dict, Tuple

import networkx as nx
import pytest

from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file
from models.bz_controller import BZController

DATASETS = [
    # name: identifier used for parametrization and reporting
    # base: root path for the dataset files
    # blocks/prec/upit: filenames for block model, precedence, and UPIT optimization data
    # upit_sol: reference UPIT solution file to compute objective
    # ref_upit: published UPIT objective (integer or reference) used for checks
    # max_iters: cap iterations to keep runtime manageable for full-data tests
    #   - Increase for tighter LP bounds; decreases risk of early stop but runs longer.
    #   - Decrease to shorten runtime when running the slow suite.
    # topk: number of singleton seeds sorted by profit to start BZ
    #   - Increase to give the master a better initial basis (often improves first iteration objective).
    #   - Decrease to speed startup or when memory is tight.
    # min_ratio: acceptable fraction of ref_upit the BZ LP must reach (looser for large/complex cases)
    #   - Tighten (raise) to demand closer match to the reference; may cause failures if iterations are too few.
    #   - Loosen (lower) if you reduce max_iters/topk or if hardware is slow and objectives come in lower.
    {
        "name": "newman",
        "base": "data/minelib/newman",
        "blocks": "newman1.blocks",
        "prec": "newman1.prec",
        "upit": "newman1.upit",
        "upit_sol": "newman1_upit.sol",
        "ref_upit": 26_086_899,
        "max_iters": 10,
        "topk": 20,
        "min_ratio": 0.9,  # BZ LP should be close to UPIT on small instance
    },
    {
        "name": "zuck_small",
        "base": "data/minelib/zuck_small",
        "blocks": "zuck_small.blocks",
        "prec": "zuck_small.prec",
        "upit": "zuck_small.upit",
        "upit_sol": "zuck_small_upit.sol",
        "ref_upit": 1_422_726_898,
        "max_iters": 10,
        "topk": 25,
        "min_ratio": 0.9,  # Allow looser bound; LP may vary with few iterations
    },
    {
        "name": "kd",
        "base": "data/minelib/kd",
        "blocks": "kd.blocks",
        "prec": "kd.prec",
        "upit": "kd.upit",
        "upit_sol": "kd_upit.sol",
        "ref_upit": 652_195_037,
        "max_iters": 10,
        "topk": 25,
        "min_ratio": 0.9,
    },
    {
        "name": "marvin",
        "base": "data/minelib/marvin",
        "blocks": "marvin.blocks",
        "prec": "marvin.prec",
        "upit": "marvin.upit",
        "upit_sol": "marvin_upit.sol",
        "ref_upit": 1_415_655_436,
        "max_iters": 6,   # keep runtime manageable
        "topk": 20,
        "min_ratio": 0.9,  # Prior runs yielded ~0.6 of UPIT in a few iters
    },
]


def _load_full_models(cfg: Dict) -> Tuple[int, nx.DiGraph, Dict[int, float]]:
    """Load full block/precedence/optimization models and build profits dict."""
    bm = parse_blocks_file(f"{cfg['base']}/{cfg['blocks']}")
    pm = parse_precedence_file(f"{cfg['base']}/{cfg['prec']}")
    om = parse_optimization_file(f"{cfg['base']}/{cfg['upit']}")

    n_blocks = len(bm.blocks)
    G = pm.to_networkx()
    profits = {i: om.objective.get(i, [0.0])[0] for i in range(n_blocks)}
    return n_blocks, G, profits


def _load_upit_solution_obj(cfg: Dict) -> float:
    """Compute the objective of the provided UPIT solution file."""
    base = cfg["base"]
    om = parse_optimization_file(f"{base}/{cfg['upit']}")

    sol_path = f"{base}/{cfg['upit_sol']}"
    selected = []
    with open(sol_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                selected.append(int(line.split()[0]))
            except ValueError:
                continue

    return sum(om.objective.get(bid, [0.0])[0] for bid in selected)


def _run_controller(cfg: Dict) -> Dict[str, float]:
    n_blocks, G, profits = _load_full_models(cfg)
    controller = BZController(
        n_blocks=n_blocks,
        precedence_graph=G,
        profits=profits,
        max_iters=cfg["max_iters"],
        eps=1e-6,
    )
    controller.seed_with_singletons(topk=cfg["topk"])
    return controller.run(verbose=False)


@pytest.mark.full_data
@pytest.mark.parametrize("cfg", DATASETS, ids=[d["name"] for d in DATASETS])
def test_full_dataset_lp_lower_bound(cfg):
    """Run BZ on full dataset and assert a reasonable lower bound is reached."""
    res = _run_controller(cfg)
    objective = res.get("objective", 0.0)

    expected_min = cfg["ref_upit"] * cfg["min_ratio"]
    assert objective >= expected_min, (
        f"{cfg['name']} objective too low: {objective:.2f} < {expected_min:.2f}"
    )

    # Basic sanity: should not exceed UPIT
    assert objective <= cfg["ref_upit"] * 1.05, (
        f"{cfg['name']} objective unexpectedly exceeds UPIT: {objective:.2f}"
    )


@pytest.mark.full_data
@pytest.mark.parametrize("cfg", DATASETS, ids=[d["name"] for d in DATASETS])
def test_full_dataset_solution_objective_matches_reference(cfg):
    """Solution file objective should closely match documented reference."""
    sol_obj = _load_upit_solution_obj(cfg)

    expected = cfg["ref_upit"]
    rel_err = abs(sol_obj - expected) / max(abs(expected), 1.0)

    # Require very tight agreement with published values
    assert rel_err < 5e-4, (
        f"{cfg['name']} solution objective {sol_obj:.2f} differs from "
        f"reference {expected:.2f} by {rel_err*100:.3f}%"
    )
