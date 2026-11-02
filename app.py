"""Entry point:  streamlit run app.py"""
import streamlit as st

from core.auth import current_user, is_admin, login_screen, logout
from core.config import APP_TITLE
from ui.render import html, inject_css, logo_path, today_id

st.set_page_config(page_title=APP_TITLE, page_icon=str(logo_path()) if logo_path() else "📦", layout="wide", initial_sidebar_state="collapsed")
inject_css()

if not login_screen():
    st.stop()

pages = [
    st.Page("pages_views/dashboard.py", title="Dashboard Utama", icon="🏠", default=True),
    st.Page("pages_views/input_sellin.py", title="Input & Update Stok", icon="📝"),
    st.Page("pages_views/report.py", title="Report & Analisa", icon="📈"),
    st.Page("pages_views/mtd.py", title="Analisa MTD & Master Data", icon="🗓️"),
]
if is_admin():
    pages.append(st.Page("pages_views/upload_stock.py", title="Upload Stock (Admin)", icon="📦"))

nav = st.navigation(pages, position="top")

c1, c2, c3, c4 = st.columns([5, 2.4, 0.6, 1.1], vertical_alignment="center")
with c1:
    html("header.html", today=today_id())
with c2:
    html("conn_pill.html", ok=True)
with c3:
    if st.button("🔄", key="btn_refresh", help="Muat ulang data dari Supabase"):
        st.cache_data.clear()
        st.rerun()
with c4:
    if st.button("🚪 Keluar", key="btn_logout", help=f"Login sebagai {current_user()['name']}"):
        logout()

nav.run()
