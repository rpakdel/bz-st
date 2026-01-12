import streamlit as st
from models.bz_controller import BZController
import networkx as nx


def render_solver_settings(df=None, pm=None, om=None, config=None):
    st.markdown("---")
    st.write("#### BZ Algorithm Settings")
    
    # Algorithm Parameters in columns for side-by-side view
    c1, c2, c3 = st.columns(3)
    max_iter = c1.number_input("Max Iterations", min_value=1, max_value=1000, value=100)
    epsilon = c2.number_input("Epsilon (Tolerance)", min_value=1e-9, max_value=1e-1, value=1e-6, format="%.1e")
    solver = c3.selectbox("L Master Solver", ["CBC (Native)", "CPLEX (Future)"])
    
    # Optimization Run
    if st.button("🚀 Run BZ Optimizer", use_container_width=True):
        st.info("Starting BZ Optimizer")

        if df is None or om is None or pm is None:
            st.error("Dataset not loaded for solver run")
        else:
            # Build precedence graph from pm (assumed to be models.precedence.PrecedenceModel)
            G = pm.to_networkx()

            # Prepare profits: use objective if available
            profits = {b.id: (om.objective.get(b.id, [0.0])[0] if om and hasattr(om, 'objective') else 0.0) for b in df.to_dict('records')}

            controller = BZController(n_blocks=len(df), precedence_graph=G, profits=profits, max_iters=int(max_iter))

            progress = st.progress(0)
            status_area = st.empty()
            logs = st.empty()

            def cb(entry):
                # Update progress and logs
                it = entry['iter']
                obj = entry['objective']
                cols = entry['n_columns']
                progress.progress(min(100, int(100 * (it + 1) / max_iter)))
                logs.write(f"Iter {it}: obj={obj} cols={cols} red_cost={entry['reduced_cost']}")

            controller.add_iteration_callback(cb)

            res = controller.run(verbose=False)
            status_area.write(res)
    
    return {
        "max_iter": max_iter,
        "epsilon": epsilon,
        "solver": solver
    }
