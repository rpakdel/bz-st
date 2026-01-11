import streamlit as st
import plotly.graph_objects as go

def render_precedence_3d(sub_G, df, target_block, title_suffix):
    sub_df = df[df['id'].isin(sub_G.nodes())]
    
    node_trace = go.Scatter3d(
        x=sub_df['x'], y=sub_df['y'], z=sub_df['z'],
        mode='markers+text',
        marker=dict(
            size=6,
            color=['#ff4b4b' if i == target_block else '#31333F' for i in sub_df['id']],
            opacity=0.8
        ),
        text=[f"B{i}" for i in sub_df['id']],
        hoverinfo='text',
        name='Blocks'
    )

    edge_x, edge_y, edge_z = [], [], []
    for u, v in sub_G.edges():
        u_info = df[df['id'] == u].iloc[0]
        v_info = df[df['id'] == v].iloc[0]
        edge_x.extend([u_info['x'], v_info['x'], None])
        edge_y.extend([u_info['y'], v_info['y'], None])
        edge_z.extend([u_info['z'], v_info['z'], None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines',
        name='Precedence'
    )

    fig = go.Figure(data=[node_trace, edge_trace])
    fig.update_layout(
        title=f"3D Precedence Graph {title_suffix}",
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z (Level)', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    st.plotly_chart(fig, width='stretch')
