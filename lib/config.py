"""Konfigurasi global aplikasi SmartPantry AI.

Kredensial database dibaca dari file .env (lihat .env.example).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Root project = satu folder di atas lib/
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

# Muat variabel dari .env (tidak meng-override env var sistem yang sudah ada)
load_dotenv(BASE_DIR / ".env")


def db_config() -> dict:
    """Mengembalikan parameter koneksi PostgreSQL/Supabase dari environment."""
    return {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "6543"),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "sslmode": os.getenv("DB_SSLMODE", "require"),
    }


# Path file model (hasil training dari Google Colab)
MODEL_FILES = {
    "forecast": MODELS_DIR / "model_forecasting.pkl",
    "classify": MODELS_DIR / "model_klasifikasi.pkl",
    "label_encoder": MODELS_DIR / "label_encoder_prioritas.pkl",
    "feat_forecast": MODELS_DIR / "fitur_forecasting.pkl",
    "feat_classify": MODELS_DIR / "fitur_klasifikasi.pkl",
}

# Urutan prioritas (paling mendesak -> paling aman) untuk sorting & pewarnaan
PRIORITY_ORDER = ["segera_beli", "beli_minggu_ini", "masih_aman"]

PRIORITY_LABEL_ID = {
    "segera_beli": "Segera Beli",
    "beli_minggu_ini": "Beli Minggu Ini",
    "masih_aman": "Masih Aman",
    "habis": "Habis",
    "unknown": "Belum Diketahui",
}

PRIORITY_COLOR = {
    "segera_beli": "#f43f5e",      # Rose 500
    "beli_minggu_ini": "#f59e0b",  # Amber 500
    "masih_aman": "#14b8a6",       # Teal 500
    "habis": "#991b1b",            # Red 800
    "unknown": "#64748b",          # Slate 500
}

# Kategori transaksi keuangan yang ada di database
INCOME_CATEGORIES = ["gaji", "kiriman_ortu", "pemasukan_tambahan"]
EXPENSE_CATEGORIES = ["kebutuhan_rumah_tangga", "transportasi", "hiburan", "lainnya"]

APP_TITLE = "SmartPantry AI"
APP_ICON = "assets/logo.png"
