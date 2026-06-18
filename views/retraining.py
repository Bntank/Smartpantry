"""Halaman Retraining Model.

Melatih ulang model Forecasting & Klasifikasi dari data terbaru di database,
menyimpan metrik (MAE/RMSE/Accuracy) ke tabel ml_training_log, dan menampilkan
riwayat performa. Mendukung pilihan jadwal: mingguan / bulanan / manual.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from lib import db, ml, ui

SCHEDULE_OPTIONS = {
    "manual": "Manual",
    "mingguan": "Mingguan",
    "bulanan": "Bulanan",
}
SCHEDULE_DELTA = {"mingguan": timedelta(days=7), "bulanan": timedelta(days=30)}


def _due_banner(log: pd.DataFrame) -> None:
    """Menampilkan status apakah retraining sudah jatuh tempo."""
    if log.empty:
        st.info("Model belum pernah dilatih ulang di aplikasi (masih memakai model awal dari Colab).")
        return
    for model_type in ["forecasting", "klasifikasi"]:
        active = log[(log["model_type"] == model_type) & (log["is_active"])]
        if active.empty:
            continue
        row = active.iloc[0]
        sched = row["retrain_schedule"]
        trained_at = pd.to_datetime(row["trained_at"])
        if sched in SCHEDULE_DELTA:
            due = trained_at + SCHEDULE_DELTA[sched]
            if datetime.now() >= due:
                st.warning(
                    f"⚠️ Retraining **{model_type}** ({SCHEDULE_OPTIONS[sched]}) "
                    f"sudah jatuh tempo (terakhir {trained_at:%d %b %Y})."
                )
            else:
                st.success(
                    f"✅ Model **{model_type}** terkini. Jadwal berikutnya: {due:%d %b %Y}."
                )


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.title("🤖 Retraining Model")
    st.caption("Latih ulang model dari data pengguna terbaru & pantau performanya.")

    log = db.get_training_log()
    _due_banner(log)

    st.divider()
    col1, col2 = st.columns([1, 2])
    with col1:
        schedule = st.selectbox(
            "Jadwal Retraining", list(SCHEDULE_OPTIONS.keys()),
            format_func=lambda k: SCHEDULE_OPTIONS[k],
        )
        st.caption(
            "Jadwal disimpan bersama hasil training. Saat jatuh tempo, "
            "banner peringatan akan muncul di halaman ini."
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        run_fc = st.button("🔄 Retrain Forecasting", width="stretch")
    with c2:
        run_cls = st.button("🔄 Retrain Klasifikasi", width="stretch")
    with c3:
        run_all = st.button("⚡ Retrain Keduanya", type="primary", width="stretch")

    if run_fc or run_all:
        with st.spinner("Melatih ulang model forecasting..."):
            try:
                res = ml.retrain_forecasting(schedule=schedule, user_id=user_id)
                st.success(
                    f"Forecasting selesai · {res['rows']:,} baris · "
                    f"MAE {res['mae']:.2f} · RMSE {res['rmse']:.2f}".replace(",", ".")
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal retrain forecasting: {exc}")

    if run_cls or run_all:
        with st.spinner("Melatih ulang model klasifikasi..."):
            try:
                res = ml.retrain_classification(schedule=schedule, user_id=user_id)
                st.success(
                    f"Klasifikasi selesai · {res['rows']:,} baris · "
                    f"Accuracy {res['accuracy']*100:.1f}%".replace(",", ".")
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal retrain klasifikasi: {exc}")

    if run_fc or run_cls or run_all:
        log = db.get_training_log()

    st.divider()
    st.subheader("📈 Riwayat Performa Model")
    if log.empty:
        st.info("Belum ada riwayat retraining.")
        return

    disp = log.copy()
    disp["trained_at"] = pd.to_datetime(disp["trained_at"]).dt.strftime("%d %b %Y %H:%M")
    disp["is_active"] = disp["is_active"].map({True: "✅ Aktif", False: "—"})
    disp = disp.rename(columns={
        "model_type": "Tipe",
        "model_name": "Model",
        "trained_at": "Waktu",
        "training_data_rows": "Baris Data",
        "mae_score": "MAE",
        "rmse_score": "RMSE",
        "accuracy_score": "Accuracy",
        "is_active": "Status",
        "retrain_schedule": "Jadwal",
    })
    st.dataframe(
        disp[["Tipe", "Model", "Waktu", "Baris Data", "MAE", "RMSE",
              "Accuracy", "Jadwal", "Status"]],
        width="stretch", hide_index=True,
        column_config={
            "Accuracy": st.column_config.NumberColumn(format="%.3f"),
            "MAE": st.column_config.NumberColumn(format="%.2f"),
            "RMSE": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    # Tren metrik antar waktu
    fc_hist = log[log["model_type"] == "forecasting"].sort_values("trained_at")
    if len(fc_hist) > 1:
        st.caption("Tren MAE Forecasting")
        st.line_chart(fc_hist.set_index("trained_at")["mae_score"])
    cls_hist = log[log["model_type"] == "klasifikasi"].sort_values("trained_at")
    if len(cls_hist) > 1:
        st.caption("Tren Accuracy Klasifikasi")
        st.line_chart(cls_hist.set_index("trained_at")["accuracy_score"])
