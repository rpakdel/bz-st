import streamlit as st
from models.bz_controller import BZController
import networkx as nx
import pandas as pd
import io
import os
import sys
import json
import time
import uuid
import tempfile
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class SolverState:
    run_id: str
    status: str  # 'idle', 'running', 'stopped', 'completed', 'error'
    progress: int
    objective: float
    iterations: int
    error_msg: str = ""
    temp_dir: str = ""
    max_iter: int = 100


def validate_inputs(df, pm, om):
    if df is None or df.empty:
        st.error("Block data not loaded.")
        return False
    if pm is None:
        st.error("Precedence model not loaded.")
        return False
    if om is None:
        st.error("Optimization model not loaded.")
        return False
    return True


def start_solver(state, df, pm, om, max_iter, epsilon):
    state.run_id = str(uuid.uuid4())
    state.status = 'running'
    state.progress = 0
    state.objective = 0.0
    state.iterations = 0
    state.error_msg = ""
    state.max_iter = max_iter
    state.temp_dir = tempfile.mkdtemp(prefix=f"bz_solver_{state.run_id}_")

    # Prepare data for subprocess
    status_file = Path(state.temp_dir) / "status.json"
    result_file = Path(state.temp_dir) / "result.json"

    # Serialize inputs
    input_data = {
        'n_blocks': len(df),
        'orig_ids': list(df['id'].astype(int)),
        'edges': list(pm.to_networkx().edges()),
        'profits': [float(om.objective.get(orig_id, [0.0])[0]) if orig_id in om.objective else 0.0 for orig_id in df['id'].astype(int)],
        'eps': epsilon,
        'max_iters': max_iter,
        'algorithm': st.session_state.get('solver_algorithm', 'min_cut'),
        'status_file': str(status_file),
        'result_file': str(result_file)
    }

    input_file = Path(state.temp_dir) / "input.json"
    with open(input_file, 'w') as f:
        json.dump(input_data, f)

    # Start subprocess
    script_path = Path(__file__).parent / "solver_worker.py"
    
    # Ensure project root is in PYTHONPATH
    env = os.environ.copy()
    project_root = str(Path(__file__).parents[2])
    env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"
    
    proc = subprocess.Popen(
        [sys.executable, str(script_path), str(input_file)],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Store process in session state
    st.session_state['solver_proc'] = proc
    st.session_state['solver_start_time'] = time.time()


def stop_solver(state):
    if 'solver_proc' in st.session_state and st.session_state['solver_proc'].poll() is None:
        st.session_state['solver_proc'].terminate()
    state.status = 'stopped'


def poll_solver_status(state):
    if state.status != 'running':
        return

    proc = st.session_state.get('solver_proc')
    if proc is None:
        state.status = 'error'
        state.error_msg = "Solver process lost"
        return

    if proc.poll() is not None:
        # Process finished
        result_file = Path(state.temp_dir) / "result.json"
        if result_file.exists():
            try:
                with open(result_file, 'r') as f:
                    res = json.load(f)
                state.status = res.get('status', 'error')
                state.objective = res.get('objective', 0.0)
                state.iterations = res.get('iterations', 0)
                if state.status == 'error':
                    state.error_msg = res.get('message', 'Unknown error')
            except Exception as e:
                state.status = 'error'
                state.error_msg = f"Failed to read result: {e}"
        else:
            # Check stderr for errors
            _, stderr = proc.communicate()
            state.status = 'error'
            state.error_msg = f"Solver crashed:\n{stderr}"
    else:
        # Still running, check status file
        status_file = Path(state.temp_dir) / "status.json"
        if status_file.exists():
            try:
                # Use a small delay/retry to avoid reading while writing
                with open(status_file, 'r') as f:
                    st_data = json.load(f)
                state.progress = min(100, int(100 * (st_data.get('iter', 0) + 1) / state.max_iter))
                state.objective = st_data.get('objective', 0.0)
                state.iterations = st_data.get('iter', 0)
            except Exception:
                pass


def render_progress(state):
    if state.status == 'running':
        st.progress(state.progress)
        st.write(f"Running... Iteration {state.iterations}, Objective: {state.objective:.2f}")
    elif state.status in ['completed', 'converged', 'max_iters', 'max_columns_reached']:
        st.success(f"Finished! Status: {state.status}, Objective: {state.objective:.2f}, Iterations: {state.iterations}")
    elif state.status == 'error':
        st.error(f"Error: {state.error_msg}")
    elif state.status == 'stopped':
        st.warning("Solver stopped.")


def render_results(state, df):
    if state.status not in ['completed', 'converged', 'max_iters', 'max_columns_reached']:
        return

    result_file = Path(state.temp_dir) / "result.json"
    if not result_file.exists():
        return

    try:
        with open(result_file, 'r') as f:
            res = json.load(f)

        # Assume result includes history and solution
        history = res.get('history', [])
        if history:
            hist_df = pd.DataFrame(history)
            st.write("### Iteration History")
            st.dataframe(hist_df)

        solution = res.get('solution', {})
        if solution:
            # Similar to original
            vars_map = solution.get('variables', {})
            # Need to map back, but for simplicity, assume included
            patterns_df = pd.DataFrame(solution.get('patterns', []))
            st.write("### Columns (Patterns)")
            st.dataframe(patterns_df)

            csv_buf = io.StringIO()
            patterns_df.to_csv(csv_buf, index=False)
            st.download_button("Download Columns CSV", data=csv_buf.getvalue(), file_name="bz_columns.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Failed to load results: {e}")


def render_solver_settings(df=None, pm=None, om=None, config=None):
    st.markdown("---")
    st.write("#### BZ Algorithm Settings")

    # Algorithm Parameters
    c1, c2, c3, c4 = st.columns(4)
    max_iter = c1.number_input("Max Iterations", min_value=1, max_value=1000, value=100)
    epsilon = c2.number_input("Epsilon (Tolerance)", min_value=1e-9, max_value=1e-1, value=1e-6, format="%.1e")
    solver = c3.selectbox("LP Master Solver", ["CBC (Native)", "CPLEX (Future)"])
    algorithm = c4.selectbox(
        "Closure Algorithm",
        options=["min_cut", "edmonds_karp"],
        index=0,
        help=(
            "min_cut: fastest option; good enough for most datasets but may under-estimate LP on complex cases. "
            "edmonds_karp: slower (often 10-15x) but yields a tighter LP bound; use when accuracy matters more than speed."
        )
    )

    st.caption(
        "min_cut → speed-first. edmonds_karp → accuracy-first (expect longer runtime, especially on large instances)."
    )

    st.write("Use the controls below to run the BZ column-generation solver on the loaded dataset.")

    # Initialize state
    if 'solver_state' not in st.session_state:
        st.session_state.solver_state = SolverState(run_id="", status='idle', progress=0, objective=0.0, iterations=0)

    state = st.session_state.solver_state

    # Poll status on every render if running
    if state.status == 'running':
        poll_solver_status(state)

    # Run/Stop buttons
    col1, col2 = st.columns(2)
    run_clicked = col1.button("🚀 Run BZ Optimizer", disabled=state.status == 'running')
    stop_clicked = col2.button("⏹️ Stop Solver", disabled=state.status != 'running')

    if run_clicked:
        if validate_inputs(df, pm, om):
            st.session_state['solver_algorithm'] = algorithm
            start_solver(state, df, pm, om, max_iter, epsilon)
            st.rerun()

    if stop_clicked:
        stop_solver(state)
        st.rerun()

    # Render progress and results
    render_progress(state)
    render_results(state, df)

    # If running, show a spinner and auto-refresh
    if state.status == 'running':
        st.info("Solver is running. UI will refresh automatically.")
        time.sleep(1)
        st.rerun()

    return {
        "max_iter": max_iter,
        "epsilon": epsilon,
            "solver": solver,
            "algorithm": algorithm
    }
