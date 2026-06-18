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
from views import dashboard, input_stok, input_keuangan, prediksi, retraining

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def _sidebar_user_selector() -> None:
    """Pemilih user aktif (dipakai semua halaman lewat session_state)."""
    with st.sidebar:
        st.title(f"{config.APP_ICON} {config.APP_TITLE}")
        st.caption("Sistem Prediksi & Manajemen Kebutuhan Rumah Tangga")
        st.divider()

        if not db.ping():
            st.error("Gagal terhubung ke database. Periksa file .env.")
            st.stop()

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
            "👤 Pilih Pengguna",
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
        st.Page(dashboard.render, title="Dashboard", icon="📊",
                url_path="dashboard", default=True),
        st.Page(input_stok.render, title="Input Stok", icon="📦",
                url_path="input-stok"),
        st.Page(input_keuangan.render, title="Input Keuangan", icon="💰",
                url_path="input-keuangan"),
        st.Page(prediksi.render, title="Prediksi & Alert", icon="🔔",
                url_path="prediksi-alert"),
        st.Page(retraining.render, title="Retraining Model", icon="🤖",
                url_path="retraining"),
    ]
    nav = st.navigation(pages, position="sidebar")

    with st.sidebar:
        st.divider()
        st.caption("Capstone CAMP Batch 4 · Data Science & GenAI")

    nav.run()


if __name__ == "__main__":
    main()
