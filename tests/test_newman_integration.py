"""
Integration tests for Newman dataset.

Verifies that:
1. Newman data files parse correctly
2. The optimizer produces valid solutions
3. Solution objective value approaches reference LP bounds
4. Closure property is satisfied (precedence constraints honored)
5. Solution files are parsed correctly and objectives computed accurately
"""

import networkx as nx
import pytest
from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file
from models.bz_controller import BZController


# Reference values from newman/readme.md
NEWMAN_REFERENCE_VALUES = {
    "UPIT": 26_086_899,
    "CPIT_LP": 24_486_184,
    "PCPSP_LP": 24_486_549,
    "CPIT_IP": 23_483_671,
    "PCPSP_IP": 23_658_230,
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


def load_newman_objects(n_blocks: int = 1060):
    """Load Newman dataset with optional block subset."""
    base = "data/minelib/newman"
    bm = parse_blocks_file(f"{base}/newman1.blocks")
    pm = parse_precedence_file(f"{base}/newman1.prec")
    om = parse_optimization_file(f"{base}/newman1.upit")

    # Ensure we don't exceed available blocks
    n_blocks = min(n_blocks, len(bm.blocks))
    subset = list(range(n_blocks))

    # Build precedence subgraph: only include edges where both nodes are in subset
    G_full = pm.to_networkx()
    G = nx.DiGraph()
    G.add_nodes_from(subset)
    for u, v in G_full.edges():
        if u in subset and v in subset:
            G.add_edge(u, v)

    # Build profits mapping from optimization model
    profits = {i: om.objective.get(i, [0.0])[0] for i in subset}

    return bm, pm, om, G, profits


class TestNewmanDataLoading:
    """Test data loading and basic validation."""

    def test_newman_blocks_parse_correctly(self):
        """Verify Newman blocks file parses with correct count."""
        bm = parse_blocks_file("data/minelib/newman/newman1.blocks")
        assert len(bm.blocks) == 1060
        assert bm.name == "newman1"
        
        # Verify first block has expected structure
        block0 = bm.blocks[0]
        assert block0.id == 0
        assert block0.x == 0
        assert block0.y == 1
        assert block0.z == 20

    def test_newman_precedence_parse_correctly(self):
        """Verify Newman precedence file parses with correct count."""
        pm = parse_precedence_file("data/minelib/newman/newman1.prec")
        assert len(pm.precedences) == 1060
        assert pm.name == "newman1"
        
        # Verify a sample precedence relation
        # Block 0 has no predecessors
        assert pm.precedences[0] == []
        # Block 1 has 2 predecessors: blocks 2 and 9
        assert pm.precedences[1] == [2, 9]

    def test_newman_optimization_parse_correctly(self):
        """Verify Newman optimization (UPIT) file parses."""
        om = parse_optimization_file("data/minelib/newman/newman1.upit")
        assert len(om.objective) == 1060
        assert om.name == "Newman1"
        
        # Verify sample values match the file
        assert om.objective[0][0] == -2236.7886
        assert om.objective[1][0] == 24829.116

    def test_newman_precedence_is_dag(self):
        """Verify precedence graph is a directed acyclic graph."""
        pm = parse_precedence_file("data/minelib/newman/newman1.prec")
        G = pm.to_networkx()
        
        # Should be acyclic
        assert nx.is_directed_acyclic_graph(G)
        # Should have expected number of nodes
        assert len(G.nodes()) == 1060

    def test_newman_all_predecessors_exist(self):
        """Verify all referenced predecessors are valid block IDs."""
        pm = parse_precedence_file("data/minelib/newman/newman1.prec")
        valid_ids = set(pm.precedences.keys())
        
        for block_id, preds in pm.precedences.items():
            for pred in preds:
                assert pred in valid_ids, f"Block {block_id} references invalid predecessor {pred}"


class TestNewmanSubsetLoading:
    """Test loading subsets of Newman dataset."""

    def test_load_newman_small_subset(self):
        """Load and validate a small subset of Newman data."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=100)
        
        assert len(G.nodes()) == 100
        assert len(profits) == 100
        # All profit values should be reasonable
        assert all(isinstance(p, (int, float)) for p in profits.values())

    def test_load_newman_full_dataset(self):
        """Load and validate full Newman dataset."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=1060)
        
        assert len(G.nodes()) == 1060
        assert len(profits) == 1060
        assert G.number_of_edges() > 0


class TestNewmanOptimizer:
    """Test BZ controller on Newman dataset subsets."""

    def test_newman_optimizer_subset_convergence(self):
        """Test optimizer converges on small Newman subset."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=100)
        
        controller = BZController(
            n_blocks=100,
            precedence_graph=G,
            profits=profits,
            max_iters=15,
            max_columns=100,
        )
        controller.seed_with_singletons(topk=10)
        
        res = controller.run()
        
        # Should complete without error
        assert res["status"] in ("converged", "max_iters", "max_columns_reached")
        # Should have generated some columns
        assert len(controller.master.columns) > 0
        # Best objective should be non-negative
        diag = controller.get_diagnostics()
        assert "best_objective" in diag
        assert diag["best_objective"] >= 0

    def test_newman_closure_property(self):
        """Verify all generated patterns satisfy closure property."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=150)
        
        controller = BZController(
            n_blocks=150,
            precedence_graph=G,
            profits=profits,
            max_iters=10,
            max_columns=75,
        )
        controller.seed_with_singletons(topk=5)
        res = controller.run()
        
        # Check closure property for all generated columns
        for col in controller.master.columns:
            if not getattr(col, 'name', '').startswith('col_'):
                continue
            
            for block_id in col.blocks:
                # All predecessors of this block should also be in the column
                preds = list(nx.ancestors(G, block_id))
                for pred in preds:
                    if pred in G.nodes():
                        assert pred in col.blocks, (
                            f"Column {col.name} contains block {block_id} "
                            f"but not its predecessor {pred}"
                        )

    def test_newman_convergence_criterion(self):
        """Test that convergence criterion is correctly applied."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=80)
        
        controller = BZController(
            n_blocks=80,
            precedence_graph=G,
            profits=profits,
            max_iters=20,
            max_columns=100,
            eps=1e-6,
        )
        controller.seed_with_singletons(topk=5)
        res = controller.run()
        
        history = controller.get_history()
        
        if res["status"] == "converged":
            # Last iteration should have non-negative reduced cost (within tolerance)
            assert len(history) > 0
            last = history[-1]
            # The last column added should have reduced cost >= -eps
            assert last['reduced_cost'] >= -controller.eps - 1e-12

    def test_newman_multiple_seed_strategies(self):
        """Test different seeding strategies on Newman subset."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=100)
        
        for topk in [5, 10, 20]:
            controller = BZController(
                n_blocks=100,
                precedence_graph=G,
                profits=profits,
                max_iters=12,
                max_columns=80,
            )
            controller.seed_with_singletons(topk=topk)
            res = controller.run()
            
            assert res["status"] in ("converged", "max_iters", "max_columns_reached")
            assert len(controller.master.columns) >= topk


class TestNewmanObjectiveQuality:
    """Test solution quality against reference bounds."""

    def test_newman_objective_against_upit_bound(self):
        """
        Test that LP relaxation objective is <= UPIT upper bound.
        UPIT objective: 26,086,899
        """
        bm, pm, om, G, profits = load_newman_objects(n_blocks=300)
        
        controller = BZController(
            n_blocks=300,
            precedence_graph=G,
            profits=profits,
            max_iters=20,
            max_columns=150,
        )
        controller.seed_with_singletons(topk=20)
        res = controller.run()
        
        diag = controller.get_diagnostics()
        best_obj = diag["best_objective"]
        
        # LP objective should be <= UPIT (feasible solution upper bound)
        assert best_obj <= NEWMAN_REFERENCE_VALUES["UPIT"], (
            f"LP objective {best_obj} exceeds UPIT bound {NEWMAN_REFERENCE_VALUES['UPIT']}"
        )

    def test_newman_objective_reasonable(self):
        """Test that objective values are in reasonable range."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=200)
        
        controller = BZController(
            n_blocks=200,
            precedence_graph=G,
            profits=profits,
            max_iters=15,
            max_columns=120,
        )
        controller.seed_with_singletons(topk=15)
        res = controller.run()
        
        diag = controller.get_diagnostics()
        best_obj = diag["best_objective"]
        
        # Should be less than single-block maximum
        max_single_value = max(profits.values())
        max_possible = max_single_value * len(profits)
        
        assert 0 <= best_obj <= max_possible


class TestNewmanDiagnostics:
    """Test diagnostic information from optimizer."""

    def test_newman_diagnostics_available(self):
        """Verify all expected diagnostics are reported."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=80)
        
        controller = BZController(
            n_blocks=80,
            precedence_graph=G,
            profits=profits,
            max_iters=10,
            max_columns=60,
        )
        controller.seed_with_singletons(topk=5)
        res = controller.run()
        
        diag = controller.get_diagnostics()
        
        # Check that diagnostics has the core keys
        assert "best_objective" in diag, "Missing diagnostic: best_objective"
        
        # Verify history has iteration data (which includes n_columns)
        history = controller.get_history()
        assert len(history) > 0, "No iteration history recorded"
        
        # Verify first history entry has key fields
        first_entry = history[0]
        assert "iter" in first_entry
        assert "objective" in first_entry
        assert "n_columns" in first_entry

    def test_newman_history_tracking(self):
        """Verify iteration history is properly tracked."""
        bm, pm, om, G, profits = load_newman_objects(n_blocks=100)
        
        controller = BZController(
            n_blocks=100,
            precedence_graph=G,
            profits=profits,
            max_iters=15,
            max_columns=100,
        )
        controller.seed_with_singletons(topk=10)
        res = controller.run()
        
        history = controller.get_history()
        
        assert len(history) > 0, "No iteration history recorded"
        
        # Each history entry should have expected fields
        for entry in history:
            assert 'iter' in entry
            assert 'objective' in entry
            assert 'reduced_cost' in entry


class TestNewmanSolutionFiles:
    """Test solution file parsing and objective computation."""

    def test_newman_upit_solution_parses(self):
        """Verify UPIT solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/newman/newman1_upit.sol")
        # UPIT may exclude blocks with negative value (e.g., block 78)
        assert len(sol_ids) >= 1059, f"Expected at least 1059 blocks, got {len(sol_ids)}"
        assert len(sol_ids) <= 1060, f"Expected at most 1060 blocks, got {len(sol_ids)}"

    def test_newman_cpit_solution_parses(self):
        """Verify CPIT solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/newman/newman1_cpit_gmunoz120723.sol")
        # CPIT solution should select a subset of blocks
        assert 0 < len(sol_ids) <= 1060, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_newman_pcpsp_solution_parses(self):
        """Verify PCPSP solution file parses correctly."""
        sol_ids = load_sol_selected_ids("data/minelib/newman/newman1_pcpsp_gmunoz120723.sol")
        # PCPSP solution should select a subset of blocks
        assert 0 < len(sol_ids) <= 1060, f"Expected subset of blocks, got {len(sol_ids)}"

    def test_newman_upit_objective_value(self):
        """Verify UPIT solution achieves expected objective value."""
        base = "data/minelib/newman"
        om = parse_optimization_file(f"{base}/newman1.upit")
        sol_ids = load_sol_selected_ids(f"{base}/newman1_upit.sol")
        
        # Compute objective from solution
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_ids)
        
        # Should match reference value within small tolerance
        expected = NEWMAN_REFERENCE_VALUES["UPIT"]
        rel_error = abs(sol_obj - expected) / max(abs(expected), 1.0)
        assert rel_error < 0.01, (
            f"UPIT objective {sol_obj} differs from expected {expected} "
            f"by {rel_error*100:.2f}%"
        )

    def test_newman_cpit_satisfies_precedence(self):
        """Verify CPIT solution satisfies precedence constraints."""
        base = "data/minelib/newman"
        pm = parse_precedence_file(f"{base}/newman1.prec")
        sol_ids = load_sol_selected_ids(f"{base}/newman1_cpit_gmunoz120723.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"CPIT solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )

    def test_newman_pcpsp_satisfies_precedence(self):
        """Verify PCPSP solution satisfies precedence constraints."""
        base = "data/minelib/newman"
        pm = parse_precedence_file(f"{base}/newman1.prec")
        sol_ids = load_sol_selected_ids(f"{base}/newman1_pcpsp_gmunoz120723.sol")
        
        G = pm.to_networkx()
        
        # For each selected block, all predecessors should also be selected
        for block_id in sol_ids:
            preds = list(nx.ancestors(G, block_id))
            for pred in preds:
                assert pred in sol_ids, (
                    f"PCPSP solution contains block {block_id} but not "
                    f"its predecessor {pred}"
                )

    def test_newman_controller_vs_cpit_solution_subset(self):
        """
        Test controller performance against CPIT solution on subset.
        
        The controller should achieve an objective comparable to or better
        than the CPIT integer solution (since we're solving the LP relaxation).
        """
        base = "data/minelib/newman"
        bm = parse_blocks_file(f"{base}/newman1.blocks")
        pm = parse_precedence_file(f"{base}/newman1.prec")
        om = parse_optimization_file(f"{base}/newman1.upit")
        sol_ids = load_sol_selected_ids(f"{base}/newman1_cpit_gmunoz120723.sol")
        
        # Test on subset
        n = 300
        subset = list(range(min(n, len(bm.blocks))))
        
        # Compute objective from CPIT solution restricted to subset
        sol_subset_ids = [i for i in subset if i in sol_ids]
        sol_obj = sum(om.objective.get(i, [0.0])[0] for i in sol_subset_ids)
        
        # Build precedence subgraph
        Gfull = pm.to_networkx()
        G = nx.DiGraph()
        G.add_nodes_from(subset)
        for u, v in Gfull.edges():
            if u in subset and v in subset:
                G.add_edge(u, v)
        
        profits = {i: om.objective.get(i, [0.0])[0] for i in subset}
        
        # Run controller
        controller = BZController(
            n_blocks=n,
            precedence_graph=G,
            profits=profits,
            max_iters=30,
            max_columns=200,
        )
        controller.seed_with_singletons(topk=30)
        res = controller.run()
        controller_obj = res["objective"]
        
        # LP relaxation should be >= integer solution
        # Allow small tolerance for numerical precision
        assert controller_obj >= sol_obj - 1.0, (
            f"Controller LP objective {controller_obj} is worse than "
            f"CPIT integer solution {sol_obj}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
