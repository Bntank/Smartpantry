"""Custom CSS untuk tampilan premium SmartPantry AI.

Menyuntikkan stylesheet global: Google Fonts Inter, glassmorphism card,
badge prioritas modern, notification card, progress bar stok, section
header gradient, dan gradient divider. Dipanggil sekali di app.py.
"""
import streamlit as st


def inject_global_css() -> None:
    """Inject CSS global ke halaman Streamlit aktif."""
    st.markdown(
        """
    <style>
    /* ── Google Fonts ─────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Gunakan Inter tanpa menimpa Material Icons bawaan Streamlit */
    html, body {
        font-family: 'Inter', sans-serif;
    }
    
    /* Batasi tinggi gambar utama (seperti hero image) */
    [data-testid="stImage"] img {
        max-height: 280px;
        object-fit: cover;
        border-radius: 12px;
    }

    /* ── Penyesuaian Ruang Kosong (Spacing) ───────────────────────── */
    /* Mengurangi jarak kosong berlebih bawaan Streamlit di bagian atas */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 72rem; /* Menjaga lebar optimal keterbacaan */
    }

    /* ── KPI Card (glassmorphism) ─────────────────────────────────── */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid rgba(16, 185, 129, 0.15);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.12);
    }
    .kpi-icon  { font-size: 2rem; margin-bottom: 0.3rem; }
    .kpi-value {
        font-size: 1.75rem; font-weight: 700;
        background: linear-gradient(90deg, #10b981, #14b8a6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-value.danger {
        background: linear-gradient(90deg, #f43f5e, #fb7185);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-value.warning {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-label {
        font-size: 0.78rem; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 0.05em;
        margin-top: 0.15rem;
    }
    .kpi-delta {
        font-size: 0.72rem; color: #64748b;
        margin-top: 0.25rem;
    }

    /* ── Badge prioritas modern ───────────────────────────────────── */
    .badge-urgent {
        display: inline-flex; align-items: center; gap: 0.35rem;
        padding: 0.3rem 0.85rem; border-radius: 999px;
        font-size: 0.76rem; font-weight: 600;
        white-space: nowrap;
    }
    .badge-segera  { background: rgba(244,63,94,0.12); color: #f43f5e; border: 1px solid rgba(244,63,94,0.25); }
    .badge-minggu  { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); }
    .badge-aman    { background: rgba(20,184,166,0.12);  color: #14b8a6; border: 1px solid rgba(20,184,166,0.25); }
    .badge-habis   { background: rgba(153,27,27,0.15);   color: #fca5a5; border: 1px solid rgba(153,27,27,0.3); }

    /* ── Notification card ────────────────────────────────────────── */
    .notif-card {
        background: #1e293b;
        border-left: 4px solid;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.6rem;
        transition: background 0.2s ease;
    }
    .notif-card:hover { background: #263347; }
    .notif-segera { border-left-color: #f43f5e; }
    .notif-minggu { border-left-color: #f59e0b; }
    .notif-aman   { border-left-color: #14b8a6; }

    /* ── Progress bar stok ────────────────────────────────────────── */
    .stock-progress {
        height: 6px; border-radius: 3px;
        background: #334155; overflow: hidden;
        margin-top: 0.25rem;
    }
    .stock-progress-fill {
        height: 100%; border-radius: 3px;
        transition: width 0.6s ease;
    }

    /* ── Section header gradient ──────────────────────────────────── */
    .section-header {
        display: flex; align-items: center; gap: 0.5rem;
        margin: 1rem 0 0.5rem;
    }
    .section-header-text {
        margin: 0; font-weight: 600; font-size: 1.15rem;
        background: linear-gradient(90deg, #f1f5f9, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ── Gradient divider ─────────────────────────────────────────── */
    .gradient-divider {
        height: 1px; border: none; margin: 1.5rem 0;
        background: linear-gradient(90deg,
            transparent, rgba(16,185,129,0.3) 20%,
            rgba(16,185,129,0.3) 80%, transparent);
    }

    /* ── Sidebar branding ─────────────────────────────────────────── */
    .sidebar-brand {
        text-align: center; padding: 1rem 0 0.5rem;
    }
    .sidebar-brand-icon { font-size: 2.5rem; }
    .sidebar-brand-title {
        margin: 0; font-weight: 700; font-size: 1.4rem;
        background: linear-gradient(90deg, #10b981, #14b8a6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-brand-sub {
        color: #64748b; font-size: 0.78rem; margin-top: 0.15rem;
    }

    /* ── Status dot ───────────────────────────────────────────────── */
    .status-dot {
        display: inline-block; width: 8px; height: 8px;
        border-radius: 50%; margin-right: 6px;
    }
    .status-dot.online  { background: #10b981; box-shadow: 0 0 6px #10b981; }
    .status-dot.offline { background: #f43f5e; box-shadow: 0 0 6px #f43f5e; }
    </style>
    """,
        unsafe_allow_html=True,
    )
