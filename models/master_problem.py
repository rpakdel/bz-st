from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import pulp
from models.optimization import OptimizationModel

@dataclass
class BlockPattern:
    """Represents a column/pattern in the master problem"""
    id: int
    blocks: List[int]  # List of block IDs in this pattern
    profit: float      # Total profit of this pattern
    name: str = ""     # Optional name for debugging

@dataclass
class MasterSolution:
    """Solution from the master problem"""
    objective_value: float
    duals: Dict[int, float]  # block_id -> dual value
    convexity_dual: float    # dual of convexity constraint
    variable_values: Dict[int, float]  # pattern_id -> lambda value

class MasterProblem:
    """
    Restricted Master Problem for BZ algorithm.
    Uses PuLP to solve the LP relaxation.
    """

    def __init__(self, n_blocks: int, solver: str = 'cbc'):
        """
        Initialize the master problem.

        Args:
            n_blocks: Total number of blocks in the instance
            solver: Solver to use ('cbc' or 'cplex')
        """
        self.n_blocks = n_blocks
        self.solver = solver

        # PuLP model
        self.model = pulp.LpProblem("BZ_Master", pulp.LpMaximize)

        # Decision variables: lambda_j for each pattern j
        self.lambda_vars: Dict[int, pulp.LpVariable] = {}

        # Constraints
        self.convexity_constraint: Optional[pulp.LpConstraint] = None
        self.block_constraints: Dict[int, pulp.LpConstraint] = {}  # block_id -> constraint

        # Columns (patterns)
        self.columns: List[BlockPattern] = []
        self.next_column_id = 0
        self.constraint_version = 0  # For unique constraint names

        # Initialize with convexity constraint
        self._initialize_convexity_constraint()

        # Initialize block constraints (one per block)
        self._initialize_block_constraints()

    def _initialize_convexity_constraint(self):
        """Add convexity constraint: sum lambda_j = 1"""
        # We'll rebuild this constraint when adding columns
        pass

    def _initialize_block_constraints(self):
        """Initialize block constraints: for each block i, sum lambda_j <= 1 where j contains i"""
        # We'll add these when we have variables
        pass

    def _rebuild_convexity_constraint(self):
        """Rebuild the convexity constraint with current variables"""
        # Remove old convexity constraints
        to_remove = [name for name in self.model.constraints.keys() if name.startswith("convexity_")]
        for name in to_remove:
            del self.model.constraints[name]
        
        # If no variables, convexity is trivially satisfied (0 = 1 is false, but we handle this)
        if self.lambda_vars:
            convexity_expr = pulp.lpSum(self.lambda_vars.values())
        else:
            convexity_expr = 0  # 0 = 1, which will make the problem infeasible, but we handle it
        
        self.convexity_constraint = pulp.LpConstraint(
            e=convexity_expr,
            sense=pulp.LpConstraintEQ,
            rhs=1.0,
            name=f"convexity_{self.constraint_version}"
        )
        self.model.addConstraint(self.convexity_constraint)

    def _rebuild_block_constraints(self):
        """Rebuild all block constraints with current variables"""
        # Remove old block constraints
        to_remove = [name for name in self.model.constraints.keys() if name.startswith("block_")]
        for name in to_remove:
            del self.model.constraints[name]
        
        # Clear our dictionary
        self.block_constraints.clear()
        
        # Rebuild each block constraint
        for block_id in range(self.n_blocks):
            # Find all patterns that contain this block
            relevant_vars = []
            for pattern in self.columns:
                if block_id in pattern.blocks:
                    relevant_vars.append(self.lambda_vars[pattern.id])
            
            if relevant_vars:  # Only add constraint if there are variables
                block_expr = pulp.lpSum(relevant_vars)
                constraint = pulp.LpConstraint(
                    e=block_expr,
                    sense=pulp.LpConstraintLE,
                    rhs=1.0,
                    name=f"block_{block_id}_{self.constraint_version}"
                )
                self.block_constraints[block_id] = constraint
                self.model.addConstraint(constraint)

    def initialize(self, initial_patterns: List[BlockPattern]):
        """
        Initialize the master problem with initial columns.

        Args:
            initial_patterns: List of initial patterns to start with
        """
        for pattern in initial_patterns:
            self.add_column(pattern)

    def add_column(self, pattern: BlockPattern):
        """
        Add a new column (pattern) to the master problem.

        Args:
            pattern: The pattern to add
        """
        # Assign ID if not set
        if pattern.id is None:
            pattern.id = self.next_column_id
            self.next_column_id += 1

        # Create lambda variable
        lambda_var = pulp.LpVariable(f"lambda_{pattern.id}", lowBound=0, cat='Continuous')
        self.lambda_vars[pattern.id] = lambda_var

        # Add to objective
        if self.model.objective is None:
            self.model.objective = pattern.profit * lambda_var
        else:
            self.model.objective += pattern.profit * lambda_var

        # Store the pattern
        self.columns.append(pattern)

        # Increment version for unique constraint names
        self.constraint_version += 1

        # Rebuild constraints
        self._rebuild_convexity_constraint()
        self._rebuild_block_constraints()

    def solve(self) -> MasterSolution:
        """
        Solve the master problem LP.

        Returns:
            MasterSolution with objective value, duals, and variable values
        """
        # Set solver
        if self.solver == 'cbc':
            solver = pulp.PULP_CBC_CMD(msg=False)
        elif self.solver == 'cplex':
            solver = pulp.CPLEX_CMD()
        else:
            solver = pulp.PULP_CBC_CMD(msg=False)

        # Special case: no variables
        if not self.lambda_vars:
            return MasterSolution(
                objective_value=0.0,
                duals={},
                convexity_dual=0.0,
                variable_values={}
            )

        # Solve
        status = self.model.solve(solver)

        if status != pulp.LpStatusOptimal:
            raise ValueError(f"Master problem not solved optimally. Status: {pulp.LpStatus[status]}")

        # Extract solution
        if self.model.objective is None:
            objective_value = 0.0
        else:
            objective_value = pulp.value(self.model.objective)

        # Extract duals
        duals = {}
        convexity_dual = None

        for name, constraint in self.model.constraints.items():
            if name.startswith("convexity_"):
                convexity_dual = constraint.pi
            elif name.startswith("block_"):
                # Extract block_id from name like "block_123_5"
                parts = name.split("_")
                if len(parts) >= 2:
                    try:
                        block_id = int(parts[1])
                        duals[block_id] = constraint.pi
                    except ValueError:
                        pass

        # Extract variable values
        variable_values = {}
        for pattern_id, var in self.lambda_vars.items():
            variable_values[pattern_id] = pulp.value(var)

        return MasterSolution(
            objective_value=objective_value,
            duals=duals,
            convexity_dual=convexity_dual,
            variable_values=variable_values
        )

    def get_duals(self) -> Dict[int, float]:
        """
        Get the current dual values for blocks.
        Assumes the model has been solved recently.

        Returns:
            Dictionary mapping block_id to dual value
        """
        duals = {}
        for name, constraint in self.model.constraints.items():
            if name.startswith("block_"):
                block_id = int(name.split("_")[1])
                duals[block_id] = constraint.pi
        return duals

    def export_solution(self) -> Dict[str, Any]:
        """
        Export the current solution for analysis.

        Returns:
            Dictionary with solution details
        """
        if not self.lambda_vars:
            return {"status": "no_variables"}

        # Get current solution
        try:
            solution = self.solve()
            return {
                "status": "optimal",
                "objective": solution.objective_value,
                "duals": solution.duals,
                "variables": solution.variable_values,
                "n_columns": len(self.columns)
            }
        except ValueError as e:
            return {"status": "error", "message": str(e)}

    def get_column_count(self) -> int:
        """Get the number of columns in the master problem."""
        return len(self.columns)

    def get_block_dual(self, block_id: int) -> float:
        """Get the dual value for a specific block."""
        constraint_name = f"block_{block_id}"
        if constraint_name in self.model.constraints:
            return self.model.constraints[constraint_name].pi
        return 0.0