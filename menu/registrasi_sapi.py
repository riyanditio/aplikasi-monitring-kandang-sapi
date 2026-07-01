import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_registrasi(df_sapi, list_jenis_sapi, struktur_kandang, save_data, add_activity_log, user_name):
    st.subheader("➕ Registrasi Sapi Baru Masuk Kandang")
    st.markdown("Silakan masukkan data sapi baru secara lengkap untuk disimpan ke database.")

    with st.form("form_registrasi_sapi", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # 1. Penyesuaian Identitas Utama Sapi (Sesuai Dashboard Baru)
            kode_sapi = st.text_input("Kode Tiba / ID Anting", placeholder="Contoh: SP-001").strip()
            rfid_tag_asal = st.text_input("RFID / Tag Asal (Opsional)", placeholder="Scan/ketik RFID bawaan asal supplier").strip()
            rfid_tag_kandang = st.text_input("RFID / Tag Kandang (Opsional)", placeholder="Scan/ketik nomor RFID internal kandang").strip()
            
            st.markdown("---")
            jenis_sapi = st.selectbox("Jenis / Ras Sapi", list_jenis_sapi)
            jenis_kelamin = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"])

        with col2:
            umur_masuk = st.number_input("Estimasi Umur Masuk (Bulan)", min_value=1, max_value=120, value=12)
            asal_negara = st.text_input("Asal Negara / Daerah", placeholder="Contoh: Australia / Bali").strip()
            tgl_masuk = st.date_input("Tanggal Masuk Kandang", datetime.now().date())
            bobot_awal = st.number_input("Bobot Awal Masuk (kg)", min_value=50.0, max_value=1500.0, value=300.0, step=1.0)
            
            st.markdown("---")
            # --- FITUR DROPDOWN BERTINGKAT UNTUK LOKASI BLOK & PEN ---
            pilihan_blok = st.selectbox("Pilih Blok Kandang", list(struktur_kandang.keys()))
            
            # Mengambil daftar pen yang hanya ada di dalam blok terpilih
            daftar_pen_tersedia = struktur_kandang[pilihan_blok]
            pilihan_pen = st.selectbox("Pilih Nomor/Bagian Pen", daftar_pen_tersedia)

        st.markdown("---")
        submit_btn = st.form_submit_button("Simpan Data Sapi Baru", type="primary", use_container_width=True)

        if submit_btn:
            if not kode_sapi:
                st.error("❌ Gagal Simpan! 'Kode Tiba / ID Anting' wajib diisi.")
                return

            # Cek apakah Kode Sapi sudah terdaftar untuk menghindari duplikasi
            if not df_sapi.empty and kode_sapi.lower() in df_sapi["Kode Sapi"].astype(str).str.lower().values:
                st.error(f"❌ Gagal Simpan! Kode Tiba '{kode_sapi}' sudah terdaftar di sistem.")
                return

            # Gabungkan Nama Blok dan Pen untuk disimpan ke kolom 'Lokasi Pen' di database
            lokasi_pen_final = f"{pilihan_blok} - {pilihan_pen}"

            # Siapkan baris data baru dengan menyisipkan kolom 'RFID/Tag Asal' ke dalam database
            new_cow = {
                "Kode Sapi": kode_sapi,                             # Key internal tetap agar tidak merusak menu lain
                "RFID/Tag Asal": rfid_tag_asal if rfid_tag_asal else "-", # Kolom Baru terintegrasi ke Sheet
                "RFID/Tag": rfid_tag_kandang if rfid_tag_kandang else "-", # Key internal tetap penunjuk tag kandang
                "Jenis Sapi": jenis_sapi,
                "Jenis Kelamin": jenis_kelamin,
                "Umur Masuk (Bulan)": int(umur_masuk),
                "Asal Negara": asal_negara if asal_negara else "Lokal",
                "Tgl Masuk": tgl_masuk.strftime("%Y-%m-%d"),
                "Bobot Awal (kg)": float(bobot_awal),
                "Tgl Cek Akhir": tgl_masuk.strftime("%Y-%m-%d"),
                "Bobot Akhir (kg)": float(bobot_awal),
                "ADG (kg/hari)": 0.0,
                "Total Pakan (kg)": 0.0,
                "Tgl Pakan Terakhir": "-",
                "Lokasi Pen": lokasi_pen_final
            }

            # Masukkan ke DataFrame dan simpan (Pandas otomatis membuat kolom baru jika belum ada di database lama)
            df_baru = pd.concat([df_sapi, pd.DataFrame([new_cow])], ignore_index=True)
            save_data(df_baru)
            
            # Catat ke log aktivitas operator
            add_activity_log(user_name, "Registrasi Sapi", f"Mendaftarkan Sapi {kode_sapi} di {lokasi_pen_final}")
            
            st.success(f"🎉 Berhasil! Sapi dengan Kode Tiba {kode_sapi} telah berhasil didaftarkan di {lokasi_pen_final}.")
            st.balloons()
            st.rerun()