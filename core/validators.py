"""Validasi & pembersihan file upload (stok & sell-in) sebelum masuk database."""
import pandas as pd

from core.config import INT_COLUMNS, REQUIRED_COLUMNS, SELLIN_COLUMNS, TEXT_COLUMNS


def read_any(file, sheet: str | None = None) -> pd.DataFrame:
    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file, dtype=str, keep_default_na=False)
    xl = pd.ExcelFile(file)
    name = sheet if sheet in xl.sheet_names else xl.sheet_names[0]
    return xl.parse(name, dtype=str, keep_default_na=False)


def _parse_date(s: pd.Series) -> pd.Series:
    # Format sumber: dd/mm/yyyy. Excel kadang memberi yyyy-mm-dd; keduanya aman.
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(dmy).fillna(pd.to_datetime(s, dayfirst=True, errors="coerce"))


def clean_stock(df_raw: pd.DataFrame):
    """Return (df_bersih, daftar_peringatan, daftar_error)."""
    errors, warns = [], []
    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, warns, [f"Kolom tidak ditemukan: {', '.join(missing)}"]
    df = df[REQUIRED_COLUMNS].copy()

    for c in TEXT_COLUMNS:
        df[c] = df[c].astype(str).str.strip().replace({"": None, "nan": None, "None": None})
    df["account"] = df["account"].str.upper()
    for c in INT_COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["date"] = _parse_date(df["date"])
    bad = df["date"].isna() | df["id_outlet"].isna() | df["account"].isna() | df["id_product"].isna()
    if bad.any():
        warns.append(f"{int(bad.sum())} baris dibuang (tanggal / id_outlet / account / id_product kosong atau tidak valid).")
        df = df[~bad]

    for c in ["stock_pajang", "stock_gudang", "total_stock"]:
        df[c] = df[c].fillna(0).clip(lower=0)
    # total_stock harus = pajang + gudang
    mism = df["total_stock"] != df["stock_pajang"] + df["stock_gudang"]
    if mism.any():
        warns.append(f"{int(mism.sum())} baris total_stock ≠ pajang + gudang; total_stock dihitung ulang.")
        df.loc[mism, "total_stock"] = df.loc[mism, "stock_pajang"] + df.loc[mism, "stock_gudang"]
    for c in INT_COLUMNS:
        df[c] = df[c].astype("Int64")
    df["id_product"] = df["id_product"].astype(int)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    dup = df.duplicated(["date", "id_outlet", "id_product"], keep="last")
    if dup.any():
        warns.append(f"{int(dup.sum())} baris duplikat (tanggal+outlet+SKU) dalam file; dipakai baris terakhir.")
        df = df[~dup]
    return df.reset_index(drop=True), warns, errors


def _norm_code(s: pd.Series) -> pd.Series:
    """Samakan format kode: teks, tanpa spasi pinggir, huruf besar, tanpa '.0' hasil Excel."""
    return s.astype(str).str.strip().str.replace(r"\.0+$", "", regex=True).str.upper()


def clean_sellin(df_raw: pd.DataFrame, master_outlet: pd.DataFrame, master_sku: pd.DataFrame,
                 sku_map: pd.DataFrame | None = None):
    """Return (df_valid, df_ditolak, peringatan).

    SKU bisa diisi lewat `kode_sku` (kode principle yang dikenal sales, dicocokkan ke `sku_map`)
    atau `id_product` (format lama). df_valid selalu berisi kolom SELLIN_COLUMNS dengan id_product
    internal, jadi tabel sell_in & seluruh perhitungan tidak berubah.
    """
    warns = []
    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    use_kode = "kode_sku" in df.columns
    sku_col = "kode_sku" if use_kode else "id_product"
    missing = [c for c in ["date", "id_outlet", sku_col, "qty"] if c not in df.columns]
    if missing:
        return None, None, [f"Kolom wajib tidak ada: {', '.join(missing)}"]
    if use_kode and (sku_map is None or sku_map.empty):
        return None, None, ["Master kode SKU principle belum ada di database. Jalankan sql/sku_principle.sql di Supabase."]
    if "notes" not in df.columns:
        df["notes"] = None
    key_cols = ["date", "id_outlet", sku_col, "qty"]
    df = df[key_cols + ["notes"]].copy()
    df = df[~(df[key_cols].astype(str).apply(lambda s: s.str.strip() == "").all(axis=1))]

    df["date"] = _parse_date(df["date"])
    df["id_outlet"] = df["id_outlet"].astype(str).str.strip()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    df["notes"] = df["notes"].astype(str).str.strip().replace({"": None, "nan": None})

    ok_outlet = df["id_outlet"].isin(master_outlet["id_outlet"].astype(str))
    reasons = pd.Series("", index=df.index)
    reasons[df["date"].isna()] += "Tanggal tidak valid; "
    reasons[~ok_outlet] += "id_outlet tidak ada di master; "

    if use_kode:
        df["kode_sku"] = _norm_code(df["kode_sku"])
        known = set(_norm_code(sku_map["kode_sku"]))
        linked = sku_map.dropna(subset=["id_product"])
        df["id_product"] = pd.to_numeric(df["kode_sku"].map(dict(zip(_norm_code(linked["kode_sku"]), linked["id_product"]))),
                                         errors="coerce")
        unknown = ~df["kode_sku"].isin(known)
        reasons[unknown] += "kode_sku tidak ada di master principle; "
        reasons[~unknown & df["id_product"].isna()] += "kode_sku belum terhubung ke SKU di data stok; "
    else:
        df["id_product"] = pd.to_numeric(df["id_product"], errors="coerce")
        reasons[~df["id_product"].isin(master_sku["id_product"])] += "id_product tidak ada di master; "
    reasons[df["qty"].isna() | (df["qty"] < 0)] += "qty harus angka ≥ 0; "

    rejected = df[reasons != ""].assign(alasan=reasons[reasons != ""])
    valid = df[reasons == ""][SELLIN_COLUMNS].copy()
    valid["id_product"] = valid["id_product"].astype(int)
    valid["qty"] = valid["qty"].astype(int)
    dup = valid.duplicated(["date", "id_outlet", "id_product"], keep=False)
    if dup.any():
        warns.append("Ada baris dengan tanggal+outlet+SKU sama; qty dijumlahkan.")
        valid = (valid.groupby(["date", "id_outlet", "id_product"], as_index=False)
                      .agg(qty=("qty", "sum"), notes=("notes", "first")))
    return valid.reset_index(drop=True), rejected.reset_index(drop=True), warns
