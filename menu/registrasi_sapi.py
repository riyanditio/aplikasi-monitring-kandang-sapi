import streamlit as st
import pandas as pd
from datetime import datetime  # <-- Diperlukan untuk mencatat tanggal masuk karantina

def tampilkan_menu_registrasi(df_sapi, LIST_JENIS_SAPI, save_data, add_activity_log, user_name):
    st.subheader("➕ Manajemen Registrasi Sapi Masuk")
    with st.form("form_registrasi"):
        col_a, col_b = st.columns(2)
        with col_a:
            kode_sapi_inp = st.text_input("Kode Sapi (Internal)", placeholder="Contoh: SP-001")
            tag_id = st.text_input("Nomor Tag / RFID Sapi")
            jenis_sapi_sel = st.selectbox("Pilih Jenis Sapi", LIST_JENIS_SAPI)
            jenis_kelamin = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"])
            umur_masuk = st.number_input("Umur saat Masuk (Bulan)", min_value=1, value=18)
        with col_b:
            asal = st.text_input("Negara/Daerah Asal", "Australia")
            tgl_masuk = st.date_input("Tanggal Masuk Karantina", datetime.now())
            bobot_awal = st.number_input("Bobot Awal Masuk (kg)", min_value=50.0, step=1.0)
        
        if st.form_submit_button("Daftarkan Sapi Keluar Karantina", type="primary"):
            if not tag_id: 
                st.error("RFID wajib diisi!")
            elif not kode_sapi_inp.strip(): 
                st.error("Kode Sapi wajib diisi!")
            elif not df_sapi.empty and tag_id in df_sapi["RFID/Tag"].values.astype(str): 
                st.error("RFID sudah ada!")
            else:
                new_cow = {
                    "Kode Sapi": kode_sapi_inp.strip(), "RFID/Tag": tag_id, "Jenis Sapi": jenis_sapi_sel, 
                    "Jenis Kelamin": jenis_kelamin, "Umur Masuk (Bulan)": int(umur_masuk), "Asal Negara": asal, 
                    "Tgl Masuk": tgl_masuk.strftime("%Y-%m-%d"), "Bobot Awal (kg)": bobot_awal, 
                    "Tgl Cek Akhir": tgl_masuk.strftime("%Y-%m-%d"), "Bobot Akhir (kg)": bobot_awal, 
                    "ADG (kg/hari)": 0.0, "Total Pakan (kg)": 0.0, "Tgl Pakan Terakhir": "-", "Locations Pen": "Pen Karantina"
                }
                df_sapi = pd.concat([df_sapi, pd.DataFrame([new_cow])], ignore_index=True)
                save_data(df_sapi)
                add_activity_log(user_name, "Registrasi Sapi", f"Mendaftarkan sapi baru Kode: {kode_sapi_inp.strip()} | RFID: {tag_id} | Bobot: {bobot_awal} kg.")
                st.success("Berhasil didaftarkan!")
                st.rerun()