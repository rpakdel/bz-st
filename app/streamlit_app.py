import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# Add root directory to path for parsers
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file

st.set_page_config(page_title="MineLib BZ Solver", layout="wide")

st.title("⚒️ MineLib Block Model Visualizer")

# Sidebar for dataset selection
st.sidebar.header("Dataset Selection")
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'minelib')
available_datasets = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
selected_dataset = st.sidebar.selectbox("Choose a dataset", available_datasets)

@st.cache_data
def load_data(dataset_name):
    path = os.path.join(data_dir, dataset_name)
    
    # Configuration for different datasets
    config = {
        "zuck_small": {
            "blocks": "zuck_small.blocks",
            "attr_names": ["cost", "value", "rock_tonnes", "ore_tonnes"],
            "color_by": "value"
        },
        "kd": {
            "blocks": "kd.blocks",
            "attr_names": ["tonn", "blockvalue", "destination", "CU_pct", "process_profit"],
            "color_by": "blockvalue"
        }
    }
    
    cfg = config.get(dataset_name, {"blocks": f"{dataset_name}.blocks", "attr_names": [], "color_by": None})
    blocks_path = os.path.join(path, cfg["blocks"])
    
    if not os.path.exists(blocks_path):
        st.error(f"Blocks file not found: {blocks_path}")
        return None, None
    
    bm = parse_blocks_file(blocks_path, attribute_names=cfg["attr_names"])
    df = bm.to_dataframe()
    return df, cfg

df, config = load_data(selected_dataset)

if df is not None:
    st.write(f"### Dataset: {selected_dataset}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Blocks", len(df))
    col2.metric("Levels (Z)", df['z'].nunique())
    col3.metric("Max Profit", f"${df[config['color_by']].max():,.2f}" if config['color_by'] else "N/A")

    st.sidebar.markdown("---")
    st.sidebar.header("Filter Settings")
    
    # Filter by level
    min_z, max_z = int(df['z'].min()), int(df['z'].max())
    z_range = st.sidebar.slider("Levels (Z)", min_z, max_z, (min_z, max_z))

    # Filter by X
    min_x, max_x = int(df['x'].min()), int(df['x'].max())
    x_range = st.sidebar.slider("X Range", min_x, max_x, (min_x, max_x))

    # Filter by Y
    min_y, max_y = int(df['y'].min()), int(df['y'].max())
    y_range = st.sidebar.slider("Y Range", min_y, max_y, (min_y, max_y))
    
    # Filter by value
    if config['color_by']:
        min_val, max_val = float(df[config['color_by']].min()), float(df[config['color_by']].max())
        val_range = st.sidebar.slider(f"{config['color_by']} Range", min_val, max_val, (min_val, max_val))
        
        filtered_df = df[
            (df['z'] >= z_range[0]) & 
            (df['z'] <= z_range[1]) &
            (df['x'] >= x_range[0]) &
            (df['x'] <= x_range[1]) &
            (df['y'] >= y_range[0]) &
            (df['y'] <= y_range[1]) &
            (df[config['color_by']] >= val_range[0]) &
            (df[config['color_by']] <= val_range[1])
        ]
    else:
        filtered_df = df[
            (df['z'] >= z_range[0]) & 
            (df['z'] <= z_range[1]) &
            (df['x'] >= x_range[0]) &
            (df['x'] <= x_range[1]) &
            (df['y'] >= y_range[0]) &
            (df['y'] <= y_range[1])
        ]

    st.write(f"Showing {len(filtered_df)} blocks after filtering.")

    # 3D visualization
    st.write("#### 3D View")
    
    # Selective coloring based on user choice
    available_color_cols = [c for c in df.columns if c not in ['id', 'x', 'y', 'z']]
    default_color = config['color_by'] if config['color_by'] in available_color_cols else available_color_cols[0]
    color_selection = st.selectbox("Color blocks by", available_color_cols, index=available_color_cols.index(default_color) if default_color in available_color_cols else 0)

    # Optimization: Don't plot too many points for performance
    if len(filtered_df) > 5000:
        st.warning("Sampling points to maintain performance (showing 5000 blocks).")
        plot_df = filtered_df.sample(5000)
    else:
        plot_df = filtered_df

    fig = px.scatter_3d(
        plot_df, 
        x='x', y='y', z='z', 
        color=color_selection,
        color_continuous_scale='Viridis',
        opacity=0.6,
        labels={'z': 'Depth (Level)'},
        title=f"3D Block Model: {selected_dataset} (Colored by {color_selection})",
        hover_data=['id'] + (config['attr_names'] if config['attr_names'] else [])
    )
    
    fig.update_traces(marker=dict(size=3))
    fig.update_layout(scene=dict(aspectmode='data'))
    
    st.plotly_chart(fig, width='stretch')

    # Data preview
    with st.expander("Preview Data"):
        st.dataframe(filtered_df.head(100))

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
else:
    st.error("Could not load data.")
