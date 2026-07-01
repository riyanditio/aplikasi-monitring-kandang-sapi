import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name):
    st.subheader("⚖️ Input Pencatatan Timbangan Berkala Sapi")
    st.markdown("Gunakan filter Blok & Pen untuk mempercepat pencarian sapi yang sedang berada di jembatan timbang.")

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi aktif yang tersedia untuk ditimbang.")
        return

    # --- FIX: Paksa kolom numerik menjadi Float agar tidak memicu TypeError saat input desimal ---
    df_sapi["Bobot Awal (kg)"] = pd.to_numeric(df_sapi["Bobot Awal (kg)"], errors='coerce').fillna(0.0).astype(float)
    df_sapi["Bobot Akhir (kg)"] = pd.to_numeric(df_sapi["Bobot Akhir (kg)"], errors='coerce').fillna(0.0).astype(float)
    df_sapi["ADG (kg/hari)"] = pd.to_numeric(df_sapi["ADG (kg/hari)"], errors='coerce').fillna(0.0).astype(float)

    TARGET_ADG = 1.6

    list_lokasi_eksis = df_sapi["Lokasi Pen"].unique()
    grid_filter = {}
    for item in list_lokasi_eksis:
        if " - " in str(item):
            b, p = str(item).split(" - ", 1)
            if b not in grid_filter:
                grid_filter[b] = []
            grid_filter[b].append(p)
        else:
            if "Format Lama" not in grid_filter:
                grid_filter["Format Lama"] = []
            grid_filter["Format Lama"].append(str(item))

    st.markdown("#### 🔍 Saring Sapi Berdasarkan Lokasi")
    cf1, cf2 = st.columns(2)
    with cf1:
        filter_blok = st.selectbox("Pilih Blok Kandang Sapi:", list(grid_filter.keys()))
    with cf2:
        filter_pen = st.selectbox("Pilih Nomor/Bagian Pen Sapi:", list(set(grid_filter[filter_blok])))

    lokasi_pencarian = f"{filter_blok} - {filter_pen}" if filter_blok != "Format Lama" else filter_pen
    df_sapi_terfilter = df_sapi[df_sapi["Lokasi Pen"] == lokasi_pencarian]

    if df_sapi_terfilter.empty:
        st.info(f"ℹ️ Pen **{lokasi_pencarian}** saat ini sedang tidak diisi oleh sapi aktif.")
        return

    opsi_sapi = df_sapi_terfilter.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
    sapi_pilihan = st.selectbox("Pilih Kode Sapi Yang Ditimbang:", opsi_sapi)
    
    kode_sapi_asli = sapi_pilihan.split(" - ")[0]
    idx_master = df_sapi[df_sapi["Kode Sapi"] == kode_sapi_asli].index[0]
    row_sapi = df_sapi.iloc[idx_master]

    is_penimbangan_pertama = (str(row_sapi['Tgl Cek Akhir']) == str(row_sapi['Tgl Masuk']))
    status_timbang_text = "🟢 PENIMBANGAN PERTAMA (Evaluasi Awal Masa Karantina)" if is_penimbangan_pertama else "🔵 PENIMBANGAN BERKALA / RUTIN"

    # --- INTEGRASI: Menampilkan RFID/Tag Asal di Kartu Informasi Historis Timbangan ---
    st.info(f"📋 **Data Historis Sapi:** ({status_timbang_text})\n* Tanggal Masuk Area: {row_sapi['Tgl Masuk']} | Berat Awal: {row_sapi['Bobot Awal (kg)']} kg\n* RFID Asal: {row_sapi.get('RFID/Tag Asal', '-')} | RFID Baru: {row_sapi['RFID/Tag']}\n* Timbangan Terakhir: {row_sapi['Tgl Cek Akhir']} | Berat Akhir: {row_sapi['Bobot Akhir (kg)']} kg")

    st.markdown("---")
    with st.form("form_timbangan_berkala", clear_on_submit=True):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tgl_timbang_sekarang = st.date_input("Tanggal Penimbangan Hari Ini", datetime.now().date())
        with col_t2:
            bobot_timbang_baru = st.number_input("Hasil Berat Timbangan Baru (kg)", min_value=30.0, max_value=1500.0, value=float(row_sapi["Bobot Akhir (kg)"]), step=1.0)

        submit_timbang = st.form_submit_button("Simpan & Kalkulasi ADG Baru", type="primary", use_container_width=True)

        if submit_timbang:
            adg_terbaru = float(calculate_adg(row_sapi["Tgl Masuk"], row_sapi["Bobot Awal (kg)"], tgl_timbang_sekarang.strftime("%Y-%m-%d"), bobot_timbang_baru))
            
            df_sapi.at[idx_master, "Tgl Cek Akhir"] = tgl_timbang_sekarang.strftime("%Y-%m-%d")
            df_sapi.at[idx_master, "Bobot Akhir (kg)"] = float(bobot_timbang_baru)
            df_sapi.at[idx_master, "ADG (kg/hari)"] = adg_terbaru
            
            save_data(df_sapi)
            add_activity_log(user_name, "Timbangan Rutin", f"Menimbang Sapi {row_sapi['Kode Sapi']} di {row_sapi['Lokasi Pen']} dengan bobot {bobot_timbang_baru}kg (ADG Baru: {adg_terbaru} kg/hari)")
            
            if adg_terbaru < TARGET_ADG:
                st.error(f"⚠️ **ALARM PERFORMA RENDAH:** Sapi {row_sapi['Kode Sapi']} berhasil disimpan. ADG hasil timbangan berkala ini hanya mencapai `{adg_terbaru} kg/hari` (Di bawah target standar {TARGET_ADG} kg/hari). Direkomendasikan cek kesehatan/pakan.")
            else:
                st.success(f"🎉 Sukses! Bobot Sapi {row_sapi['Kode Sapi']} diperbarui ke {bobot_timbang_baru} kg dengan capaian ADG Bagus: `{adg_terbaru} kg/hari`.")
                st.balloons()
            st.rerun()