import streamlit as st
import plotly.express as px

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
