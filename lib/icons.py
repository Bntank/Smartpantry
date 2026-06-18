"""Inline SVG icon system untuk SmartPantry AI.

Semua ikon mengikuti style Lucide/Feather: 24×24 viewBox, 2px stroke,
round linecap/linejoin.  Warna default mengikuti palet Emerald-Slate.

Penggunaan:
    from lib import icons
    st.markdown(icons.icon_package(28, "#10b981"), unsafe_allow_html=True)
"""
from __future__ import annotations


def _svg(path: str, size: int = 24, color: str = "#10b981") -> str:
    """Bungkus path SVG menjadi elemen <svg> inline."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
        f'height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:middle">'
        f"{path}</svg>"
    )


# ─── Inventory ────────────────────────────────────────────────────
def icon_package(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/>'
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4'
        'A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4'
        'A2 2 0 0 0 21 16z"/>'
        '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
        '<line x1="12" y1="22.08" x2="12" y2="12"/>',
        s, c,
    )


def icon_alert_triangle(s: int = 24, c: str = "#f43f5e") -> str:
    return _svg(
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94'
        'a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>',
        s, c,
    )


def icon_clock(s: int = 24, c: str = "#f59e0b") -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>',
        s, c,
    )


def icon_wallet(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/>'
        '<path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/>'
        '<path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/>',
        s, c,
    )


# ─── Navigation / Section ────────────────────────────────────────
def icon_shopping_cart(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<circle cx="9" cy="21" r="1"/>'
        '<circle cx="20" cy="21" r="1"/>'
        '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72'
        'a2 2 0 0 0 2-1.61L23 6H6"/>',
        s, c,
    )


def icon_trending_up(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
        '<polyline points="17 6 23 6 23 12"/>',
        s, c,
    )


def icon_bell(s: int = 24, c: str = "#f59e0b") -> str:
    return _svg(
        '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>'
        '<path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
        s, c,
    )


# ─── Finance ─────────────────────────────────────────────────────
def icon_arrow_up_circle(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="16 12 12 8 8 12"/>'
        '<line x1="12" y1="16" x2="12" y2="8"/>',
        s, c,
    )


def icon_arrow_down_circle(s: int = 24, c: str = "#f43f5e") -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="8 12 12 16 16 12"/>'
        '<line x1="12" y1="8" x2="12" y2="16"/>',
        s, c,
    )


def icon_credit_card(s: int = 24, c: str = "#14b8a6") -> str:
    return _svg(
        '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>'
        '<line x1="1" y1="10" x2="23" y2="10"/>',
        s, c,
    )


def icon_receipt(s: int = 24, c: str = "#94a3b8") -> str:
    return _svg(
        '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2'
        'l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/>'
        '<path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/>',
        s, c,
    )


# ─── AI / Prediction ─────────────────────────────────────────────
def icon_brain(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44'
        " 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58"
        ' 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/>'
        '<path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44'
        " 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58"
        ' 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/>',
        s, c,
    )


def icon_bar_chart(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<line x1="12" y1="20" x2="12" y2="10"/>'
        '<line x1="18" y1="20" x2="18" y2="4"/>'
        '<line x1="6" y1="20" x2="6" y2="16"/>',
        s, c,
    )


def icon_pie_chart(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>'
        '<path d="M22 12A10 10 0 0 0 12 2v10z"/>',
        s, c,
    )


def icon_refresh(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<polyline points="23 4 23 10 17 10"/>'
        '<polyline points="1 20 1 14 7 14"/>'
        '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/>'
        '<path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"/>',
        s, c,
    )


# ─── Status ──────────────────────────────────────────────────────
def icon_check_circle(s: int = 24, c: str = "#10b981") -> str:
    return _svg(
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>',
        s, c,
    )


def icon_hourglass(s: int = 24, c: str = "#f59e0b") -> str:
    return _svg(
        '<path d="M5 22h14"/><path d="M5 2h14"/>'
        '<path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12'
        "l-4.414 4.414A2 2 0 0 0 7 17.828V22\"/>"
        '<path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12'
        'l4.414-4.414A2 2 0 0 0 17 6.172V2"/>',
        s, c,
    )


def icon_user(s: int = 24, c: str = "#94a3b8") -> str:
    return _svg(
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>',
        s, c,
    )


# ─── Priority dot (tiny colored circle for KPI) ──────────────────
def dot(c: str = "#10b981", s: int = 12) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" '
        f'height="{s}" viewBox="0 0 12 12" '
        f'style="display:inline-block;vertical-align:middle">'
        f'<circle cx="6" cy="6" r="5" fill="{c}" opacity="0.9"/>'
        f'<circle cx="6" cy="6" r="3" fill="{c}"/></svg>'
    )
