"""Halaman Dashboard — ringkasan stok, prioritas beli, dan keuangan.

Redesign: hero greeting, KPI card glassmorphism, notification card,
Plotly charts, dan progress bar stok. Logika data tidak diubah.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from lib import config, db, icons, ml, ui


def _greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Selamat Pagi"
    if h < 17:
        return "Selamat Siang"
    return "Selamat Malam"


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    # ── Hero greeting ────────────────────────────────────────────
    now = datetime.now()
    
    # Render hero image, ukurannya akan dibatasi oleh CSS global di styles.py
    st.image("assets/hero_dashboard.png", use_container_width=True)
    st.markdown(
        f"""
    <div style="padding:0.5rem 0 0.25rem">
        <span style="font-size:0.88rem;color:#94a3b8">
            {_greeting()}, {user['username']}
        </span>
        <h1 style="margin:0;font-weight:700;font-size:2rem;
            background:linear-gradient(90deg,#10b981,#14b8a6);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent">
            SmartPantry Dashboard
        </h1>
        <p style="color:#64748b;margin-top:0.15rem;font-size:0.85rem">
            {user['persona_type']} · {user['city']} · {now:%d %b %Y}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Hitung tabel prioritas (forecasting + klasifikasi) ───────
    with st.spinner("AI sedang menganalisis pola konsumsi..."):
        try:
            prio = ml.build_priority_table(user_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Gagal menghitung prediksi: {exc}")
            prio = pd.DataFrame()

    mf = db.get_monthly_finance(user_id)

    # ── KPI ──────────────────────────────────────────────────────
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
    with c1:
        ui.kpi_card(icons.icon_package(28), "Item Dipantau", n_items)
    with c2:
        ui.kpi_card(icons.icon_alert_triangle(28), "Segera Beli", n_segera, variant="danger")
    with c3:
        ui.kpi_card(icons.icon_clock(28), "Beli Minggu Ini", n_minggu, variant="warning")
    with c4:
        ui.kpi_card(icons.icon_wallet(28), "Sisa Budget", ui.rupiah(sisa),
                    delta="bulan terakhir")

    ui.gradient_divider()

    # ── Konten utama: Prioritas + Keuangan ───────────────────────
    left, right = st.columns([3, 2])

    # ---- Daftar prioritas beli ----
    with left:
        ui.section_header(icons.icon_shopping_cart(24), "Prioritas Belanja")
        if prio.empty:
            st.info(
                "Belum ada data stok untuk pengguna ini. "
                "Tambahkan di menu **Input Stok**."
            )
        else:
            disp = pd.DataFrame(
                {
                    "Item": prio["item_name"].values,
                    "Kategori": prio["category"].values,
                    "Perkiraan Habis": pd.to_datetime(
                        prio["estimated_finish_date"]
                    )
                    .dt.strftime("%d %b %Y")
                    .values,
                    "Sisa Hari": prio["sisa_hari"].values,
                    "Prioritas": prio["priority_label"]
                    .map(config.PRIORITY_LABEL_ID)
                    .values,
                }
            )

            color_by_text = {
                config.PRIORITY_LABEL_ID[k]: v
                for k, v in config.PRIORITY_COLOR.items()
                if k in config.PRIORITY_LABEL_ID
            }

            def _color_row(row):
                c = color_by_text.get(row["Prioritas"], "")
                return [f"background-color: {c}18" if c else ""] * len(row)

            st.dataframe(
                disp.style.apply(_color_row, axis=1).format(
                    {"Sisa Hari": "{:.0f}"}
                ),
                width="stretch",
                hide_index=True,
                column_config={
                    "Sisa Hari": st.column_config.ProgressColumn(
                        "Sisa Hari",
                        min_value=0,
                        max_value=30,
                        format="%d hari",
                    ),
                },
            )

    # ---- Keuangan ----
    with right:
        ui.section_header(icons.icon_trending_up(24), "Tren Keuangan")
        if mf.empty:
            st.info("Belum ada data keuangan.")
        else:
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
            # Rename traces for display
            for trace in fig.data:
                if trace.name == "total_income":
                    trace.name = "Pemasukan"
                elif trace.name == "total_expense":
                    trace.name = "Pengeluaran"
            st.plotly_chart(fig, use_container_width=True)

            ym = mf.iloc[-1]["bulan"]
            exp_cat = db.get_expense_by_category(user_id, ym)
            if not exp_cat.empty:
                st.caption(f"Pengeluaran per kategori ({ym})")
                fig2 = px.bar(
                    exp_cat,
                    x="total",
                    y="category",
                    orientation="h",
                    color_discrete_sequence=["#f59e0b"],
                    labels={"total": "Rupiah", "category": ""},
                )
                fig2.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#94a3b8"),
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig2, use_container_width=True)

    ui.gradient_divider()

    # ── Notifikasi cepat ─────────────────────────────────────────
    ui.section_header(icons.icon_bell(24), "Perlu Perhatian")
    if not prio.empty:
        urgent = prio[
            prio["priority_label"].isin(["segera_beli", "beli_minggu_ini"])
        ]
        if urgent.empty:
            st.success(
                "Semua stok masih aman. Tidak ada yang perlu segera dibeli."
            )
        else:
            for r in urgent.itertuples():
                ui.notif_card(
                    item_name=r.item_name,
                    priority=r.priority_label,
                    sisa_hari=r.sisa_hari,
                    tanggal=pd.to_datetime(r.estimated_finish_date).strftime(
                        "%d %b %Y"
                    ),
                )
    else:
        st.info("Tidak ada notifikasi.")
