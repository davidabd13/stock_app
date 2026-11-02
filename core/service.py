"""Gabungan loader + kalkulasi, di-cache agar tiap halaman cepat."""
import pandas as pd
import streamlit as st

from core.calculations import aggregate_pairs, build_flow, compute_metrics
from core.database import load_sellin, load_stock


@st.cache_data(ttl=120, show_spinner="Menghitung stok keluar, SPD & DSI...")
def load_flow() -> pd.DataFrame:
    stock = load_stock()
    if stock.empty:
        return pd.DataFrame()
    return build_flow(stock, load_sellin())


def select_data(flow: pd.DataFrame, f) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Terapkan filter, return (flow_terfilter, ringkasan_per_outlet_sku_dengan_metrik)."""
    d = flow[flow["account"].isin(f.accounts)]
    if f.outlets:
        d = d[d["outlet"].isin(f.outlets)]
    d = d[(d["date"] >= pd.Timestamp(f.start)) & (d["date"] <= pd.Timestamp(f.end))]
    pairs = aggregate_pairs(flow[flow["account"].isin(f.accounts)].pipe(
        lambda x: x[x["outlet"].isin(f.outlets)] if f.outlets else x), f.start, f.end)
    return d, (compute_metrics(pairs, f.hari) if not pairs.empty else pairs)
