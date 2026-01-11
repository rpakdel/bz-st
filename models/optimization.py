from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

@dataclass
class ResourceLimit:
    resource: int
    period: int
    type: str  # 'L', 'G', 'I'
    v1: float
    v2: Optional[float] = None

@dataclass
class OptimizationModel:
    name: str
    type: str
    n_blocks: int
    n_periods: Optional[int] = None
    n_destinations: Optional[int] = None
    discount_rate: Optional[float] = None
    objective: Dict[int, List[float]] = field(default_factory=dict)  # block_id -> profits per destination
    resource_coeffs: Dict[Tuple, float] = field(default_factory=dict) # (b, r) or (b, d, r) -> coeff
    resource_limits: List[ResourceLimit] = field(default_factory=list)
