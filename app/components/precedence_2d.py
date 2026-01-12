import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import json

def render_precedence_2d(sub_G, df, target_block):
    net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
    
    # We need a JSON string for options in PyVis
    options = {
        "layout": {
            "hierarchical": {
                "enabled": True,
                "direction": "UD",
                "sortMethod": "directed",
                "levelSeparation": 150,
                "nodeSpacing": 100
            }
        },
        "physics": {"enabled": False},
        "nodes": {"font": {"size": 12}},
        "edges": {"color": {"inherit": True}, "smooth": False}
    }
    net.set_options(json.dumps(options))

    max_z = df['z'].max()
    for node in sub_G.nodes():
        color = "#ff4b4b" if node == target_block else "#31333F"
        block_info = df[df['id'] == node].iloc[0]
        label = f"Block {node}"
        title = f"ID: {node}<br>Z: {block_info['z']}<br>X: {block_info['x']}<br>Y: {block_info['y']}"
        level = int(max_z - block_info['z'])
        net.add_node(node, label=label, title=title, color=color, level=level)
        
    for u, v in sub_G.edges():
        net.add_edge(u, v)
        
    # Render directly from generated HTML to avoid writing to disk
    html = net.generate_html()
    components.html(html, height=600)
