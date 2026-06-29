import streamlit as st
from datetime import datetime  # <-- Diperlukan untuk mendeteksi waktu input penimbangan

def tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name):
    st.subheader("⚖️ Pencatatan Timbangan Berkala")
    if df_sapi.empty: 
        st.warning("Belum ada sapi.")
    else:
        pilihan_sapi = df_sapi["RFID/Tag"].astype(str).tolist()
        selected_tag = st.selectbox("Pilih Nomor Tag / RFID Sapi", pilihan_sapi)
        idx = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag].index[0]
        data_sapi = df_sapi.loc[idx]
        st.info(f"🐂 Kode Sapi: {data_sapi.get('Kode Sapi', '-')} | Bobot Terakhir: {data_sapi['Bobot Akhir (kg)']} kg")
        
        with st.form("form_timbangan"):
            tgl_akhir = st.date_input("Tanggal Penimbangan Baru", datetime.now())
            bobot_akhir = st.number_input("Bobot Timbangan Baru (kg)", min_value=50.0, value=float(data_sapi['Bobot Akhir (kg)']))
            
            if st.form_submit_button("Simpan Data Baru"):
                adg_baru = calculate_adg(data_sapi['Tgl Masuk'], data_sapi['Bobot Awal (kg)'], tgl_akhir, bobot_akhir)
                df_sapi.at[idx, "Tgl Cek Akhir"] = tgl_akhir.strftime("%Y-%m-%d")
                df_sapi.at[idx, "Bobot Akhir (kg)"] = bobot_akhir
                df_sapi.at[idx, "ADG (kg/hari)"] = adg_baru
                
                save_data(df_sapi)
                add_activity_log(user_name, "Timbangan Berkala", f"Mencatat bobot baru Sapi Kode {data_sapi.get('Kode Sapi', '-')} (RFID {selected_tag}) -> {bobot_akhir} kg.")
                
                st.success("Timbangan berhasil disimpan!")
                st.rerun()