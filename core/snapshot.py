"""Membuat 1 baris snapshot stok (format raw_oos 22 kolom) dari input manual 'Stok Akhir'."""
from datetime import timedelta

import pandas as pd

from core.config import REQUIRED_COLUMNS

_MON = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES"]


def week_label(d) -> str:
    d = pd.Timestamp(d)
    mon = d - timedelta(days=d.weekday())
    sun = mon + timedelta(days=6)
    return f"{d.isocalendar().week}. {mon:%d} {_MON[mon.month - 1]} - {sun:%d} {_MON[sun.month - 1]} {sun.year}"


def build_snapshot(stock: pd.DataFrame, outlet_row: pd.Series, id_product: int, product: str, tgl, akhir: int) -> pd.DataFrame:
    wk = week_label(tgl)
    known = stock.drop_duplicates("week").set_index("week")["periode"] if not stock.empty else pd.Series(dtype=float)
    if wk in known.index:
        periode = int(known[wk])
    else:
        periode = int(pd.to_numeric(stock["periode"], errors="coerce").max() + 1) if not stock.empty else 1
    kosong = akhir <= 0
    rec = {
        "week": wk, "periode": periode, "date": pd.Timestamp(tgl).strftime("%Y-%m-%d"),
        "user": outlet_row.get("user"), "jabatan": outlet_row.get("jabatan"),
        "area": outlet_row.get("area"), "area_fix": outlet_row.get("area_fix"), "dc_mm": None,
        "channel": outlet_row.get("channel"), "account": outlet_row.get("account"),
        "id_outlet": outlet_row["id_outlet"], "outlet": outlet_row["outlet"],
        "ket_prioritas": outlet_row.get("ket_prioritas"), "id_product": int(id_product), "product": product,
        "stock_pajang": int(akhir), "stock_gudang": 0, "total_stock": int(akhir),
        "stock_kosong": "YA" if kosong else "TIDAK", "index_oos": 1 if kosong else 0,
        "oos_reason": "(OOS) BELUM ADA PENGIRIMAN DARI DC / DISTRIBUTOR" if kosong else "STOCK TERSEDIA",
        "skam": outlet_row.get("skam"),
    }
    return pd.DataFrame([rec])[REQUIRED_COLUMNS]
