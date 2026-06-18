"""Halaman Prediksi & Alert.

Menampilkan prediksi prioritas beli per item (forecasting + klasifikasi)
serta pengelolaan notifikasi yang disimpan ke tabel stock_alerts.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from lib import config, db, ml, ui


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.title("🔔 Prediksi & Alert")
    st.caption("Prioritas beli mempertimbangkan pola konsumsi & kondisi finansial.")

    with st.spinner("Menghitung prediksi..."):
        try:
            prio = ml.build_priority_table(user_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Gagal menghitung prediksi: {exc}")
            return

    if prio.empty:
        st.info("Belum ada data stok untuk pengguna ini.")
        return

    tab1, tab2 = st.tabs(["📋 Prediksi Prioritas", "🔔 Notifikasi"])

    # ------------------------------------------------------------------ Tab 1
    with tab1:
        disp = pd.DataFrame({
            "Item": prio["item_name"].values,
            "Kategori": prio["category"].values,
            "Beli Terakhir": pd.to_datetime(prio["purchase_date"]).dt.strftime("%d %b %Y").values,
            "Rata2 Hari Habis": prio["avg_days_personal"].round(1).values,
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
            disp.style.apply(_color_row, axis=1).format(
                {"Sisa Hari": "{:.0f}", "Rata2 Hari Habis": "{:.1f}"}
            ),
            width="stretch", hide_index=True,
        )

        st.markdown("##### Ringkasan")
        counts = prio["priority_label"].value_counts()
        cols = st.columns(3)
        for col, key in zip(cols, config.PRIORITY_ORDER):
            col.metric(config.PRIORITY_LABEL_ID[key], int(counts.get(key, 0)))

    # ------------------------------------------------------------------ Tab 2
    with tab2:
        urgent = prio[prio["priority_label"].isin(["segera_beli", "beli_minggu_ini"])]
        st.write(
            f"Terdapat **{len(urgent)}** item yang perlu perhatian "
            "(segera beli / beli minggu ini)."
        )

        if st.button("🔔 Buat & Simpan Notifikasi", type="primary", disabled=urgent.empty):
            try:
                for r in urgent.itertuples():
                    sisa = int(r.sisa_hari) if pd.notna(r.sisa_hari) else None
                    db.insert_alert(
                        user_id=user_id, item_id=int(r.item_id),
                        alert_date=date.today(), priority_label=r.priority_label,
                        estimated_days_left=sisa,
                    )
                st.success(f"{len(urgent)} notifikasi tersimpan ke stock_alerts.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal menyimpan notifikasi: {exc}")

        st.divider()

        col_a, col_b = st.columns([3, 1])
        with col_b:
            show_resolved = st.toggle("Tampilkan terselesaikan", value=False)
            if st.button("✅ Tandai semua selesai"):
                db.resolve_all_alerts(user_id)
                st.rerun()

        alerts = db.get_alerts(user_id, only_unresolved=not show_resolved)
        if alerts.empty:
            st.info("Belum ada notifikasi.")
        else:
            for r in alerts.itertuples():
                badge = ui.priority_badge(r.priority_label)
                status = "✅" if r.is_resolved else "⏳"
                days = f"{int(r.estimated_days_left)} hari lagi" if pd.notna(
                    r.estimated_days_left) else "-"
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(
                        f"{status} {badge} &nbsp; **{r.item_name}** · {days} · "
                        f"{pd.to_datetime(r.alert_date):%d %b %Y}",
                        unsafe_allow_html=True,
                    )
                with c2:
                    if not r.is_resolved:
                        if st.button("Selesai", key=f"res_{r.alert_id}"):
                            db.resolve_alert(int(r.alert_id))
                            st.rerun()
