import streamlit as st
import pandas as pd

def tampilkan_menu_edit_hapus(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, save_data, add_activity_log, user_name):
    st.subheader("⚙️ Koreksi Data Sapi")
    
    if df_sapi.empty: 
        st.warning("Tidak ada data sapi aktif.")
    else:
        selected_tag = st.selectbox("Pilih Nomor Tag / RFID yang akan Dikoreksi", df_sapi["RFID/Tag"].astype(str).tolist())
        idx = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag].index[0]
        data_sapi = df_sapi.loc[idx]
        
        with st.form("form_edit"):
            col1, col2 = st.columns(2)
            with col1:
                new_kode = st.text_input("Koreksi Kode Sapi", value=str(data_sapi.get("Kode Sapi", "-")))
                new_tag = st.text_input("Koreksi RFID", value=str(data_sapi["RFID/Tag"]))
                new_jenis = st.selectbox("Jenis", LIST_JENIS_SAPI, index=LIST_JENIS_SAPI.index(data_sapi["Jenis Sapi"]) if data_sapi["Jenis Sapi"] in LIST_JENIS_SAPI else 0)
                new_pen = st.selectbox("Koreksi Pen", DAFTAR_PEN, index=DAFTAR_PEN.index(data_sapi["Lokasi Pen"]) if data_sapi["Lokasi Pen"] in DAFTAR_PEN else 0)
            with col2:
                new_bobot_awal = st.number_input("Bobot Awal (kg)", min_value=50.0, value=float(data_sapi["Bobot Awal (kg)"]) if pd.notna(data_sapi["Bobot Awal (kg)"]) else 50.0)
                new_pakan = st.number_input("Total Pakan (kg)", min_value=0.0, value=float(data_sapi["Total Pakan (kg)"]) if pd.notna(data_sapi["Total Pakan (kg)"]) else 0.0)
            
            if st.form_submit_button("Simpan Perubahan"):
                df_sapi.at[idx, "Kode Sapi"] = new_kode.strip()
                df_sapi.at[idx, "RFID/Tag"] = new_tag
                df_sapi.at[idx, "Lokasi Pen"] = new_pen
                df_sapi.at[idx, "Bobot Awal (kg)"] = new_bobot_awal
                df_sapi.at[idx, "Total Pakan (kg)"] = new_pakan
                
                # Menjalankan fungsi simpan dan log yang dikirim dari app.py
                save_data(df_sapi)
                add_activity_log(user_name, "Koreksi Data Cepat", f"Koreksi cepat Sapi Kode {new_kode.strip()} (RFID {selected_tag}).")
                
                st.success("Koreksi berhasil!")
                st.rerun()