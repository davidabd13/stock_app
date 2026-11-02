from datetime import date

import pandas as pd
import streamlit as st

from core.auth import current_user
from core.calculations import KEY, aggregate_pairs, assign_sellin, compute_metrics
from core.config import HARI_BERJALAN_DEFAULT
from core.database import (delete_sellin, load_master_outlet, load_master_sku, load_sellin, load_sku_principle,
                           load_stock, upsert_sellin, upsert_stock)
from core.exports import sellin_template, summary_table, to_excel
from core.service import load_flow
from core.snapshot import build_snapshot
from core.validators import clean_sellin, read_any
from ui.filters import mtd_range
from ui.render import card_title, table

user = current_user()["username"]
mo, ms, stock, sellin = load_master_outlet(), load_master_sku(), load_stock(), load_sellin()
sku_map = load_sku_principle()   # kode principle -> id_product (kosong = mode lama)
if mo.empty or ms.empty:
    st.warning("Master outlet / SKU masih kosong. Upload data stok dulu di menu Upload Stock (Admin).")
    st.stop()


def _reset():
    st.session_state["f_tambah"] = 0
    st.session_state["f_akhir"] = None


if st.session_state.pop("_do_reset", False):   # reset aman: dilakukan sebelum widget dibuat
    _reset()


# ================================================================== FORM CARD
with st.container(key="card-form"):
    card_title("Form Update & Input Stok Produk", "Data yang diinput langsung tersimpan otomatis ke Supabase.")
    t_form, t_excel, t_bulk = st.tabs(["✍️ Input Form", "📁 Upload Excel Sell-in", "🗂️ Input Banyak SKU (per Toko)"])

    # ---------------------------------------------------------- form tunggal
    with t_form:
        c1, c2, c3 = st.columns(3)
        tgl = c1.date_input("Tanggal", date.today(), key="f_tgl", format="DD/MM/YYYY")
        acc = c2.selectbox("Nama Account", sorted(mo["account"].unique()), key="f_acc")
        outs = mo[mo["account"] == acc].sort_values("outlet")
        outlet_name = c3.selectbox("Nama Toko", outs["outlet"].tolist(), key="f_toko")
        orow = outs[outs["outlet"] == outlet_name].iloc[0]
        id_outlet = orow["id_outlet"]

        st_o = stock[stock["id_outlet"].astype(str) == id_outlet]
        skus = ms[ms["id_product"].isin(st_o["id_product"].unique())] if not st_o.empty else ms
        skus = skus.sort_values("product")
        d1, d2 = st.columns([2, 1])
        produk = d1.selectbox("Produk (SKU)", skus["product"].tolist(), key="f_sku")
        id_product = int(skus.loc[skus["product"] == produk, "id_product"].iloc[0])

        prev = st_o[(st_o["id_product"] == id_product) & (st_o["date"] < pd.Timestamp(tgl))].sort_values("date")
        awal = int(prev["total_stock"].iloc[-1]) if not prev.empty else 0
        d2.number_input("Stok Awal (stok hari sebelumnya)", value=awal, disabled=True, key=f"awal_{id_outlet}_{id_product}_{tgl}",
                        help="Otomatis dari snapshot stok terakhir sebelum tanggal ini.")

        e1, e2 = st.columns(2)
        tambah = e1.number_input("Stok Tambahan (Sell-in)", min_value=0, step=1, value=0, key="f_tambah")
        akhir = e2.number_input("Stok Produk Akhir (opsional)", min_value=0, step=1, value=None, placeholder="Contoh: 80", key="f_akhir",
                                help="Isi bila Anda juga ingin mencatat stok hari ini. Disimpan sebagai snapshot stok.")
        total = awal + tambah
        info = f"Total stok = **{total:,}** (awal {awal:,} + tambah {tambah:,})"
        if akhir is not None:
            info += f" · Stok keluar = **{max(0, total - akhir):,}**"
        st.caption(info)

        b1, b2, _ = st.columns([1, 1.4, 5])
        b1.button("Reset", on_click=_reset)
        if b2.button("💾 Simpan ke Supabase", type="primary"):
            if tambah == 0 and akhir is None:
                st.warning("Isi Stok Tambahan (sell-in) dan/atau Stok Produk Akhir.")
            else:
                errs = []
                if tambah > 0:
                    _, e = upsert_sellin(pd.DataFrame({"date": [tgl], "id_outlet": [id_outlet], "id_product": [id_product],
                                                       "qty": [int(tambah)], "notes": [None]}), "manual", user)
                    errs += e
                if akhir is not None:
                    _, e = upsert_stock(build_snapshot(stock, orow, id_product, produk, tgl, int(akhir)))
                    errs += e
                if errs:
                    st.error("\n".join(errs))
                else:
                    st.success("Data tersimpan. Stok keluar, SPD & DSI sudah diperbarui.")
                    st.session_state["_do_reset"] = True
                    st.rerun()

    # ---------------------------------------------------------- upload Excel
    with t_excel:
        st.markdown("**Langkah:** 1) unduh template → 2) isi (dropdown outlet & SKU dari master) → 3) upload → 4) cek validasi → 5) simpan.")
        st.download_button("⬇️ Unduh Template Sell-in (+ Master Outlet & SKU)", sellin_template(mo, ms, sku_map), "Template_SellIn.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_tpl")
        up = st.file_uploader("Upload file sell-in (.xlsx / .csv)", type=["xlsx", "csv"], key="si_up")
        if up:
            try:
                valid, rejected, warns = clean_sellin(read_any(up, "Template_SellIn"), mo, ms, sku_map)
            except Exception as e:  # noqa: BLE001
                valid, rejected, warns = None, None, [f"Gagal membaca file: {e}"]
            if valid is None:
                st.error(warns[0])
            else:
                for w in warns:
                    st.warning(w)
                m1, m2 = st.columns(2)
                m1.metric("Baris valid", len(valid))
                m2.metric("Baris ditolak", len(rejected))
                if not rejected.empty:
                    st.error("Baris berikut ditolak (periksa penamaan / ID):")
                    st.dataframe(rejected, hide_index=True)
                if not valid.empty:
                    pv = valid.merge(mo[["id_outlet", "outlet"]], on="id_outlet").merge(ms, on="id_product")
                    st.dataframe(pv[["date", "outlet", "product", "qty", "notes"]], hide_index=True, height=260)
                    if st.button("🚀 Simpan ke Database", type="primary", key="si_save_x"):
                        ok, errs = upsert_sellin(valid, "excel", user)
                        if errs:
                            st.error("\n".join(errs))
                        else:
                            st.success(f"{ok} baris tersimpan.")
                            st.rerun()

    # ---------------------------------------------------------- bulk per toko
    with t_bulk:
        k1, k2, k3 = st.columns(3)
        b_tgl = k1.date_input("Tanggal sell-in", date.today(), key="b_tgl", format="DD/MM/YYYY")
        b_acc = k2.selectbox("Account", sorted(mo["account"].unique()), key="b_acc")
        b_outs = mo[mo["account"] == b_acc].sort_values("outlet")
        b_name = k3.selectbox("Toko", b_outs["outlet"].tolist(), key="b_toko")
        b_id = b_outs.loc[b_outs["outlet"] == b_name, "id_outlet"].iloc[0]
        st_b = stock[stock["id_outlet"].astype(str) == b_id]
        sk_b = (ms[ms["id_product"].isin(st_b["id_product"].unique())] if not st_b.empty else ms)
        last = st_b.sort_values("date").groupby("id_product")["total_stock"].last() if not st_b.empty else pd.Series(dtype=float)
        exist = (sellin[(sellin["id_outlet"].astype(str) == b_id) & (sellin["date"] == pd.Timestamp(b_tgl))]
                 .set_index("id_product")["qty"] if not sellin.empty else pd.Series(dtype=int))
        grid = pd.DataFrame({"id_product": sk_b["id_product"].values, "Produk": sk_b["product"].values,
                             "Stok Terakhir": sk_b["id_product"].map(last).fillna(0).astype(int).values,
                             "Sell-in (pcs)": sk_b["id_product"].map(exist).fillna(0).astype(int).values}
                            ).sort_values("Produk").reset_index(drop=True)
        ed = st.data_editor(grid, hide_index=True, key=f"bulk_{b_id}_{b_tgl}", height=min(400, 38 * (len(grid) + 1)),
                            disabled=["id_product", "Produk", "Stok Terakhir"],
                            column_config={"Sell-in (pcs)": st.column_config.NumberColumn(min_value=0, step=1, format="%d"),
                                           "id_product": st.column_config.NumberColumn("ID", format="%d")})
        todo = ed[ed["Sell-in (pcs)"] > 0]
        st.caption(f"{len(todo)} SKU · total {int(todo['Sell-in (pcs)'].sum()):,} pcs. Baris 0 diabaikan; simpan ulang menimpa qty lama.")
        if st.button("💾 Simpan Sell-in", type="primary", disabled=todo.empty, key="bulk_save"):
            ok, errs = upsert_sellin(pd.DataFrame({"date": b_tgl, "id_outlet": b_id, "id_product": todo["id_product"].astype(int),
                                                   "qty": todo["Sell-in (pcs)"].astype(int), "notes": None}), "manual", user)
            if errs:
                st.error("\n".join(errs))
            else:
                st.success(f"{ok} baris tersimpan.")
                st.rerun()

# ================================================================== RIWAYAT CARD
flow = load_flow()
with st.container(key="card-hist"):
    h1, h2 = st.columns([3, 1.4], vertical_alignment="center")
    with h1:
        card_title("Riwayat Catatan Stok & Sinkronisasi Supabase", "Stok awal = snapshot sebelumnya · Keluar = Awal + Tambah − Akhir")
    q = h2.text_input("Cari", placeholder="Cari Toko atau Produk...", label_visibility="collapsed", key="h_q")
    only_si = st.checkbox("Hanya baris yang ada sell-in", key="h_only")
    if flow.empty:
        st.info("Belum ada data.")
    else:
        lo, hi = mtd_range(flow)
        pairs_all = compute_metrics(aggregate_pairs(flow, lo, hi), HARI_BERJALAN_DEFAULT)[KEY + ["status_po"]]
        v = flow.merge(pairs_all, on=KEY, how="left")
        if only_si:
            v = v[v["sell_in"] > 0]
        if q:
            v = v[v["outlet"].str.contains(q, case=False, na=False) | v["product"].str.contains(q, case=False, na=False)]
        v = v.sort_values(["date", "account", "outlet"], ascending=[False, True, True]).head(300).copy()
        v["tgl"] = v["date"].dt.strftime("%d/%m/%Y")
        v["awal"] = v["stok_awal"].fillna(v["total_stock"])
        v["total"] = v["awal"] + v["sell_in"]
        v["status_po"] = v["status_po"].fillna("Kuning - Normal")
        table(v, [("tgl", "TANGGAL", "text"), ("account", "ACCOUNT", "account"), ("outlet", "TOKO", "text"),
                  ("product", "PRODUK", "text"), ("awal", "AWAL", "int"), ("sell_in", "TAMBAH", "int", "blue"),
                  ("total", "TOTAL", "int", "bold"), ("total_stock", "AKHIR", "int"), ("total_keluar", "KELUAR", "int", "red"),
                  ("status_po", "STATUS PO", "status")], max_rows=300,
              note="300 baris terbaru. Status PO berdasarkan DSI periode MTD.")

        pairs_x = compute_metrics(aggregate_pairs(flow, flow["date"].min(), flow["date"].max()), HARI_BERJALAN_DEFAULT)
        a = assign_sellin(sellin, stock) if not sellin.empty else pd.DataFrame()
        sheets = {"Stok Terupdate": summary_table(pairs_x)}
        if not a.empty:
            a = a.merge(mo[["id_outlet", "outlet", "account"]], on="id_outlet", how="left").merge(ms, on="id_product", how="left")
            sheets["Riwayat Sell-in"] = pd.DataFrame({
                "Tanggal": a["date"].dt.strftime("%d/%m/%Y"), "Account": a["account"], "Toko": a["outlet"],
                "Produk": a["product"], "Sell-in": a["qty"], "Sumber": a["source"], "Oleh": a["created_by"]})
        st.download_button("📥 Export Riwayat + Stok Terupdate (.xlsx)", to_excel(sheets), "SellIn_Stok_Terupdate.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", key="hist_dl")

        with st.expander("🗑️ Kelola / hapus data sell-in"):
            if sellin.empty:
                st.caption("Belum ada sell-in.")
            else:
                s = sellin.merge(mo[["id_outlet", "outlet", "account"]], on="id_outlet", how="left").merge(ms, on="id_product", how="left")
                s = s.sort_values("date", ascending=False).head(200)
                grid = pd.DataFrame({"Hapus": False, "id": s["id"], "Tanggal": s["date"].dt.strftime("%d/%m/%Y"),
                                     "Account": s["account"], "Toko": s["outlet"], "Produk": s["product"], "Sell-in": s["qty"],
                                     "Sumber": s["source"]})
                ed = st.data_editor(grid, hide_index=True, key="del_ed", height=300,
                                    disabled=[c for c in grid.columns if c != "Hapus"], column_config={"id": None})
                sel = ed[ed["Hapus"]]
                if st.button(f"Hapus {len(sel)} baris terpilih", disabled=sel.empty, key="del_btn"):
                    delete_sellin(sel["id"].tolist())
                    st.rerun()
