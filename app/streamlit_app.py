import streamlit as st
import os
import sys

# Add root directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.data_loader import get_available_datasets, load_dataset
from app.components.sidebar import render_dataset_selector, render_instance_summary
from app.components.filters import render_filters
from app.components.visualizer import render_3d_view, render_upit_analysis
from app.components.precedence_view import render_precedence_view
from app.components.solver_ui import render_solver_settings

# Page Configuration
st.set_page_config(page_title="MineLib BZ Solver", layout="wide")

st.title("⚒️ MineLib Block Model Visualizer")

# 1. Dataset Selection
available_datasets = get_available_datasets()
if not available_datasets:
    st.error("No datasets found in data/minelib/")
    st.stop()

selected_dataset = render_dataset_selector(available_datasets)

# 1.1 Dataset Change Reset logic
if "last_selected_dataset" not in st.session_state:
    st.session_state.last_selected_dataset = selected_dataset

if st.session_state.last_selected_dataset != selected_dataset:
    # Clear all solver-related session state
    keys_to_clear = [
        'solver_state', 
        'solver_proc', 
        'solver_start_time',
        'bz_controller'  # from older versions just in case
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            if key == 'solver_proc':
                try:
                    if st.session_state[key].poll() is None:
                        st.session_state[key].terminate()
                except:
                    pass
            del st.session_state[key]
    
    st.session_state.last_selected_dataset = selected_dataset
    st.rerun()

# 2. Data Loading
df, pm, om, config = load_dataset(selected_dataset)

if df is not None:
    # 3. Instance Summary in Sidebar
    render_instance_summary(df, om, config)

    # 4. Filter Settings in Sidebar
    filtered_df = render_filters(df, config)

    # Main Area Content
    st.write(f"### Dataset: {selected_dataset}")
    
    # Use tabs for different views
    tab_model, tab_prec, tab_bz = st.tabs(["🧊 Block Model", "🔗 Precedence Graph", "⚡ BZ Solver"])

    with tab_model:
        st.write(f"Showing {len(filtered_df)} blocks after filtering.")
        # 5. 3D Visualization
        render_3d_view(df, filtered_df, config, selected_dataset)

        # UPIT Objective Visualization
        if om:
            with st.expander("📊 UPIT Objective Analysis"):
                render_upit_analysis(om)

        # 6. Data Preview
        with st.expander("Preview Data"):
            st.dataframe(filtered_df.head(100))

    with tab_prec:
        render_precedence_view(df, pm, selected_dataset, filtered_df)

    with tab_bz:
        # 7. Solver Settings & Execution
        render_solver_settings(df=df, pm=pm, om=om, config=config)
else:
    st.error(f"Could not load data for {selected_dataset}.")
