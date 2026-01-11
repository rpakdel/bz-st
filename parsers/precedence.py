import os
from models.precedence import PrecedenceModel

def parse_precedence_file(file_path: str) -> PrecedenceModel:
    """
    Parses a .prec file according to the MineLib specification.
    """
    precedences = {}
    name = os.path.basename(file_path).replace(".prec", "")
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            
            # Replace ':' and tabs with space for easier splitting
            line = line.replace(':', ' ').replace('\t', ' ')
            parts = line.split()
            
            if not parts:
                continue
            
            block_id = int(parts[0])
            n_predecessors = int(parts[1])
            predecessor_ids = [int(p) for p in parts[2:2+n_predecessors]]
            
            precedences[block_id] = predecessor_ids
            
    return PrecedenceModel(name=name, precedences=precedences)
