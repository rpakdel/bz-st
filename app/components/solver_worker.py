import sys
import json
import networkx as nx
from pathlib import Path
from models.bz_controller import BZController

def main():
    if len(sys.argv) != 2:
        print("Usage: python solver_worker.py <input_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Input file {input_file} not found")
        sys.exit(1)

    with open(input_file, 'r') as f:
        data = json.load(f)

    n_blocks = data['n_blocks']
    orig_ids = data['orig_ids']
    edges = data['edges']
    profits = data['profits']
    eps = data['eps']
    max_iters = data['max_iters']
    status_file = Path(data['status_file'])
    result_file = Path(data['result_file'])

    # Build graph
    G = nx.DiGraph()
    id_to_idx = {orig_id: idx for idx, orig_id in enumerate(orig_ids)}
    idx_to_id = {idx: orig_id for orig_id, idx in id_to_idx.items()}
    for u, v in edges:
        if u in id_to_idx and v in id_to_idx:
            G.add_edge(id_to_idx[u], id_to_idx[v])

    # Profits dict
    profits_dict = {idx: p for idx, p in enumerate(profits)}

    controller = BZController(n_blocks=n_blocks, precedence_graph=G, profits=profits_dict, eps=eps, max_iters=max_iters)

    def cb(entry):
        status = {
            'iter': entry.get('iter', -1),
            'objective': entry.get('objective', 0.0),
            'n_columns': entry.get('n_columns', 0),
            'reduced_cost': entry.get('reduced_cost'),
            'total_weight': entry.get('total_weight', 0.0)
        }
        tmp_status = str(status_file) + ".tmp"
        try:
            with open(tmp_status, 'w') as f:
                json.dump(status, f)
            import os
            os.replace(tmp_status, str(status_file))
        except Exception:
            pass

    controller.add_iteration_callback(cb)
    controller.seed_with_singletons(topk=10)

    try:
        res = controller.run(verbose=False)
        # Prepare patterns
        final_sol = controller.master.export_solution()
        vars_map = final_sol.get('variables', {})
        patterns = []
        for p in controller.master.columns:
            lam = vars_map.get(p.id, 0.0)
            orig_blocks = [str(idx_to_id.get(b, b)) for b in p.blocks]
            patterns.append({
                'pattern_id': p.id,
                'lambda': lam,
                'n_blocks': len(p.blocks),
                'blocks': ";".join(orig_blocks),
                'profit': p.profit
            })
        
        # Define result dictionary
        result = {
            'status': res.get('status'),
            'objective': res.get('objective'),
            'iterations': res.get('iterations'),
            'history': controller.history,
            'patterns': patterns
        }

        # Write result
        tmp_result = str(result_file) + ".tmp"
        with open(tmp_result, 'w') as f:
            json.dump(result, f)
        import os
        os.replace(tmp_result, str(result_file))
    except Exception as e:
        result = {
            'status': 'error',
            'message': str(e)
        }
        tmp_result = str(result_file) + ".tmp"
        with open(tmp_result, 'w') as f:
            json.dump(result, f)
        import os
        os.replace(tmp_result, str(result_file))

if __name__ == "__main__":
    main()