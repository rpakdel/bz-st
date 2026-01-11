import os
from models.optimization import OptimizationModel, ResourceLimit

def parse_optimization_file(file_path: str) -> OptimizationModel:
    """
    Parses an optimization model file (.upit, .cpit, .pcpsp) according to MineLib spec.
    """
    model = OptimizationModel(name="", type="", n_blocks=0)
    
    with open(file_path, 'r') as f:
        current_section = None
        
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('%'):
                i += 1
                continue
            
            # Check for section headers (robust to spaces/underscores and colons)
            normalized_line = line.replace('_', ' ').replace(':', '').strip()
            
            if normalized_line.startswith('NAME'):
                model.name = line.split(':', 1)[1].strip() if ':' in line else line.split(None, 1)[1].strip()
            elif normalized_line.startswith('TYPE'):
                model.type = line.split(':', 1)[1].strip() if ':' in line else line.split(None, 1)[1].strip()
            elif normalized_line.startswith('NBLOCKS'):
                model.n_blocks = int(line.split(':', 1)[1].strip()) if ':' in line else int(line.split(None, 1)[1].strip())
            elif normalized_line.startswith('NPERIODS'):
                model.n_periods = int(line.split(':', 1)[1].strip()) if ':' in line else int(line.split(None, 1)[1].strip())
            elif normalized_line.startswith('NDESTINATIONS'):
                model.n_destinations = int(line.split(':', 1)[1].strip()) if ':' in line else int(line.split(None, 1)[1].strip())
            elif normalized_line.startswith('DISCOUNT RATE'):
                model.discount_rate = float(line.split(':', 1)[1].strip()) if ':' in line else float(line.split(None, 1)[1].strip())
            elif normalized_line.startswith('OBJECTIVE FUNCTION'):
                current_section = 'OBJECTIVE'
            elif normalized_line.startswith('RESOURCE CONSTRAINT COEFFICIENTS'):
                current_section = 'RES_COEFFS'
            elif normalized_line.startswith('RESOURCE CONSTRAINT LIMITS'):
                current_section = 'RES_LIMITS'
            elif normalized_line.startswith('NGENERAL SIDE CONSTRAINTS') or normalized_line.startswith('NRESOURCE SIDE CONSTRAINTS'):
                pass
            elif current_section == 'OBJECTIVE':
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        b_id = int(parts[0])
                        profits = [float(p) for p in parts[1:]]
                        model.objective[b_id] = profits
                        if len(model.objective) == model.n_blocks:
                            current_section = None
                    except ValueError:
                        # Might be a section header we missed
                        current_section = None
                        continue
            elif current_section == 'RES_COEFFS':
                # Check if next section starts
                if any(normalized_line.startswith(s) for s in ['RESOURCE CONSTRAINT LIMITS', 'OBJECTIVE FUNCTION', 'GENERAL']):
                   current_section = None
                   continue # Re-evaluate this line
                parts = line.split()
                if len(parts) == 3: # b r v
                    try:
                        b, r, v = int(parts[0]), int(parts[1]), float(parts[2])
                        model.resource_coeffs[(b, r)] = v
                    except ValueError: pass
                elif len(parts) == 4: # b d r v
                    try:
                        b, d, r, v = int(parts[0]), int(parts[1]), int(parts[2]), float(parts[3])
                        model.resource_coeffs[(b, d, r)] = v
                    except ValueError: pass
            elif current_section == 'RES_LIMITS':
                 # Check if next section starts
                 if any(normalized_line.startswith(s) for s in ['RESOURCE CONSTRAINT COEFFICIENTS', 'OBJECTIVE FUNCTION']):
                    current_section = None
                    continue
                 parts = line.split()
                 if len(parts) >= 4:
                     try:
                         r, t, c, v1 = int(parts[0]), int(parts[1]), parts[2], float(parts[3])
                         v2 = float(parts[4]) if len(parts) > 4 else None
                         model.resource_limits.append(ResourceLimit(r, t, c, v1, v2))
                     except ValueError: pass
            
            i += 1
            
    return model
