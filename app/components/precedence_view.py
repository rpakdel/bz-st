import streamlit as st
import networkx as nx
from .precedence_2d import render_precedence_2d
from .precedence_3d import render_precedence_3d

def render_precedence_view(df, pm, selected_dataset, filtered_df):
    st.write("#### Precedence Graph Visualization")
    
    if pm is None:
        st.warning("No precedence data available for this dataset.")
        return

    # Filter to a subset of blocks for visualization to avoid browser crash
    st.info("Visualizing precedence for a single block and its immediate dependencies.")
    
    target_block = st.number_input("Enter Block ID to inspect dependencies", 
                                   min_value=int(df['id'].min()), 
                                   max_value=int(df['id'].max()), 
                                   value=int(df['id'].min()))
    
    # Selection for focus mode
    focus_mode = st.radio("Focus Mode", ["Single Block Dependency", "Spatial Region (All edges in filter)"])
    
    # Selection for depth
    dependency_depth = "Ancestors Only"
    if focus_mode == "Single Block Dependency":
        dependency_depth = st.radio("Dependency Depth", ["Ancestors Only", "Ancestors + Descendants"])
    
    view_mode = st.radio("View Mode", ["2D Hierarchical", "3D Spatial"])
    
    # Get full graph
    G = pm.to_networkx()
    
    if focus_mode == "Single Block Dependency":
        if target_block not in G:
            st.error(f"Block {target_block} not found in precedence graph.")
            return

        # Show dependency summary
        direct_preds = list(G.predecessors(target_block))
        direct_succs = list(G.successors(target_block))
        st.write(f"**Block {target_block} Summary:**")
        st.write(f"- Direct Predecessors: {len(direct_preds)}")
        st.write(f"- Direct Successors: {len(direct_succs)}")
            
        # Get ancestors (must mine before) and descendants (can mine after)
        preds = list(nx.ancestors(G, target_block))
        
        if dependency_depth == "Ancestors + Descendants":
            succs = list(nx.descendants(G, target_block))
            nodes_to_show = preds + succs + [target_block]
            title_suffix = f"for Block {target_block} (Ancestors + Descendants)"
        else:
            nodes_to_show = preds + [target_block]
            title_suffix = f"for Block {target_block} (Ancestors only)"
        
        # Limit nodes to avoid performance issues if too many
        if len(nodes_to_show) > 500:
            st.warning(f"Too many dependencies ({len(nodes_to_show)}). Showing 500 nearest nodes.")
            # For now just slice, but ideally would be breadth-first search reachability limit
            nodes_to_show = nodes_to_show[:500]
            
        sub_G = G.subgraph(nodes_to_show)
    else:
        # Spatial Region mode - use blocks from the filtered_df
        nodes_to_show = filtered_df['id'].tolist()
        
        # Limit nodes to avoid performance issues
        if len(nodes_to_show) > 500:
            st.warning(f"Region contains too many blocks ({len(nodes_to_show)}). Only showing first 500.")
            nodes_to_show = nodes_to_show[:500]
            
        sub_G = G.subgraph(nodes_to_show)
        title_suffix = "in selected region"
        
    if view_mode == "2D Hierarchical":
        render_precedence_2d(sub_G, df, target_block)
    else:  # 3D Spatial
        render_precedence_3d(sub_G, df, target_block, title_suffix)
