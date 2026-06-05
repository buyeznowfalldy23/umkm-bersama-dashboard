# UMKM Bersama

Platform manajemen keuangan untuk warung sembako kecil di Indonesia. Aplikasi ini membantu pemilik warung mengubah catatan transaksi harian jadi insight bisnis yang berguna, tanpa perlu paham akuntansi.

Dibuat sebagai proyek capstone Coding Camp 2026 powered by DBS Foundation oleh tim CC26-PSU328.

## Latar Belakang

Banyak pemilik warung sembako masih mencatat keuangan secara manual, atau bahkan tidak mencatat sama sekali. Akibatnya mereka sulit tahu untung ruginya, tidak sadar saat ada pengeluaran yang janggal, dan sering kaget ketika kasnya tiba-tiba menipis. UMKM Bersama dibuat untuk membantu masalah ini.

## Fitur Utama

- **Cash Flow Forecast** memprediksi arus kas warung beberapa minggu ke depan dan memberi peringatan kalau kas berpotensi menipis.
- **Anomaly Detection** menandai pengeluaran yang tidak wajar secara otomatis menggunakan Isolation Forest.
- **BCG Matrix** mengelompokkan produk berdasarkan margin dan volume penjualan supaya pemilik tahu produk mana yang perlu didorong dan mana yang perlu dievaluasi.

## Struktur Proyek
umkm-bersama-dashboard/
├── dataset_sintetis/        Dataset mentah hasil generate (belum bersih)
├── dataset_bersih/          Dataset hasil cleaning, dipakai untuk model dan dashboard
├── models/                  Model dan hasil klasifikasi BCG serta anomaly
├── notebooks/               Notebook wrangling, EDA, dan training model
├── 0. Data Dictionary.docx  Penjelasan tiap kolom dataset
├── dashboard.py             Dashboard Streamlit
└── requirements.txt         Daftar library yang dibutuhkan

## Cara Menjalankan

Install dulu library yang dibutuhkan:
pip install -r requirements.txt

Lalu jalankan dashboard:
streamlit run dashboard.py

Dashboard akan terbuka di browser, biasanya di http://localhost:8501. Pastikan folder `dataset_bersih` dan `models` berada di folder yang sama dengan `dashboard.py`.

## Tech Stack

Python, Pandas, NumPy, Scikit-learn, Streamlit, Plotly, Matplotlib, Seaborn.

## Tim

CC26-PSU328, tim capstone lintas learning path yang terdiri dari Data Science, AI Engineer, dan Full-Stack Web Developer.
