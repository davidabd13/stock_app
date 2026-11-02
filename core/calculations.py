"""
Logika bisnis murni (tanpa Streamlit/Supabase) supaya mudah dites.

Aturan:
  Total Keluar = Stok hari sebelumnya + Sell-in - Stok hari berikutnya   (minimal 0)
  SPD          = Total Keluar / hari berjalan (default 12)
  DSI          = Stok Akhir / SPD
"""
import numpy as np
import pandas as pd

from core.config import (DEFAULT_RULE, DSI_CAP, DSI_RULES, STATUS_HIJAU,
                         STATUS_KUNING, STATUS_MERAH)

KEY = ["id_outlet", "id_product"]


def _prep_stock(stock: pd.DataFrame) -> pd.DataFrame:
    df = stock.copy()
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    df["id_outlet"] = df["id_outlet"].astype(str)
    df["id_product"] = df["id_product"].astype(int)
    df["total_stock"] = pd.to_numeric(df["total_stock"], errors="coerce").fillna(0)
    return df.sort_values(KEY + ["date"]).reset_index(drop=True)


def assign_sellin(sellin: pd.DataFrame, stock: pd.DataFrame) -> pd.DataFrame:
    """Setiap sell-in dikaitkan ke snapshot stok PERTAMA pada/ setelah tanggal sell-in
    (per outlet+SKU). Kolom baru `snap_date`; NaT = belum ada stok pembanding (pending)."""
    s = sellin.copy()
    if s.empty:
        s["snap_date"] = pd.NaT
        return s
    s["date"] = pd.to_datetime(s["date"]).astype("datetime64[ns]")
    s["id_outlet"] = s["id_outlet"].astype(str)
    s["id_product"] = s["id_product"].astype(int)
    snaps = _prep_stock(stock)[KEY + ["date"]].drop_duplicates()
    right = snaps.rename(columns={"date": "snap_date"})
    right["date"] = right["snap_date"]
    out = pd.merge_asof(s.sort_values("date"), right.sort_values("date"),
                        on="date", by=KEY, direction="forward")
    return out


def build_flow(stock: pd.DataFrame, sellin: pd.DataFrame) -> pd.DataFrame:
    """Hitung pergerakan per snapshot (tanggal x outlet x SKU)."""
    df = _prep_stock(stock)
    grp = df.groupby(KEY)
    df["stok_awal"] = grp["total_stock"].shift()          # stok snapshot sebelumnya
    df["tgl_sebelumnya"] = grp["date"].shift()

    if sellin is None or sellin.empty:
        df["sell_in"] = 0
    else:
        a = assign_sellin(sellin, df).dropna(subset=["snap_date"])
        agg = (a.groupby(KEY + ["snap_date"], as_index=False)["qty"].sum()
                 .rename(columns={"qty": "sell_in", "snap_date": "date"}))
        df = df.merge(agg, on=KEY + ["date"], how="left")
    df["sell_in"] = df["sell_in"].fillna(0)

    has_prev = df["stok_awal"].notna()
    selisih = df["stok_awal"] + df["sell_in"] - df["total_stock"]
    df["total_keluar"] = selisih.clip(lower=0).where(has_prev, 0)
    # stok naik lebih dari sell-in tercatat -> kemungkinan sell-in belum diinput
    df["stok_naik_tanpa_sellin"] = (-selisih).clip(lower=0).where(has_prev, 0)
    return df


def aggregate_pairs(flow: pd.DataFrame, start, end) -> pd.DataFrame:
    """Ringkas per outlet x SKU untuk rentang tanggal [start, end]."""
    f = flow[(flow["date"] >= pd.Timestamp(start)) & (flow["date"] <= pd.Timestamp(end))]
    if f.empty:
        return pd.DataFrame()
    f = f.sort_values(KEY + ["date"])
    first = lambda s: s.iloc[0]  # noqa: E731  (groupby.first() melewati NaN, ini tidak)
    p = f.groupby(KEY).agg(
        account=("account", "last"), outlet=("outlet", "last"), product=("product", "last"),
        _awal=("stok_awal", first), _first_stock=("total_stock", first),
        stok_tambahan=("sell_in", "sum"), stok_akhir=("total_stock", "last"),
        total_keluar=("total_keluar", "sum"),
        stok_naik_tanpa_sellin=("stok_naik_tanpa_sellin", "sum"),
        update_terakhir=("date", "max"),
    ).reset_index()
    p["stok_awal"] = p["_awal"].fillna(p["_first_stock"])
    return p.drop(columns=["_awal", "_first_stock"])


def _status(account: pd.Series, dsi: pd.Series) -> pd.Series:
    rules = account.astype(str).str.strip().str.upper().map(lambda a: DSI_RULES.get(a, DEFAULT_RULE))
    hijau = rules.map(lambda r: r[0])
    merah = rules.map(lambda r: r[1])
    return pd.Series(np.select([dsi < hijau, dsi < merah], [STATUS_HIJAU, STATUS_KUNING],
                               default=STATUS_MERAH), index=dsi.index)


def compute_metrics(df: pd.DataFrame, hari: int) -> pd.DataFrame:
    """Tambahkan SPD, DSI, dan Status PO ke tabel yang punya stok_akhir & total_keluar."""
    d = df.copy()
    d["spd"] = d["total_keluar"] / hari
    dsi = (d["stok_akhir"] / d["spd"].where(d["spd"] > 0)).fillna(DSI_CAP)
    d["dsi"] = dsi.where(d["stok_akhir"] > 0, 0.0).clip(upper=DSI_CAP)   # stok 0 -> DSI 0
    d["status_po"] = _status(d["account"], d["dsi"]) if "account" in d.columns else ""
    return d


def rollup(pairs: pd.DataFrame, by: list[str], hari: int) -> pd.DataFrame:
    """Gabungkan hasil per outlet x SKU ke level lain (account / toko / produk) lalu hitung ulang SPD & DSI."""
    if pairs.empty:
        return pairs
    cols = ["stok_awal", "stok_tambahan", "stok_akhir", "total_keluar"]
    r = pairs.groupby(by, as_index=False)[cols].sum()
    return compute_metrics(r, hari)
