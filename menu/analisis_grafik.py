import streamlit as st
import pandas as pd

def tampilkan_menu_analisis_grafik(df_sapi, DAFTAR_PEN):
    st.subheader("📈 Analisis Tren Visual Kelompok Sapi")
    if df_sapi.empty: 
        st.warning("Belum ada data populasi sapi aktif.")
    else:
        df_analisis = df_sapi.copy()
        df_analisis["Lama Peliharaan (Hari)"] = (pd.to_datetime(df_analisis["Tgl Cek Akhir"]) - pd.to_datetime(df_analisis["Tgl Masuk"])).dt.days
        df_analisis["Total Gain (kg)"] = df_analisis["Bobot Akhir (kg)"] - df_analisis["Bobot Awal (kg)"]
        df_analisis["FCR"] = df_analisis.apply(lambda row: round(row["Total Pakan (kg)"] / row["Total Gain (kg)"], 2) if row["Total Gain (kg)"] > 0 else 0.0, axis=1)
        
        st.markdown("### 📊 Distribusi Populasi Stok Sapi Saat Ini")
        col_pop1, col_pop2 = st.columns(2)
        with col_pop1:
            st.markdown("#### 🏠 Jumlah Sapi per Pen / Kandang (Ekor)")
            df_pop_pen = df_analisis.groupby("Lokasi Pen").size().reset_index(name="Jumlah (Ekor)")
            df_pop_pen = pd.DataFrame({"Locations Pen": DAFTAR_PEN}).merge(df_pop_pen, left_on="Locations Pen", right_on="Lokasi Pen", how="left").fillna(0)
            st.bar_chart(data=df_pop_pen, x="Locations Pen", y="Jumlah (Ekor)", use_container_width=True)
        with col_pop2:
            st.markdown("#### 🐂 Jumlah Sapi berdasarkan Varietas (Ekor)")
            st.bar_chart(data=df_analisis.groupby("Jenis Sapi").size().reset_index(name="Jumlah (Ekor)"), x="Jenis Sapi", y="Jumlah (Ekor)", use_container_width=True)
            
        st.markdown("---")
        st.markdown("### 📈 Grafik Analisis Performa Pertumbuhan")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.bar_chart(data=df_analisis.groupby("Jenis Sapi")["ADG (kg/hari)"].mean().reset_index(), x="Jenis Sapi", y="ADG (kg/hari)", use_container_width=True)
        with col_g2:
            df_fcr_aktif = df_analisis[df_analisis["FCR"] > 0]
            if not df_fcr_aktif.empty: 
                st.bar_chart(data=df_fcr_aktif.groupby("Jenis Sapi")["FCR"].mean().reset_index(), x="Jenis Sapi", y="FCR", use_container_width=True)
            else: 
                st.info("Grafik FCR menunggu data timbangan.")