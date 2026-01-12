import streamlit as st
import os
import sys
from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'minelib')

def get_available_datasets():
    if not os.path.exists(DATA_DIR):
        return []
    return [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]

@st.cache_data
def load_dataset(dataset_name):
    path = os.path.join(DATA_DIR, dataset_name)
    
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
            },
        "marvin": {
            "blocks": "marvin.blocks",
            "attr_names": ["tonnage", "au_ppm", "cu_pct", "proc_profit_per_tonne"],
            "color_by": "proc_profit_per_tonne"
        },
        "newman": {
            "blocks": "newman1.blocks",
            "prec": "newman1.prec",
            "upit": "newman1.upit",
            "attr_names": ["tonn", "blockvalue", "destination", "blocktype", "process_profit"],
            "color_by": "blockvalue"
        }
    }
    
    cfg = config.get(dataset_name, {"blocks": f"{dataset_name}.blocks", "prec": f"{dataset_name}.prec", "attr_names": [], "color_by": None})
    blocks_path = os.path.join(path, cfg.get("blocks", ""))
    prec_path = os.path.join(path, cfg.get("prec", f"{dataset_name}.prec"))
    upit_path = os.path.join(path, cfg.get("upit", f"{dataset_name}.upit"))
    
    if not os.path.exists(blocks_path):
        return None, None, None, None
    
    bm = parse_blocks_file(blocks_path, attribute_names=cfg["attr_names"])
    pm = parse_precedence_file(prec_path) if os.path.exists(prec_path) else None
    om = parse_optimization_file(upit_path) if os.path.exists(upit_path) else None
    
    df = bm.to_dataframe()
    return df, pm, om, cfg
