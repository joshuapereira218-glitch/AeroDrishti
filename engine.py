import math
import hashlib
import json
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# 1. PERSONA DEFINITIONS (8 Traveller Twins)
# -------------------------------------------------------------------
TWIN_PERSONAS = {
    "Student Homegoer": {"lead_days": 20, "max_price_weight": 0.8, "red_eye_ok": True, "baggage_req": False},
    "IT Commuter": {"lead_days": 7, "max_price_weight": 0.5, "red_eye_ok": False, "baggage_req": False},
    "Business Flyer": {"lead_days": 2, "max_price_weight": 0.2, "red_eye_ok": False, "baggage_req": False},
    "Festival Family": {"lead_days": 35, "max_price_weight": 0.6, "red_eye_ok": False, "baggage_req": True},
    "Last-minute Emergency": {"lead_days": 1, "max_price_weight": 0.1, "red_eye_ok": True, "baggage_req": False},
    "Senior / Pilgrim": {"lead_days": 20, "max_price_weight": 0.5, "red_eye_ok": False, "baggage_req": True},
    "Tier-2 First-timer": {"lead_days": 10, "max_price_weight": 0.7, "red_eye_ok": False, "baggage_req": False},
    "Weekend Leisure": {"lead_days": 10, "max_price_weight": 0.6, "red_eye_ok": True, "baggage_req": False},
}

ROUTES = ["DEL-BOM", "BLR-DEL", "BOM-CCU", "MAA-DEL", "HYD-BOM", "IXE-BLR"]
AIRLINES = ["IndiGo", "Air India", "Akasa Air", "SpiceJet"]

# -------------------------------------------------------------------
# 2. RAW VAULT & CHECKOUT-TRUTH FARE GENERATOR
# -------------------------------------------------------------------
def generate_quote_vault(num_records=120):
    """
    Simulates raw web search quotes collected by Playwright/Scrapy.
    Calculates Checkout-Truth pricing (Base + Taxes + UDF + Convenience Fees).
    """
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_records):
        timestamp = base_time + timedelta(hours=i * 6)
        route = random.choice(ROUTES)
        airline = random.choice(AIRLINES)
        base_fare = round(random.uniform(2500, 8500), 2)
        
        # Checkout-Truth Add-ons (UDF, Taxes, Convenience Fee)
        taxes = round(base_fare * 0.12, 2)
        udf = 450.0  # User Development Fee
        convenience_fee = 350.0  # Hidden OTA/Airline checkout fee
        all_in_fare = round(base_fare + taxes + udf + convenience_fee, 2)
        
        seats_left = random.randint(1, 15)
        raw_json = json.dumps({
            "route": route,
            "airline": airline,
            "base": base_fare,
            "all_in": all_in_fare,
            "ts": timestamp.isoformat()
        })
        quote_hash = hashlib.sha256(raw_json.encode()).hexdigest()[:12]
        
        data.append({
            "quote_id": f"QT-{quote_hash}",
            "timestamp": timestamp,
            "route": route,
            "airline": airline,
            "base_fare": base_fare,
            "all_in_fare": all_in_fare,  # Checkout-Truth Fare
            "seats_left": seats_left,
            "raw_hash": quote_hash
        })
        
    return pd.DataFrame(data)

# -------------------------------------------------------------------
# 3. TWIN EVALUATION & JEVONS INDEX COMPUTATION
# -------------------------------------------------------------------
def calculate_jevons_apix(df, atf_shock_pct=0.0):
    """
    Calculates the APIx using Jevons Geometric Mean formula across Twins and Routes.
    Applies optional Macro ATF Fuel shock (+/- %).
    """
    df = df.copy()
    # Apply ATF fuel shock impact on all-in fares
    df["adjusted_fare"] = df["all_in_fare"] * (1.0 + (atf_shock_pct * 0.35 / 100.0))
    
    # Calculate geometric mean per route (Jevons Price-Relative)
    route_indices = {}
    for route, group in df.groupby("route"):
        fares = group["adjusted_fare"].values
        # Geometric Mean: exp(mean(log(fares)))
        geom_mean = math.exp(np.mean(np.log(fares)))
        route_indices[route] = round(geom_mean, 2)
        
    # Overall Aggregate APIx Index
    overall_index = math.exp(np.mean(np.log(df["adjusted_fare"].values)))
    
    return round(overall_index, 2), route_indices

# -------------------------------------------------------------------
# 4. STL SURGE DECOMPOSITION (Trend vs. Surge)
# -------------------------------------------------------------------
def decompose_apix_trend(df):
    """
    Splits total index into Core APIx (Trend) vs Surge Meter (Festival/Demand Spike).
    """
    df_sorted = df.sort_values("timestamp")
    timeseries = df_sorted.set_index("timestamp")["all_in_fare"].resample("D").mean().ffill()
    
    # Simple Moving Average representation of STL decomposition
    core_apix = timeseries.rolling(window=5, min_periods=1).mean()
    surge_meter = timeseries - core_apix
    
    result_df = pd.DataFrame({
        "Total_Fare": timeseries,
        "Core_APIx": core_apix.round(2),
        "Surge_Component": surge_meter.round(2)
    }).reset_index()
    
    return result_df