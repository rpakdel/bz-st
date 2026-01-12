import os
from typing import List, Optional
from models.block import Block, BlockModel

def parse_blocks_file(file_path: str, attribute_names: Optional[List[str]] = None) -> BlockModel:
    """
    Parses a .blocks file according to the MineLib specification.
    
    Handles both numeric-only attributes (e.g., zuck_small) and mixed attributes 
    (e.g., newman with string 'type' field). String attributes are stored as 0.0
    in the numeric attributes list, and the original string values are preserved
    separately if needed.
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
            
            # Parse remaining parts, converting to float where possible
            # For strings (like block types), we store 0.0 as placeholder
            attributes = []
            for p in parts[4:]:
                try:
                    attributes.append(float(p))
                except ValueError:
                    # Non-numeric attribute (e.g., block type string)
                    # Store 0.0 as placeholder - string values can be preserved elsewhere if needed
                    attributes.append(0.0)
            
            blocks.append(Block(id=block_id, x=x, y=y, z=z, attributes=attributes))
            
    return BlockModel(name=name, blocks=blocks, attribute_names=attribute_names or [])
