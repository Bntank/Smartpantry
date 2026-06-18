"""SmartPantry AI — Aplikasi Streamlit multi-page.

Menjalankan: streamlit run app.py

Halaman:
- Dashboard         : ringkasan stok, prioritas beli, dan kondisi keuangan.
- Input Stok        : catat pembelian barang (otomatis prediksi tanggal habis).
- Input Keuangan    : catat pemasukan & pengeluaran.
- Prediksi & Alert  : prediksi prioritas beli + kelola notifikasi.
- Retraining Model  : latih ulang model dari data terbaru + riwayat performa.
"""
import streamlit as st

from lib import config, db
from lib.styles import inject_global_css
from views import dashboard, input_stok, input_keuangan, prediksi, retraining

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS global (font Inter, glassmorphism cards, badges, dll.)
inject_global_css()


def _sidebar_user_selector() -> None:
    """Pemilih user aktif (dipakai semua halaman lewat session_state)."""
    with st.sidebar:
        # ── Branding visual ──────────────────────────────────────
        st.image("assets/sidebar_logo.png", use_container_width=True)
        st.divider()

        # ── Status koneksi DB ────────────────────────────────────
        if db.ping():
            st.markdown(
                '<span class="status-dot online"></span> Database terhubung',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-dot offline"></span> Database terputus '
                "— periksa file .env",
                unsafe_allow_html=True,
            )
            st.stop()

        st.divider()

        # ── Pemilih pengguna ─────────────────────────────────────
        try:
            users = db.get_users()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Gagal memuat data user: {exc}")
            st.stop()

        if users.empty:
            st.warning("Belum ada user pada database.")
            st.stop()

        options = users["user_id"].tolist()
        labels = {
            r.user_id: f"{r.username} · {r.city}" for r in users.itertuples()
        }
        default_idx = options.index(st.session_state["user_id"]) if \
            st.session_state.get("user_id") in options else 0

        selected = st.selectbox(
            "Pilih Pengguna",
            options=options,
            index=default_idx,
            format_func=lambda uid: labels.get(uid, str(uid)),
        )
        st.session_state["user_id"] = selected

        user = db.get_user(selected)
        if user is not None:
            st.markdown(
                f"**Persona:** {user['persona_type']}  \n"
                f"**Pemasukan/bln:** Rp{float(user['monthly_income']):,.0f}".replace(",", ".")
            )
        st.divider()


def main() -> None:
    _sidebar_user_selector()

    pages = [
        st.Page(dashboard.render, title="Dashboard", icon=":material/dashboard:",
                url_path="dashboard", default=True),
        st.Page(input_stok.render, title="Input Stok", icon=":material/inventory_2:",
                url_path="input-stok"),
        st.Page(input_keuangan.render, title="Input Keuangan", icon=":material/account_balance_wallet:",
                url_path="input-keuangan"),
        st.Page(prediksi.render, title="Prediksi & Alert", icon=":material/notifications:",
                url_path="prediksi-alert"),
        st.Page(retraining.render, title="Retraining Model", icon=":material/model_training:",
                url_path="retraining"),
    ]
    nav = st.navigation(pages, position="sidebar")

    with st.sidebar:
        st.divider()
        st.caption("Capstone CAMP Batch 4 · Data Science & GenAI")

    nav.run()


if __name__ == "__main__":
    main()
