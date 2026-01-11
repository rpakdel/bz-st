import streamlit as st

def render_filters(df, config):
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
    val_range = None
    if config['color_by']:
        min_val, max_val = float(df[config['color_by']].min()), float(df[config['color_by']].max())
        val_range = st.sidebar.slider(f"{config['color_by']} Range", min_val, max_val, (min_val, max_val))
        
    # Apply filtering
    mask = (
        (df['z'] >= z_range[0]) & 
        (df['z'] <= z_range[1]) &
        (df['x'] >= x_range[0]) &
        (df['x'] <= x_range[1]) &
        (df['y'] >= y_range[0]) &
        (df['y'] <= y_range[1])
    )
    
    if val_range:
        mask &= (df[config['color_by']] >= val_range[0]) & (df[config['color_by']] <= val_range[1])
        
    filtered_df = df[mask]
    return filtered_df
