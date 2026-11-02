"""Login sederhana berbasis st.secrets (tanpa password di dalam kode)."""
import hmac
import streamlit as st
from ui.render import html


def _users() -> dict:
    try:
        return dict(st.secrets["users"])
    except Exception:
        return {}


def _verify(username: str, password: str):
    user = _users().get(username)
    if not user:
        return None
    if hmac.compare_digest(str(user.get("password", "")), password):
        return {"username": username, "name": user.get("name", username), "role": user.get("role", "user")}
    return None


def current_user() -> dict | None:
    return st.session_state.get("user")


def is_admin() -> bool:
    u = current_user()
    return bool(u and u.get("role") == "admin")


def login_screen() -> bool:
    """Tampilkan form login. Return True bila sudah login."""
    if current_user():
        return True

    html("login_header.html")
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if not _users():
            st.error("Belum ada user di secrets. Isi bagian [users.*] di .streamlit/secrets.toml.")
            return False
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            ok = st.form_submit_button("Masuk", type="primary")
        if ok:
            user = _verify(username.strip(), password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            st.error("Username atau password salah.")
    return False


def logout():
    st.session_state.pop("user", None)
    st.cache_data.clear()
    st.rerun()
