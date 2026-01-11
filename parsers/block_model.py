import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import io
import os

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
        for b in self.blocks:
            row = [b.id, b.x, b.y, b.z] + b.attributes
            data.append(row)
        
        columns = ["id", "x", "y", "z"] + self.attribute_names
        # Handle cases where we have more attributes than names
        if len(self.attribute_names) < len(self.blocks[0].attributes):
            for i in range(len(self.attribute_names), len(self.blocks[0].attributes)):
                columns.append(f"attr_{i}")
        
        return pd.DataFrame(data, columns=columns)

def parse_blocks_file(file_path: str, attribute_names: Optional[List[str]] = None) -> BlockModel:
    """
    Parses a .blocks file according to the MineLib specification.
    """
    blocks = []
    name = os.path.basename(file_path).replace(".blocks", "")
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            
            # Replace ':' and tabs with space for easier splitting
            line = line.replace(':', ' ').replace('\t', ' ')
            parts = line.split()
            
            if len(parts) < 4:
                continue
            
            block_id = int(parts[0])
            x = int(parts[1])
            y = int(parts[2])
            z = int(parts[3])
            attributes = [float(p) for p in parts[4:]]
            
            blocks.append(Block(id=block_id, x=x, y=y, z=z, attributes=attributes))
            
    return BlockModel(name=name, blocks=blocks, attribute_names=attribute_names or [])
