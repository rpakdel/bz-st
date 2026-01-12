import streamlit as st

def render_dataset_selector(available_datasets):
    st.sidebar.header("Dataset Selection")
    return st.sidebar.selectbox("Choose a dataset", available_datasets)

def render_instance_summary(df, om, config):
    if df is None:
        return
        
    with st.sidebar:
        st.markdown("#### Instance Summary")
        
        # Max profit calculation
        max_p = "N/A"
        if config['color_by'] and config['color_by'] in df.columns:
            max_p = f"${df[config['color_by']].max():,.2f}"

        # UPIT info
        upit_info = ""
        if om:
            obj_values = [om.objective[i][0] for i in range(om.n_blocks) if i in om.objective]
            if obj_values:
                upit_info = f"<b>UPIT Obj Range:</b> ${min(obj_values):,.0f} to ${max(obj_values):,.0f}<br>"

        st.markdown(f"""
        <div style="font-size: 0.85em; color: #888;">
            <b>Total Blocks:</b> {len(df)}<br>
            <b>Max Profit:</b> {max_p}<br>
            {upit_info}
        </div>
        """, unsafe_allow_html=True)
