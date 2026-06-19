"""Halaman Input Keuangan — mencatat pemasukan & pengeluaran.

Redesign: KPI card glassmorphism, Plotly charts, gradient dividers.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from lib import config, db, icons, ui


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.markdown(
        """
    <h1 style="margin:0;font-weight:700;
        background:linear-gradient(90deg,#10b981,#14b8a6);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent">
        Input Keuangan
    </h1>
    <p style="color:#64748b;font-size:0.85rem;margin-top:0.15rem">
        Catat pemasukan &amp; pengeluaran untuk analisis prioritas belanja.
    </p>
    """,
        unsafe_allow_html=True,
    )

    with st.form("form_keuangan", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ttype = st.radio(
                "Jenis Transaksi",
                ["expense", "income"],
                format_func=lambda x: "Pengeluaran"
                if x == "expense"
                else "Pemasukan",
                horizontal=True,
            )
            log_date = st.date_input("Tanggal", value=date.today())
            amount = st.number_input(
                "Jumlah (Rp)", min_value=0.0, value=0.0, step=1000.0
            )
        with col2:
            categories = (
                config.EXPENSE_CATEGORIES
                if ttype == "expense"
                else config.INCOME_CATEGORIES
            )
            category = st.selectbox("Kategori", categories, format_func=lambda x: x.replace('_', ' ').title())
            description = st.text_area("Deskripsi (opsional)")

        submitted = st.form_submit_button(
            "Simpan Transaksi", type="primary"
        )

    if submitted:
        if amount <= 0:
            st.warning("Jumlah harus lebih besar dari 0.")
        else:
            try:
                db.insert_finance(
                    user_id=user_id,
                    log_date=log_date,
                    transaction_type=ttype,
                    amount=amount,
                    category=category,
                    description=description or None,
                )
                label = "Pemasukan" if ttype == "income" else "Pengeluaran"
                st.success(
                    f"{label} {ui.rupiah(amount)} ({category}) tersimpan."
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal menyimpan: {exc}")

    ui.gradient_divider()

    # ── Ringkasan bulanan ────────────────────────────────────────
    mf = db.get_monthly_finance(user_id)
    if not mf.empty:
        last = mf.iloc[-1]
        income_val = float(last["total_income"])
        expense_val = float(last["total_expense"])
        saldo = income_val - expense_val

        c1, c2, c3 = st.columns(3)
        with c1:
            ui.kpi_card(
                icons.icon_arrow_up_circle(28), f"Pemasukan ({last['bulan']})", ui.rupiah(income_val)
            )
        with c2:
            ui.kpi_card(
                icons.icon_arrow_down_circle(28),
                f"Pengeluaran ({last['bulan']})",
                ui.rupiah(expense_val),
                variant="danger",
            )
        with c3:
            ui.kpi_card(icons.icon_credit_card(28), "Saldo Bersih", ui.rupiah(saldo))

        st.markdown("<br>", unsafe_allow_html=True)

        fig = px.bar(
            mf,
            x="bulan",
            y=["total_income", "total_expense"],
            barmode="group",
            color_discrete_map={
                "total_income": "#10b981",
                "total_expense": "#f43f5e",
            },
            labels={
                "value": "Rupiah",
                "bulan": "Bulan",
                "variable": "Tipe",
            },
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94a3b8"),
            legend_title_text="",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#334155"),
        )
        for trace in fig.data:
            if trace.name == "total_income":
                trace.name = "Pemasukan"
            elif trace.name == "total_expense":
                trace.name = "Pengeluaran"
        st.plotly_chart(fig, use_container_width=True)

    # ── Transaksi terbaru ────────────────────────────────────────
    ui.section_header(icons.icon_receipt(24), "Transaksi Terbaru")
    recent = db.get_recent_finance(user_id, limit=15)
    if recent.empty:
        st.info("Belum ada transaksi tercatat.")
    else:
        disp = recent.copy()
        disp["log_date"] = pd.to_datetime(disp["log_date"]).dt.strftime(
            "%d %b %Y"
        )
        disp["transaction_type"] = disp["transaction_type"].map(
            {"income": "Pemasukan", "expense": "Pengeluaran"}
        )
        disp["category"] = disp["category"].str.replace('_', ' ').str.title()
        disp = disp.rename(
            columns={
                "log_date": "Tanggal",
                "transaction_type": "Jenis",
                "amount": "Jumlah",
                "category": "Kategori",
                "description": "Deskripsi",
            }
        )
        st.dataframe(
            disp,
            width="stretch",
            hide_index=True,
            column_config={
                "Jumlah": st.column_config.NumberColumn(format="Rp%d")
            },
        )
