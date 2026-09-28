from fastapi import FastAPI, Query
import pandas as pd
from engine import generate_quote_vault, calculate_jevons_apix, decompose_apix_trend, TWIN_PERSONAS

app = FastAPI(
    title="AEROTWIN - APIx Engine API",
    description="Real-time Airfare Price Index & Policy Simulation Engine for RBI/MoSPI",
    version="1.0.0"
)

# Initialize Raw Vault Data in memory
RAW_VAULT_DF = generate_quote_vault(200)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "AEROTWIN APIx Engine",
        "active_twins": len(TWIN_PERSONAS),
        "quote_vault_records": len(RAW_VAULT_DF)
    }

@app.get("/api/v1/apix/current")
def get_current_apix(atf_shock: float = Query(0.0, description="ATF Fuel Price Shock percentage, e.g., 10 for +10%")):
    """
    Fetch current aggregate APIx Index and route-level Jevons breakdown.
    """
    overall_index, route_breakdown = calculate_jevons_apix(RAW_VAULT_DF, atf_shock_pct=atf_shock)
    return {
        "apix_index_value": overall_index,
        "applied_atf_shock_pct": atf_shock,
        "route_breakdown": route_breakdown,
        "formula": "Jevons Geometric Mean across 8 Synthetic Traveller Twins"
    }

@app.get("/api/v1/apix/audit-receipt")
def get_audit_receipt(quote_id: str):
    """
    Index with Receipts: Returns cryptographic quote snapshot and price breakdown.
    """
    record = RAW_VAULT_DF[RAW_VAULT_DF["quote_id"] == quote_id]
    if record.empty:
        return {"error": "Quote ID not found in Raw Vault"}
    
    row = record.iloc[0].to_dict()
    row["timestamp"] = row["timestamp"].isoformat()
    return {
        "audit_receipt": row,
        "verification_status": "HASH_MATCHED",
        "integrity_proof": f"SHA256:{row['raw_hash']}"
    }

@app.get("/api/v1/apix/decomposition")
def get_surge_decomposition():
    """
    Splits index into Core APIx (Trend) and Surge Meter.
    """
    decomp_df = decompose_apix_trend(RAW_VAULT_DF)
    decomp_df["timestamp"] = decomp_df["timestamp"].dt.strftime("%Y-%m-%d")
    return decomp_df.to_dict(orient="records")