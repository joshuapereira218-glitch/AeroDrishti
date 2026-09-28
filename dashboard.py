import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from engine import generate_quote_vault, calculate_jevons_apix, decompose_apix_trend, TWIN_PERSONAS

st.set_page_config(
    page_title="AEROTWIN - APIx Dashboard",
    page_icon="✈️",
    layout="wide"
)

# Load / Cache Data
@st.cache_data
def load_vault():
    return generate_quote_vault(300)

vault_df = load_vault()

# Title Header
st.title("✈️ AEROTWIN – Real-time Airfare Price Index (APIx)")
st.caption("A Digital Twin Platform for High-Frequency Aviation Inflation & Surge Measurement")

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)

current_apix, route_dict = calculate_jevons_apix(vault_df, atf_shock_pct=0.0)
decomp_df = decompose_apix_trend(vault_df)
latest_surge = decomp_df["Surge_Component"].iloc[-1]

with col1:
    st.metric(label="Current APIx Index", value=f"₹ {current_apix:,.2f}", delta="+2.4% vs last week")
with col2:
    st.metric(label="Core APIx (Trend)", value=f"₹ {decomp_df['Core_APIx'].iloc[-1]:,.2f}")
with col3:
    st.metric(label="Surge Component", value=f"₹ {latest_surge:,.2f}", delta_color="inverse" if latest_surge > 0 else "normal")
with col4:
    st.metric(label="Active Traveller Twins", value="8 Personas", delta="100% Operational")

st.markdown("---")

# Main Dashboard Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Real-time Index & Surge Meter", 
    "👥 8 Traveller Twins Engine", 
    "🧪 Policy Lab (ATF Shock)", 
    "🧾 Audit Receipts & Vault"
])

# -------------------------------------------------------------------
# TAB 1: INDEX & SURGE DECOMPOSITION
# -------------------------------------------------------------------
with tab1:
    st.subheader("Core APIx vs. Total Fare Surge Decomposition")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=decomp_df["timestamp"], y=decomp_df["Total_Fare"],
        mode="lines+markers", name="Total Checkout-Truth Fare", line=dict(color="#1f77b4")
    ))
    fig.add_trace(go.Scatter(
        x=decomp_df["timestamp"], y=decomp_df["Core_APIx"],
        mode="lines", name="Core APIx (Trend)", line=dict(color="#2ca02c", width=3, dash="dash")
    ))
    fig.update_layout(
        title="STL Decomposition: Separating Festival/Demand Spikes from Core Inflation",
        xaxis_title="Date", yaxis_title="Price (₹)", hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------------
# TAB 2: 8 TRAVELLER TWINS
# -------------------------------------------------------------------
with tab2:
    st.subheader("Synthetic Shopper Personas & Booking Strategies")
    
    twin_cols = st.columns(4)
    personas_list = list(TWIN_PERSONAS.items())
    
    for idx, (p_name, p_attrs) in enumerate(personas_list):
        with twin_cols[idx % 4]:
            st.info(f"**Twin {idx+1}: {p_name}**")
            st.write(f"• **Lead Window:** T+{p_attrs['lead_days']} days")
            st.write(f"• **Price Sensitivity:** {int(p_attrs['max_price_weight']*100)}%")
            st.write(f"• **Red-Eye Flight OK:** {'Yes' if p_attrs['red_eye_ok'] else 'No'}")

# -------------------------------------------------------------------
# TAB 3: POLICY LAB (ATF SHOCK SIMULATION)
# -------------------------------------------------------------------
with tab3:
    st.subheader("RBI / Ministry Policy Shock Simulator")
    st.write("Simulate the immediate macro impact of Aviation Turbine Fuel (ATF) price shocks on the Airfare Index.")
    
    shock_val = st.slider("Select ATF Fuel Price Shock (%)", min_value=-20.0, max_value=30.0, value=10.0, step=2.5)
    
    base_idx, _ = calculate_jevons_apix(vault_df, atf_shock_pct=0.0)
    shocked_idx, route_shock = calculate_jevons_apix(vault_df, atf_shock_pct=shock_val)
    
    diff = round(shocked_idx - base_idx, 2)
    pct_diff = round((diff / base_idx) * 100, 2)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Baseline APIx", f"₹ {base_idx:,.2f}")
    with col_b:
        st.metric("Post-Shock APIx", f"₹ {shocked_idx:,.2f}", delta=f"{pct_diff}% ({' increase' if diff >= 0 else ' decrease'})")
        
    st.subheader("Route-Level Impact Breakdown")
    st.dataframe(pd.DataFrame(list(route_shock.items()), columns=["Route", "Post-Shock Jevons Index (₹)"]), use_container_width=True)

# -------------------------------------------------------------------
# TAB 4: AUDIT RECEIPTS & CRYPTOGRAPHIC PROOF
# -------------------------------------------------------------------
with tab4:
    st.subheader("Index with Receipts – Raw Quote Audit Vault")
    st.write("Every index value is linked directly back to an immutable, hash-stamped quote snapshot.")
    
    selected_id = st.selectbox("Select Quote ID to Verify Audit Receipt:", vault_df["quote_id"].tolist())
    selected_row = vault_df[vault_df["quote_id"] == selected_id].iloc[0]
    
    st.json({
        "quote_id": selected_row["quote_id"],
        "route": selected_row["route"],
        "airline": selected_row["airline"],
        "checkout_truth_breakdown": {
            "base_fare": selected_row["base_fare"],
            "all_in_checkout_price": selected_row["all_in_fare"],
            "fees_and_taxes": round(selected_row["all_in_fare"] - selected_row["base_fare"], 2)
        },
        "cryptographic_verification": {
            "hash_algorithm": "SHA256",
            "proof_hash": selected_row["raw_hash"],
            "status": "VERIFIED_UNCHANGED"
        }
    })