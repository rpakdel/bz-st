from typing import Dict, List, Optional
import logging
import time
import networkx as nx

from models.master_problem import MasterProblem, BlockPattern
from models.pricer import ClosurePricer, PricingResult


class BZController:
    """
    Simple Bienstock-Zuckerberg column generation controller.

    This minimal controller is intended for testing and small instances. It
    uses the provided `MasterProblem` and `ClosurePricer` to iteratively
    generate columns until no improving column (reduced_cost < -eps) is found
    or `max_iters` is reached.
    """

    def __init__(self, n_blocks: int, precedence_graph: nx.DiGraph, profits: Dict[int, float], eps: float = 1e-6, max_iters: int = 50, max_columns: Optional[int] = None, logger: Optional[logging.Logger] = None):
        self.master = MasterProblem(n_blocks=n_blocks)
        self.pricer = ClosurePricer(precedence_graph=precedence_graph, profits=profits)
        self.eps = eps
        self.max_iters = max_iters
        self.max_columns = max_columns
        self.profits = profits

        # Setup logger
        self.logger = logger or logging.getLogger(__name__)
        if not self.logger.handlers:
            # Basic configuration for library use; host app may configure logging
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Detailed iteration history
        self.history: List[Dict] = []
        # Callbacks invoked each iteration with signature cb(entry_dict)
        self.iter_callbacks: List = []
        # Diagnostics summary
        self.diagnostics: Dict = {}

    def seed_with_singletons(self, limit: Optional[int] = None, topk: Optional[int] = None):
        """Seed the master with singleton block patterns.

        Args:
            limit: maximum number of singletons to add (iterates blocks in id order)
            topk: if provided, seed with the `topk` blocks by profit instead
        """
        ids = list(range(self.master.n_blocks))
        if topk is not None:
            # choose top-k by profit
            ids = sorted(ids, key=lambda i: self.profits.get(i, 0.0), reverse=True)[:topk]

        count = 0
        for b in ids:
            pattern = BlockPattern(id=self.master.next_column_id, blocks=[b], profit=self.profits.get(b, 0.0), name=f"init_{b}")
            self.master.add_column(pattern)
            self.master.next_column_id += 1
            count += 1
            if limit is not None and count >= limit:
                break

    def run(self, verbose: bool = False) -> Dict[str, object]:
        """Run the column-generation loop.

        Returns a dict with `status`, `iterations`, `objective`, and detailed `history`.
        """
        start_time = time.time()
        self.history.clear()

        for it in range(self.max_iters):
            sol = self.master.solve()

            duals = sol.duals
            convex_dual = sol.convexity_dual or 0.0

            pr_res: PricingResult = self.pricer.price(duals=duals, convexity_dual=convex_dual)

            # Record rich history
            # Compute dual-based upper bound
            sum_duals = sum(duals.values()) if duals else 0.0
            W_star = pr_res.total_weight
            z = convex_dual
            ub = sum_duals + max(z, W_star)

            entry = {
                "iter": it,
                "objective": sol.objective_value,
                "n_columns": len(self.master.columns),
                "reduced_cost": pr_res.reduced_cost,
                "total_weight": pr_res.total_weight,
                "selected_blocks": list(pr_res.selected_blocks),
                "convexity_dual": convex_dual,
                "dual_norm": sum(abs(v) for v in duals.values()),
                # dual upper bound and relative gap
                "ub": ub,
                "rel_gap": (ub - sol.objective_value) / max(1.0, ub) if ub > 0 else 0.0,
            }
            self.history.append(entry)

            # Logging
            self.logger.info("Iter %d obj=%s cols=%d red_cost=%.6g sel=%d", it, sol.objective_value, len(self.master.columns), pr_res.reduced_cost, len(pr_res.selected_blocks))
            if verbose:
                print(entry)

            # Invoke callbacks
            for cb in self.iter_callbacks:
                try:
                    cb(entry)
                except Exception:
                    self.logger.exception("Iterator callback failed")

            # If reduced cost is not improving, stop
            if pr_res.reduced_cost >= -self.eps:
                # finalize diagnostics
                self.diagnostics['best_rel_gap'] = min((h.get('rel_gap', 0.0) for h in self.history), default=0.0)
                self.diagnostics['best_objective'] = max((h.get('objective', 0.0) for h in self.history), default=sol.objective_value)
                self.diagnostics['last_ub'] = ub
                return {
                    "status": "converged",
                    "iterations": it,
                    "objective": sol.objective_value,
                    "history": self.history,
                    "time": time.time() - start_time,
                }

            # Check max_columns guard
            if self.max_columns is not None and len(self.master.columns) >= self.max_columns:
                self.logger.warning("Max columns reached (%d); stopping before adding new columns.", self.max_columns)
                return {
                    "status": "max_columns_reached",
                    "iterations": it,
                    "objective": sol.objective_value,
                    "history": self.history,
                    "time": time.time() - start_time,
                }

            # Otherwise add the new column (closure) to master
            pattern_profit = sum(self.profits.get(b, 0.0) for b in pr_res.selected_blocks)
            new_pattern = BlockPattern(id=self.master.next_column_id, blocks=pr_res.selected_blocks, profit=pattern_profit, name=f"col_{it}")
            self.master.add_column(new_pattern)
            self.master.next_column_id += 1

        # Reached max_iters
        final_obj = self.master.solve().objective_value
        self.diagnostics['best_rel_gap'] = min((h.get('rel_gap', 0.0) for h in self.history), default=0.0)
        self.diagnostics['best_objective'] = max((h.get('objective', 0.0) for h in self.history), default=final_obj)
        # store last UB if history exists
        if self.history:
            self.diagnostics['last_ub'] = self.history[-1].get('ub')
        return {
            "status": "max_iters",
            "iterations": self.max_iters,
            "objective": final_obj,
            "history": self.history,
            "time": time.time() - start_time,
        }

    def get_history(self) -> List[Dict]:
        return list(self.history)

    def get_diagnostics(self) -> Dict:
        return dict(self.diagnostics)

    def add_iteration_callback(self, cb):
        """Register a callback to be called each iteration with the history entry."""
        self.iter_callbacks.append(cb)

    def prune_low_activity_columns(self, keep_top_k: int = 50):
        """Prune columns that have zero or low activity in recent solutions.

        Note: This is a heuristic for testing and small instances. The MasterProblem
        stores patterns in `self.master.columns` and variables in `self.master.lambda_vars`.
        We'll prune columns with the smallest profit that are currently zero in the
        last solution.
        """
        if not self.master.columns:
            return 0

        # Solve to get current lambda values
        sol = self.master.solve()
        lambda_vals = sol.variable_values

        # Pair patterns with lambda activity
        pattern_activity = []
        for p in self.master.columns:
            val = lambda_vals.get(p.id, 0.0)
            pattern_activity.append((p, val))

        # Sort by activity then by profit
        pattern_activity.sort(key=lambda x: (x[1], x[0].profit))

        # Keep top-k by activity (reverse sorted by activity)
        to_keep = set(p.id for p, _ in sorted(pattern_activity, key=lambda x: (x[1], x[0].profit), reverse=True)[:keep_top_k])

        # Build new columns list and delete variables for pruned ones
        new_columns = []
        removed = 0
        for p in self.master.columns:
            if p.id in to_keep:
                new_columns.append(p)
            else:
                # remove variable if exists
                if p.id in self.master.lambda_vars:
                    del self.master.lambda_vars[p.id]
                removed += 1

        self.master.columns = new_columns
        # Rebuild constraints with the reduced variable set
        self.master._rebuild_convexity_constraint()
        self.master._rebuild_block_constraints()

        self.logger.info("Pruned %d columns, kept %d", removed, len(new_columns))
        return removed
