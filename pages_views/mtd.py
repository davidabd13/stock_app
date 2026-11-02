import pandas as pd
import streamlit as st

from core.calculations import aggregate_pairs, compute_metrics
from core.config import HARI_BERJALAN_DEFAULT, STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH
from core.exports import summary_table, to_excel
from core.service import load_flow
from ui.render import BULAN, card_title, table

flow = load_flow()
if flow.empty:
    st.info("Belum ada data stok.")
    st.stop()

months = sorted(flow["date"].dt.to_period("M").unique(), reverse=True)
with st.container(key="card-mtd"):
    h1, h2, h3, h4 = st.columns([3, 2, 2, 1.4], vertical_alignment="bottom")
    with h1:
        card_title("Analisa 1 Bulan Penuh (MTD) & Pencarian", "Cari toko atau produk secara instan dan filter berdasarkan status PO")
    q = h2.text_input("Cari", placeholder="Cari Toko atau Produk...", label_visibility="collapsed")
    stat = h3.selectbox("Status", ["Semua Status PO", STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH], label_visibility="collapsed")
    per = h4.selectbox("Bulan", months, format_func=lambda p: f"{BULAN[p.month - 1]} {p.year}", label_visibility="collapsed")

    start, end = per.start_time, min(per.end_time.normalize(), flow["date"].max())
    pairs = compute_metrics(aggregate_pairs(flow, start, end), HARI_BERJALAN_DEFAULT)
    if pairs.empty:
        st.info("Tidak ada data pada bulan ini.")
        st.stop()
    d = pairs.copy()
    if q:
        m = d["outlet"].str.contains(q, case=False, na=False) | d["product"].str.contains(q, case=False, na=False)
        d = d[m]
    if stat != "Semua Status PO":
        d = d[d["status_po"] == stat]
    d = d.sort_values(["account", "outlet", "product"])
    d["tgl"] = d["update_terakhir"].dt.strftime("%d/%m/%Y")

    table(d, [("tgl", "TANGGAL", "text"), ("account", "ACCOUNT", "account"), ("outlet", "TOKO", "text"),
              ("product", "PRODUK", "text"), ("stok_awal", "AWAL", "int", "blue"), ("stok_tambahan", "TAMBAH", "int", "blue"),
              ("stok_akhir", "AKHIR", "int", "blue"), ("total_keluar", "KELUAR", "int", "red"),
              ("dsi", "DSI", "dsi_h", "bold"), ("status_po", "STATUS", "status")], max_rows=600,
          note=f"MTD {start:%d/%m/%Y} – {end:%d/%m/%Y} · SPD = Keluar / {HARI_BERJALAN_DEFAULT} hari · Tanggal = update stok terakhir.")
    st.download_button("📥 Export hasil filter (.xlsx)", to_excel({"MTD": summary_table(d)}), "Analisa_MTD.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="mtd_dl")
