"""
Dashboard UMKM Bersama -- CC26-PSU328
Platform manajemen keuangan cerdas untuk warung sembako.

Menampilkan:
- Ringkasan (overview metrik utama)
- Exploratory Data Analysis & Business Questions
- BCG Matrix (Profitability Clustering)
- Anomaly Detection (Smart Anomaly Alert)
- Cash Flow Forecasting

Jalankan dengan:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib
import json
import os

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="UMKM Bersama Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PALET WARNA GLOBAL (sama persis dengan notebook EDA)
# ============================================================
PALET = {
    'primary':   '#2D6A8E',   # biru tua
    'secondary': '#3FA39B',   # teal
    'accent':    '#E8A33D',   # oranye/amber
    'danger':    '#D96459',   # merah bata
    'neutral':   '#8E9AAF',   # abu kebiruan
    'success':   '#5B9279',   # hijau sage
}
PALET_LIST = ['#2D6A8E', '#3FA39B', '#E8A33D', '#D96459', '#5B9279', '#8E9AAF', '#9B6A9E', '#C97B84']
WARNA_PEMASUKAN   = '#2D6A8E'
WARNA_PENGELUARAN = '#D96459'

# Template plotly konsisten
PLOTLY_TEMPLATE = 'plotly_white'

URUTAN_HARI = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
LABEL_HARI  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

# ============================================================
# STYLING KUSTOM
# ============================================================
st.markdown(f"""
<style>
    .main {{ background-color: #FAFBFC; }}
    h1, h2, h3 {{ color: {PALET['primary']}; }}
    .stMetric {{
        background-color: white;
        border: 1px solid #E5E9EF;
        border-radius: 10px;
        padding: 15px;
    }}
    [data-testid="stMetricValue"] {{ color: {PALET['primary']}; }}
    .block-container {{ padding-top: 2rem; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA (dengan caching)
# ============================================================
# Path dibuat relatif terhadap lokasi file dashboard.py ini,
# bukan lokasi terminal saat menjalankan streamlit run.
# Jadi dashboard tetap menemukan data di mana pun perintah dijalankan.
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, 'dataset_bersih')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

@st.cache_data
def load_data():
    df_transaksi = pd.read_csv(f'{DATA_DIR}/transaksi_bersih.csv', parse_dates=['tanggal'])
    df_produk    = pd.read_csv(f'{DATA_DIR}/produk_bersih.csv')
    df_warung    = pd.read_csv(f'{DATA_DIR}/warung_bersih.csv')
    return df_transaksi, df_produk, df_warung

@st.cache_data
def load_hasil_model():
    hasil = {}
    bcg_path = f'{MODEL_DIR}/bcg_hasil_klasifikasi.csv'
    ano_path = f'{MODEL_DIR}/anomaly_hasil_deteksi.csv'
    if os.path.exists(bcg_path):
        hasil['bcg'] = pd.read_csv(bcg_path)
    if os.path.exists(ano_path):
        hasil['anomaly'] = pd.read_csv(ano_path, parse_dates=['tanggal'])
    return hasil

# Coba load data, beri pesan jelas jika file tidak ditemukan
try:
    df_transaksi, df_produk, df_warung = load_data()
    DATA_LOADED = True
except FileNotFoundError:
    st.error(
        "**Data tidak ditemukan.**\n\n"
        f"Dashboard mencari file di folder:\n\n`{DATA_DIR}`\n\n"
        "Pastikan folder 'dataset_bersih' berada di lokasi yang sama dengan dashboard.py, "
        "dan berisi tiga file berikut:\n"
        "- transaksi_bersih.csv\n"
        "- produk_bersih.csv\n"
        "- warung_bersih.csv\n\n"
        "File ini dihasilkan dari notebook Wrangling & EDA. Jalankan notebook itu sampai selesai dulu."
    )
    st.stop()

hasil_model = load_hasil_model()

# ============================================================
# SIDEBAR -- NAVIGASI & FILTER
# ============================================================
st.sidebar.title("UMKM Bersama")
st.sidebar.caption("Dashboard Manajemen Keuangan Warung Sembako")

halaman = st.sidebar.radio(
    "Navigasi",
    ["Ringkasan", "Exploratory Data Analysis", "BCG Matrix", "Anomaly Detection", "Cash Flow Forecast"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filter")

# Filter warung
daftar_warung = ['Semua Warung'] + sorted(df_warung['nama_warung'].tolist())
pilih_warung  = st.sidebar.selectbox("Pilih Warung", daftar_warung)

# Filter rentang tanggal
tgl_min = df_transaksi['tanggal'].min().date()
tgl_max = df_transaksi['tanggal'].max().date()
rentang_tgl = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(tgl_min, tgl_max),
    min_value=tgl_min,
    max_value=tgl_max
)

# Terapkan filter
df = df_transaksi.copy()
if pilih_warung != 'Semua Warung':
    id_warung_terpilih = df_warung[df_warung['nama_warung'] == pilih_warung]['id_warung'].values[0]
    df = df[df['id_warung'] == id_warung_terpilih]

if len(rentang_tgl) == 2:
    start, end = rentang_tgl
    df = df[(df['tanggal'].dt.date >= start) & (df['tanggal'].dt.date <= end)]

st.sidebar.markdown("---")
st.sidebar.caption("CC26-PSU328 | Data Science")

# ============================================================
# HELPER: format rupiah
# ============================================================
def rupiah(nilai):
    if abs(nilai) >= 1_000_000:
        return f"Rp{nilai/1_000_000:.1f} jt"
    elif abs(nilai) >= 1_000:
        return f"Rp{nilai/1_000:.0f} rb"
    return f"Rp{nilai:.0f}"

# ============================================================
# HALAMAN 1: RINGKASAN
# ============================================================
if halaman == "Ringkasan":
    st.title("Ringkasan Keuangan")
    st.caption(f"Menampilkan data: {pilih_warung}")

    total_masuk  = df[df['jenis'] == 'Pemasukan']['nominal'].sum()
    total_keluar = df[df['jenis'] == 'Pengeluaran']['nominal'].sum()
    laba_bersih  = total_masuk - total_keluar
    n_transaksi  = len(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pemasukan", rupiah(total_masuk))
    col2.metric("Total Pengeluaran", rupiah(total_keluar))
    col3.metric("Laba Bersih", rupiah(laba_bersih),
                delta=f"{(laba_bersih/total_masuk*100):.1f}% margin" if total_masuk > 0 else None)
    col4.metric("Jumlah Transaksi", f"{n_transaksi:,}")

    st.markdown("---")

    # Tren pemasukan vs pengeluaran harian
    st.subheader("Tren Pemasukan dan Pengeluaran Harian")
    harian = df.groupby(['tanggal', 'jenis'])['nominal'].sum().unstack(fill_value=0).reset_index()

    fig = go.Figure()
    if 'Pemasukan' in harian.columns:
        fig.add_trace(go.Scatter(
            x=harian['tanggal'], y=harian['Pemasukan'],
            name='Pemasukan', line=dict(color=WARNA_PEMASUKAN, width=2)
        ))
    if 'Pengeluaran' in harian.columns:
        fig.add_trace(go.Scatter(
            x=harian['tanggal'], y=harian['Pengeluaran'],
            name='Pengeluaran', line=dict(color=WARNA_PENGELUARAN, width=2)
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE, height=400,
        yaxis_title="Total Nominal (Rp)", xaxis_title="Tanggal",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Dua kolom: komposisi pengeluaran + metode bayar
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Komposisi Pengeluaran")
        pengeluaran = df[df['jenis'] == 'Pengeluaran'].groupby('kategori')['nominal'].sum().sort_values(ascending=False)
        if len(pengeluaran) > 0:
            fig_donut = go.Figure(data=[go.Pie(
                labels=pengeluaran.index, values=pengeluaran.values,
                hole=0.5, marker=dict(colors=PALET_LIST[:len(pengeluaran)])
            )])
            fig_donut.update_traces(textposition='inside', textinfo='percent')
            fig_donut.update_layout(template=PLOTLY_TEMPLATE, height=350,
                                    legend=dict(orientation="v", x=1.0, y=0.5))
            st.plotly_chart(fig_donut, use_container_width=True)

    with col_b:
        st.subheader("Distribusi Metode Pembayaran")
        metode = df[df['jenis'] == 'Pemasukan'].groupby('metode_bayar')['nominal'].sum()
        warna_metode = {'Cash': PALET['primary'], 'Transfer': PALET['secondary'], 'QRIS': PALET['accent']}
        if len(metode) > 0:
            fig_metode = go.Figure(data=[go.Bar(
                x=metode.index, y=metode.values,
                marker_color=[warna_metode.get(m, PALET['neutral']) for m in metode.index]
            )])
            fig_metode.update_layout(template=PLOTLY_TEMPLATE, height=350,
                                     yaxis_title="Total Nominal (Rp)")
            st.plotly_chart(fig_metode, use_container_width=True)

# ============================================================
# HALAMAN 2: EDA
# ============================================================
elif halaman == "Exploratory Data Analysis":
    st.title("Exploratory Data Analysis")
    st.caption(f"Menampilkan data: {pilih_warung}")

    # BQ3: Pola jam dan hari
    st.subheader("Pola Penjualan per Jam dan Hari")
    df_jam = df[(df['jenis'] == 'Pemasukan') & (df['jam_encoded'].notna())].copy()

    col1, col2 = st.columns(2)
    with col1:
        per_jam = df_jam.groupby('jam_encoded')['nominal'].sum().sort_index()
        if len(per_jam) > 0:
            jam_puncak = per_jam.idxmax()
            warna = [PALET['accent'] if j == jam_puncak else PALET['primary'] for j in per_jam.index]
            fig = go.Figure(data=[go.Bar(x=per_jam.index, y=per_jam.values, marker_color=warna)])
            fig.update_layout(template=PLOTLY_TEMPLATE, height=350,
                              title="Total Penjualan per Jam",
                              xaxis_title="Jam", yaxis_title="Total Penjualan (Rp)")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        per_hari = df_jam.groupby('nama_hari')['nominal'].sum().reindex(URUTAN_HARI)
        if per_hari.notna().any():
            hari_puncak = per_hari.idxmax()
            warna = [PALET['accent'] if h == hari_puncak else PALET['secondary'] for h in URUTAN_HARI]
            fig = go.Figure(data=[go.Bar(x=LABEL_HARI, y=per_hari.values, marker_color=warna)])
            fig.update_layout(template=PLOTLY_TEMPLATE, height=350,
                              title="Total Penjualan per Hari",
                              xaxis_title="Hari", yaxis_title="Total Penjualan (Rp)")
            st.plotly_chart(fig, use_container_width=True)

    # Heatmap jam x hari
    st.subheader("Heatmap Penjualan per Jam x Hari")
    if len(df_jam) > 0:
        df_jam['jam_encoded'] = df_jam['jam_encoded'].astype(int)
        pivot = df_jam.groupby(['hari_dalam_minggu', 'jam_encoded'])['nominal'].sum().unstack(fill_value=0)
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values, x=pivot.columns, y=[LABEL_HARI[i] for i in pivot.index],
            colorscale='YlGnBu', colorbar=dict(title="Penjualan (Rp)")
        ))
        fig.update_layout(template=PLOTLY_TEMPLATE, height=400,
                          xaxis_title="Jam", yaxis_title="Hari")
        st.plotly_chart(fig, use_container_width=True)

    # Top produk dan margin
    st.subheader("Analisis Produk")
    df_join = df[df['jenis'] == 'Pemasukan'].merge(
        df_produk[['id_produk', 'nama_produk', 'harga_jual', 'harga_pokok', 'kategori_produk']],
        on='id_produk', how='left'
    )

    col3, col4 = st.columns(2)
    with col3:
        top_vol = df_join.groupby('nama_produk')['qty'].sum().sort_values(ascending=False).head(10)
        if len(top_vol) > 0:
            fig = go.Figure(data=[go.Bar(
                x=top_vol.values[::-1], y=top_vol.index[::-1], orientation='h',
                marker_color=PALET['primary']
            )])
            fig.update_layout(template=PLOTLY_TEMPLATE, height=400,
                              title="Top 10 Produk Terlaris (Volume)",
                              xaxis_title="Total Qty Terjual")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        df_margin = df_produk.copy()
        df_margin['margin_pct'] = ((df_margin['harga_jual'] - df_margin['harga_pokok']) / df_margin['harga_jual'] * 100).round(1)
        margin_kat = df_margin.groupby('kategori_produk')['margin_pct'].mean().sort_values(ascending=False)
        warna_m = [PALET['secondary'] if m >= 15 else PALET['accent'] if m >= 10 else PALET['danger'] for m in margin_kat.values]
        fig = go.Figure(data=[go.Bar(x=margin_kat.index, y=margin_kat.values, marker_color=warna_m)])
        fig.update_layout(template=PLOTLY_TEMPLATE, height=400,
                          title="Rata-rata Margin per Kategori",
                          yaxis_title="Margin (%)")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# HALAMAN 3: BCG MATRIX
# ============================================================
elif halaman == "BCG Matrix":
    st.title("BCG Matrix -- Profitability Clustering")
    st.caption("Klasifikasi produk berdasarkan margin keuntungan dan volume penjualan")

    if 'bcg' not in hasil_model:
        st.warning(
            "Hasil BCG Matrix belum tersedia. Jalankan dulu notebook bcg_matrix.ipynb "
            "untuk menghasilkan file models/bcg_hasil_klasifikasi.csv"
        )
    else:
        df_bcg = hasil_model['bcg']

        # Ringkasan per kuadran
        col1, col2, col3, col4 = st.columns(4)
        warna_kuadran = {
            'Star': PALET['primary'], 'Cash Cow': PALET['success'],
            'Question Mark': PALET['accent'], 'Dog': PALET['danger']
        }
        for col, kuadran in zip([col1, col2, col3, col4], ['Star', 'Cash Cow', 'Question Mark', 'Dog']):
            n = len(df_bcg[df_bcg['kuadran'] == kuadran])
            col.metric(kuadran, f"{n} produk")

        st.markdown("---")

        # Scatter plot BCG
        st.subheader("Posisi Produk dalam BCG Matrix")
        median_qty    = df_bcg['qty_terjual'].median()
        median_margin = df_bcg['margin_pct'].median()

        fig = px.scatter(
            df_bcg, x='qty_terjual', y='margin_pct',
            color='kuadran', hover_name='nama_produk',
            color_discrete_map=warna_kuadran,
            labels={'qty_terjual': 'Total Qty Terjual', 'margin_pct': 'Margin (%)'},
            size_max=15
        )
        fig.update_traces(marker=dict(size=12, line=dict(width=1, color='white')))
        fig.add_vline(x=median_qty, line_dash="dash", line_color=PALET['neutral'])
        fig.add_hline(y=median_margin, line_dash="dash", line_color=PALET['neutral'])
        fig.update_layout(template=PLOTLY_TEMPLATE, height=550)
        st.plotly_chart(fig, use_container_width=True)

        # Tabel rekomendasi per kuadran
        st.subheader("Rekomendasi per Produk")
        kuadran_filter = st.multiselect(
            "Filter kuadran",
            options=['Star', 'Cash Cow', 'Question Mark', 'Dog'],
            default=['Star', 'Cash Cow', 'Question Mark', 'Dog']
        )
        df_tampil = df_bcg[df_bcg['kuadran'].isin(kuadran_filter)][
            ['nama_produk', 'kategori_produk', 'margin_pct', 'qty_terjual', 'kuadran', 'rekomendasi']
        ].sort_values('kuadran')
        st.dataframe(df_tampil, use_container_width=True, hide_index=True)

# ============================================================
# HALAMAN 4: ANOMALY DETECTION
# ============================================================
elif halaman == "Anomaly Detection":
    st.title("Anomaly Detection -- Smart Anomaly Alert")
    st.caption("Deteksi otomatis pengeluaran yang tidak wajar")

    if 'anomaly' not in hasil_model:
        st.warning(
            "Hasil Anomaly Detection belum tersedia. Jalankan dulu notebook anomaly_detection.ipynb "
            "untuk menghasilkan file models/anomaly_hasil_deteksi.csv"
        )
    else:
        df_ano = hasil_model['anomaly'].copy()

        # Filter sesuai warung jika dipilih
        if pilih_warung != 'Semua Warung':
            id_w = df_warung[df_warung['nama_warung'] == pilih_warung]['id_warung'].values[0]
            df_ano = df_ano[df_ano['id_warung'] == id_w]

        n_total   = len(df_ano)
        n_anomali = int(df_ano['is_anomaly'].sum())
        pct       = (n_anomali / n_total * 100) if n_total > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pengeluaran Dianalisis", f"{n_total:,}")
        col2.metric("Terdeteksi Anomali", f"{n_anomali}")
        col3.metric("Persentase Anomali", f"{pct:.1f}%")

        st.markdown("---")

        # Scatter nominal vs waktu, highlight anomali
        st.subheader("Sebaran Transaksi dan Anomali")
        kat_pilih = st.selectbox("Pilih kategori", ['Semua'] + sorted(df_ano['kategori'].unique().tolist()))
        df_plot = df_ano if kat_pilih == 'Semua' else df_ano[df_ano['kategori'] == kat_pilih]

        fig = go.Figure()
        normal  = df_plot[df_plot['is_anomaly'] == 0]
        anomali = df_plot[df_plot['is_anomaly'] == 1]
        fig.add_trace(go.Scatter(
            x=normal['tanggal'], y=normal['nominal'], mode='markers',
            name='Normal', marker=dict(color=PALET['primary'], size=6, opacity=0.4)
        ))
        fig.add_trace(go.Scatter(
            x=anomali['tanggal'], y=anomali['nominal'], mode='markers',
            name='Anomali', marker=dict(color=PALET['danger'], size=11, symbol='x', line=dict(width=2))
        ))
        fig.update_layout(template=PLOTLY_TEMPLATE, height=450,
                          yaxis_title="Nominal (Rp)", xaxis_title="Tanggal",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

        # Tabel daftar anomali
        st.subheader("Daftar Transaksi Anomali")
        df_anomali_list = df_ano[df_ano['is_anomaly'] == 1].sort_values('anomaly_score')[
            ['tanggal', 'kategori', 'nominal', 'rolling_mean_7d', 'rasio_vs_baseline', 'anomaly_score', 'catatan']
        ]
        if len(df_anomali_list) > 0:
            st.dataframe(df_anomali_list, use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada transaksi anomali terdeteksi pada filter ini.")

# ============================================================
# HALAMAN 5: CASH FLOW FORECAST
# ============================================================
elif halaman == "Cash Flow Forecast":
    st.title("Cash Flow Forecast")
    st.caption("Proyeksi arus kas berdasarkan pola historis")

    # Agregasi pemasukan harian
    ts = df[df['jenis'] == 'Pemasukan'].groupby('tanggal')['nominal'].sum().reset_index()
    ts.columns = ['ds', 'y']
    ts = ts.sort_values('ds')
    ts['rolling_7d'] = ts['y'].rolling(7, min_periods=1).mean()

    if len(ts) < 14:
        st.warning("Data tidak cukup untuk menampilkan tren forecasting (minimal 14 hari).")
    else:
        st.subheader("Tren Pemasukan Harian dan Rata-rata Bergerak")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts['ds'], y=ts['y'], name='Harian',
                                 line=dict(color=PALET['neutral'], width=1)))
        fig.add_trace(go.Scatter(x=ts['ds'], y=ts['rolling_7d'], name='Rolling 7 hari',
                                 line=dict(color=PALET['primary'], width=2.5)))
        fig.update_layout(template=PLOTLY_TEMPLATE, height=450,
                          yaxis_title="Total Pemasukan (Rp)", xaxis_title="Tanggal",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                          hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        # Slider untuk simulasi proyeksi sederhana (rata-rata bergerak diteruskan)
        st.subheader("Simulasi Proyeksi Sederhana")
        st.caption(
            "Catatan: ini proyeksi sederhana berbasis rata-rata bergerak untuk ilustrasi. "
            "Model forecasting final (Prophet/time series) akan menggantikan ini setelah selesai dilatih."
        )
        horizon = st.slider("Horizon proyeksi (hari ke depan)", 7, 28, 14)

        rata_terakhir = ts['rolling_7d'].iloc[-1]
        std_harian    = ts['y'].std()
        tgl_terakhir  = ts['ds'].max()
        tgl_proyeksi  = pd.date_range(tgl_terakhir + pd.Timedelta(days=1), periods=horizon)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ts['ds'], y=ts['y'], name='Aktual',
                                  line=dict(color=PALET['neutral'], width=1)))
        fig2.add_trace(go.Scatter(
            x=tgl_proyeksi, y=[rata_terakhir] * horizon,
            name='Proyeksi', line=dict(color=PALET['accent'], width=2.5, dash='dash')
        ))
        # Pita kepercayaan sederhana
        fig2.add_trace(go.Scatter(
            x=list(tgl_proyeksi) + list(tgl_proyeksi[::-1]),
            y=[rata_terakhir + std_harian] * horizon + [rata_terakhir - std_harian] * horizon,
            fill='toself', fillcolor='rgba(232,163,61,0.15)',
            line=dict(color='rgba(0,0,0,0)'), name='Rentang', showlegend=True
        ))
        fig2.update_layout(template=PLOTLY_TEMPLATE, height=450,
                           yaxis_title="Total Pemasukan (Rp)", xaxis_title="Tanggal",
                           legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig2, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric("Proyeksi rata-rata harian", rupiah(rata_terakhir))
        col2.metric(f"Proyeksi total {horizon} hari", rupiah(rata_terakhir * horizon))
