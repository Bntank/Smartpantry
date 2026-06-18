"""Halaman Prediksi & Alert.

Redesign: gradient title, notification card, modernized badge, section
headers, Plotly donut chart ringkasan, gradient dividers. Logika prediksi
dan alert tidak diubah.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from lib import config, db, icons, ml, ui


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.markdown(
        """
    <h1 style="margin:0;font-weight:700;
        background:linear-gradient(90deg,#10b981,#14b8a6);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent">
        Prediksi &amp; Alert
    </h1>
    <p style="color:#64748b;font-size:0.85rem;margin-top:0.15rem">
        Prioritas beli mempertimbangkan pola konsumsi &amp; kondisi finansial.
    </p>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("AI sedang menganalisis pola konsumsi..."):
        try:
            prio = ml.build_priority_table(user_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Gagal menghitung prediksi: {exc}")
            return

    if prio.empty:
        st.info("Belum ada data stok untuk pengguna ini.")
        return

    tab1, tab2 = st.tabs(["Prediksi Prioritas", "Notifikasi"])

    # ────────────────────────────────────────────────── Tab 1
    with tab1:
        disp = pd.DataFrame(
            {
                "Item": prio["item_name"].values,
                "Kategori": prio["category"].values,
                "Beli Terakhir": pd.to_datetime(prio["purchase_date"])
                .dt.strftime("%d %b %Y")
                .values,
                "Rata² Hari Habis": prio["avg_days_personal"].round(1).values,
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
                {"Sisa Hari": "{:.0f}", "Rata² Hari Habis": "{:.1f}"}
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

        ui.gradient_divider()

        # ── Ringkasan visual ─────────────────────────────────────
        ui.section_header(icons.icon_pie_chart(24), "Ringkasan Prioritas")
        counts = prio["priority_label"].value_counts()

        col_kpi, col_chart = st.columns([1, 1])
        with col_kpi:
            for key in config.PRIORITY_ORDER:
                variant = (
                    "danger"
                    if key == "segera_beli"
                    else "warning"
                    if key == "beli_minggu_ini"
                    else "default"
                )
                ui.kpi_card(
                    icons.dot(config.PRIORITY_COLOR.get(key, "#10b981"), 16),
                    config.PRIORITY_LABEL_ID[key],
                    int(counts.get(key, 0)),
                    variant=variant,
                )
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        with col_chart:
            chart_data = pd.DataFrame(
                {
                    "Prioritas": [
                        config.PRIORITY_LABEL_ID[k]
                        for k in config.PRIORITY_ORDER
                    ],
                    "Jumlah": [
                        int(counts.get(k, 0)) for k in config.PRIORITY_ORDER
                    ],
                }
            )
            chart_data = chart_data[chart_data["Jumlah"] > 0]
            if not chart_data.empty:
                fig = px.pie(
                    chart_data,
                    values="Jumlah",
                    names="Prioritas",
                    hole=0.5,
                    color="Prioritas",
                    color_discrete_map={
                        config.PRIORITY_LABEL_ID[k]: config.PRIORITY_COLOR[k]
                        for k in config.PRIORITY_ORDER
                    },
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#94a3b8"),
                    margin=dict(l=0, r=0, t=10, b=10),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                    ),
                    showlegend=True,
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="value+percent",
                    textfont_size=13,
                )
                st.plotly_chart(fig, use_container_width=True)

    # ────────────────────────────────────────────────── Tab 2
    with tab2:
        urgent = prio[
            prio["priority_label"].isin(["segera_beli", "beli_minggu_ini"])
        ]
        st.write(
            f"Terdapat **{len(urgent)}** item yang perlu perhatian "
            "(segera beli / beli minggu ini)."
        )

        if st.button(
            "Buat & Simpan Notifikasi",
            type="primary",
            disabled=urgent.empty,
        ):
            try:
                for r in urgent.itertuples():
                    sisa = int(r.sisa_hari) if pd.notna(r.sisa_hari) else None
                    db.insert_alert(
                        user_id=user_id,
                        item_id=int(r.item_id),
                        alert_date=date.today(),
                        priority_label=r.priority_label,
                        estimated_days_left=sisa,
                    )
                st.success(
                    f"{len(urgent)} notifikasi tersimpan ke stock_alerts."
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal menyimpan notifikasi: {exc}")

        ui.gradient_divider()

        col_a, col_b = st.columns([3, 1])
        with col_b:
            show_resolved = st.toggle("Tampilkan terselesaikan", value=False)
            if st.button("Tandai semua selesai"):
                db.resolve_all_alerts(user_id)
                st.rerun()

        alerts = db.get_alerts(user_id, only_unresolved=not show_resolved)
        if alerts.empty:
            st.info("Belum ada notifikasi.")
        else:
            for r in alerts.itertuples():
                c1, c2 = st.columns([5, 1])
                with c1:
                    status_icon = icons.icon_check_circle(16) if r.is_resolved else icons.icon_hourglass(16)
                    tanggal = pd.to_datetime(r.alert_date).strftime("%d %b %Y")
                    ui.notif_card(
                        item_name=f"{status_icon} {r.item_name}",
                        priority=r.priority_label,
                        sisa_hari=r.estimated_days_left,
                        tanggal=tanggal,
                    )
                with c2:
                    if not r.is_resolved:
                        if st.button("Selesai", key=f"res_{r.alert_id}"):
                            db.resolve_alert(int(r.alert_id))
                            st.rerun()
