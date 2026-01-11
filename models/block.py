from dataclasses import dataclass, field
from typing import List
import pandas as pd

@dataclass
class Block:
    id: int
    x: int
    y: int
    z: int
    attributes: List[float]

@dataclass
class BlockModel:
    name: str
    blocks: List[Block]
    attribute_names: List[str] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        data = []
        if not self.blocks:
            columns = ["id", "x", "y", "z"] + self.attribute_names
            return pd.DataFrame(columns=columns)
            
        for b in self.blocks:
            row = [b.id, b.x, b.y, b.z] + b.attributes
            data.append(row)
        
        columns = ["id", "x", "y", "z"] + self.attribute_names
        # Handle cases where we have more attributes than names
        if len(self.attribute_names) < len(self.blocks[0].attributes):
            for i in range(len(self.attribute_names), len(self.blocks[0].attributes)):
                columns.append(f"attr_{i}")
        
        return pd.DataFrame(data, columns=columns)
