# SmartPantry AI — Aplikasi Streamlit

Sistem Prediksi & Manajemen Kebutuhan Rumah Tangga Personal.
Capstone Project — Data Science & Generative AI, CAMP Batch 4.

Aplikasi ini menghubungkan database PostgreSQL (Supabase) dengan dua model
Machine Learning (XGBoost) untuk:

1. **Forecasting** — memprediksi kapan suatu barang akan habis.
2. **Klasifikasi Prioritas Beli** — menentukan `segera_beli` / `beli_minggu_ini` /
   `masih_aman` dengan mempertimbangkan kondisi finansial pengguna.

## Fitur Aplikasi (multi-page)

| Halaman | Fungsi |
|---|---|
| 📊 **Dashboard** | KPI stok, daftar prioritas belanja, tren keuangan, notifikasi cepat |
| 📦 **Input Stok** | Catat pembelian; tanggal habis diprediksi otomatis oleh model forecasting |
| 💰 **Input Keuangan** | Catat pemasukan & pengeluaran + ringkasan bulanan |
| 🔔 **Prediksi & Alert** | Prediksi prioritas beli per item + kelola notifikasi (tabel `stock_alerts`) |
| 🤖 **Retraining Model** | Latih ulang model dari data terbaru, simpan metrik ke `ml_training_log` |

## Struktur Project

```
smartpantry-streamlit/
├── app.py                  # Entry point + navigasi multi-page + pemilih user
├── lib/
│   ├── config.py           # Konfigurasi & pembacaan .env
│   ├── db.py               # Lapisan akses database (query/insert)
│   ├── ml.py               # Load model, encoder, prediksi, retraining
│   └── ui.py               # Helper tampilan (format Rupiah, badge, dll.)
├── views/
│   ├── dashboard.py
│   ├── input_stok.py
│   ├── input_keuangan.py
│   ├── prediksi.py
│   └── retraining.py
├── models/                 # File .pkl hasil training (Google Colab)
│   ├── model_forecasting.pkl
│   ├── model_klasifikasi.pkl
│   ├── label_encoder_prioritas.pkl
│   ├── fitur_forecasting.pkl
│   └── fitur_klasifikasi.pkl
├── requirements.txt
├── .env                    # Kredensial DB (TIDAK di-commit)
└── .env.example
```

## Cara Menjalankan

1. Buat & aktifkan virtual environment, lalu install dependency:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

2. Salin `.env.example` menjadi `.env` dan isi kredensial Supabase Anda.

3. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Catatan Teknis

- **Encoder fitur** (`category_enc`, `item_enc`, `persona_enc`) tidak disimpan saat
  training, sehingga direkonstruksi dari master data memakai `LabelEncoder`
  (urut alfabetis, sama seperti default sklearn saat training). Validasi: prediksi
  forecasting menghasilkan MAE ~2.7 hari pada data nyata, konsisten dengan hasil
  training (MAE 2.96).
- **Label retraining klasifikasi** diturunkan dari `days_to_finish` aktual dengan
  ambang `<= 7 hari → segera_beli`, `<= 14 hari → beli_minggu_ini`, selebihnya
  `masih_aman` (selaras dengan jendela waktu pada view `v_latest_stock`).
- Koneksi database memakai **Supabase Connection Pooler** (port 6543, SSL required).
