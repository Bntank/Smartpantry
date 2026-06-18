"""Halaman Dashboard — ringkasan stok, prioritas beli, dan keuangan."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import config, db, ml, ui


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.title("📊 Dashboard")
    st.caption(
        f"Ringkasan kebutuhan rumah tangga untuk **{user['username']}** "
        f"({user['persona_type']} · {user['city']})"
    )

    # --- Hitung tabel prioritas (forecasting + klasifikasi) ---
    with st.spinner("Menghitung prediksi prioritas beli..."):
        try:
            prio = ml.build_priority_table(user_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Gagal menghitung prediksi: {exc}")
            prio = pd.DataFrame()

    mf = db.get_monthly_finance(user_id)

    # --- KPI ---
    n_items = len(prio)
    n_segera = int((prio["priority_label"] == "segera_beli").sum()) if not prio.empty else 0
    n_minggu = int((prio["priority_label"] == "beli_minggu_ini").sum()) if not prio.empty else 0

    if not mf.empty:
        last = mf.iloc[-1]
        income_now = float(last["total_income"])
        expense_now = float(last["total_expense"])
    else:
        income_now = float(user["monthly_income"])
        expense_now = 0.0
    sisa = income_now - expense_now

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Item Dipantau", n_items)
    c2.metric("🔴 Segera Beli", n_segera)
    c3.metric("🟠 Beli Minggu Ini", n_minggu)
    c4.metric("Sisa Budget (bln terakhir)", ui.rupiah(sisa))

    st.divider()

    left, right = st.columns([3, 2])

    # --- Daftar prioritas beli ---
    with left:
        st.subheader("🛒 Prioritas Belanja")
        if prio.empty:
            st.info("Belum ada data stok untuk pengguna ini. Tambahkan di menu Input Stok.")
        else:
            disp = pd.DataFrame({
                "Item": prio["item_name"].values,
                "Kategori": prio["category"].values,
                "Perkiraan Habis": pd.to_datetime(prio["estimated_finish_date"]).dt.strftime("%d %b %Y").values,
                "Sisa Hari": prio["sisa_hari"].values,
                "Prioritas": prio["priority_label"].map(config.PRIORITY_LABEL_ID).values,
            })

            color_by_text = {
                config.PRIORITY_LABEL_ID[k]: v for k, v in config.PRIORITY_COLOR.items()
                if k in config.PRIORITY_LABEL_ID
            }

            def _color_row(row):
                c = color_by_text.get(row["Prioritas"], "")
                return [f"background-color: {c}22" if c else ""] * len(row)

            st.dataframe(
                disp.style.apply(_color_row, axis=1).format({"Sisa Hari": "{:.0f}"}),
                width="stretch",
                hide_index=True,
            )

    # --- Keuangan ---
    with right:
        st.subheader("💰 Tren Keuangan")
        if mf.empty:
            st.info("Belum ada data keuangan.")
        else:
            chart_df = mf.set_index("bulan")[["total_income", "total_expense"]]
            chart_df.columns = ["Pemasukan", "Pengeluaran"]
            st.bar_chart(chart_df, color=["#27ae60", "#e74c3c"])

            ym = mf.iloc[-1]["bulan"]
            exp_cat = db.get_expense_by_category(user_id, ym)
            if not exp_cat.empty:
                st.caption(f"Pengeluaran per kategori ({ym})")
                st.bar_chart(exp_cat.set_index("category")["total"], horizontal=True)

    st.divider()

    # --- Notifikasi cepat ---
    st.subheader("🔔 Perlu Perhatian")
    if not prio.empty:
        urgent = prio[prio["priority_label"].isin(["segera_beli", "beli_minggu_ini"])]
        if urgent.empty:
            st.success("Semua stok masih aman. Tidak ada yang perlu segera dibeli. 🎉")
        else:
            for r in urgent.itertuples():
                badge = ui.priority_badge(r.priority_label)
                sisa_txt = f"{int(r.sisa_hari)} hari lagi" if pd.notna(r.sisa_hari) else "segera"
                st.markdown(
                    f"{badge} &nbsp; **{r.item_name}** — perkiraan habis "
                    f"{pd.to_datetime(r.estimated_finish_date):%d %b %Y} ({sisa_txt})",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Tidak ada notifikasi.")
