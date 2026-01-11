import streamlit as st

def render_solver_settings():
    st.markdown("---")
    st.write("#### BZ Algorithm Settings")
    
    # Algorithm Parameters in columns for side-by-side view
    c1, c2, c3 = st.columns(3)
    max_iter = c1.number_input("Max Iterations", min_value=1, max_value=1000, value=100)
    epsilon = c2.number_input("Epsilon (Tolerance)", min_value=1e-9, max_value=1e-1, value=1e-6, format="%.1e")
    solver = c3.selectbox("L Master Solver", ["CBC (Native)", "CPLEX (Future)"])
    
    # Optimization Run
    if st.button("🚀 Run BZ Optimizer", use_container_width=True):
        st.info("BZ Optimizer implementation is pending. This will run the Bienstock–Zuckerberg algorithm on the selected instance.")
        st.status("Initializing RMP...", state="running")
        # TODO: Integrate BZ Controller here
    
    return {
        "max_iter": max_iter,
        "epsilon": epsilon,
        "solver": solver
    }
