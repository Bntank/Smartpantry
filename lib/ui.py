"""Helper tampilan bersama untuk halaman-halaman Streamlit."""
from __future__ import annotations

import streamlit as st

from . import config, db


def rupiah(value) -> str:
    """Format angka menjadi string Rupiah (Rp1.234.567)."""
    try:
        return "Rp" + f"{float(value):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp0"


def current_user_id() -> int:
    """Mengambil user aktif dari session_state; hentikan halaman bila kosong."""
    uid = st.session_state.get("user_id")
    if uid is None:
        st.warning("Silakan pilih pengguna pada sidebar terlebih dahulu.")
        st.stop()
    return int(uid)


def current_user():
    user = db.get_user(current_user_id())
    if user is None:
        st.warning("Data pengguna tidak ditemukan.")
        st.stop()
    return user


def priority_badge(label: str) -> str:
    """HTML badge berwarna untuk label prioritas."""
    color = config.PRIORITY_COLOR.get(label, "#95a5a6")
    text = config.PRIORITY_LABEL_ID.get(label, label)
    return (
        f"<span style='background:{color};color:white;padding:3px 10px;"
        f"border-radius:12px;font-size:0.8rem;font-weight:600;'>{text}</span>"
    )


def style_priority(df, col: str = "priority_label"):
    """Pewarnaan baris DataFrame berdasarkan label prioritas."""
    def _row_style(row):
        color = config.PRIORITY_COLOR.get(row[col], "")
        if not color:
            return [""] * len(row)
        return [f"background-color: {color}22"] * len(row)

    return df.style.apply(_row_style, axis=1)
