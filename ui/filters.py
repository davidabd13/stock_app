"""Filter global: periode (default MTD), account, toko, hari SPD."""
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from core.config import HARI_BERJALAN_DEFAULT


@dataclass
class Filters:
    start: pd.Timestamp
    end: pd.Timestamp
    accounts: list
    outlets: list     # kosong = semua toko
    hari: int


def mtd_range(flow: pd.DataFrame):
    hi = flow["date"].max()
    lo = max(flow["date"].min(), hi.replace(day=1))
    return lo.date(), hi.date()


def global_filters(flow: pd.DataFrame, key: str, container=None) -> Filters:
    """container=None -> satu baris kolom; container diberikan -> disusun vertikal (panel kiri)."""
    lo_all, hi_all = flow["date"].min().date(), flow["date"].max().date()
    lo, hi = mtd_range(flow)
    accounts_all = sorted(flow["account"].dropna().unique())

    if container is None:
        c = st.columns([2, 2, 3, 1])
        w_rng, w_acc, w_out, w_hari = c
    else:
        w_rng = w_acc = w_out = w_hari = container

    rng = w_rng.date_input("Periode (default MTD)", value=(lo, hi), min_value=lo_all, max_value=hi_all, key=f"{key}_rng")
    if not isinstance(rng, (list, tuple)) or len(rng) != 2:
        st.info("Pilih tanggal awal dan akhir.")
        st.stop()
    acc_sel = w_acc.selectbox("Pilih Account", ["Semua Account"] + accounts_all, key=f"{key}_acc")
    accounts = accounts_all if acc_sel == "Semua Account" else [acc_sel]
    opts = sorted(flow[flow["account"].isin(accounts)]["outlet"].dropna().unique())
    out_sel = w_out.selectbox("Pilih Toko", ["Semua Toko"] + opts, key=f"{key}_out")
    outlets = [] if out_sel == "Semua Toko" else [out_sel]
    hari = w_hari.number_input("Hari berjalan (pembagi SPD)", 1, 90, HARI_BERJALAN_DEFAULT, key=f"{key}_hari",
                               help="SPD = Total Keluar / Jumlah Hari Berjalan. Default 12.")
    return Filters(pd.Timestamp(rng[0]), pd.Timestamp(rng[1]), accounts, outlets, int(hari))
