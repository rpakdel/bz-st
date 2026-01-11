import pytest
import os
from parsers.block_model import parse_blocks_file
from parsers.precedence import parse_precedence_file
from parsers.optimization import parse_optimization_file

def test_parse_zuck_small_blocks():
    # Use absolute path for reliability
    base_path = "/workspaces/bz-st/data/minelib/zuck_small/zuck_small.blocks"
    
    # Column names according to zuck_small/readme.md
    attr_names = ["cost", "value", "rock_tonnes", "ore_tonnes"]
    
    bm = parse_blocks_file(base_path, attribute_names=attr_names)
    
    assert bm.name == "zuck_small"
    assert len(bm.blocks) == 9400
    
    # Verify the first block
    # 0 13 17 10 64395.01407 95076.276 71550.01563 71550
    first_block = bm.blocks[0]
    assert first_block.id == 0
    assert first_block.x == 13
    assert first_block.y == 17
    assert first_block.z == 10
    assert first_block.attributes[0] == pytest.approx(64395.01407)
    assert first_block.attributes[1] == pytest.approx(95076.276)
    assert first_block.attributes[2] == pytest.approx(71550.01563)
    assert first_block.attributes[3] == pytest.approx(71550)
    
    # Test dataframe conversion
    df = bm.to_dataframe()
    assert df.shape == (9400, 8)
    assert list(df.columns) == ["id", "x", "y", "z", "cost", "value", "rock_tonnes", "ore_tonnes"]
    assert df.iloc[0]["id"] == 0
    assert df.iloc[1]["id"] == 1

def test_parse_zuck_small_prec():
    base_path = "/workspaces/bz-st/data/minelib/zuck_small/zuck_small.prec"
    
    pm = parse_precedence_file(base_path)
    
    assert pm.name == "zuck_small"
    assert len(pm.precedences) == 9400
    
    # 0 13 86 79 87 97 88 204 228 196 242 360 462 374 443
    assert 0 in pm.precedences
    preds = pm.precedences[0]
    assert len(preds) == 13
    assert set(preds) == {86, 79, 87, 97, 88, 204, 228, 196, 242, 360, 462, 374, 443}
    
    # Test networkx conversion
    G = pm.to_networkx()
    assert G.number_of_nodes() == 9400
    # Check one edge: 86 -> 0 (since 86 is a predecessor of 0)
    assert G.has_edge(86, 0)
    assert not G.has_edge(0, 86)

def test_parse_zuck_small_cpit():
    base_path = "/workspaces/bz-st/data/minelib/zuck_small/zuck_small.cpit"
    
    model = parse_optimization_file(base_path)
    
    assert model.name == "Zuck_small"
    assert model.type == "CPIT"
    assert model.n_blocks == 9400
    assert model.n_periods == 20
    assert model.discount_rate == 0.1
    
    # Check resource limits
    # 0 0 L 60000000
    assert len(model.resource_limits) > 0
    limit0 = model.resource_limits[0]
    assert limit0.resource == 0
    assert limit0.period == 0
    assert limit0.type == "L"
    assert limit0.v1 == 60000000
    
    # Check objective
    # 0 30681.26193
    assert 0 in model.objective
    assert model.objective[0][0] == pytest.approx(30681.26193)

def test_parse_kd_blocks():
    base_path = "/workspaces/bz-st/data/minelib/kd/kd.blocks"
    attr_names = ["tonn", "blockvalue", "destination", "CU_pct", "process_profit"]
    
    bm = parse_blocks_file(base_path, attribute_names=attr_names)
    
    assert bm.name == "kd"
    assert len(bm.blocks) == 14153
    
    # 0 11 0 18 16380 -12285 2 0 0
    first_block = bm.blocks[0]
    assert first_block.id == 0
    assert first_block.attributes[0] == 16380
    assert first_block.attributes[1] == -12285
    
    df = bm.to_dataframe()
    assert df.shape == (14153, 9)

def test_parse_kd_prec():
    base_path = "/workspaces/bz-st/data/minelib/kd/kd.prec"
    pm = parse_precedence_file(base_path)
    assert len(pm.precedences) == 14153
    
    # 18 1 0
    assert 18 in pm.precedences
    assert pm.precedences[18] == [0]
    
    import networkx as nx
    G = pm.to_networkx()
    assert G.has_edge(0, 18)
    
    ancestors = nx.ancestors(G, 18)
    assert 0 in ancestors
    assert ancestors == {0}

def test_parse_kd_upit():
    base_path = "/workspaces/bz-st/data/minelib/kd/kd.upit"
    model = parse_optimization_file(base_path)
    assert model.name == "KD"
    assert model.type == "UPIT"
    assert model.n_blocks == 14153
    # 0 -12285
    assert model.objective[0][0] == -12285
