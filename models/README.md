# Models Package Documentation

This document summarizes the data classes and primary methods defined in the `models` package.

**Block Model**
- `Block` (dataclass)
  - Attributes:
    - `id: int` - Unique integer identifier for the block.
    - `x: int`, `y: int`, `z: int` - Coordinates (grid indices or real positions).
    - `attributes: List[float]` - Numeric attributes (e.g., tonnage, grade, value).

- `BlockModel` (dataclass)
  - Attributes:
    - `name: str` - Human-readable name for the block model instance.
    - `blocks: List[Block]` - List of `Block` objects.
    - `attribute_names: List[str]` - Optional names for numeric attributes.
  - Methods:
    - `to_dataframe() -> pandas.DataFrame` - Convert blocks into a `DataFrame` with columns `id, x, y, z, <attributes...>`.

**Initial Patterns**
- Functions in `initial_patterns.py`:
  - `generate_initial_patterns(om: OptimizationModel, max_patterns: int = 50) -> List[BlockPattern]`
    - Creates seed columns/patterns for the master problem. For `UPIT` problems this generates single-block patterns using `om.objective` values. Returns a list of `BlockPattern` objects.
  - `create_trivial_pattern(n_blocks: int) -> BlockPattern`
    - Returns a trivial (empty) `BlockPattern` with zero profit. Useful to ensure feasibility.

**Master Problem**
- `BlockPattern` (dataclass)
  - Attributes:
    - `id: int` - Pattern identifier.
    - `blocks: List[int]` - List of block IDs included in this pattern.
    - `profit: float` - Profit (objective contribution) of the pattern.
    - `name: str` - Optional human-readable name.

- `MasterSolution` (dataclass)
  - Attributes:
    - `objective_value: float` - LP objective value.
    - `duals: Dict[int, float]` - Map block_id -> dual value.
    - `convexity_dual: float` - Dual for the convexity constraint (sum of lambdas = 1).
    - `variable_values: Dict[int, float]` - Map pattern_id -> lambda value.

- `MasterProblem` (class)
  - Purpose: Implements the Restricted Master Problem (RMP) for the Bienstock–Zuckerberg column generation algorithm using PuLP.
  - Constructor: `MasterProblem(n_blocks: int, solver: str = 'cbc')`
    - `n_blocks`: total number of blocks in the instance.
    - `solver`: `'cbc'` (default) or `'cplex'` (if available).
  - Important attributes:
    - `model`: `pulp.LpProblem` instance.
    - `lambda_vars: Dict[int, pulp.LpVariable]`: decision variables per pattern.
    - `columns: List[BlockPattern]`: current pool of patterns (columns).
    - `block_constraints: Dict[int, pulp.LpConstraint]`: per-block constraints ensuring a block is used at most once.
  - Key methods:
    - `_initialize_convexity_constraint()` - placeholder to set up convexity; real building is done in `_rebuild_convexity_constraint`.
    - `_initialize_block_constraints()` - placeholder for block constraints; rebuilt when columns change.
    - `_rebuild_convexity_constraint()` - (re)creates the equality constraint `sum_j lambda_j = 1` with unique names.
    - `_rebuild_block_constraints()` - (re)creates `sum_{j: i in pattern_j} lambda_j <= 1` for each block `i` that appears in at least one pattern.
    - `initialize(initial_patterns: List[BlockPattern])` - add a set of starting columns.
    - `add_column(pattern: BlockPattern)` - add a single pattern to the RMP, creates a variable, updates objective, and rebuilds constraints.
    - `solve() -> MasterSolution` - solve the LP and return a `MasterSolution` with objective, duals, and variable values. Raises `ValueError` if not optimal.
    - `get_duals() -> Dict[int, float]` - convenience to extract block duals from the model's constraints.
    - `export_solution() -> Dict[str, Any]` - wrapper that tries to solve and returns a serializable result with status, objective, duals, variables, and column count.
    - `get_column_count() -> int` - number of columns currently in the master.
    - `get_block_dual(block_id: int) -> float` - returns the dual for a specific block constraint (or `0.0` if missing).

**Optimization Model**
- `ResourceLimit` (dataclass)
  - Attributes:
    - `resource: int` - Resource identifier.
    - `period: int` - Time period index.
    - `type: str` - 'L', 'G', or 'I' (left/right inequality type; project-specific semantics).
    - `v1: float`, `v2: Optional[float]` - Numeric limit parameters.

- `OptimizationModel` (dataclass)
  - Attributes:
    - `name: str` - Instance name.
    - `type: str` - Problem type string (e.g., 'UPIT').
    - `n_blocks: int` - Number of blocks.
    - `n_periods: Optional[int]` - Number of periods (if applicable).
    - `n_destinations: Optional[int]` - Number of destinations (if applicable).
    - `discount_rate: Optional[float]` - Discount rate.
    - `objective: Dict[int, List[float]]` - Mapping block_id -> list of profits per destination.
    - `resource_coeffs: Dict[Tuple, float]` - Resource coefficients keyed by tuple (b, r) or (b, d, r).
    - `resource_limits: List[ResourceLimit]` - Resource limit objects.

**Precedence Model**
- `PrecedenceModel` (dataclass)
  - Attributes:
    - `name: str` - Instance name.
    - `precedences: Dict[int, List[int]]` - Mapping block_id -> list of predecessor block IDs.
  - Methods:
    - `to_networkx() -> networkx.DiGraph` - Builds and returns a `DiGraph` where an edge `(u, v)` means `u` must be mined before `v` (i.e., predecessors -> block).

Notes
- The implementations favor simplicity for use in the BZ algorithm. Some methods are implemented as rebuild-on-change (reconstruct constraints fully when columns change) which is clearer but may be inefficient for very large column pools.
- The `MasterProblem` uses PuLP's solver wrappers; set `solver='cplex'` if `CPLEX_CMD` is available in your environment and you have a license.

If you want, I can also generate Sphinx-style docstrings or inline `#` comments for each class and method, or create a `docs/` page. Which format do you prefer next?
