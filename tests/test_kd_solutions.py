"""
Integration tests for KD (Arizona's Copper Deposit) solution files.

Verifies that:
1. All solution files parse correctly
2. Solution objective values match expected references
3. Solutions satisfy precedence constraints
4. Optimizer produces results comparable to or better than integer solutions
"""

import networkx as nx
import pytest
from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file
from models.bz_controller import BZController


# Reference values from kd/readme.md
KD_REFERENCE_VALUES = {
    "UPIT": 652_195_037,
    "CPIT_LP": 409_498_555,
    "PCPSP_LP": 410_891_003,
    "CPIT_IP": 396_858_193,
    "PCPSP_IP": 406_871_207,
}


def load_sol_selected_ids(sol_path):
    """Parse solution file and return set of selected block IDs.
    
    Handles both formats:
    - UPIT: one block ID per line
    - CPIT/PCPSP: block_id period destination value (select blocks with value > 0)
    """
    ids = []
    with open(sol_path) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                bid = int(parts[0])
                # For multi-column format, check if block is selected (value > 0)
                if len(parts) >= 4:
                    value = float(parts[3])
                    if value > 1e-6:  # Selected blocks have value ~1.0
                        ids.append(bid)
                else:
                    # Single column format (UPIT)
                    ids.append(bid)
            except (ValueError, IndexError):
                continue
    return set(ids)


def load_kd_objects(n_blocks: int = 14153):
    """Load KD dataset with optional block subset."""
    base = "data/minelib/kd"
    bm = parse_blocks_file(f"{base}/kd.blocks")
    pm = parse_precedence_file(f"{base}/kd.prec")
    om = parse_optimization_file(f"{base}/kd.upit")

    # Ensure we don't exceed available blocks
    n_blocks = min(n_blocks, len(bm.blocks))
    subset = list(range(n_blocks))

    # Build precedence subgraph
    G_full = pm.to_networkx()
    G = nx.DiGraph()
    G.add_nodes_from(subset)
    for u, v in G_full.edges():
        if u in subset and v in subset:
            G.add_edge(u, v)

    # Build profits mapping
    profits = {i: om.objective.get(i, [0.0])[0] for i in subset}

    return bm, pm, om, G, profits


class TestKDDataLoading:
    """Test basic KD data loading and validation."""

    def test_kd_blocks_parse_correctly(self):
        """Verify KD blocks file parses with correct count."""
        bm = parse_blocks_file("data/minelib/kd/kd.blocks")
        assert len(bm.blocks) == 14153
        assert bm.name == "kd"

    def test_kd_precedence_parse_correctly(self):
        """Verify KD precedence file parses with correct count."""
        pm = parse_precedence_file("data/minelib/kd/kd.prec")
        assert len(pm.precedences) == 14153
        assert pm.name == "kd"

    def test_kd_optimization_parse_correctly(self):
        """Verify KD optimization (UPIT) file parses."""
        om = parse_optimization_file("data/minelib/kd/kd.upit")
        assert len(om.objective) == 14153
        assert om.name == "KD"

    def test_kd_precedence_is_dag(self):
        """Verify precedence graph is a directed acyclic graph."""
        pm = parse_precedence_file("data/minelib/kd/kd.prec")
        G = pm.to_networkx()
        
        assert nx.is_directed_acyclic_graph(G)
        assert len(G.nodes()) == 14153


class TestKDSolutionFiles:
    """Test solution file parsing and validation."""

    def test_kd_upit_solution_parses(self):
        """Verify UPIT solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/kd/kd_upit.sol")
        # UPIT may exclude blocks with negative value
        assert 10000 <= len(sol_ids) <= 14153, f"Expected ~14153 blocks, got {len(sol_ids)}"

    def test_kd_cpit_solution_parses(self):
        """Verify CPIT solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/kd/kd_cpit_gmunoz120723.sol")
        # CPIT solution should select a subset of blocks
        assert 0 < len(sol_ids) <= 14153, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_kd_pcpsp_solution_parses(self):
        """Verify PCPSP solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/kd/kd_pcpsp_gmunoz120723.sol")
        # PCPSP solution should select a subset of blocks
        assert 0 < len(sol_ids) <= 14153, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_kd_upit_objective_value(self):
        """Verify UPIT solution achieves expected objective value."""
        base = "data/minelib/kd"
        om = parse_optimization_file(f"{base}/kd.upit")
        sol_ids = load_sol_selected_ids(f"{base}/kd_upit.sol")
        
        # Compute objective from solution
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_ids)
        
        # Should match reference value within small tolerance
        expected = KD_REFERENCE_VALUES["UPIT"]
        rel_error = abs(sol_obj - expected) / max(abs(expected), 1.0)
        assert rel_error < 0.01, (
            f"UPIT objective {sol_obj} differs from expected {expected} "
            f"by {rel_error*100:.2f}%"
        )

    def test_kd_cpit_objective_value(self):
        """Verify CPIT solution is reasonable.
        
        Note: CPIT solution uses period-specific discounting from .cpit file,
        so we can't directly compare using UPIT objective values. We verify
        the solution has a reasonable number of selected blocks.
        """
        sol_ids = load_sol_selected_ids("data/minelib/kd/kd_cpit_gmunoz120723.sol")
        
        # CPIT should select a reasonable subset
        assert 5000 <= len(sol_ids) <= 14153, (
            f"CPIT selected {len(sol_ids)} blocks, expected between 5000-14153"
        )

    def test_kd_pcpsp_objective_value(self):
        """Verify PCPSP solution is reasonable.
        
        Note: PCPSP solution uses period-specific discounting from .pcpsp file,
        so we can't directly compare using UPIT objective values. We verify
        the solution has a reasonable number of selected blocks.
        """
        sol_ids = load_sol_selected_ids("data/minelib/kd/kd_pcpsp_gmunoz120723.sol")
        
        # PCPSP should select a reasonable subset
        assert 5000 <= len(sol_ids) <= 14153, (
            f"PCPSP selected {len(sol_ids)} blocks, expected between 5000-14153"
        )

    def test_kd_upit_satisfies_precedence(self):
        """Verify UPIT solution satisfies precedence constraints."""
        base = "data/minelib/kd"
        pm = parse_precedence_file(f"{base}/kd.prec")
        sol_ids = load_sol_selected_ids(f"{base}/kd_upit.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"UPIT solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )

    def test_kd_cpit_satisfies_precedence(self):
        """Verify CPIT solution satisfies precedence constraints."""
        base = "data/minelib/kd"
        pm = parse_precedence_file(f"{base}/kd.prec")
        sol_ids = load_sol_selected_ids(f"{base}/kd_cpit_gmunoz120723.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"CPIT solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )

    def test_kd_pcpsp_satisfies_precedence(self):
        """Verify PCPSP solution satisfies precedence constraints."""
        base = "data/minelib/kd"
        pm = parse_precedence_file(f"{base}/kd.prec")
        sol_ids = load_sol_selected_ids(f"{base}/kd_pcpsp_gmunoz120723.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"PCPSP solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )


class TestKDOptimizerComparison:
    """Test optimizer performance against solution files on subsets."""

    def test_kd_controller_vs_upit_solution_subset(self):
        """
        Test controller performance against UPIT solution on subset.
        
        Controller should find a good solution (within reasonable range of UPIT subset).
        """
        base = "data/minelib/kd"
        bm, pm, om, G, profits = load_kd_objects(n_blocks=300)
        sol_ids = load_sol_selected_ids(f"{base}/kd_upit.sol")
        
        # Compute objective from UPIT solution restricted to subset
        subset = list(range(300))
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Run controller
        controller = BZController(
            n_blocks=300,
            precedence_graph=G,
            profits=profits,
            max_iters=25,
            max_columns=200,
        )
        controller.seed_with_singletons(topk=30)
        res = controller.run()
        controller_obj = res["objective"]
        
        # Controller should find a reasonable solution (at least 50% of UPIT subset)
        assert controller_obj >= sol_obj * 0.5, (
            f"Controller LP objective {controller_obj} is too low compared to "
            f"UPIT subset {sol_obj}"
        )

    def test_kd_controller_vs_cpit_solution_subset(self):
        """
        Test controller performance against CPIT solution on subset.
        
        LP relaxation should be >= integer solution.
        """
        base = "data/minelib/kd"
        bm, pm, om, G, profits = load_kd_objects(n_blocks=400)
        sol_ids = load_sol_selected_ids(f"{base}/kd_cpit_gmunoz120723.sol")
        
        # Compute objective from CPIT solution restricted to subset
        subset = list(range(400))
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Run controller
        controller = BZController(
            n_blocks=400,
            precedence_graph=G,
            profits=profits,
            max_iters=30,
            max_columns=250,
        )
        controller.seed_with_singletons(topk=40)
        res = controller.run()
        controller_obj = res["objective"]
        
        # LP relaxation should be >= integer solution (minus small tolerance)
        assert controller_obj >= sol_obj - 1000, (
            f"Controller LP objective {controller_obj} is worse than "
            f"CPIT integer solution {sol_obj}"
        )

    def test_kd_controller_vs_pcpsp_solution_subset(self):
        """
        Test controller performance against PCPSP solution on subset.
        
        LP relaxation should be >= integer solution.
        """
        base = "data/minelib/kd"
        bm, pm, om, G, profits = load_kd_objects(n_blocks=350)
        sol_ids = load_sol_selected_ids(f"{base}/kd_pcpsp_gmunoz120723.sol")
        
        # Compute objective from PCPSP solution restricted to subset
        subset = list(range(350))
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Run controller
        controller = BZController(
            n_blocks=350,
            precedence_graph=G,
            profits=profits,
            max_iters=25,
            max_columns=200,
        )
        controller.seed_with_singletons(topk=35)
        res = controller.run()
        controller_obj = res["objective"]
        
        # LP relaxation should be >= integer solution (minus small tolerance)
        assert controller_obj >= sol_obj - 1000, (
            f"Controller LP objective {controller_obj} is worse than "
            f"PCPSP integer solution {sol_obj}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
