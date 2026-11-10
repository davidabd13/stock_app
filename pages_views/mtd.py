import pandas as pd
import streamlit as st

from core.calculations import aggregate_pairs, compute_metrics
from core.config import STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH
from core.exports import summary_table, to_excel
from core.service import load_flow
from ui.render import BULAN, card_title, table

flow = load_flow()
if flow.empty:
    st.info("Belum ada data stok.")
    st.stop()

months = sorted(flow["date"].dt.to_period("M").unique(), reverse=True)
SEMUA_ACC, SEMUA_TOKO, SEMUA_STATUS = "Semua Account", "Semua Toko", "Semua Status PO"

with st.container(key="card-mtd"):
    card_title("Analisa 1 Bulan Penuh (MTD) & Master Data", "Filter berdasarkan account, nama toko, status PO, dan bulan")
    f_acc, f_toko, f_stat, f_bln = st.columns([2, 3, 2, 1.6], vertical_alignment="bottom")

    # Bulan dipilih lebih dulu karena daftar account/toko mengikuti data bulan tsb
    per = f_bln.selectbox("Bulan", months, format_func=lambda p: f"{BULAN[p.month - 1]} {p.year}", label_visibility="collapsed")

    # MTD: sampai tanggal data terakhir pada bulan terpilih; pembagi DSI = tanggal tsb (1..31),
    # otomatis mulai lagi dari 1 saat ganti bulan.
    start = per.start_time
    end = flow.loc[flow["date"].dt.to_period("M") == per, "date"].max()
    hari_mtd = int(end.day)

    pairs = compute_metrics(aggregate_pairs(flow, start, end), hari_mtd)
    if pairs.empty:
        st.info("Tidak ada data pada bulan ini.")
        st.stop()

    acc_opts = sorted(pairs["account"].dropna().unique())
    acc = f_acc.selectbox("Account", [SEMUA_ACC] + acc_opts, label_visibility="collapsed", key="mtd_acc")
    toko_src = pairs if acc == SEMUA_ACC else pairs[pairs["account"] == acc]
    toko_opts = sorted(toko_src["outlet"].dropna().unique())
    toko = f_toko.selectbox("Toko", [SEMUA_TOKO] + toko_opts, label_visibility="collapsed", key="mtd_toko")
    stat = f_stat.selectbox("Status", [SEMUA_STATUS, STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH], label_visibility="collapsed")

    d = pairs.copy()
    if acc != SEMUA_ACC:
        d = d[d["account"] == acc]
    if toko != SEMUA_TOKO:
        d = d[d["outlet"] == toko]
    if stat != SEMUA_STATUS:
        d = d[d["status_po"] == stat]
    # Urut: tanggal update terbaru di atas, lalu account -> toko -> produk
    d = d.sort_values(["update_terakhir", "account", "outlet", "product"], ascending=[False, True, True, True])
    d["tgl"] = d["update_terakhir"].dt.strftime("%d/%m/%Y")

    table(d, [("tgl", "TANGGAL", "text"), ("account", "ACCOUNT", "account"), ("outlet", "TOKO", "text"),
              ("product", "PRODUK", "text"), ("stok_awal", "AWAL", "int", "blue"), ("stok_tambahan", "TAMBAH", "int", "blue"),
              ("stok_akhir", "AKHIR", "int", "blue"), ("total_keluar", "KELUAR", "int", "red"),
              ("dsi", "DSI MTD", "dsi_h", "bold"), ("status_po", "STATUS", "status")], max_rows=600,
          note=f"MTD {start:%d/%m/%Y} – {end:%d/%m/%Y} · DSI MTD = Stok Akhir / (Keluar / {hari_mtd} hari) · Tanggal = update stok terakhir.")
    st.download_button("📥 Export hasil filter (.xlsx)", to_excel({"MTD": summary_table(d, sort=False)}), "Analisa_MTD.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="mtd_dl")
