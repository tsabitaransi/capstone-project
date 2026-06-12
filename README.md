# 💸 Smart Financial Assistant Dashboard

Dashboard interaktif berbasis **Streamlit** untuk analisis pengeluaran pribadi, dikembangkan sebagai bagian dari **Capstone Project Coding Camp 2026 · CC26-PSU189 · Powered by DBS Foundation**.

## 📌 Deskripsi Proyek

Berikut adalah dashboard analitik yang menjawab tiga pertanyaan SMART berbasis data transaksi keuangan individu:

| # | Pertanyaan |
|---|---|
| 1 | Berapa total pengeluaran Mei vs April 2026, dan kategori apa yang mengalami kenaikan tertinggi? |
| 2 | Berapa persentase pengeluaran tiap kategori Mei 2026, dan mana yang memiliki frekuensi dan nominal terbesar? |
| 3 | Bagaimana tren pengeluaran harian 30 hari terakhir, dan pada hari apa terjadi lonjakan? |

## 🗂️ Struktur Folder

```
smart-financial-assistant-dashboard/
├── dashboard/
│   ├── dashboard.py          
│   └── main_data.csv          
├── notebook.ipynb            
├── requirements.txt          
└── README.md
```

## 🛠️ Teknologi yang Digunakan

| Library | Versi | Kegunaan |
|---|---|---|
| `streamlit` | 1.44.1 | Framework dashboard interaktif |
| `pandas` | 2.2.3 | Manipulasi dan analisis data |
| `plotly` | 6.7.0 | Visualisasi data interaktif |
| `numpy` | 1.26.4 | Komputasi numerik |

## ⚙️ Cara Instalasi & Menjalankan

### Prasyarat
- Python 3.9 atau lebih baru
- Git

### 1. Clone Repository

```bash
git clone https://github.com/tsabitaransi/capstone-project.git
cd finance-tracker-dashboard
```

### 2. Buat dan Aktifkan Virtual Environment

```bash
# Buat virtual environment
python -m venv venv

# Aktivasi — Windows (Command Prompt)
venv\Scripts\activate

# Aktivasi — Windows (PowerShell)
venv\Scripts\Activate.ps1

# Aktivasi — Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Siapkan Data

Pastikan file `main_data.csv` sudah ada di folder `dashboard/`:

```bash
cp dashboard/main_data.csv
```

### 5. Jalankan Dashboard

```bash
streamlit run dashboard/dashboard.py
```

Browser akan otomatis terbuka di `http://localhost:8501`

## 🚀 Akses Online (Streamlit Community Cloud)

Dashboard ini dapat diakses secara publik tanpa instalasi melalui:

🔗 **https://smart-financial-assistant.streamlit.app/**
