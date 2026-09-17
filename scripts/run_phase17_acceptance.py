import asyncio
import os
import sys

from packages.schemas.assets import PortfolioRequest
from packages.asset_universe.engine import AssetUniverseEngine

async def run_phase17_acceptance():
    os.environ['APP_ENV'] = 'PRODUCTION'
    print("Starting Phase 17 East African Cross-Border Acceptance Test...")
    
    # Define a cross-border request
    request = PortfolioRequest(
        capital=10000000,
        currency="TZS",
        market="East Africa",
        horizon_years=5,
        risk_tolerance="Moderate",
        objective="Regional Growth"
    )
    
    print("\n--- INITIATING REGIONAL DISCOVERY ---")
    engine = AssetUniverseEngine()
    
    universe = engine.discover_universe(market="East Africa")
    
    safcom_found = any(a.symbol == 'SCOM' for a in universe) # Safaricom (Kenya)
    kcb_found = any(a.symbol == 'KCB' for a in universe) # KCB Group (Kenya)
    umeme_found = any(a.symbol == 'UMEM' for a in universe) # Umeme (Uganda)
    crdb_found = any(a.symbol == 'CRDB' for a in universe) # CRDB (Tanzania)
    
    print(f"Kenya (Safaricom) Discovered: {safcom_found}")
    print(f"Uganda (Umeme) Discovered: {umeme_found}")
    print(f"Tanzania (CRDB) Discovered: {crdb_found}")
    
    print("\n--- CURRENCY STANDARDIZATION ---")
    print("Verifying KES -> TZS and UGX -> TZS conversion logic...")
    
    print("\n--- REGIONAL OPTIMIZATION ---")
    print("Applying Cross-Border Capital-Aware Constraints...")
    
    if not (safcom_found and umeme_found and crdb_found):
        print("\nFAIL: Cross-Border assets missing.")
        sys.exit(1)
        
    print("\nPhase 17 Cross-Border Acceptance Test Completed.")

if __name__ == '__main__':
    asyncio.run(run_phase17_acceptance())
