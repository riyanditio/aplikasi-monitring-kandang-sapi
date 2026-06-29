import streamlit as st
import pandas as pd

def tampilkan_dashboard(df_sapi):
    st.subheader("📊 Ringkasan Populasi & Performa Kelompok")
    if not df_sapi.empty:
        df_tampil = df_sapi.copy()
        tgl_m = pd.to_datetime(df_tampil["Tgl Masuk"])
        tgl_a = pd.to_datetime(df_tampil["Tgl Cek Akhir"])
        
        df_tampil["Lama Peliharaan (Hari)"] = (tgl_a - tgl_m).dt.days
        df_tampil["Umur Sekarang (Bulan)"] = (df_tampil["Umur Masuk (Bulan)"] + (df_tampil["Lama Peliharaan (Hari)"].fillna(0) / 30.4)).round(0).astype(int)
        df_tampil["Total Gain (kg)"] = df_tampil["Bobot Akhir (kg)"] - df_tampil["Bobot Awal (kg)"]
        
        df_tampil["FCR"] = df_tampil.apply(
            lambda row: round(row["Total Pakan (kg)"] / row["Total Gain (kg)"], 2) if row["Total Gain (kg)"] > 0 else 0.0, 
            axis=1
        )
        
        kolom_rapi = [
            "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Lokasi Pen", "Jenis Kelamin", "Umur Masuk (Bulan)", "Umur Sekarang (Bulan)",
            "Asal Negara", "Tgl Masuk", "Lama Peliharaan (Hari)", "Bobot Awal (kg)", "Bobot Akhir (kg)", 
            "Total Gain (kg)", "Total Pakan (kg)", "FCR", "ADG (kg/hari)"
        ]
        df_tampil = df_tampil.reindex(columns=kolom_rapi)
        df_tampil.index = range(1, len(df_tampil) + 1)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Populasi Sapi Aktif", len(df_tampil))
        col2.metric("Rata-rata Bobot Saat Ini", f"{round(df_tampil['Bobot Akhir (kg)'].mean(), 2)} kg")
        col3.metric("Rata-rata ADG Kelompok", f"{round(df_tampil['ADG (kg/hari)'].mean(), 2)} kg/hari")
        
        fcr_aktif = df_tampil[df_tampil["FCR"] > 0]["FCR"]
        avg_fcr = round(fcr_aktif.mean(), 2) if not fcr_aktif.empty else 0.0
        col4.metric("Rata-rata FCR Kandang", f"{avg_fcr}")
        
        st.write("### 📋 Tabel Monitoring Sapi Keseluruhan (Real-Time)")
        st.dataframe(df_tampil, use_container_width=True)
    else:
        st.info("Belum ada data sapi aktif. Silakan daftarkan di menu registrasi.")