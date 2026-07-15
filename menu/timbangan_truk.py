import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_timbangan_truk(add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🚛 Timbangan Armada Truk (Logistik & Manifest)")
    st.markdown("Pencatatan berat jembatan timbang untuk kontrol armada logistik dan manifestasi muatan sapi.")

    # Definisi kolom tabel jembatan timbang
    cols_truk = [
        "No Transaksi", "Tanggal", "Nama Lokasi Penimbangan", "No Plat / Armada", 
        "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", 
        "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Daftar RFID/EarTag", 
        "Rata-rata / Ekor (kg)", "Operator Lapangan"
    ]
    
    # [LAZY LOADING] Menarik data hanya saat menu ini aktif dibuka oleh user
    df_truk = read_sheet_to_df("timbangan_truk", cols_truk)

    with st.form("form_timbangan_truk", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            no_transaksi = st.text_input("No Transaksi (Otomatis jika kosong)", placeholder="Contoh: TRK-2026-001").strip()
            tgl_timbang = st.date_input("Tanggal Penimbangan", datetime.now().date())
            
            # Pilihan Lokasi Penimbangan Komprehensif
            lokasi_timbang = st.selectbox("Nama Lokasi Penimbangan", [
                "Jembatan Timbang Utama (Kandang)", 
                "Timbangan Digital Area Karantina",
                "Jembatan Timbang Pelabuhan Dalam Negeri",
                "Timbangan Luar / Pihak Ketiga"
            ])
            
            no_plat = st.text_input("No Plat / Armada Truk", placeholder="Contoh: B 9123 FDA").strip()
            
            # --- INTEGRASI TOTAL OPSI STATUS MUATAN (LAMA + BARU) ---
            opsi_muatan = [
                "Sapi Masuk (Bongkar/Unloading dari Luar)",
                "Sapi Keluar (Muat/Loading Penjualan)",
                "sapi kedatangan (pelabuhan dalam negeri)",
                "sapi keberangkatan (pelabuhan negara asal)",
                "Mutasi Antar Blok (Internal)",
                "Pakan Ternak / Konsentrat / Hijauan",
                "Logistik Umum / Muatan Lain",
                "Lain-lain"
            ]
            keterangan_muatan = st.selectbox("Keterangan Status Muatan", opsi_muatan)

        with col2:
            bruto = st.number_input("Bruto / Berat Kotor (kg)", min_value=0.0, value=0.0, step=10.0)
            tara = st.number_input("Tara / Berat Kosong Truk (kg)", min_value=0.0, value=0.0, step=10.0)
            jumlah_sapi = st.number_input("Jumlah Sapi didalam Truk (Ekor)", min_value=0, value=0, step=1)
            
            # Daftar RFID/EarTag Manifest
            rfid_list = st.text_area(
                "Daftar RFID / EarTAG didalam Truk", 
                placeholder="Scan atau ketik nomor RFID/EarTag di sini.\nGunakan tombol Enter untuk memisahkan setiap ID sapi.",
                help="Bisa digunakan untuk memisahkan manifestasi data sapi per armada truk."
            ).strip()

        st.markdown("---")
        submit_btn = st.form_submit_button("Simpan Manifest Timbangan Truk", type="primary", use_container_width=True)

        if submit_btn:
            if not no_plat:
                st.error("❌ Gagal Simpan! No Plat / Armada Truk wajib diisi.")
                return
            if bruto <= 0:
                st.error("❌ Gagal Simpan! Berat bruto harus lebih besar dari 0 kg.")
                return
            
            # Hitung Netto (Berat Bersih Muatan)
            netto = bruto - tara
            if netto < 0:
                st.error("❌ Gagal Simpan! Berat kosong (Tara) tidak boleh melebihi berat kotor (Bruto).")
                return

            # Hitung rata-rata bobot per ekor di dalam truk
            rata_per_ekor = round(netto / jumlah_sapi, 2) if jumlah_sapi > 0 else 0.0

            # Generate otomatis No Transaksi jika dikosongkan operator
            if not no_transaksi:
                waktu_str = datetime.now().strftime("%Y%m%d-%H%M%S")
                no_transaksi = f"TRK-{waktu_str}"

            # Susun baris data baru sesuai struktur kolom database utama
            new_truk_row = {
                "No Transaksi": no_transaksi,
                "Tanggal": tgl_timbang.strftime("%Y-%m-%d"),
                "Nama Lokasi Penimbangan": lokasi_timbang,
                "No Plat / Armada": no_plat,
                "Keterangan Muatan": keterangan_muatan,
                "Bruto / Kotor (kg)": float(bruto),
                "Tara / Kosong (kg)": float(tara),
                "Netto / Bersih (kg)": float(netto),
                "Jumlah Sapi (Ekor)": int(jumlah_sapi),
                "Daftar RFID/EarTag": rfid_list if rfid_list else "-",
                "Rata-rata / Ekor (kg)": float(rata_per_ekor),
                "Operator Lapangan": user_name
            }

            # Gabungkan dan simpan langsung menggunakan fungsi database utama
            df_baru = pd.concat([df_truk, pd.DataFrame([new_truk_row])], ignore_index=True)
            write_df_to_sheet("timbangan_truk", df_baru, cols_truk)

            # Catat log audit aktivitas
            add_activity_log(user_name, "Timbangan Truk", f"Mencatat {keterangan_muatan} armada {no_plat} di {lokasi_timbang}")
            
            st.success(f"🎉 Berhasil menyimpan data manifest timbangan armada {no_plat}! Bersih muatan: {netto} kg.")
            st.balloons()
            st.rerun()

    # Tampilkan Tabel Riwayat Historis Logistik
    st.markdown("### 📜 Riwayat Catatan Timbangan Armada Truk")
    if not df_truk.empty:
        st.dataframe(df_truk.sort_values(by="Tanggal", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat timbangan truk yang tercatat di sistem.")