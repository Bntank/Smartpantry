"""Lapisan Machine Learning SmartPantry AI.

Berisi:
- Pemuatan model XGBoost (forecasting & klasifikasi) dari folder models/.
- Rekonstruksi LabelEncoder untuk fitur category/persona. Encoder ini tidak
  disimpan saat training, namun karena training memakai sklearn LabelEncoder
  (urut alfabetis), encoder dapat direkonstruksi deterministik dari master data.
- Feature engineering berbasis KARAKTERISTIK item (kategori, rata-rata hari
  habis, harga), BUKAN identitas item. Dengan begitu barang yang belum pernah
  ada di data training tetap bisa diprediksi dari kemiripan karakteristiknya.
- Fungsi retraining yang menyimpan metrik ke ml_training_log.
"""
from __future__ import annotations

import warnings
from datetime import date, datetime, timedelta
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from . import config, db

warnings.filterwarnings("ignore", category=UserWarning)

# Fitur forecasting berbasis karakteristik (TANPA item_enc). Item baru cukup
# membawa kategori + avg_days_referensi + avg_price agar tetap bisa diprediksi.
FORECAST_FEATURES = [
    "category_enc",
    "persona_enc",
    "quantity_bought",
    "price_per_unit",
    "avg_days_referensi",
    "avg_price",
    "bulan",
    "hari_dalam_seminggu",
    "hari_dalam_bulan",
]


# ---------------------------------------------------------------------------
# Pemuatan model & encoder
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_models() -> dict:
    """Memuat semua artefak model dari folder models/."""
    return {
        "forecast": joblib.load(config.MODEL_FILES["forecast"]),
        "classify": joblib.load(config.MODEL_FILES["classify"]),
        "label_encoder": joblib.load(config.MODEL_FILES["label_encoder"]),
        "feat_forecast": list(joblib.load(config.MODEL_FILES["feat_forecast"])),
        "feat_classify": list(joblib.load(config.MODEL_FILES["feat_classify"])),
    }


@st.cache_resource(show_spinner=False)
def get_encoders() -> dict:
    """Merekonstruksi LabelEncoder dari master data (urut alfabetis).

    Hanya category & persona yang di-encode; identitas item TIDAK dipakai lagi
    sebagai fitur agar model dapat menggeneralisasi ke item baru.
    """
    items = db.get_items()
    users = db.get_users()
    le_cat = LabelEncoder().fit(sorted(items["category"].dropna().unique()))
    le_persona = LabelEncoder().fit(sorted(users["persona_type"].dropna().unique()))
    return {"category": le_cat, "persona": le_persona}


def _safe_transform(encoder: LabelEncoder, values) -> np.ndarray:
    """Transform aman: nilai tak dikenal -> 0 agar app tidak crash."""
    classes = {c: i for i, c in enumerate(encoder.classes_)}
    return np.array([classes.get(v, 0) for v in values], dtype=float)


# ---------------------------------------------------------------------------
# Forecasting (regresi: prediksi days_to_finish)
# ---------------------------------------------------------------------------
def predict_finish_days(
    category: str,
    persona_type: str,
    quantity_bought: float,
    price_per_unit: float,
    avg_days_referensi: float,
    avg_price: float,
    purchase_date: date,
) -> float:
    """Memprediksi berapa hari sampai 1 item habis.

    Prediksi berbasis karakteristik (kategori, harga, rata-rata hari habis),
    sehingga item baru pun bisa diprediksi selama karakteristiknya diisi.
    """
    models = load_models()
    enc = get_encoders()
    pdt = pd.Timestamp(purchase_date)
    feats = {
        "category_enc": _safe_transform(enc["category"], [category])[0],
        "persona_enc": _safe_transform(enc["persona"], [persona_type])[0],
        "quantity_bought": float(quantity_bought),
        "price_per_unit": float(price_per_unit),
        "avg_days_referensi": float(avg_days_referensi),
        "avg_price": float(avg_price),
        "bulan": pdt.month,
        "hari_dalam_seminggu": pdt.dayofweek,
        "hari_dalam_bulan": pdt.day,
    }
    X = pd.DataFrame([feats])[models["feat_forecast"]].astype(float)
    pred = float(models["forecast"].predict(X)[0])
    return max(1.0, pred)


def estimate_finish_date(
    category: str,
    persona_type: str,
    quantity_bought: float,
    price_per_unit: float,
    avg_days_referensi: float,
    avg_price: float,
    purchase_date: date,
) -> tuple[date, float]:
    """Mengembalikan (tanggal_perkiraan_habis, prediksi_hari)."""
    days = predict_finish_days(
        category, persona_type, quantity_bought,
        price_per_unit, avg_days_referensi, avg_price, purchase_date,
    )
    return purchase_date + timedelta(days=round(days)), days


# ---------------------------------------------------------------------------
# Klasifikasi prioritas beli
# ---------------------------------------------------------------------------
def _finance_context(user_id: int) -> dict:
    """Konteks finansial bulan terbaru milik user untuk fitur klasifikasi."""
    mf = db.get_monthly_finance(user_id)
    user = db.get_user(user_id)
    monthly_income = float(user["monthly_income"]) if user is not None else 0.0
    if mf.empty:
        income = monthly_income
        expense = 0.0
    else:
        last = mf.iloc[-1]
        income = float(last["total_income"]) or monthly_income
        expense = float(last["total_expense"])
    income = income if income > 0 else max(monthly_income, 1.0)
    sisa = income - expense
    rasio = expense / income if income > 0 else 0.0
    return {
        "total_income_bulan": income,
        "total_expense_bulan": expense,
        "sisa_budget": sisa,
        "rasio_pengeluaran": rasio,
    }


def build_priority_table(user_id: int) -> pd.DataFrame:
    """Membangun tabel prioritas beli untuk semua item terakhir milik user.

    Menggabungkan forecasting (estimasi hari habis) dan klasifikasi
    (label prioritas mempertimbangkan kondisi finansial).
    """
    latest = db.get_latest_stock_per_item(user_id)
    if latest.empty:
        return latest

    user = db.get_user(user_id)
    persona = user["persona_type"] if user is not None else None
    stats = db.get_personal_item_stats(user_id)
    fin = _finance_context(user_id)
    enc = get_encoders()
    models = load_models()

    df = latest.merge(stats, on="item_id", how="left")
    # Fallback berlapis untuk item tanpa riwayat personal (mis. item baru):
    # 1) rata-rata hari habis item itu sendiri (kolom referensi),
    # 2) rata-rata per kategori, 3) rata-rata global.
    cat_mean = df.groupby("category")["avg_days_to_finish"].transform("mean")
    global_mean = float(df["avg_days_to_finish"].mean()) if not df.empty else 7.0
    df["avg_days_personal"] = (
        df["avg_days_personal"]
        .fillna(df["avg_days_to_finish"])
        .fillna(cat_mean)
        .fillna(global_mean)
    )
    df["std_days_personal"] = df["std_days_personal"].fillna(0.0)
    df["frekuensi_beli"] = df["frekuensi_beli"].fillna(1).astype(float)

    pdt = pd.to_datetime(df["purchase_date"])
    df["category_enc"] = _safe_transform(enc["category"], df["category"])
    df["avg_days_referensi"] = df["avg_days_to_finish"].astype(float)
    df["quantity_bought"] = df["quantity_bought"].astype(float)
    df["bulan_beli"] = pdt.dt.month
    df["tanggal_beli"] = pdt.dt.day
    for k, v in fin.items():
        df[k] = v

    X = df[models["feat_classify"]].astype(float)
    pred_enc = models["classify"].predict(X)
    df["priority_label"] = models["label_encoder"].inverse_transform(pred_enc)

    # Estimasi sisa hari relatif hari ini (untuk alert & tampilan)
    today = pd.Timestamp(date.today())
    est = pd.to_datetime(df["estimated_finish_date"])
    df["sisa_hari"] = (est - today).dt.days

    cols = [
        "item_id", "item_name", "category", "purchase_date", "quantity_bought",
        "unit", "price_per_unit", "estimated_finish_date", "sisa_hari",
        "avg_days_personal", "frekuensi_beli", "priority_label",
    ]
    out = df[cols].copy()
    out["priority_rank"] = out["priority_label"].map(
        {p: i for i, p in enumerate(config.PRIORITY_ORDER)}
    ).fillna(99)
    return out.sort_values(["priority_rank", "sisa_hari"]).drop(columns="priority_rank")


# ---------------------------------------------------------------------------
# Retraining
# ---------------------------------------------------------------------------
def _label_from_days(d: float) -> str:
    """Aturan label prioritas dari days_to_finish aktual.

    Selaras dengan jendela waktu pada view v_latest_stock (7 & 14 hari).
    Catatan: aturan ini asumsi yang terdokumentasi karena notebook training
    tidak menyertakan definisi label eksplisit pada file model.
    """
    if d <= 7:
        return "segera_beli"
    if d <= 14:
        return "beli_minggu_ini"
    return "masih_aman"


def _build_training_frame() -> pd.DataFrame:
    """Mengambil seluruh stock_log + fitur untuk training ulang."""
    df = db.query_df(
        """
        SELECT s.user_id, s.item_id, s.purchase_date, s.quantity_bought,
               s.price_per_unit, s.days_to_finish,
               i.item_name, i.category, i.avg_days_to_finish AS avg_days_referensi,
               i.avg_price, u.persona_type
        FROM stock_log s
        JOIN items i ON s.item_id = i.item_id
        JOIN users u ON s.user_id = u.user_id
        WHERE s.days_to_finish IS NOT NULL AND u.persona_type IS NOT NULL;
        """
    )
    df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    return df


def retrain_forecasting(schedule: str = "manual", user_id: Optional[int] = None) -> dict:
    """Melatih ulang model forecasting (XGBRegressor) dari data terkini."""
    from xgboost import XGBRegressor

    df = _build_training_frame()
    if len(df) < 100:
        raise ValueError("Data terlalu sedikit untuk retraining (min 100 baris).")

    enc = get_encoders()
    df["category_enc"] = _safe_transform(enc["category"], df["category"])
    df["persona_enc"] = _safe_transform(enc["persona"], df["persona_type"])
    df["avg_days_referensi"] = pd.to_numeric(df["avg_days_referensi"], errors="coerce")
    df["avg_price"] = pd.to_numeric(df["avg_price"], errors="coerce").fillna(
        df["price_per_unit"]
    )
    df["bulan"] = df["purchase_date"].dt.month
    df["hari_dalam_seminggu"] = df["purchase_date"].dt.dayofweek
    df["hari_dalam_bulan"] = df["purchase_date"].dt.day

    feats = FORECAST_FEATURES
    X = df[feats].astype(float)
    y = df["days_to_finish"].astype(float)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    mae = float(mean_absolute_error(y_te, pred))
    rmse = float(np.sqrt(mean_squared_error(y_te, pred)))

    joblib.dump(model, config.MODEL_FILES["forecast"])
    joblib.dump(feats, config.MODEL_FILES["feat_forecast"])
    load_models.clear()

    db.insert_training_log(
        user_id=user_id, model_type="forecasting", model_name="XGBoost Regressor",
        training_data_rows=len(df), mae_score=round(mae, 4), rmse_score=round(rmse, 4),
        accuracy_score=None, retrain_schedule=schedule,
        notes="Retrain otomatis dari data stock_log terkini.",
    )
    return {"rows": len(df), "mae": mae, "rmse": rmse}


def retrain_classification(schedule: str = "manual", user_id: Optional[int] = None) -> dict:
    """Melatih ulang model klasifikasi (XGBClassifier) dari data terkini."""
    from xgboost import XGBClassifier

    df = _build_training_frame()
    if len(df) < 100:
        raise ValueError("Data terlalu sedikit untuk retraining (min 100 baris).")

    # Statistik personal per (user, item)
    grp = df.groupby(["user_id", "item_id"])["days_to_finish"]
    df["avg_days_personal"] = grp.transform("mean")
    df["std_days_personal"] = grp.transform("std").fillna(0.0)
    df["frekuensi_beli"] = grp.transform("count").astype(float)

    # Konteks finansial per (user, bulan)
    fin = db.query_df(
        """
        SELECT user_id,
               to_char(date_trunc('month', log_date), 'YYYY-MM') AS ym,
               SUM(CASE WHEN transaction_type='income'  THEN amount ELSE 0 END)::float AS total_income_bulan,
               SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END)::float AS total_expense_bulan
        FROM financial_log GROUP BY 1, 2;
        """
    )
    df["ym"] = df["purchase_date"].dt.strftime("%Y-%m")
    df = df.merge(fin, on=["user_id", "ym"], how="left")
    incomes = db.get_users().set_index("user_id")["monthly_income"].astype(float)
    df["total_income_bulan"] = df["total_income_bulan"].fillna(
        df["user_id"].map(incomes)
    ).fillna(0.0)
    df["total_expense_bulan"] = df["total_expense_bulan"].fillna(0.0)
    df["total_income_bulan"] = df["total_income_bulan"].replace(0, 1.0)
    df["sisa_budget"] = df["total_income_bulan"] - df["total_expense_bulan"]
    df["rasio_pengeluaran"] = df["total_expense_bulan"] / df["total_income_bulan"]

    enc = get_encoders()
    df["category_enc"] = _safe_transform(enc["category"], df["category"])
    df["bulan_beli"] = df["purchase_date"].dt.month
    df["tanggal_beli"] = df["purchase_date"].dt.day
    df["quantity_bought"] = df["quantity_bought"].astype(float)

    df["priority_label"] = df["days_to_finish"].apply(_label_from_days)

    models = load_models()
    feats = models["feat_classify"]
    le = models["label_encoder"]
    X = df[feats].astype(float)
    y = le.transform(df["priority_label"])
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
        objective="multi:softprob", num_class=len(le.classes_),
        eval_metric="mlogloss",
    )
    model.fit(X_tr, y_tr)
    acc = float(accuracy_score(y_te, model.predict(X_te)))

    joblib.dump(model, config.MODEL_FILES["classify"])
    load_models.clear()

    db.insert_training_log(
        user_id=user_id, model_type="klasifikasi", model_name="XGBoost Classifier",
        training_data_rows=len(df), mae_score=None, rmse_score=None,
        accuracy_score=round(acc, 4), retrain_schedule=schedule,
        notes="Retrain otomatis; label dari days_to_finish (<=7 / <=14 hari).",
    )
    return {"rows": len(df), "accuracy": acc}
