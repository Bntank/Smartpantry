"""Halaman Input Keuangan — mencatat pemasukan & pengeluaran."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from lib import config, db, ui


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.title("💰 Input Keuangan")
    st.caption("Catat pemasukan & pengeluaran untuk analisis prioritas belanja.")

    with st.form("form_keuangan", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ttype = st.radio("Jenis Transaksi", ["expense", "income"],
                             format_func=lambda x: "Pengeluaran" if x == "expense" else "Pemasukan",
                             horizontal=True)
            log_date = st.date_input("Tanggal", value=date.today())
            amount = st.number_input("Jumlah (Rp)", min_value=0.0, value=0.0, step=1000.0)
        with col2:
            categories = (config.EXPENSE_CATEGORIES if ttype == "expense"
                          else config.INCOME_CATEGORIES)
            category = st.selectbox("Kategori", categories)
            description = st.text_area("Deskripsi (opsional)")

        submitted = st.form_submit_button("💾 Simpan Transaksi", type="primary")

    if submitted:
        if amount <= 0:
            st.warning("Jumlah harus lebih besar dari 0.")
        else:
            try:
                db.insert_finance(
                    user_id=user_id, log_date=log_date, transaction_type=ttype,
                    amount=amount, category=category, description=description or None,
                )
                label = "Pemasukan" if ttype == "income" else "Pengeluaran"
                st.success(f"{label} {ui.rupiah(amount)} ({category}) tersimpan.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal menyimpan: {exc}")

    st.divider()

    # Ringkasan bulanan
    mf = db.get_monthly_finance(user_id)
    if not mf.empty:
        last = mf.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Pemasukan ({last['bulan']})", ui.rupiah(last["total_income"]))
        c2.metric(f"Pengeluaran ({last['bulan']})", ui.rupiah(last["total_expense"]))
        c3.metric("Saldo Bersih", ui.rupiah(last["total_income"] - last["total_expense"]))

        chart_df = mf.set_index("bulan")[["total_income", "total_expense"]]
        chart_df.columns = ["Pemasukan", "Pengeluaran"]
        st.bar_chart(chart_df, color=["#27ae60", "#e74c3c"])

    st.subheader("🧾 Transaksi Terbaru")
    recent = db.get_recent_finance(user_id, limit=15)
    if recent.empty:
        st.info("Belum ada transaksi tercatat.")
    else:
        disp = recent.copy()
        disp["log_date"] = pd.to_datetime(disp["log_date"]).dt.strftime("%d %b %Y")
        disp["transaction_type"] = disp["transaction_type"].map(
            {"income": "Pemasukan", "expense": "Pengeluaran"}
        )
        disp = disp.rename(columns={
            "log_date": "Tanggal",
            "transaction_type": "Jenis",
            "amount": "Jumlah",
            "category": "Kategori",
            "description": "Deskripsi",
        })
        st.dataframe(
            disp, width="stretch", hide_index=True,
            column_config={"Jumlah": st.column_config.NumberColumn(format="Rp%d")},
        )
