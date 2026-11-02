import plotly.graph_objects as go
import streamlit as st

from core.config import STATUS_COLORS
from core.exports import summary_table, to_excel
from core.ppt_export import build_dashboard_ppt
from core.service import load_flow, select_data
from ui.filters import global_filters, mtd_range
from ui.render import card_title, kpi_row

n = lambda v: f"{int(round(v)):,}".replace(",", ".")  # noqa: E731

flow = load_flow()
if flow.empty:
    st.info("Belum ada data stok. Admin dapat mengunggahnya di menu Upload Stock (Admin).")
    st.stop()

with st.expander("🔎 Filter periode, account & toko", expanded=False):
    f = global_filters(flow, "dash")
flow_f, pairs = select_data(flow, f)
if pairs.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

is_mtd = (f.start.date(), f.end.date()) == mtd_range(flow)
accs = ", ".join(a.title() for a in sorted(pairs["account"].unique()))
kpi_row([
    {"label": "Total Account", "value": pairs["account"].nunique(), "sub": accs, "icon": "🏢", "tone": "green"},
    {"label": "Total SKU Produk", "value": pairs["product"].nunique(), "sub": "SKU aktif terpantau", "icon": "📦", "tone": "blue"},
    {"label": "Total Toko", "value": pairs["outlet"].nunique(), "sub": "Cabang Terdaftar", "icon": "🏪", "tone": "indigo"},
    {"label": "Total Stok Keluar", "value": n(pairs["total_keluar"].sum()), "icon": "🚚", "tone": "red",
     "sub": "Bulan Berjalan (MTD)" if is_mtd else f"{f.start:%d/%m} – {f.end:%d/%m/%Y}"},
])
awal, tambah = pairs["stok_awal"].sum(), pairs["stok_tambahan"].sum()
kpi_row([
    {"label": "Total Stok Awal", "value": n(awal), "size": "sm", "tone": "ink"},
    {"label": "Total Stok Tambah (Sell-in)", "value": n(tambah), "size": "sm", "tone": "ink"},
    {"label": "Total Stok (Awal + Tambah)", "value": n(awal + tambah), "size": "sm", "tone": "blue"},
    {"label": "Total Stok Akhir", "value": n(pairs["stok_akhir"].sum()), "size": "sm", "tone": "green"},
])
naik = pairs["stok_naik_tanpa_sellin"].sum()
if naik > 0:
    st.caption(f"ℹ️ {n(naik)} pcs stok naik tanpa sell-in tercatat (tidak dihitung sebagai penjualan). "
               "Input sell-in yang belum tercatat agar Stok Keluar & DSI akurat.")

c1, c2 = st.columns(2)
with c1, st.container(key="card-bar"):
    card_title("Distribusi Stok Keluar per Account", icon="📊")
    acc = pairs.groupby("account", as_index=False)["total_keluar"].sum()
    fig = go.Figure(go.Bar(x=acc["account"], y=acc["total_keluar"], name="Total Stok Keluar",
                           marker_color="#10b981", text=acc["total_keluar"], texttemplate="%{text:,.0f}"))
    fig.update_layout(height=320, margin=dict(t=30, b=10, l=10, r=10), showlegend=True,
                      legend=dict(orientation="h", x=0.5, xanchor="center", y=1.12), plot_bgcolor="white")
    fig.update_yaxes(gridcolor="#e2e8f0")
    st.plotly_chart(fig, key="ch_bar")
with c2, st.container(key="card-donut"):
    card_title("Status PO & DSI Alerts Summary", icon="⚠️")
    stt = pairs["status_po"].value_counts()
    names = {"Hijau - Push PO": "Push PO", "Kuning - Normal": "Normal", "Merah - Manage PO": "Manage PO"}
    order = [k for k in names if k in stt.index]
    fig = go.Figure(go.Pie(labels=[names[k] for k in order], values=[int(stt[k]) for k in order], hole=0.55,
                           marker=dict(colors=[STATUS_COLORS[k] for k in order]), sort=False))
    fig.update_layout(height=320, margin=dict(t=30, b=10, l=10, r=10),
                      legend=dict(orientation="h", x=0.5, xanchor="center", y=1.12))
    st.plotly_chart(fig, key="ch_donut")

with st.container(key="card-trend"):
    card_title("Tren Stok Keluar Harian per Account", "Dihitung dari selisih stok antar snapshot + sell-in", "📈")
    import plotly.express as px
    trend = flow_f.groupby(["date", "account"], as_index=False)["total_keluar"].sum()
    trend["tgl"] = trend["date"].dt.strftime("%d/%m/%Y")           # sumbu X kategori, bukan skala waktu
    kw = dict(x="tgl", y="total_keluar", color="account",
              labels={"total_keluar": "Stok Keluar", "tgl": "Tanggal", "account": "Account"},
              category_orders={"tgl": list(trend.sort_values("date")["tgl"].unique())})
    if trend["date"].nunique() < 3:      # terlalu sedikit titik untuk garis -> pakai bar
        fig = px.bar(trend, barmode="group", text_auto=",.0f", **kw)
        st.caption("Baru ada " + str(trend["date"].nunique()) + " tanggal snapshot pada periode ini. "
                   "Ubah filter periode (mis. mulai 1 bulan sebelumnya) untuk melihat tren.")
    else:
        fig = px.line(trend, markers=True, **kw)
    fig.update_xaxes(type="category")
    fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor="white")
    fig.update_yaxes(gridcolor="#e2e8f0")
    st.plotly_chart(fig, key="ch_trend")

with st.container(key="card-export"):
    t, b1, b2, b3 = st.columns([5, 1.4, 1.9, 1.1], vertical_alignment="center")
    with t:
        card_title("Export & Laporan Presentasi", "Export data dashboard dan analisa ke format Excel atau siapkan slide presentasi")
    export_df = summary_table(pairs)
    detail = flow_f.sort_values(["account", "outlet", "product", "date"])[
        ["date", "account", "outlet", "product", "stok_awal", "sell_in", "total_stock", "total_keluar"]].copy()
    detail["date"] = detail["date"].dt.strftime("%d/%m/%Y")
    detail.columns = ["Tanggal", "Account", "Toko", "Produk", "Stok Sebelumnya", "Sell-in", "Stok Hari Ini", "Stok Keluar"]
    b1.download_button("📗 Export Excel", to_excel({"Stock Dashboard": export_df, "Detail Harian": detail}),
                       "Stock_Dashboard_Export.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="btn-excel")
    b2.download_button("📘 Export PPT Dashboard", build_dashboard_ppt(pairs, flow_f, f), "Stock_Dashboard.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation", type="primary", key="btn-ppt")
    b3.download_button("CSV", export_df.to_csv(index=False).encode("utf-8-sig"), "Stock_Dashboard_Export.csv", "text/csv", key="btn-csv")
