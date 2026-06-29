import streamlit as st
from datetime import datetime  # <-- WAJIB ADA untuk mencatat tanggal pemberian pakan

def tampilkan_menu_pakan(df_sapi, save_data, add_activity_log, user_name):
    st.subheader("🍽️ Log Logistik Pemberian Pakan Harian Sapi")
    if df_sapi.empty: 
        st.warning("Belum ada sapi.")
    else:
        pilihan_sapi = df_sapi["RFID/Tag"].astype(str).tolist()
        selected_tag = st.selectbox("Pilih Nomor Tag / RFID Sapi", pilihan_sapi)
        idx = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag].index[0]
        data_sapi = df_sapi.loc[idx]
        st.info(f"🐂 Kode: {data_sapi.get('Kode Sapi', '-')} | Jenis: {data_sapi['Jenis Sapi']} | Pen: {data_sapi['Lokasi Pen']} | Total Pakan Saat Ini: {data_sapi['Total Pakan (kg)']} kg")
        
        with st.form("form_pakan"):
            tgl_pakan = st.date_input("Tanggal Pemberian Pakan", datetime.now())
            pakan_hari_ini = st.number_input("Jumlah Pakan Hari Ini (kg)", min_value=0.0, value=15.0)
            
            if st.form_submit_button("Simpan & Akumulasikan"):
                df_sapi.at[idx, "Total Pakan (kg)"] = float(data_sapi["Total Pakan (kg)"]) + pakan_hari_ini
                df_sapi.at[idx, "Tgl Pakan Terakhir"] = tgl_pakan.strftime("%Y-%m-%d")
                
                save_data(df_sapi)
                add_activity_log(user_name, "Input Pakan", f"Menambahkan pakan sebanyak {pakan_hari_ini} kg ke Sapi Kode {data_sapi.get('Kode Sapi', '-')} (RFID {selected_tag}).")
                
                st.success("Pakan terupdate!")
                st.rerun()