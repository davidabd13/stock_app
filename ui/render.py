"""Jembatan HTML/CSS -> Streamlit. Markup di ui/templates/*.html, gaya di ui/static/style.css."""
import base64
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config import STATUS_HIJAU, STATUS_KUNING, STATUS_MERAH

UI_DIR = Path(__file__).parent
_env = Environment(loader=FileSystemLoader(UI_DIR / "templates"), autoescape=select_autoescape(["html"]))
_env.filters["num"] = lambda v: f"{int(round(float(v))):,}".replace(",", ".")
_env.filters["dec"] = lambda v, n=1: f"{float(v):,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September",
         "Oktober", "November", "Desember"]
ACC_TONE = {"TIP TOP": "green", "NAGA": "blue", "HARI HARI": "red"}
PILL = {STATUS_HIJAU: "pill-hijau", STATUS_KUNING: "pill-kuning", STATUS_MERAH: "pill-merah"}


def _compact(text: str) -> str:
    return "\n".join(l.strip() for l in text.splitlines() if l.strip())


# ---- Logo perusahaan: taruh file di  ui/static/logo_uj.png  (atau .jpg/.jpeg/.webp/.svg) ----
_LOGO_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
              ".webp": "image/webp", ".svg": "image/svg+xml"}


def logo_path() -> Path | None:
    """Path file logo bila ada, selain itu None (aplikasi otomatis pakai emoji/ikon bawaan)."""
    for ext in _LOGO_MIME:
        f = UI_DIR / "static" / f"logo_uj{ext}"
        if f.exists():
            return f
    return None


@st.cache_resource
def logo_uri() -> str:
    """Logo sebagai data URI (Streamlit tidak bisa memuat gambar lokal lewat HTML biasa)."""
    f = logo_path()
    if not f:
        return ""
    b64 = base64.b64encode(f.read_bytes()).decode()
    return f"data:{_LOGO_MIME[f.suffix.lower()]};base64,{b64}"


def render(template: str, **ctx) -> str:
    ctx.setdefault("logo", logo_uri())
    return _compact(_env.get_template(template).render(**ctx))


def html(template: str, **ctx):
    st.markdown(render(template, **ctx), unsafe_allow_html=True)


def inject_css():
    css = (UI_DIR / "static" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{_compact(css)}</style>", unsafe_allow_html=True)


def today_id() -> str:
    d = datetime.now()
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"


def card_title(title: str, sub: str = "", icon: str = ""):
    html("card_title.html", title=title, sub=sub, icon=icon)


def kpi_row(items: list[dict]):
    """items: [{label, value, sub?, icon?, tone?, size? ('sm' = kartu kecil)}]"""
    html("kpi_grid.html", items=items)


def acc_tone(account: str) -> str:
    return ACC_TONE.get(str(account).upper(), "slate")


def _fmt(v, kind):
    if kind == "int":
        return f"{int(round(v)):,}".replace(",", ".")
    if kind == "dec2":
        return f"{v:,.2f}".replace(".", ",") if abs(v) < 1000 else f"{v:,.0f}".replace(",", ".")
    if kind == "dsi":
        return f"{v:,.1f} hari".replace(".", ",") if v < 999 else "999+ hari"
    if kind == "dsi_h":
        return f"{v:,.1f}h" if v < 999 else "999h"
    return "" if pd.isna(v) else str(v)


def table(df: pd.DataFrame, spec: list[tuple], max_rows: int = 500, note: str | None = None):
    """Tabel bergaya contoh. spec: [(kolom_df, label, jenis, kelas_css?)].
    jenis: text | int | dec2 | dsi | dsi_h | status | account"""
    if df.empty:
        st.info("Tidak ada data untuk ditampilkan.")
        return
    shown = df.head(max_rows)
    cols = [{"label": s[1], "align": "r" if s[2] in ("int", "dec2", "dsi", "dsi_h") else ("c" if s[2] in ("status", "account") else "")}
            for s in spec]
    rows = []
    for rec in shown.to_dict("records"):
        row = []
        for s in spec:
            v, kind, cls = rec[s[0]], s[2], (s[3] if len(s) > 3 else "")
            if kind == "status":
                row.append({"text": str(v).split(" - ")[-1] if False else str(v), "pill": PILL.get(v, "pill-kuning"), "cls": "c"})
            elif kind == "account":
                row.append({"text": v, "pill": f"pa pa-{acc_tone(v)}", "cls": "c"})
            else:
                row.append({"text": _fmt(v, kind), "cls": ("r " if kind in ("int", "dec2", "dsi", "dsi_h") else "") + cls})
        rows.append(row)
    extra = f"Menampilkan {len(shown):,} dari {len(df):,} baris. " if len(df) > max_rows else ""
    html("data_table.html", cols=cols, rows=rows, note=(extra + (note or "")).strip())
