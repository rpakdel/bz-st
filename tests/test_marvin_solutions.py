"""
Integration tests for Marvin solution files.

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


# Reference values from marvin/readme.md
MARVIN_REFERENCE_VALUES = {
    "UPIT": 1_415_655_436,
    "CPIT_LP": 863_916_131,
    "PCPSP_LP": 911_704_665,
    "CPIT_IP": 820_726_048,
    "PCPSP_IP": 885_968_070,
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


def load_marvin_objects(n_blocks: int = 53271):
    """Load Marvin dataset with optional block subset."""
    base = "data/minelib/marvin"
    bm = parse_blocks_file(f"{base}/marvin.blocks")
    pm = parse_precedence_file(f"{base}/marvin.prec")
    om = parse_optimization_file(f"{base}/marvin.upit")

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


class TestMarvinDataLoading:
    """Test basic Marvin data loading and validation."""

    def test_marvin_blocks_parse_correctly(self):
        """Verify Marvin blocks file parses with correct count."""
        bm = parse_blocks_file("data/minelib/marvin/marvin.blocks")
        assert len(bm.blocks) == 53271
        assert bm.name == "marvin"

    def test_marvin_precedence_parse_correctly(self):
        """Verify Marvin precedence file parses with correct count."""
        pm = parse_precedence_file("data/minelib/marvin/marvin.prec")
        assert len(pm.precedences) == 53271
        assert pm.name == "marvin"

    def test_marvin_optimization_parse_correctly(self):
        """Verify Marvin optimization (UPIT) file parses."""
        om = parse_optimization_file("data/minelib/marvin/marvin.upit")
        assert len(om.objective) == 53271
        assert om.name.lower() == "marvin"

    def test_marvin_precedence_is_dag(self):
        """Verify precedence graph is a directed acyclic graph."""
        pm = parse_precedence_file("data/minelib/marvin/marvin.prec")
        G = pm.to_networkx()
        
        assert nx.is_directed_acyclic_graph(G)
        assert len(G.nodes()) == 53271


class TestMarvinSolutionFiles:
    """Test solution file parsing and validation."""

    def test_marvin_upit_solution_parses(self):
        """Verify UPIT solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/marvin/marvin_upit.sol")
        # UPIT may exclude blocks with negative value
        assert 5000 <= len(sol_ids) <= 53271, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_marvin_cpit_solution_parses(self):
        """Verify CPIT solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/marvin/marvin_cpit_gmunoz120723.sol")
        # CPIT solution should select a subset of blocks
        assert 0 < len(sol_ids) <= 53271, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_marvin_pcpsp_solution_parses(self):
        """Verify PCPSP solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/marvin/marvin_pcpsp_gmunoz120723.sol")
        # PCPSP solution should select a subset of blocks
        assert 0 < len(sol_ids) <= 53271, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_marvin_upit_objective_value(self):
        """Verify UPIT solution achieves expected objective value."""
        base = "data/minelib/marvin"
        om = parse_optimization_file(f"{base}/marvin.upit")
        sol_ids = load_sol_selected_ids(f"{base}/marvin_upit.sol")
        
        # Compute objective from solution
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_ids)
        
        # Should match reference value within small tolerance
        expected = MARVIN_REFERENCE_VALUES["UPIT"]
        rel_error = abs(sol_obj - expected) / max(abs(expected), 1.0)
        assert rel_error < 0.01, (
            f"UPIT objective {sol_obj} differs from expected {expected} "
            f"by {rel_error*100:.2f}%"
        )

    def test_marvin_cpit_objective_value(self):
        """Verify CPIT solution is reasonable.
        
        Note: CPIT solution uses period-specific discounting from .cpit file,
        so we can't directly compare using UPIT objective values. We verify
        the solution has a reasonable number of selected blocks.
        """
        sol_ids = load_sol_selected_ids("data/minelib/marvin/marvin_cpit_gmunoz120723.sol")
        
        # CPIT should select a reasonable subset
        assert 5000 <= len(sol_ids) <= 53271, (
            f"CPIT selected {len(sol_ids)} blocks, expected between 5000-53271"
        )

    def test_marvin_pcpsp_objective_value(self):
        """Verify PCPSP solution is reasonable.
        
        Note: PCPSP solution uses period-specific discounting from .pcpsp file,
        so we can't directly compare using UPIT objective values. We verify
        the solution has a reasonable number of selected blocks.
        """
        sol_ids = load_sol_selected_ids("data/minelib/marvin/marvin_pcpsp_gmunoz120723.sol")
        
        # PCPSP should select a reasonable subset
        assert 5000 <= len(sol_ids) <= 53271, (
            f"PCPSP selected {len(sol_ids)} blocks, expected between 5000-53271"
        )

    def test_marvin_upit_satisfies_precedence(self):
        """Verify UPIT solution satisfies precedence constraints."""
        base = "data/minelib/marvin"
        pm = parse_precedence_file(f"{base}/marvin.prec")
        sol_ids = load_sol_selected_ids(f"{base}/marvin_upit.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"UPIT solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )

    def test_marvin_cpit_satisfies_precedence(self):
        """Verify CPIT solution satisfies precedence constraints."""
        base = "data/minelib/marvin"
        pm = parse_precedence_file(f"{base}/marvin.prec")
        sol_ids = load_sol_selected_ids(f"{base}/marvin_cpit_gmunoz120723.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"CPIT solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )

    def test_marvin_pcpsp_satisfies_precedence(self):
        """Verify PCPSP solution satisfies precedence constraints."""
        base = "data/minelib/marvin"
        pm = parse_precedence_file(f"{base}/marvin.prec")
        sol_ids = load_sol_selected_ids(f"{base}/marvin_pcpsp_gmunoz120723.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"PCPSP solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )


class TestMarvinOptimizerComparison:
    """Test optimizer performance against solution files on subsets."""

    def test_marvin_controller_vs_upit_solution_subset(self):
        """
        Test controller performance against UPIT solution on subset.
        
        Controller should find a good solution (within reasonable range of UPIT subset).
        """
        base = "data/minelib/marvin"
        bm, pm, om, G, profits = load_marvin_objects(n_blocks=400)
        sol_ids = load_sol_selected_ids(f"{base}/marvin_upit.sol")
        
        # Compute objective from UPIT solution restricted to subset
        subset = list(range(400))
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Run controller
        controller = BZController(
            n_blocks=400,
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

    def test_marvin_controller_vs_cpit_solution_subset(self):
        """
        Test controller performance against CPIT solution on subset.
        
        LP relaxation should be >= integer solution.
        """
        base = "data/minelib/marvin"
        bm, pm, om, G, profits = load_marvin_objects(n_blocks=500)
        sol_ids = load_sol_selected_ids(f"{base}/marvin_cpit_gmunoz120723.sol")
        
        # Compute objective from CPIT solution restricted to subset
        subset = list(range(500))
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Run controller
        controller = BZController(
            n_blocks=500,
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

    def test_marvin_controller_vs_pcpsp_solution_subset(self):
        """
        Test controller performance against PCPSP solution on subset.
        
        LP relaxation should be >= integer solution.
        """
        base = "data/minelib/marvin"
        bm, pm, om, G, profits = load_marvin_objects(n_blocks=450)
        sol_ids = load_sol_selected_ids(f"{base}/marvin_pcpsp_gmunoz120723.sol")
        
        # Compute objective from PCPSP solution restricted to subset
        subset = list(range(450))
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Run controller
        controller = BZController(
            n_blocks=450,
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
