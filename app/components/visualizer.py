import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def render_3d_view(df, filtered_df, config, selected_dataset):
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

    if not plot_df.empty:
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
    else:
        st.warning("No blocks match current filters.")

def render_upit_analysis(om):
    if not om or not om.objective:
        st.warning("No UPIT objective data available.")
        return
    
    # Extract objective values
    obj_values = [om.objective[i][0] for i in range(om.n_blocks) if i in om.objective]
    
    if not obj_values:
        st.warning("No objective values found.")
        return
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Blocks", len(obj_values))
    with col2:
        st.metric("Max Objective", f"${max(obj_values):,.0f}")
    with col3:
        st.metric("Min Objective", f"${min(obj_values):,.0f}")
    with col4:
        positive = sum(1 for v in obj_values if v > 0)
        st.metric("Profitable Blocks", f"{positive} ({positive/len(obj_values)*100:.1f}%)")
    
    # Histogram
    st.write("#### Objective Value Distribution")
    fig_hist = px.histogram(
        x=obj_values,
        nbins=50,
        title="Distribution of UPIT Objective Values",
        labels={'x': 'Objective Value ($)', 'y': 'Number of Blocks'}
    )
    fig_hist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
    st.plotly_chart(fig_hist, width='stretch')
    
    # Cumulative distribution
    st.write("#### Cumulative Objective Value")
    sorted_obj = sorted(obj_values, reverse=True)
    cumulative = np.cumsum(sorted_obj)
    
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=list(range(1, len(sorted_obj)+1)),
        y=cumulative,
        mode='lines',
        name='Cumulative Profit'
    ))
    fig_cum.update_layout(
        title="Cumulative Profit from Top Blocks",
        xaxis_title="Number of Blocks (sorted by profit)",
        yaxis_title="Cumulative Profit ($)"
    )
    st.plotly_chart(fig_cum, width='stretch')
