from dataclasses import dataclass
from typing import Dict, List, Tuple
import networkx as nx


@dataclass
class PricingResult:
    reduced_cost: float
    selected_blocks: List[int]
    total_weight: float


class ClosurePricer:
    """
    Pricing subproblem for BZ: given duals for block constraints and convexity dual,
    build node weights (profit - dual) and find a maximum-weight closure using
    a min-cut construction on a DAG (precedence graph). The result is a pattern
    (closure) with its reduced cost.

    This implementation is intentionally backend-agnostic and uses NetworkX
    for graph operations. It expects the precedence graph to be a DAG (edges
    u->v mean u is predecessor of v, so closure must be closed under successors).
    """

    def __init__(self, precedence_graph: nx.DiGraph, profits: Dict[int, float]):
        """
        Args:
            precedence_graph: `nx.DiGraph` where an edge (u, v) means u is predecessor of v.
            profits: mapping block_id -> profit (unreduced, e.g., objective contribution)
        """
        self.G = precedence_graph.copy()
        self.profits = profits

    def _build_cut_graph(self, weights: Dict[int, float]) -> nx.DiGraph:
        """
        Build an s-t graph for minimum s-t cut to find maximum-weight closure.
        For each node i with weight w:
          - If w >= 0: add edge (s -> i) with capacity = w
          - If w < 0: add edge (i -> t) with capacity = -w
        For each precedence edge (u -> v) enforce closure by adding infinite-capacity
        edge (u -> v) in the cut graph.
        """
        H = nx.DiGraph()
        s = "__source__"
        t = "__sink__"
        H.add_node(s)
        H.add_node(t)

        for n, w in weights.items():
            H.add_node(n)
            if w >= 0:
                H.add_edge(s, n, capacity=float(w))
            else:
                H.add_edge(n, t, capacity=float(-w))

        # Add precedence/infinite capacity edges to forbid selecting successors without predecessors
        # Use a sufficiently large capacity (sum of positive weights + 1) to simulate infinity
        finite_cap = sum(max(0.0, w) for w in weights.values()) + 1.0
        for u, v in self.G.edges():
            # In the precedence graph an edge (u -> v) means u is a predecessor of v
            # (u must be mined before v). For the closure construction we must ensure
            # that if v is selected then u is also selected. To enforce this with a
            # min-cut we add an infinite-capacity edge from v -> u (reverse direction)
            # so cutting v from the source without cutting u would incur infinite cost.
            H.add_edge(v, u, capacity=finite_cap)

        return H

    def price(self, duals: Dict[int, float], convexity_dual: float = 0.0) -> PricingResult:
        """
        Compute pricing: node weight = profit - block_dual - convexity_dual * 0
        (convexity dual applies to column creation cost; here patterns are free so we
        only subtract block duals — if a different formulation is used, adapt here).

        Returns a PricingResult with reduced_cost = (convexity_dual - total_weight)
        following the usual pricing sign convention for maximization master.
        """
        # Build weights: profit - dual. If a block missing profit, assume 0
        weights = {}
        for n in self.G.nodes():
            if n == '__source__' or n == '__sink__':
                continue
            p = self.profits.get(n, 0.0)
            dual = duals.get(n, 0.0)
            weights[n] = p - dual

        # Build cut graph
        H = self._build_cut_graph(weights)

        # Compute minimum s-t cut
        s = "__source__"
        t = "__sink__"

        # networkx.minimum_cut requires a DiGraph with 'capacity' attributes
        cut_value, (S, T) = nx.minimum_cut(H, s, t, capacity='capacity')

        # Nodes reachable from source (S) correspond to selected nodes with positive contribution
        selected = [n for n in S if n not in (s, t)]

        total_weight = sum(weights.get(n, 0.0) for n in selected)

        # Reduced cost: for maximization master, reduced cost of column = convexity_dual - total_weight
        reduced_cost = convexity_dual - total_weight

        return PricingResult(reduced_cost=reduced_cost, selected_blocks=selected, total_weight=total_weight)
