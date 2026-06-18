"""Halaman Input Stok — mencatat pembelian barang baru.

Saat disimpan, sistem otomatis memprediksi tanggal barang habis
menggunakan model forecasting (XGBoost).
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from lib import db, ml, ui


def render() -> None:
    user = ui.current_user()
    user_id = int(user["user_id"])

    st.title("📦 Input Stok")
    st.caption("Catat pembelian barang. Tanggal habis diprediksi otomatis oleh AI.")

    items = db.get_items()
    item_map = {r.item_name: r for r in items.itertuples()}

    NEW_ITEM = "➕ Item baru…"
    NEW_CATEGORY = "➕ Kategori baru…"

    pilihan = st.selectbox("Nama Item", [NEW_ITEM, *item_map.keys()])
    is_new = pilihan == NEW_ITEM
    if is_new:
        st.info(
            "Mode item baru: isi karakteristik barang (kategori, perkiraan umur "
            "pakai, harga). AI memprediksi berdasarkan karakteristik ini, jadi "
            "barang yang belum pernah dicatat pun tetap bisa diprediksi."
        )

    with st.form("form_stok", clear_on_submit=True):
        col1, col2 = st.columns(2)

        if is_new:
            with col1:
                new_name = st.text_input("Nama Item Baru", placeholder="mis. Kopi Sachet")
                kategori_pilih = st.selectbox(
                    "Kategori", [*db.get_categories(), NEW_CATEGORY]
                )
                kategori_baru = st.text_input(
                    "Nama Kategori Baru",
                    placeholder="mis. minuman_instan",
                    disabled=kategori_pilih != NEW_CATEGORY,
                )
                unit = st.text_input("Satuan", value="pcs")
            with col2:
                avg_days = st.number_input(
                    "Perkiraan Umur Pakai (hari)",
                    min_value=1, value=14, step=1,
                    help="Rata-rata berapa hari biasanya item ini habis.",
                )
                avg_price = st.number_input(
                    "Perkiraan Harga Acuan (Rp)",
                    min_value=0.0, value=10000.0, step=500.0,
                    help="Harga normal item ini, dipakai sebagai karakteristik model.",
                )
                purchase_date = st.date_input("Tanggal Beli", value=date.today())
                quantity = st.number_input(
                    "Jumlah Dibeli", min_value=0.1, value=1.0, step=0.5
                )
                price = st.number_input(
                    "Harga per Satuan saat Beli (Rp)",
                    min_value=0.0, value=10000.0, step=500.0,
                )
        else:
            sel = item_map[pilihan]
            with col1:
                purchase_date = st.date_input("Tanggal Beli", value=date.today())
                quantity = st.number_input(
                    "Jumlah Dibeli", min_value=0.1, value=1.0, step=0.5
                )
            with col2:
                st.text_input("Kategori", value=sel.category, disabled=True)
                unit = st.text_input("Satuan", value=sel.unit)
                price = st.number_input(
                    "Harga per Satuan (Rp)",
                    min_value=0.0, value=float(sel.avg_price or 0.0), step=500.0,
                )

        notes = st.text_area("Catatan (opsional)", placeholder="mis. beli di pasar")
        submitted = st.form_submit_button("💾 Simpan & Prediksi", type="primary")

    if submitted:
        try:
            if is_new:
                nama = (new_name or "").strip()
                if not nama:
                    st.error("Nama item baru wajib diisi.")
                    return
                kategori = (
                    (kategori_baru or "").strip()
                    if kategori_pilih == NEW_CATEGORY
                    else kategori_pilih
                )
                if not kategori:
                    st.error("Kategori wajib diisi.")
                    return
                item_id = db.insert_item(
                    item_name=nama,
                    category=kategori,
                    unit=unit or "pcs",
                    avg_days_to_finish=int(avg_days),
                    avg_price=float(avg_price),
                )
                item_name_disp = nama
                category = kategori
                avg_days_ref = float(avg_days)
                avg_price_ref = float(avg_price)
            else:
                sel = item_map[pilihan]
                item_id = int(sel.item_id)
                item_name_disp = sel.item_name
                category = sel.category
                avg_days_ref = float(sel.avg_days_to_finish or 14)
                avg_price_ref = float(sel.avg_price or price)

            est_date, pred_days = ml.estimate_finish_date(
                category=category,
                persona_type=user["persona_type"],
                quantity_bought=quantity,
                price_per_unit=price,
                avg_days_referensi=avg_days_ref,
                avg_price=avg_price_ref,
                purchase_date=purchase_date,
            )
            db.insert_stock(
                user_id=user_id,
                item_id=item_id,
                purchase_date=purchase_date,
                quantity_bought=quantity,
                unit=unit,
                price_per_unit=price,
                estimated_finish_date=est_date,
                notes=notes or None,
            )
            prefix = "Item baru terdaftar & tersimpan!" if is_new else "Tersimpan!"
            st.success(
                f"{prefix} Prediksi **{item_name_disp}** habis dalam "
                f"~**{pred_days:.0f} hari** (perkiraan {est_date:%d %b %Y})."
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Gagal menyimpan: {exc}")

    st.divider()
    st.subheader("🧾 Pembelian Terbaru")
    recent = db.get_recent_stock(user_id, limit=15)
    if recent.empty:
        st.info("Belum ada pembelian tercatat.")
    else:
        disp = recent.copy()
        disp["purchase_date"] = pd.to_datetime(disp["purchase_date"]).dt.strftime("%d %b %Y")
        disp["estimated_finish_date"] = pd.to_datetime(
            disp["estimated_finish_date"]
        ).dt.strftime("%d %b %Y")
        disp = disp.rename(columns={
            "purchase_date": "Tgl Beli",
            "item_name": "Item",
            "quantity_bought": "Jumlah",
            "unit": "Satuan",
            "price_per_unit": "Harga/Satuan",
            "total_price": "Total",
            "estimated_finish_date": "Perkiraan Habis",
            "notes": "Catatan",
        })
        st.dataframe(
            disp,
            width="stretch",
            hide_index=True,
            column_config={
                "Harga/Satuan": st.column_config.NumberColumn(format="Rp%d"),
                "Total": st.column_config.NumberColumn(format="Rp%d"),
            },
        )
