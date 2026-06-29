import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

def tampilkan_menu_pakan(df_sapi, save_data, add_activity_log, user_name, read_sheet_to_df=None, write_df_to_sheet=None):
    st.subheader("🍽️ Input Pakan Harian Sapi")
    
    # Konfigurasi zona waktu lokal WIB (UTC+7)
    zona_wib = timezone(timedelta(hours=7))
    tgl_hari_ini = datetime.now(zona_wib).strftime("%Y-%m-%d")
    waktu_sekarang = datetime.now(zona_wib).strftime("%H:%M:%S")

    # Skema kolom untuk database riwayat pakan
    cols_riwayat = ["Tanggal", "Waktu", "Metode", "Pen/Lokasi", "Kode Sapi", "RFID/Tag", "Jumlah Pakan (kg)", "Operator"]

    # Ambil data riwayat pakan dari Google Sheets / CSV Lokal
    if read_sheet_to_df and write_df_to_sheet:
        df_riwayat = read_sheet_to_df("riwayat_pakan", cols_riwayat)
    else:
        if os.path.exists("riwayat_pakan.csv"):
            df_riwayat = pd.read_csv("riwayat_pakan.csv")
        else:
            df_riwayat = pd.DataFrame(columns=cols_riwayat)

    # Membagi visualisasi menjadi 2 Tab: Input Data & Riwayat Data
    tab_input, tab_riwayat = st.tabs(["➕ Input Pakan Baru", "📜 Riwayat Pemberian Pakan"])

    # ==================== TAB 1: INPUT PAKAN BARU ====================
    with tab_input:
        if df_sapi.empty:
            st.warning("⚠️ Belum ada data sapi aktif di dalam kandang. Jalankan Registrasi Sapi Baru terlebih dahulu.")
            return

        st.markdown("### 📋 Pilih Metode Distribusi Pakan")
        metode = st.radio("Metode Penginputan:", ["Individu (Per Ekor Sapi)", "Serentak (Per Pen / Kandang)"], horizontal=True)
        st.markdown("---")

        # --- OPSI A: INPUT PAKAN PER EKOR INDIVIDU ---
        if metode == "Individu (Per Ekor Sapi)":
            st.markdown("#### 🐂 Input Pakan Per Ekor Sapi")
            
            # Gabungkan informasi kode, rfid, dan pen saat ini agar operator tidak tertukar
            opsi_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - {r['RFID/Tag']} ({r['Lokasi Pen']})", axis=1).tolist()
            pilihan_sapi = st.selectbox("Pilih Sapi Sasaran:", opsi_sapi)
            
            idx_terpilih = opsi_sapi.index(pilihan_sapi)
            sapi_row = df_sapi.iloc[idx_terpilih]
            
            jumlah_pakan = st.number_input("Jumlah Volume Pakan (kg):", min_value=0.1, max_value=100.0, value=10.0, step=0.5)
            
            if st.button("Simpan Pakan Individu", type="primary", use_container_width=True):
                # Validasi nilai pakan lama jika kosong
                pakan_lama = sapi_row["Total Pakan (kg)"]
                pakan_lama_float = float(pakan_lama) if pd.notna(pakan_lama) and str(pakan_lama).strip() != "" else 0.0
                
                # Update data utama sapi
                df_sapi.at[idx_terpilih, "Total Pakan (kg)"] = pakan_lama_float + jumlah_pakan
                df_sapi.at[idx_terpilih, "Tgl Pakan Terakhir"] = tgl_hari_ini
                save_data(df_sapi)
                
                # Masukkan entri baru ke dataframe riwayat pakan
                new_entry = {
                    "Tanggal": tgl_hari_ini,
                    "Waktu": waktu_sekarang,
                    "Metode": "Individu",
                    "Pen/Lokasi": sapi_row["Lokasi Pen"],
                    "Kode Sapi": sapi_row["Kode Sapi"],
                    "RFID/Tag": sapi_row["RFID/Tag"],
                    "Jumlah Pakan (kg)": jumlah_pakan,
                    "Operator": user_name
                }
                df_riwayat = pd.concat([df_riwayat, pd.DataFrame([new_entry])], ignore_index=True)
                
                if write_df_to_sheet:
                    write_df_to_sheet("riwayat_pakan", df_riwayat, cols_riwayat)
                else:
                    df_riwayat.to_csv("riwayat_pakan.csv", index=False)
                    
                add_activity_log(user_name, "Input Pakan Individu", f"Menginput pakan {jumlah_pakan} kg untuk Sapi {sapi_row['Kode Sapi']}")
                st.success(f"✅ Berhasil mencatat pakan {jumlah_pakan} kg untuk Sapi {sapi_row['Kode Sapi']}!")
                st.rerun()

        # --- OPSI B: INPUT PAKAN SERENTAK PER PEN (PERMINTAAN ANDA) ---
        else:
            st.markdown("#### 🏠 Input Pakan Serentak Berdasarkan Pen / Blok")
            daftar_pen = ["Pen Karantina", "Pen A (Bobot < 350kg)", "Pen B (Bobot 350-450kg)", "Pen C (Bobot > 450kg)", "Pen D (Khusus/Isolasi Sakit)"]
            selected_pen = st.selectbox("Pilih Target Pen Kandang:", daftar_pen)
            
            # Filter populasi sapi yang benar-benar ada di dalam pen tersebut saat ini
            sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == selected_pen]
            jumlah_sapi = len(sapi_di_pen)
            
            if jumlah_sapi == 0:
                st.warning(f"ℹ️ Tidak ditemukan adanya sapi aktif di dalam {selected_pen} saat ini.")
            else:
                st.info(f"📊 Deteksi Sistem: Ada **{jumlah_sapi} ekor** sapi aktif di dalam **{selected_pen}**.")
            
            jumlah_pakan_per_ekor = st.number_input("Jumlah Pakan RATA-RATA per Ekor (kg):", min_value=0.1, max_value=100.0, value=15.0, step=0.5)
            total_pakan_pen = jumlah_pakan_per_ekor * jumlah_sapi
            
            st.metric("Estimasi Total Berkas Keluar Pakan Pen", f"{total_pakan_pen:,.1f} kg", help="Hasil kali antara jumlah sapi di pen dengan pakan per ekor.")
            
            if st.button("🚀 Eksekusi Pemberian Pakan Serentak", type="primary", use_container_width=True):
                if jumlah_sapi == 0:
                    st.error("❌ Gagal menyimpan! Pengisian ditolak karena tidak ada sapi di pen ini.")
                else:
                    new_entries = []
                    
                    # Looping massal untuk memperbarui seluruh sapi di dalam pen terpilih
                    for idx, row in sapi_di_pen.iterrows():
                        pakan_lama = df_sapi.at[idx, "Total Pakan (kg)"]
                        pakan_lama_float = float(pakan_lama) if pd.notna(pakan_lama) and str(pakan_lama).strip() != "" else 0.0
                        
                        # Tambahkan pakan ke masing-masing sapi
                        df_sapi.at[idx, "Total Pakan (kg)"] = pakan_lama_float + jumlah_pakan_per_ekor
                        df_sapi.at[idx, "Tgl Pakan Terakhir"] = tgl_hari_ini
                        
                        # Buat catatan riwayat log terpisah per ekor demi audit data timbangan berkala nanti
                        new_entries.append({
                            "Tanggal": tgl_hari_ini,
                            "Waktu": waktu_sekarang,
                            "Metode": "Serentak Pen",
                            "Pen/Lokasi": selected_pen,
                            "Kode Sapi": row["Kode Sapi"],
                            "RFID/Tag": row["RFID/Tag"],
                            "Jumlah Pakan (kg)": jumlah_pakan_per_ekor,
                            "Operator": user_name
                        })
                    
                    # Simpan data master utama sapi
                    save_data(df_sapi)
                    
                    # Gabungkan riwayat pakan baru ke database utama log pakan
                    df_riwayat = pd.concat([df_riwayat, pd.DataFrame(new_entries)], ignore_index=True)
                    if write_df_to_sheet:
                        write_df_to_sheet("riwayat_pakan", df_riwayat, cols_riwayat)
                    else:
                        df_riwayat.to_csv("riwayat_pakan.csv", index=False)
                        
                    # Catat transaksi ke log aktivitas sistem utama
                    add_activity_log(user_name, "Input Pakan Serentak", f"Menginput pakan serentak {jumlah_pakan_per_ekor} kg/ekor untuk {jumlah_sapi} ekor di {selected_pen}")
                    st.success(f"🔥 Sukses! Seluruh sapi ({jumlah_sapi} ekor) di {selected_pen} otomatis terisi masing-masing {jumlah_pakan_per_ekor} kg!")
                    st.rerun()

    # ==================== TAB 2: RIWAYAT PEMBERIAN PAKAN ====================
    with tab_riwayat:
        st.markdown("### 📜 Log Riwayat Pemberian Pakan Harian")
        
        if df_riwayat.empty:
            st.info("ℹ️ Belum ada riwayat aktivitas pemberian pakan yang terekam.")
        else:
            # Sediakan filter dinamis untuk memudahkan peninjauan mandor kandang
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_pen = st.selectbox("Saring Lokasi Pen:", ["Semua"] + list(df_riwayat["Pen/Lokasi"].unique()))
            with col_f2:
                filter_metode = st.selectbox("Saring Jenis Input:", ["Semua", "Individu", "Serentak Pen"])
            
            df_filtered = df_riwayat.copy()
            if filter_pen != "Semua":
                df_filtered = df_filtered[df_filtered["Pen/Lokasi"] == filter_pen]
            if filter_metode != "Semua":
                df_filtered = df_filtered[df_filtered["Metode"] == filter_metode]
            
            # Balik data agar entri pakan terbaru selalu berada di paling atas tabel
            df_display = df_filtered.sort_values(by=["Tanggal", "Waktu"], ascending=False).reset_index(drop=True)
            st.dataframe(df_display, use_container_width=True)
            
            # Kalkulasi total muatan pakan yang keluar berdasarkan hasil filter
            total_pakan_terdistribusi = df_display["Jumlah Pakan (kg)"].astype(float).sum()
            st.metric("Total Pakan Terpakai di Lapangan (Sesuai Filter)", f"{total_pakan_terdistribusi:,.1f} kg")