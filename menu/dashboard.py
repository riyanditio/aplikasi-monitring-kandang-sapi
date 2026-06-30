import streamlit as st
import pandas as pd

def tampilkan_dashboard(df_sapi):
    st.subheader("📊 Dashboard Utama & Pemantauan Populasi Kontinu")

    if df_sapi.empty:
        st.info("👋 Selamat Datang! Database kosong. Sapi baru belum ada yang terregistrasi masuk kandang.")
        return

    # Hitung KPI Utama Global
    total_ekor = len(df_sapi)
    rata_bobot = df_sapi["Bobot Akhir (kg)"].mean()
    rata_adg = df_sapi["ADG (kg/hari)"].mean()

    m1, m2, m3 = st.columns(3)
    m1.metric("📦 Total Populasi Aktif", f"{total_ekor} Ekor")
    m2.metric("⚖️ Rata-rata Bobot Sapi", f"{rata_bobot:.1f} kg")
    m3.metric("📈 Rata-rata ADG Kandang", f"{rata_adg:.2f} kg/hari")

    st.markdown("---")
    st.markdown("### 🏢 Ringkasan Kinerja per Blok Kandang")

    # Ekstrak nama Blok Kandang
    df_sapi['Blok Kandang'] = df_sapi['Lokasi Pen'].apply(lambda x: str(x).split(' - ')[0] if ' - ' in str(x) else 'Format Lama')
    
    df_summary_blok = df_sapi.groupby('Blok Kandang').agg(
        Pop=( 'Kode Sapi', 'count'),
        Adg_Blok=('ADG (kg/hari)', 'mean')
    ).reset_index()

    # Tampilkan Grid Dinamis Metric per Blok Kandang
    cols_blok = st.columns(len(df_summary_blok))
    for i, row_b in df_summary_blok.iterrows():
        with cols_blok[i]:
            st.metric(
                label=f"🏢 {row_b['Blok Kandang'].upper()}", 
                value=f"{row_b['Pop']} Ekor", 
                delta=f"{row_b['Adg_Blok']:.2f} kg/hari ADG"
            )

    st.markdown("---")
    st.markdown("### 📋 Tabel Monitor Seluruh Sapi di Area")
    st.dataframe(df_sapi.drop(columns=['Blok Kandang']), use_container_width=True, hide_index=True)