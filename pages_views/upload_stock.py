from datetime import date

import pandas as pd
import streamlit as st

from core.auth import is_admin
from core.config import REQUIRED_COLUMNS
from core.database import delete_stock_range, get_client, upsert_stock
from core.exports import stock_template
from core.validators import clean_stock, read_any
from ui.render import card_title

card_title("📦 Upload & Management Raw Stock", "Khusus Admin: update data stok harian dari Excel/CSV tanpa membuka Supabase.")

if not is_admin():
    st.error("Halaman ini hanya untuk Admin.")
    st.stop()

tab_up, tab_view, tab_del = st.tabs(["📤 Upload File Stok", "📊 Data di Database", "🗑️ Hapus Periode"])

# ------------------------------------------------------------------ UPLOAD
with tab_up:
    st.download_button("⬇️ Unduh Template Header (22 kolom)", stock_template(), "Template_Raw_OOS.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    up = st.file_uploader("Pilih file Excel (.xlsx) atau CSV", type=["csv", "xlsx"], key="st_up")
    if up:
        try:
            df, warns, errs = clean_stock(read_any(up))
        except Exception as e:  # noqa: BLE001
            st.error(f"Gagal membaca file: {e}")
            st.stop()
        if errs:
            st.error(errs[0])
            st.stop()
        st.success(f"**{up.name}** terbaca & tervalidasi: {len(df):,} baris.")
        for w in warns:
            st.warning(w)

        d = pd.to_datetime(df["date"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Baris", f"{len(df):,}")
        c2.metric("Jumlah Outlet", df["id_outlet"].nunique())
        c3.metric("Jumlah SKU", df["id_product"].nunique())
        c4.metric("Rentang Tanggal", f"{d.min():%d/%m} – {d.max():%d/%m/%Y}")
        with st.expander("👁️ Preview 10 baris pertama", expanded=True):
            st.dataframe(df.head(10), hide_index=True)

        st.info("Data dengan tanggal + outlet + SKU yang sama akan **diperbarui** (bukan dobel).")
        if st.button("🚀 Proses & Simpan ke Database", type="primary"):
            bar, txt = st.progress(0), st.empty()

            def cb(cur, tot):
                bar.progress(int(cur / tot * 100))
                txt.text(f"Mengunggah {cur:,}/{tot:,} baris")

            ok, errors = upsert_stock(df, progress=cb)
            if ok:
                st.success(f"{ok:,} baris berhasil disimpan. Master outlet & SKU ikut diperbarui.")
            for e in errors:
                st.error(e)

# ------------------------------------------------------------------ LIHAT
with tab_view:
    c1, c2, c3 = st.columns(3)
    acc = c1.selectbox("Account", ["Semua", "TIP TOP", "HARI HARI", "NAGA"])
    rng = c2.date_input("Rentang tanggal", (date.today().replace(day=1), date.today()), key="v_rng")
    lim = c3.number_input("Maks baris", 10, 5000, 500)
    if st.button("🔄 Tampilkan Data"):
        q = get_client().table("raw_stock_oos").select("*").order("date", desc=True).limit(int(lim))
        if acc != "Semua":
            q = q.eq("account", acc)
        if isinstance(rng, (list, tuple)) and len(rng) == 2:
            q = q.gte("date", str(rng[0])).lte("date", str(rng[1]))
        data = q.execute().data
        if data:
            dfv = pd.DataFrame(data)
            st.write(f"{len(dfv):,} baris:")
            st.dataframe(dfv, hide_index=True)
            st.download_button("📥 Export CSV", dfv.to_csv(index=False).encode("utf-8-sig"), "raw_stock_export.csv", "text/csv")
        else:
            st.warning("Tidak ada data untuk filter ini.")

# ------------------------------------------------------------------ HAPUS
with tab_del:
    st.warning("Menghapus data stok bersifat permanen. Gunakan jika salah upload periode.")
    r = st.date_input("Periode yang dihapus", (date.today(), date.today()), key="d_rng")
    sure = st.checkbox("Saya yakin ingin menghapus data stok pada periode tersebut")
    if st.button("Hapus Data Periode", disabled=not (sure and isinstance(r, (list, tuple)) and len(r) == 2)):
        delete_stock_range(str(r[0]), str(r[1]))
        st.success("Data periode terhapus.")
