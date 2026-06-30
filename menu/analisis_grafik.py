import streamlit as st
import pandas as pd

def tampilkan_menu_analisis_grafik(df_sapi, daftar_pen):
    st.subheader("📈 Analisis & Grafik Performa Pertumbuhan Sapi (ADG)")
    
    if df_sapi.empty:
        st.info("ℹ️ Belum ada data performa pertumbuhan yang bisa dianalisis.")
        return

    # Ekstrak data Blok Kandang secara real-time dari kolom Lokasi Pen
    df_sapi['Blok Kandang'] = df_sapi['Lokasi Pen'].apply(lambda x: str(x).split(' - ')[0] if ' - ' in str(x) else 'Format Lama / Luar Blok')

    dimensi = st.radio("Pilih Dimensi Analisis Visual:", ["📊 Ringkasan per Blok Kandang (Makro)", "🏪 Detail Per Pen Kandang (Mikro)"], horizontal=True)

    if "Blok Kandang" in dimensi:
        st.markdown("### 🏬 Rata-rata ADG (kg/hari) Berdasarkan Blok Kandang")
        df_blok = df_sapi.groupby('Blok Kandang').agg(
            Populasi=('Kode Sapi', 'count'),
            Rata_Bobot_Akhir=('Bobot Akhir (kg)', 'mean'),
            Rata_ADG=('ADG (kg/hari)', 'mean')
        ).reset_index()

        st.bar_chart(data=df_blok, x='Blok Kandang', y='Rata_ADG', use_container_width=True)
        
        # Sajikan tabel detail di bawah grafik
        df_blok.columns = ["Nama Blok Kandang", "Populasi (Ekor)", "Rata Bobot Akhir (kg)", "Rata ADG (kg/hari)"]
        st.dataframe(df_blok.style.format({"Rata Bobot Akhir (kg)": "{:.2f}", "Rata ADG (kg/hari)": "{:.2f}"}), use_container_width=True, hide_index=True)

    else:
        st.markdown("### 🎯 Perbandingan Rata-rata ADG Antar Pen Aktif")
        df_pen = df_sapi.groupby('Lokasi Pen').agg(
            Populasi=('Kode Sapi', 'count'),
            Rata_ADG=('ADG (kg/hari)', 'mean')
        ).reset_index()

        st.bar_chart(data=df_pen, x='Lokasi Pen', y='Rata_ADG', use_container_width=True)
        st.dataframe(df_pen.rename(columns={"Lokasi Pen": "Lokasi Blok & Pen", "Populasi": "Jumlah Sapi (Ekor)", "Rata_ADG": "Rata ADG (kg/hari)"}), use_container_width=True, hide_index=True)