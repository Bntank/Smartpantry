"""Lapisan akses database PostgreSQL/Supabase untuk SmartPantry AI.

Koneksi memakai kredensial dari .env (lihat lib/config.py). Koneksi di-cache
sebagai resource Streamlit dan otomatis dibangun ulang bila terputus.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional, Sequence

import pandas as pd
import psycopg2
import streamlit as st

from . import config


@st.cache_resource(show_spinner=False)
def _connect():
    """Membuat koneksi baru ke database (di-cache antar rerun Streamlit)."""
    return psycopg2.connect(**config.db_config())


def _live_connection():
    """Mengembalikan koneksi yang dipastikan hidup; reconnect bila perlu."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
    except psycopg2.Error:
        # Koneksi mati / pooler menutup sesi -> buang cache & buat ulang.
        _connect.clear()
        conn = _connect()
    return conn


def query_df(sql: str, params: Optional[Sequence[Any]] = None) -> pd.DataFrame:
    """Menjalankan SELECT dan mengembalikan hasil sebagai DataFrame."""
    conn = _live_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    except psycopg2.Error:
        conn.rollback()
        raise


def execute(sql: str, params: Optional[Sequence[Any]] = None, returning: bool = False):
    """Menjalankan INSERT/UPDATE/DELETE. Bila returning=True, kembalikan 1 baris."""
    conn = _live_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchone() if returning else None
        conn.commit()
        return result
    except psycopg2.Error:
        conn.rollback()
        raise


def ping() -> bool:
    """Cek cepat apakah database dapat dijangkau."""
    try:
        _live_connection()
        return True
    except psycopg2.Error:
        return False


# ---------------------------------------------------------------------------
# Master data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def get_users() -> pd.DataFrame:
    return query_df(
        """
        SELECT user_id, username, email, city, persona_type, monthly_income
        FROM users
        WHERE persona_type IS NOT NULL
        ORDER BY user_id;
        """
    )


@st.cache_data(ttl=600, show_spinner=False)
def get_items() -> pd.DataFrame:
    return query_df(
        """
        SELECT item_id, item_name, category, unit, avg_days_to_finish, avg_price
        FROM items
        ORDER BY item_name;
        """
    )


def get_user(user_id: int) -> Optional[pd.Series]:
    users = get_users()
    row = users[users["user_id"] == user_id]
    return None if row.empty else row.iloc[0]


def get_categories() -> list[str]:
    """Daftar kategori item yang sudah ada (urut alfabetis)."""
    items = get_items()
    return sorted(items["category"].dropna().unique().tolist())


def insert_item(
    item_name: str,
    category: str,
    unit: str,
    avg_days_to_finish: Optional[int],
    avg_price: Optional[float],
) -> int:
    """Mendaftarkan item/barang baru ke tabel items dan mengembalikan item_id.

    avg_days_to_finish & avg_price menjadi karakteristik acuan yang dipakai
    model untuk memprediksi item baru ini.
    """
    row = execute(
        """
        INSERT INTO items (item_name, category, unit, avg_days_to_finish, avg_price)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING item_id;
        """,
        (item_name, category, unit, avg_days_to_finish, avg_price),
        returning=True,
    )
    get_items.clear()  # segarkan cache master data agar item baru langsung muncul
    return int(row[0])


# ---------------------------------------------------------------------------
# Stock log
# ---------------------------------------------------------------------------
def get_latest_stock_per_item(user_id: int) -> pd.DataFrame:
    """Pembelian terakhir untuk tiap item milik user (1 baris per item)."""
    return query_df(
        """
        WITH latest AS (
            SELECT DISTINCT ON (item_id) *
            FROM stock_log
            WHERE user_id = %s
            ORDER BY item_id, purchase_date DESC, log_id DESC
        )
        SELECT l.log_id, l.item_id, l.purchase_date, l.quantity_bought,
               l.unit, l.price_per_unit, l.total_price,
               l.estimated_finish_date, l.actual_finish_date, l.days_to_finish,
               i.item_name, i.category, i.avg_days_to_finish, i.avg_price
        FROM latest l
        JOIN items i ON l.item_id = i.item_id
        ORDER BY i.item_name;
        """,
        (user_id,),
    )


def get_recent_stock(user_id: int, limit: int = 15) -> pd.DataFrame:
    return query_df(
        """
        SELECT s.purchase_date, i.item_name, s.quantity_bought, s.unit,
               s.price_per_unit, s.total_price, s.estimated_finish_date, s.notes
        FROM stock_log s
        JOIN items i ON s.item_id = i.item_id
        WHERE s.user_id = %s
        ORDER BY s.purchase_date DESC, s.log_id DESC
        LIMIT %s;
        """,
        (user_id, limit),
    )


def get_personal_item_stats(user_id: int) -> pd.DataFrame:
    """Statistik personal per item: rata-rata & std hari habis, frekuensi beli."""
    return query_df(
        """
        SELECT item_id,
               AVG(days_to_finish)::float                  AS avg_days_personal,
               COALESCE(STDDEV_SAMP(days_to_finish), 0)::float AS std_days_personal,
               COUNT(*)::int                               AS frekuensi_beli
        FROM stock_log
        WHERE user_id = %s AND days_to_finish IS NOT NULL
        GROUP BY item_id;
        """,
        (user_id,),
    )


def insert_stock(
    user_id: int,
    item_id: int,
    purchase_date: date,
    quantity_bought: float,
    unit: str,
    price_per_unit: float,
    estimated_finish_date: Optional[date],
    notes: Optional[str] = None,
) -> int:
    """Menyimpan pembelian baru; total_price adalah generated column di DB."""
    row = execute(
        """
        INSERT INTO stock_log
            (user_id, item_id, purchase_date, quantity_bought, unit,
             price_per_unit, estimated_finish_date, notes, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING log_id;
        """,
        (user_id, item_id, purchase_date, quantity_bought, unit,
         price_per_unit, estimated_finish_date, notes),
        returning=True,
    )
    return int(row[0])


# ---------------------------------------------------------------------------
# Financial log
# ---------------------------------------------------------------------------
def insert_finance(
    user_id: int,
    log_date: date,
    transaction_type: str,
    amount: float,
    category: str,
    description: Optional[str] = None,
) -> int:
    row = execute(
        """
        INSERT INTO financial_log
            (user_id, log_date, transaction_type, amount, category, description, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        RETURNING finance_id;
        """,
        (user_id, log_date, transaction_type, amount, category, description),
        returning=True,
    )
    return int(row[0])


def get_recent_finance(user_id: int, limit: int = 15) -> pd.DataFrame:
    return query_df(
        """
        SELECT log_date, transaction_type, amount, category, description
        FROM financial_log
        WHERE user_id = %s
        ORDER BY log_date DESC, finance_id DESC
        LIMIT %s;
        """,
        (user_id, limit),
    )


def get_monthly_finance(user_id: int) -> pd.DataFrame:
    return query_df(
        """
        SELECT to_char(date_trunc('month', log_date), 'YYYY-MM') AS bulan,
               SUM(CASE WHEN transaction_type = 'income'  THEN amount ELSE 0 END)::float AS total_income,
               SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END)::float AS total_expense
        FROM financial_log
        WHERE user_id = %s
        GROUP BY 1
        ORDER BY 1;
        """,
        (user_id,),
    )


def get_expense_by_category(user_id: int, ym: Optional[str] = None) -> pd.DataFrame:
    if ym:
        return query_df(
            """
            SELECT category, SUM(amount)::float AS total
            FROM financial_log
            WHERE user_id = %s AND transaction_type = 'expense'
              AND to_char(date_trunc('month', log_date), 'YYYY-MM') = %s
            GROUP BY category ORDER BY total DESC;
            """,
            (user_id, ym),
        )
    return query_df(
        """
        SELECT category, SUM(amount)::float AS total
        FROM financial_log
        WHERE user_id = %s AND transaction_type = 'expense'
        GROUP BY category ORDER BY total DESC;
        """,
        (user_id,),
    )


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
def insert_alert(user_id: int, item_id: int, alert_date: date,
                 priority_label: str, estimated_days_left: Optional[int]) -> None:
    execute(
        """
        INSERT INTO stock_alerts
            (user_id, item_id, alert_date, priority_label, estimated_days_left,
             is_resolved, created_at)
        VALUES (%s, %s, %s, %s, %s, FALSE, NOW());
        """,
        (user_id, item_id, alert_date, priority_label, estimated_days_left),
    )


def get_alerts(user_id: int, only_unresolved: bool = False) -> pd.DataFrame:
    cond = "AND a.is_resolved = FALSE" if only_unresolved else ""
    return query_df(
        f"""
        SELECT a.alert_id, a.alert_date, i.item_name, a.priority_label,
               a.estimated_days_left, a.is_resolved
        FROM stock_alerts a
        JOIN items i ON a.item_id = i.item_id
        WHERE a.user_id = %s {cond}
        ORDER BY a.alert_date DESC, a.alert_id DESC;
        """,
        (user_id,),
    )


def resolve_alert(alert_id: int) -> None:
    execute("UPDATE stock_alerts SET is_resolved = TRUE WHERE alert_id = %s;", (alert_id,))


def resolve_all_alerts(user_id: int) -> None:
    execute(
        "UPDATE stock_alerts SET is_resolved = TRUE WHERE user_id = %s AND is_resolved = FALSE;",
        (user_id,),
    )


# ---------------------------------------------------------------------------
# ML training log
# ---------------------------------------------------------------------------
def insert_training_log(
    user_id: Optional[int],
    model_type: str,
    model_name: str,
    training_data_rows: int,
    mae_score: Optional[float],
    rmse_score: Optional[float],
    accuracy_score: Optional[float],
    retrain_schedule: str,
    notes: Optional[str] = None,
) -> None:
    # Nonaktifkan model lama bertipe sama supaya hanya 1 yang aktif.
    execute(
        "UPDATE ml_training_log SET is_active = FALSE WHERE model_type = %s;",
        (model_type,),
    )
    execute(
        """
        INSERT INTO ml_training_log
            (user_id, model_type, model_name, trained_at, training_data_rows,
             mae_score, rmse_score, accuracy_score, is_active, retrain_schedule, notes)
        VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, TRUE, %s, %s);
        """,
        (user_id, model_type, model_name, training_data_rows,
         mae_score, rmse_score, accuracy_score, retrain_schedule, notes),
    )


def get_training_log() -> pd.DataFrame:
    return query_df(
        """
        SELECT training_id, model_type, model_name, trained_at, training_data_rows,
               mae_score, rmse_score, accuracy_score, is_active, retrain_schedule, notes
        FROM ml_training_log
        ORDER BY trained_at DESC, training_id DESC;
        """
    )
