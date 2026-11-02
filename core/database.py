"""Semua akses Supabase ada di sini. Kredensial dari st.secrets (bukan hardcode)."""
import json

import pandas as pd
import streamlit as st
from supabase import Client, create_client

from core.config import (INT_COLUMNS, MASTER_OUTLET_COLUMNS, REQUIRED_COLUMNS)

PAGE = 1000  # batas baris per request Supabase


@st.cache_resource
def get_client() -> Client:
    try:
        url, key = st.secrets["supabase"]["url"], st.secrets["supabase"]["key"]
    except Exception:
        st.error("Secrets Supabase belum diisi. Lihat .streamlit/secrets.toml.example")
        st.stop()
    return create_client(url, key)


def _fetch_all(table: str, order: list[str]) -> pd.DataFrame:
    """Ambil SEMUA baris dengan pagination (default Supabase hanya 1000 baris)."""
    sb, rows, start = get_client(), [], 0
    while True:
        q = sb.table(table).select("*")
        for col in order:
            q = q.order(col)
        data = q.range(start, start + PAGE - 1).execute().data
        rows += data
        if len(data) < PAGE:
            break
        start += PAGE
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- loaders
@st.cache_data(ttl=120, show_spinner="Memuat data stok...")
def load_stock() -> pd.DataFrame:
    df = _fetch_all("raw_stock_oos", ["date", "id_outlet", "id_product"])
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=120)
def load_sellin() -> pd.DataFrame:
    df = _fetch_all("sell_in", ["id"])
    if df.empty:
        return pd.DataFrame(columns=["id", "date", "id_outlet", "id_product", "qty", "notes",
                                     "source", "created_by", "created_at"])
    df["date"] = pd.to_datetime(df["date"])
    df["qty"] = pd.to_numeric(df["qty"]).fillna(0).astype(int)
    return df


@st.cache_data(ttl=300)
def load_master_outlet() -> pd.DataFrame:
    df = _fetch_all("master_outlet", ["account", "outlet"])
    return df if not df.empty else pd.DataFrame(columns=MASTER_OUTLET_COLUMNS)


@st.cache_data(ttl=300)
def load_master_sku() -> pd.DataFrame:
    df = _fetch_all("master_sku", ["product"])
    return df if not df.empty else pd.DataFrame(columns=["id_product", "product"])


@st.cache_data(ttl=300)
def load_sku_principle() -> pd.DataFrame:
    """Master kode SKU principle (tabel sku_principle). Kosong bila tabel belum dibuat -> app pakai mode lama (id_product)."""
    cols = ["kode_sku", "short_sku", "sub_brand", "id_product"]
    try:
        df = _fetch_all("sku_principle", ["kode_sku"])
    except Exception:  # noqa: BLE001  (tabel belum ada)
        return pd.DataFrame(columns=cols)
    if df.empty:
        return pd.DataFrame(columns=cols)
    df["kode_sku"] = df["kode_sku"].astype(str).str.strip()
    df["id_product"] = pd.to_numeric(df["id_product"], errors="coerce").astype("Int64")
    return df


def clear_cache():
    st.cache_data.clear()


# ---------------------------------------------------------------- writers
def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list dict aman JSON (NaN -> null, numpy -> python)."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _upsert(table: str, df: pd.DataFrame, conflict: str, batch: int = 500, progress=None):
    recs, ok, errors = _records(df), 0, []
    sb = get_client()
    for i in range(0, len(recs), batch):
        chunk = recs[i:i + batch]
        try:
            sb.table(table).upsert(chunk, on_conflict=conflict).execute()
            ok += len(chunk)
        except Exception as e:  # noqa: BLE001
            errors.append(f"Batch {i // batch + 1} gagal: {e}")
        if progress:
            progress(min(i + batch, len(recs)), len(recs))
    return ok, errors


def upsert_stock(df: pd.DataFrame, progress=None):
    """df harus sudah dibersihkan (lihat core.validators)."""
    # master_outlet & master_sku adalah VIEW dari raw_stock_oos -> otomatis ikut terbarui
    res = _upsert("raw_stock_oos", df[REQUIRED_COLUMNS], "date,id_outlet,id_product", progress=progress)
    clear_cache()
    return res


def upsert_sellin(df: pd.DataFrame, source: str, user: str):
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d["source"], d["created_by"] = source, user
    res = _upsert("sell_in", d[["date", "id_outlet", "id_product", "qty", "notes", "source", "created_by"]],
                  "date,id_outlet,id_product")
    clear_cache()
    return res


def delete_sellin(ids: list[int]):
    get_client().table("sell_in").delete().in_("id", [int(i) for i in ids]).execute()
    clear_cache()


def delete_stock_range(start: str, end: str):
    get_client().table("raw_stock_oos").delete().gte("date", start).lte("date", end).execute()
    clear_cache()
