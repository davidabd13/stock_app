import streamlit as st

from core.calculations import rollup
from core.config import DSI_RULES
from core.exports import summary_table, to_excel
from core.service import load_flow, select_data
from ui.filters import global_filters
from ui.render import acc_tone, card_title, html, table

n = lambda v: f"{int(round(v)):,}".replace(",", ".")  # noqa: E731

flow = load_flow()
if flow.empty:
    st.info("Data belum tersedia untuk dianalisis.")
    st.stop()

left, right = st.columns([1, 2.6])
with left, st.container(key="card-filter"):
    card_title("Filter & Parameter Report")
    f = global_filters(flow, "rep", container=st.container())
    groups = {}
    for acc, rule in DSI_RULES.items():
        groups.setdefault(rule, []).append(acc.title())
    html("rules_box.html", rules=[{"label": " & ".join(a), "g": g, "m": m, "cls": c}
                                   for (a, (g, m)), c in zip(((v, k) for k, v in groups.items()), ["g", "b", "r"])])

_, pairs = select_data(flow, f)
if pairs.empty:
    right.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

acc = rollup(pairs, ["account"], f.hari)
prod = rollup(pairs, ["product"], f.hari)
toko = rollup(pairs, ["account", "outlet"], f.hari)

with right:
    html("account_card.html", accounts=[
        {"name": r.account, "tone": acc_tone(r.account), "total_stok": r.stok_awal + r.stok_tambahan,
         "keluar": r.total_keluar, "stok_akhir": r.stok_akhir} for r in acc.itertuples()])
    with st.container(key="card-unggulan"):
        card_title("Analisa Produk & Toko Unggulan")
        tk = prod.loc[prod["total_keluar"].idxmax()]
        ts = prod.loc[prod["stok_akhir"].idxmax()]
        tt = toko.loc[toko["total_keluar"].idxmax()]
        low = prod[prod["stok_akhir"] > 0].sort_values(["spd", "stok_akhir"], ascending=[True, False])
        items = [
            {"title": "Produk Keluar Tertinggi", "text": f"{tk['product']} ({n(tk['total_keluar'])} pcs)", "tone": "n"},
            {"title": "Produk Stok Terbanyak", "text": f"{ts['product']} ({n(ts['stok_akhir'])} pcs)", "tone": "n"},
            {"title": "Toko Keluar Terbesar", "text": f"{tt['outlet']} ({tt['account']})", "tone": "n"},
        ]
        if not low.empty:
            items.append({"title": "Produk SPD Terendah (Perlu Perhatian)",
                          "text": f"{low.iloc[0]['product']} (SPD {low.iloc[0]['spd']:.2f})", "tone": "red"})
        html("highlight_card.html", items=items)

with st.container(key="card-dsi"):
    t1, t2 = st.columns([3, 2], vertical_alignment="center")
    with t1:
        card_title("Analisa DSI & Status PO Toko")
    with t2:
        st.markdown(f"<div style='text-align:right;font-size:.75rem;color:#64748b'>SPD = Total Keluar / Jumlah Hari Berjalan "
                    f"({f.hari} hari)</div>", unsafe_allow_html=True)
    level = st.radio("Level tampilan", ["Per Toko", "Per Toko & SKU"], horizontal=True, key="rep_level", label_visibility="collapsed")
    base = (toko if level == "Per Toko" else pairs).sort_values(["account", "outlet"])
    spec = [("account", "ACCOUNT", "account"), ("outlet", "NAMA TOKO", "text")]
    if level != "Per Toko":
        spec.append(("product", "PRODUK", "text"))
    spec += [("stok_akhir", "STOK AKHIR", "int"), ("total_keluar", "TOTAL KELUAR", "int", "red"),
             ("spd", "SPD", "dec2"), ("dsi", "DSI (HARI)", "dsi", "bold"), ("status_po", "STATUS PO & NOTIF", "status")]
    table(base, spec, note="DSI 999+ = ada stok tetapi tidak ada barang keluar (SPD 0). Stok 0 = DSI 0.")
    cols = ["account", "outlet", "stok_akhir", "total_keluar", "spd", "dsi", "status_po"]
    st.download_button("📥 Export Laporan Analisa (.xlsx)",
                       to_excel({"Per Toko-SKU": summary_table(pairs), "Per Toko": toko[cols].round(2)}),
                       "Report_Analisa.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="rep_dl")
