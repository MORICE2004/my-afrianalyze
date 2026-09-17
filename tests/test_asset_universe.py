from packages.asset_universe.engine import AssetUniverseEngine

def test_asset_discovery():
    engine = AssetUniverseEngine()
    assets = engine.discover_assets()
    
    assert len(assets) > 0
    # check that we have CRDB
    crdb = next((a for a in assets if a.id == "dse_crdb"), None)
    assert crdb is not None
    assert crdb.asset_type.value == "SECURITY"
    assert crdb.sub_type.value == "EQUITY"
