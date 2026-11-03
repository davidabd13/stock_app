"""Pembuat file Excel: laporan berwarna & template upload (dengan master + dropdown)."""
from io import BytesIO

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from core.config import REQUIRED_COLUMNS, STATUS_COLORS, STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH

_HEAD = PatternFill("solid", fgColor="1E3A8A")
_FILL = {s: PatternFill("solid", fgColor=c.lstrip("#")) for s, c in STATUS_COLORS.items()}


def summary_table(pairs: pd.DataFrame) -> pd.DataFrame:
    """Format kolom export (mengikuti Stock_Dashboard_GoogleSheets_Export)."""
    t = pairs.sort_values(["account", "outlet", "product"])
    return pd.DataFrame({
        "Account": t["account"], "Toko": t["outlet"], "Produk": t["product"],
        "Stok Awal": t["stok_awal"].astype(int), "Stok Tambah": t["stok_tambahan"].astype(int),
        "Total Stok (Awal+Tambah)": (t["stok_awal"] + t["stok_tambahan"]).astype(int),
        "Stok Akhir": t["stok_akhir"].astype(int), "Stok Keluar": t["total_keluar"].astype(int),
        "SPD": t["spd"].round(2), "DSI (Hari)": t["dsi"].round(1), "Status PO": t["status_po"],
        "Update Terakhir": t["update_terakhir"].dt.strftime("%d/%m/%Y"),
    }).reset_index(drop=True)


def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            ws.freeze_panes = "A2"
            for c in ws[1]:
                c.fill, c.font = _HEAD, Font(bold=True, color="FFFFFF")
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            for i, col in enumerate(df.columns, 1):
                width = max([len(str(col))] + [len(str(v)) for v in df[col].head(300)]) + 3
                ws.column_dimensions[get_column_letter(i)].width = min(width, 45)
            for col in ("Status PO", "status_po"):
                if col in df.columns:
                    idx = list(df.columns).index(col) + 1
                    for r in range(2, len(df) + 2):
                        cell = ws.cell(row=r, column=idx)
                        if cell.value in _FILL:
                            cell.fill = _FILL[cell.value]
                            cell.font = Font(bold=True, color="FFFFFF")
            ws.auto_filter.ref = ws.dimensions
    return buf.getvalue()


def stock_template() -> bytes:
    return to_excel({"raw_oos": pd.DataFrame(columns=REQUIRED_COLUMNS)})


def _code_cell(v):
    """Kode angka disimpan sebagai angka (cocok dengan ketikan/paste sales), kode lain sebagai teks."""
    v = str(v).strip()
    return int(v) if v.isdigit() else v


def sellin_template(master_outlet: pd.DataFrame, master_sku: pd.DataFrame,
                    sku_map: pd.DataFrame | None = None, rows: int = 500) -> bytes:
    """Template sell-in: dropdown NAMA TOKO (bisa diedit/diketik) & kode_sku (kode principle).
    id_outlet dan nama produk terisi otomatis lewat lookup (sales cukup tahu nama toko).

    Bila sku_map (tabel sku_principle) kosong, template memakai id_product seperti versi lama.
    """
    use_kode = sku_map is not None and not sku_map.empty and sku_map["id_product"].notna().any()
    sku_head = "kode_sku" if use_kode else "id_product"

    wb = Workbook()
    ws = wb.active
    ws.title = "Template_SellIn"
    heads = ["date", "outlet", "id_outlet", sku_head, "product", "qty", "notes"]
    ws.append(heads)

    mo = wb.create_sheet("Master_Outlet")
    mo.append(["id_outlet", "outlet", "account", "area_fix"])
    for r in master_outlet.sort_values(["outlet", "account"]).itertuples():
        mo.append([r.id_outlet, r.outlet, r.account, getattr(r, "area_fix", None)])
    ms = wb.create_sheet("Master_SKU")
    if use_kode:
        ms.append(["kode_sku", "product", "short_sku"])
        k = (sku_map.dropna(subset=["id_product"]).assign(id_product=lambda d: d["id_product"].astype(int))
             .merge(master_sku, on="id_product", how="left"))
        k["product"] = k["product"].fillna(k["sub_brand"])
        for r in k.sort_values("product").itertuples():
            ms.append([_code_cell(r.kode_sku), r.product, r.short_sku])
        n_sku = len(k)
    else:
        ms.append(["id_product", "product"])
        for r in master_sku.sort_values("product").itertuples():
            ms.append([int(r.id_product), r.product])
        n_sku = len(master_sku)

    info = wb.create_sheet("Petunjuk")
    dup_names = (master_outlet.assign(_k=master_outlet["outlet"].astype(str).str.strip().str.upper())
                 .groupby("_k")["id_outlet"].nunique())
    n_dup = int((dup_names > 1).sum())
    lines = ["CARA PAKAI",
             f"1. Isi sheet Template_SellIn: date, outlet (NAMA TOKO: pilih dari dropdown atau ketik), {sku_head} (dropdown / ketik kode), qty.",
             "2. Kolom id_outlet & product (abu-abu) terisi otomatis, jangan diubah. Jika id_outlet kosong = nama toko tidak ada di Master_Outlet; jika product kosong = kode tidak dikenal.",
             "3. Format tanggal dd/mm/yyyy. qty = jumlah sell-in (pcs), angka ≥ 0.",
             "4. Jangan ubah nama header. Jangan hapus sheet Master_*.",
             "5. Satu baris per tanggal + toko + SKU. Upload kembali di menu Input Sell-in."]
    if n_dup:
        lines.append(f"6. Ada {n_dup} nama toko yang dipakai lebih dari satu outlet. Untuk toko tersebut isi juga kolom id_outlet secara manual (lihat sheet Master_Outlet).")
    for line in lines:
        info.append([line])
    info.column_dimensions["A"].width = 100
    info["A1"].font = Font(bold=True, size=13)

    grey = PatternFill("solid", fgColor="E5E7EB")
    for c in ws[1]:
        c.fill, c.font = _HEAD, Font(bold=True, color="FFFFFF")
    for r in range(2, rows + 2):
        ws[f"C{r}"] = f'=IF(TRIM(B{r})="","",IFERROR(INDEX(Master_Outlet!$A:$A,MATCH(TRIM(B{r}),Master_Outlet!$B:$B,0)),""))'
        ws[f"E{r}"] = f'=IFERROR(VLOOKUP(D{r},Master_SKU!$A:$B,2,FALSE),"")'
        ws[f"C{r}"].fill = ws[f"E{r}"].fill = grey
        ws[f"A{r}"].number_format = "DD/MM/YYYY"
    n_o, n_s = max(len(master_outlet), 1) + 1, max(n_sku, 1) + 1
    # errorStyle="warning": nama toko boleh diedit/diketik bebas; nama di luar master hanya diberi peringatan
    dv_o = DataValidation(type="list", formula1=f"=Master_Outlet!$B$2:$B${n_o}", allow_blank=True, errorStyle="warning",
                          errorTitle="Nama toko tidak ada di master",
                          error="Nama toko ini tidak ditemukan di Master_Outlet. Lanjutkan hanya jika Anda yakin.")
    dv_s = DataValidation(type="list", formula1=f"=Master_SKU!$A$2:$A${n_s}", allow_blank=True)
    dv_q = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
    for dv, col in ((dv_o, "B"), (dv_s, "D"), (dv_q, "F")):
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{rows + 1}")
    for col, w in zip("ABCDEFG", [14, 38, 14, 16, 44, 10, 28]):
        ws.column_dimensions[col].width = w
    for sh in (mo, ms):
        for c in sh[1]:
            c.fill, c.font = _HEAD, Font(bold=True, color="FFFFFF")
        sh.column_dimensions["A"].width, sh.column_dimensions["B"].width = 16, 44
    if use_kode:
        ms.column_dimensions["C"].width = 20
    ws.freeze_panes = "A2"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
