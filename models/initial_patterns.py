from models.master_problem import BlockPattern
from models.optimization import OptimizationModel
from typing import List

def generate_initial_patterns(om: OptimizationModel, max_patterns: int = 50) -> List[BlockPattern]:
    """
    Generate initial patterns for the master problem.
    For BZ algorithm, we typically start with single-block patterns or heuristic patterns.

    Args:
        om: Optimization model with objective values
        max_patterns: Maximum number of initial patterns to generate

    Returns:
        List of initial BlockPattern objects
    """
    patterns = []

    # For UPIT problems, single-block patterns are feasible
    if om.type == "UPIT":
        for block_id in range(min(om.n_blocks, max_patterns)):
            if block_id in om.objective:
                profit = om.objective[block_id][0]  # Single destination for UPIT
                pattern = BlockPattern(
                    id=len(patterns),
                    blocks=[block_id],
                    profit=profit,
                    name=f"single_block_{block_id}"
                )
                patterns.append(pattern)

    # For more complex problems, we might need precedence-feasible patterns
    # For now, we'll stick with single blocks and let the algorithm find better ones

    return patterns

def create_trivial_pattern(n_blocks: int) -> BlockPattern:
    """
    Create a trivial pattern with no blocks (do nothing).
    This ensures feasibility.

    Args:
        n_blocks: Total number of blocks (for ID assignment)

    Returns:
        Trivial pattern with zero profit
    """
    return BlockPattern(
        id=999999,  # High ID to avoid conflicts
        blocks=[],
        profit=0.0,
        name="trivial"
    )