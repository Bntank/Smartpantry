"""Helper tampilan bersama untuk halaman-halaman Streamlit.

Menyediakan komponen visual premium: KPI card (glassmorphism),
notification card, progress bar stok, badge prioritas modern,
format Rupiah, dan akses user aktif dari session_state.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from . import config, db


# ---------------------------------------------------------------------------
# Format & akses user
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Badge prioritas (modern pill)
# ---------------------------------------------------------------------------
_BADGE_CLASS = {
    "segera_beli": "badge-segera",
    "beli_minggu_ini": "badge-minggu",
    "masih_aman": "badge-aman",
    "habis": "badge-habis",
}


def priority_badge(label: str) -> str:
    """HTML badge berwarna untuk label prioritas (pill style)."""
    css = _BADGE_CLASS.get(label, "badge-aman")
    text = config.PRIORITY_LABEL_ID.get(label, label)
    return f'<span class="badge-urgent {css}">{text}</span>'


# ---------------------------------------------------------------------------
# Pewarnaan baris DataFrame
# ---------------------------------------------------------------------------
def style_priority(df, col: str = "priority_label"):
    """Pewarnaan baris DataFrame berdasarkan label prioritas."""
    def _row_style(row):
        color = config.PRIORITY_COLOR.get(row[col], "")
        if not color:
            return [""] * len(row)
        return [f"background-color: {color}18"] * len(row)

    return df.style.apply(_row_style, axis=1)


# ---------------------------------------------------------------------------
# KPI Card (glassmorphism)
# ---------------------------------------------------------------------------
def kpi_card(
    icon: str,
    label: str,
    value,
    variant: str = "default",
    delta: str = "",
) -> None:
    """Render KPI card bergaya glassmorphism.

    Parameters
    ----------
    icon : emoji atau ikon teks
    label : teks label kecil di bawah angka
    value : angka atau teks utama
    variant : "default" | "danger" | "warning" — menentukan warna gradien
    delta : teks opsional kecil di bawah label
    """
    val_class = "kpi-value"
    if variant == "danger":
        val_class += " danger"
    elif variant == "warning":
        val_class += " warning"
    delta_html = (
        f'<div class="kpi-delta">{delta}</div>' if delta else ""
    )
    st.markdown(
        f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="{val_class}">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Notification card
# ---------------------------------------------------------------------------
_NOTIF_CLASS = {
    "segera_beli": "notif-segera",
    "beli_minggu_ini": "notif-minggu",
    "masih_aman": "notif-aman",
}


def notif_card(
    item_name: str,
    priority: str,
    sisa_hari,
    tanggal: str,
) -> None:
    """Render notification card dengan border-left berwarna."""
    css_class = _NOTIF_CLASS.get(priority, "notif-aman")
    badge = priority_badge(priority)
    sisa_txt = (
        f"{int(sisa_hari)} hari lagi"
        if pd.notna(sisa_hari)
        else "segera"
    )
    st.markdown(
        f"""
    <div class="notif-card {css_class}">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
                <strong style="color:#f1f5f9">{item_name}</strong>
                <span style="color:#64748b;font-size:0.82rem"> · {sisa_txt}</span>
            </div>
            {badge}
        </div>
        <div style="color:#64748b;font-size:0.75rem;margin-top:0.3rem">
            Perkiraan habis {tanggal}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Progress bar stok
# ---------------------------------------------------------------------------
def stock_progress(sisa_hari: float, max_hari: float = 30) -> None:
    """Render mini progress bar berwarna berdasarkan sisa hari."""
    pct = max(0, min(100, (sisa_hari / max_hari) * 100))
    color = (
        "#f43f5e" if pct < 25
        else "#f59e0b" if pct < 50
        else "#14b8a6"
    )
    st.markdown(
        f"""
    <div class="stock-progress">
        <div class="stock-progress-fill"
             style="width:{pct:.0f}%;background:{color}"></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Section header & gradient divider
# ---------------------------------------------------------------------------
def section_header(icon: str, text: str) -> None:
    """Render section header bergradien."""
    st.markdown(
        f"""
    <div class="section-header">
        <span style="display:inline-flex;align-items:center">{icon}</span>
        <span class="section-header-text">{text}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def gradient_divider() -> None:
    """Render gradient divider horizontal."""
    st.markdown('<hr class="gradient-divider">', unsafe_allow_html=True)
