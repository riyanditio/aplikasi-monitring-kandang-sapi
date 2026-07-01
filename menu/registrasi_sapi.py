import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_registrasi(df_sapi, list_jenis_sapi, struktur_kandang, save_data, add_activity_log, user_name):
    st.subheader("➕ Registrasi Sapi Baru Masuk Kandang")
    st.markdown("Silakan masukkan data batch sapi baru. **Kode Tiba** bisa diisi sama untuk kuantiti sapi yang banyak.")

    with st.form("form_registrasi_sapi", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # --- PERBAIKAN: Menggunakan Kode Tiba sebagai identitas utama & BISA DUPLIKAT ---
            kode_tiba = st.text_input("Kode Tiba / No. Batch Kedatangan", placeholder="Contoh: S2").strip()
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
            # 1. Validasi Input Wajib
            if not kode_tiba:
                st.error("❌ Gagal Simpan! 'Kode Tiba / No. Batch Kedatangan' wajib diisi.")
                return

            # 2. Validasi Keunikan Elektronik (Hanya mengunci RFID Kandang jika diisi, agar data scan alat tidak tertukar)
            if rfid_tag_kandang and rfid_tag_kandang != "-":
                if not df_sapi.empty and "RFID/Tag" in df_sapi.columns:
                    if rfid_tag_kandang.lower() in df_sapi["RFID/Tag"].astype(str).str.lower().values:
                        st.error(f"❌ Gagal Simpan! RFID Kandang '{rfid_tag_kandang}' sudah digunakan oleh sapi lain.")
                        return

            # Gabungkan Nama Blok dan Pen untuk disimpan ke kolom 'Lokasi Pen' di database
            lokasi_pen_final = f"{pilihan_blok} - {pilihan_pen}"

            # Siapkan baris data baru dengan menyisipkan kolom 'RFID/Tag Asal' ke dalam database
            new_cow = {
                "Kode Tiba": kode_tiba,                                    # Menyimpan kode batch kelompok
                "Kode Sapi": kode_tiba,                                    # Disamakan dengan kode tiba agar backward-compatible dengan menu lain
                "RFID/Tag Asal": rfid_tag_asal if rfid_tag_asal else "-",  # Kolom Baru terintegrasi ke Sheet
                "RFID/Tag": rfid_tag_kandang if rfid_tag_kandang else "-",  # Key internal penunjuk tag kandang
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

            # Masukkan ke DataFrame dan simpan
            df_baru = pd.concat([df_sapi, pd.DataFrame([new_cow])], ignore_index=True)
            save_data(df_baru)
            
            # Catat ke log aktivitas operator
            add_activity_log(user_name, "Registrasi Sapi", f"Mendaftarkan Sapi Kelompok {kode_tiba} di {lokasi_pen_final}")
            
            st.success(f"🎉 Berhasil! Sapi dengan Kode Tiba {kode_tiba} telah berhasil didaftarkan di {lokasi_pen_final}.")
            st.balloons()
            st.rerun()