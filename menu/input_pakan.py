import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_pakan(df_sapi, struktur_kandang, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🍽️ Input Pemberian Pakan Harian per Pen")
    st.markdown("Pilih lokasi pen untuk mencatat berat pakan. Sistem akan otomatis membagi rata pakan ke seluruh sapi di pen tersebut.")

    # --- BLOCK 1: PILIHAN HIRARKI LOKASI KANDANG ---
    col_a, col_b = st.columns(2)
    with col_a:
        pilihan_blok = st.selectbox("1. Pilih Blok Kandang", list(struktur_kandang.keys()))
    with col_b:
        daftar_pen_tersedia = struktur_kandang[pilihan_blok]
        pilihan_pen = st.selectbox("2. Pilih Nomor / Bagian Pen", daftar_pen_tersedia)

    # Gabungkan menjadi format database utama
    lokasi_pen_final = f"{pilihan_blok} - {pilihan_pen}"

    # --- BLOCK 2: DETEKSI POLRASI SAPI DI PEN ---
    if not df_sapi.empty:
        df_sapi_pen = df_sapi[df_sapi["Lokasi Pen"].astype(str).str.strip().str.lower() == lokasi_pen_final.strip().lower()]
        jumlah_sapi = len(df_sapi_pen)
    else:
        df_sapi_pen = pd.DataFrame()
        jumlah_sapi = 0

    # Tampilkan informasi populasi pen secara informatif
    st.info(f"📊 **Status Lokasi:** {lokasi_pen_final} saat ini berisi **{jumlah_sapi} ekor** sapi.")

    # --- BLOCK 3: FORM INPUT PAKAN ---
    st.markdown("---")
    with st.form("form_input_pakan", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            jenis_pakan = st.selectbox("Jenis Pakan", ["Konsentrat", "Hijauan / Silase", "Pakan Campuran (TMR)", "Suplemen / Vitamin"])
            tgl_pakan = st.date_input("Tanggal Pemberian Pakan", datetime.now().date())
        
        with col2:
            total_pakan_kg = st.number_input("Total Berat Pakan Dikucurkan (kg)", min_value=0.0, max_value=5000.0, value=50.0, step=5.0, help="Input total berat pakan yang diberikan untuk SATU PEN ini.")
            
            # Hitung estimasi jatah per ekor secara real-time di UI
            jatah_per_ekor = round(total_pakan_kg / jumlah_sapi, 2) if jumlah_sapi > 0 else 0.0
            st.write(f"⚖️ *Estimasi Konsumsi: ~{jatah_per_ekor} kg / ekor*")

        submit_pakan = st.form_submit_button("Simpan & Distribusikan Pakan", type="primary", use_container_width=True)

        if submit_pakan:
            if total_pakan_kg <= 0:
                st.error("❌ Gagal Simpan! Total berat pakan harus lebih dari 0 kg.")
                return

            if jumlah_sapi == 0:
                st.warning("⚠️ Perhatian: Tidak ada sapi aktif di pen ini. Data pakan hanya akan dicatat di Log Histori Pakan saja.")
            
            # 1. Update data akumulasi pakan di database utama (jika ada sapinya)
            if jumlah_sapi > 0:
                # Cari indeks baris sapi-sapi yang berada di pen tersebut
                indeks_sapi_pen = df_sapi[df_sapi["Lokasi Pen"].astype(str).str.strip().str.lower() == lokasi_pen_final.strip().lower()].index
                
                # Tambahkan jatah pakan per ekor ke kolom 'Total Pakan (kg)' dan update tanggalnya
                df_sapi.loc[indeks_sapi_pen, "Total Pakan (kg)"] = df_sapi.loc[indeks_sapi_pen, "Total Pakan (kg)"].astype(float) + jatah_per_ekor
                df_sapi.loc[indeks_sapi_pen, "Tgl Pakan Terakhir"] = tgl_pakan.strftime("%Y-%m-%d")
                
                # Simpan dataframe utama yang diperbarui
                save_data(df_sapi)

            # 2. Catat histori pengucuran pakan ke Google Sheets tab 'log_pakan'
            cols_log_pakan = ["Tanggal", "Lokasi Pen", "Jumlah Sapi (Ekor)", "Jenis Pakan", "Total Pakan (kg)", "Rata-rata/Ekor (kg)", "Operator"]
            df_histori_pakan = read_sheet_to_df("log_pakan", cols_log_pakan)
            
            new_log_pakan = {
                "Tanggal": tgl_pakan.strftime("%Y-%m-%d"),
                "Lokasi Pen": lokasi_pen_final,
                "Jumlah Sapi (Ekor)": int(jumlah_sapi),
                "Jenis Pakan": jenis_pakan,
                "Total Pakan (kg)": float(total_pakan_kg),
                "Rata-rata/Ekor (kg)": float(jatah_per_ekor),
                "Operator": user_name
            }
            
            df_histori_pakan = pd.concat([df_histori_pakan, pd.DataFrame([new_log_pakan])], ignore_index=True)
            write_df_to_sheet("log_pakan", df_histori_pakan, cols_log_pakan)

            # 3. Catat ke log aktivitas audit operator global
            add_activity_log(user_name, "Input Pakan", f"Mengisi {jenis_pakan} sebanyak {total_pakan_kg}kg di {lokasi_pen_final}")
            
            st.success(f"🎉 Berhasil! Pakan {jenis_pakan} sebesar {total_pakan_kg} kg telah dicatat untuk {lokasi_pen_final}.")
            st.balloons()

    # --- BLOCK 4: TABEL RIWAYAT HISTORI PANDANGAN ---
    st.markdown("### 📜 Riwayat Pengucuran Pakan Terakhir")
    cols_log_pakan = ["Tanggal", "Lokasi Pen", "Jumlah Sapi (Ekor)", "Jenis Pakan", "Total Pakan (kg)", "Rata-rata/Ekor (kg)", "Operator"]
    df_view_pakan = read_sheet_to_df("log_pakan", cols_log_pakan)
    
    if not df_view_pakan.empty:
        # Urutkan dari tanggal terbaru di atas
        df_view_pakan = df_view_pakan.sort_values(by="Tanggal", ascending=False).head(10)
        st.dataframe(df_view_pakan, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat pemberian pakan yang tercatat.")