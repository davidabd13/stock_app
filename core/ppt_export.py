"""Export dashboard ke PowerPoint (python-pptx, grafik native & bisa diedit)."""
from io import BytesIO

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from core.calculations import rollup
from core.config import STATUS_COLORS, STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH

NAVY, BLUE, INK, SLATE, LINE = "0B1220", "2563EB", "0F172A", "64748B", "E2E8F0"
n = lambda v: f"{int(round(v)):,}".replace(",", ".")  # noqa: E731


def _rgb(h):
    return RGBColor.from_string(h.lstrip("#").upper())


def _text(slide, x, y, w, h, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = str(text)
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, _rgb(color), "Calibri"
    return tb


def _card(slide, x, y, w, h, fill="FFFFFF", line=LINE):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = _rgb(fill)
    s.line.color.rgb = _rgb(line)
    s.shadow.inherit = False
    return s


def _slide(prs, title, subtitle=""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = _rgb("F1F5F9")
    _text(s, 0.6, 0.35, 12, 0.6, title, 26, True)
    if subtitle:
        _text(s, 0.6, 0.95, 12, 0.4, subtitle, 12, color=SLATE)
    return s


def _table(slide, header, rows, x, y, w, col_w, row_h=0.36, size=11, status_col=None):
    shape = slide.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(w), Inches(row_h * (len(rows) + 1)))
    t = shape.table
    for i, cw in enumerate(col_w):
        t.columns[i].width = Inches(cw)
    for j, h in enumerate(header):
        c = t.cell(0, j)
        c.fill.solid()
        c.fill.fore_color.rgb = _rgb(NAVY)
        c.text = h
        para = c.text_frame.paragraphs[0]
        para.font.size, para.font.bold, para.font.color.rgb = Pt(size), True, _rgb("FFFFFF")
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            c = t.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = _rgb("EFF6FF" if i % 2 else "F0FDF4")
            c.text = str(v)
            para = c.text_frame.paragraphs[0]
            para.font.size, para.font.color.rgb = Pt(size), _rgb(INK)
            if j >= 1 and str(v).replace(".", "").replace(",", "").replace(" hari", "").isdigit():
                para.alignment = PP_ALIGN.RIGHT
            if status_col is not None and j == status_col and v in STATUS_COLORS:
                c.fill.fore_color.rgb = _rgb(STATUS_COLORS[v])
                para.font.color.rgb, para.font.bold = _rgb("FFFFFF"), True
    return t


def build_dashboard_ppt(pairs, flow_f, f) -> bytes:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    periode = f"{f.start:%d %b %Y} – {f.end:%d %b %Y}"

    # 1. Judul
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = _rgb(NAVY)
    _text(s, 0.8, 2.5, 11.5, 1, "Stock Dashboard & Analysis", 40, True, "FFFFFF")
    _text(s, 0.8, 3.5, 11.5, 0.5, "PT Ultrajaya Inventory System", 18, color="93C5FD")
    _text(s, 0.8, 4.1, 11.5, 0.5, f"Periode {periode} · SPD = Total Keluar / {f.hari} hari", 14, color="CBD5E1")

    # 2. KPI
    s = _slide(prs, "Ringkasan Eksekutif", periode)
    awal, tambah, akhir = pairs["stok_awal"].sum(), pairs["stok_tambahan"].sum(), pairs["stok_akhir"].sum()
    kpis = [("Total Account", pairs["account"].nunique(), INK), ("Total SKU Produk", pairs["product"].nunique(), INK),
            ("Total Toko", pairs["outlet"].nunique(), INK), ("Total Stok Keluar", n(pairs["total_keluar"].sum()), "E11D48"),
            ("Total Stok Awal", n(awal), INK), ("Total Stok Tambah (Sell-in)", n(tambah), BLUE),
            ("Total Stok (Awal+Tambah)", n(awal + tambah), BLUE), ("Total Stok Akhir", n(akhir), "059669")]
    for i, (lab, val, col) in enumerate(kpis):
        x, y = 0.6 + (i % 4) * 3.1, 1.7 + (i // 4) * 2.3
        _card(s, x, y, 2.9, 2.0)
        _text(s, x + 0.2, y + 0.3, 2.5, 0.4, lab.upper(), 11, True, SLATE)
        _text(s, x + 0.2, y + 0.8, 2.5, 0.9, val, 34, True, col)

    # 3. Grafik
    s = _slide(prs, "Distribusi Stok Keluar & Status PO", periode)
    acc = rollup(pairs, ["account"], f.hari)
    cd = CategoryChartData()
    cd.categories = list(acc["account"])
    cd.add_series("Total Stok Keluar", [int(v) for v in acc["total_keluar"]])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.6), Inches(6.2), Inches(5.3), cd)
    ch = gf.chart
    ch.has_legend, ch.legend.position, ch.legend.include_in_layout = True, XL_LEGEND_POSITION.TOP, False
    ch.plots[0].series[0].format.fill.solid()
    ch.plots[0].series[0].format.fill.fore_color.rgb = _rgb("10B981")
    ch.plots[0].has_data_labels = True
    ch.plots[0].data_labels.font.size = Pt(11)
    stt = pairs["status_po"].value_counts()
    cd2 = CategoryChartData()
    order = [x for x in (STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH) if x in stt.index]
    cd2.categories = order
    cd2.add_series("Jumlah toko-SKU", [int(stt[x]) for x in order])
    gf2 = s.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Inches(7.1), Inches(1.6), Inches(5.6), Inches(5.3), cd2)
    c2 = gf2.chart
    c2.has_legend, c2.legend.position, c2.legend.include_in_layout = True, XL_LEGEND_POSITION.BOTTOM, False
    c2.plots[0].has_data_labels = True
    for i, name in enumerate(order):
        pt = c2.plots[0].series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = _rgb(STATUS_COLORS[name])

    # 4. Tabel account
    s = _slide(prs, "Analisa DSI per Account", f"SPD = Total Keluar / {f.hari} hari · DSI = Stok Akhir / SPD")
    cnt = pairs.groupby(["account", "status_po"]).size().unstack(fill_value=0)
    rows = []
    for r in acc.itertuples():
        c = cnt.loc[r.account] if r.account in cnt.index else {}
        rows.append([r.account, n(r.stok_akhir), n(r.total_keluar), f"{r.spd:,.1f}", f"{r.dsi:,.1f} hari", r.status_po,
                     int(c.get(STATUS_HIJAU, 0)), int(c.get(STATUS_KUNING, 0)), int(c.get(STATUS_MERAH, 0))])
    _table(s, ["Account", "Stok Akhir", "Total Keluar", "SPD", "DSI", "Status PO", "# Hijau", "# Kuning", "# Merah"], rows,
           0.6, 1.7, 12.1, [1.8, 1.4, 1.4, 1.1, 1.4, 2.2, 0.9, 1.0, 0.9], row_h=0.5, size=13, status_col=5)

    # 5. Prioritas Manage PO
    s = _slide(prs, "Prioritas Manage PO", "10 toko-SKU berstatus Merah dengan stok akhir terbanyak")
    m = pairs[pairs["status_po"] == STATUS_MERAH].nlargest(10, "stok_akhir")
    rows = [[r.account, r.outlet, r.product, n(r.stok_akhir), n(r.total_keluar), f"{r.dsi:,.1f} hari"] for r in m.itertuples()]
    if rows:
        _table(s, ["Account", "Toko", "Produk", "Stok Akhir", "Keluar", "DSI"], rows, 0.6, 1.6, 12.1,
               [1.4, 2.9, 4.0, 1.3, 1.1, 1.4], row_h=0.42, size=11)
    else:
        _text(s, 0.6, 2, 12, 1, "Tidak ada toko-SKU berstatus Merah pada periode ini 🎉", 18, color=SLATE)

    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()
