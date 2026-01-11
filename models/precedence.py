from dataclasses import dataclass
from typing import List, Dict
import networkx as nx

@dataclass
class PrecedenceModel:
    name: str
    precedences: Dict[int, List[int]]  # block_id -> list of predecessor IDs

    def to_networkx(self) -> nx.DiGraph:
        """
        Builds a DiGraph where an edge (u, v) means block u MUST be mined before v.
        In MineLib, p1...pn are predecessors of b, so edges are (pi, b).
        """
        G = nx.DiGraph()
        for block_id, predecessors in self.precedences.items():
            G.add_node(block_id)
            for p in predecessors:
                G.add_edge(p, block_id)
        return G
