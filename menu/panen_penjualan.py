import streamlit as st
import pandas as pd
from datetime import datetime

# Fungsi Helper untuk Format Rupiah Indonesia (Pemisah Titik)
def format_rupiah(angka):
    try:
        return f"Rp {int(float(angka)):,}".replace(",", ".")
    except:
        return "Rp 0"

# Fungsi Helper untuk Konversi Nilai Numerik yang Aman dari Database/CSV (Antisipasi ValueError)
def safe_float(val, default=0.0):
    try:
        if pd.isna(val) or str(val).strip() in ["", "-", "None", "NaN"]:
            return default
        return float(val)
    except:
        return default

def tampilkan_menu_panen_penjualan(df_sapi, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("💰 Manajemen Panen & Penjualan Sapi")
    tab_form_panen, tab_riwayat = st.tabs(["🛒 Proses Panen Sapi", "📑 Riwayat Sapi Terjual/Panen"])
    
    # Definisi kolom tabel data panen
    cols_panen = [
        "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", 
        "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", 
        "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", 
        "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"
    ]
    
    # [LAZY LOADING] Menarik data riwayat penjualan hanya saat menu ini aktif dibuka
    df_panen = read_sheet_to_df("data_panen", cols_panen)
    
    with tab_form_panen:
        if df_sapi.empty: 
            st.info("Tidak ada sapi aktif di kandang.")
        else:
            st.write("### 📝 Form Pencatatan Keluar / Panen")
            pilihan_sapi = df_sapi["RFID/Tag"].astype(str).tolist()
            selected_tag = st.selectbox("Pilih RFID Sapi yang Akan Dipanen:", options=pilihan_sapi)
            idx = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag].index[0]
            data_sapi = df_sapi.loc[idx]
            
            try: 
                hari_pelihara = (datetime.now().date() - datetime.strptime(str(data_sapi["Tgl Masuk"]), "%Y-%m-%d").date()).days
            except: 
                hari_pelihara = 1
            if hari_pelihara <= 0: 
                hari_pelihara = 1
            
            col_p1, col_p2 = st.columns(2)
            
            # --- KOLOM 1: INFORMASI LENGKAP SAPI ---
            with col_p1:
                st.info(f"""
* **Kode Sapi:** {data_sapi.get('Kode Sapi', '-')}
* **RFID/Tag Asal:** {data_sapi.get('RFID/Tag Asal', '-')}
* **RFID/Tag Baru:** {data_sapi['RFID/Tag']}
* **Jenis Sapi:** {data_sapi['Jenis Sapi']}
* **Lama Pelihara:** {hari_pelihara} Hari
* **Bobot Awal Masuk:** {safe_float(data_sapi.get('Bobot Awal (kg)'))} kg
                """)
                
            # --- KOLOM 2: FORM PROSES INPUT PANEN ---
            with col_p2:
                tgl_panen = st.date_input("Tanggal Panen", datetime.now().date())
                
                bobot_akhir_default = safe_float(data_sapi.get('Bobot Akhir (kg)'), 50.0)
                if bobot_akhir_default < 50.0:
                    bobot_akhir_default = 50.0
                    
                bobot_panen = st.number_input("Bobot Timbangan Saat Panen (kg)", min_value=50.0, value=float(bobot_akhir_default))
                harga_per_kg = st.number_input("Harga Jual per kg (Rp)", min_value=0, value=52000, step=1000)
                
                st.caption(f"Format Terbaca: :green[**{format_rupiah(harga_per_kg)}** / kg]")
                pembeli = st.text_input("Nama Pembeli / RPH", placeholder="Contoh: RPH Cakung")
                
                # Hitung data kalkulasi secara real-time
                bobot_awal_safe = safe_float(data_sapi.get('Bobot Awal (kg)'))
                total_gain = float(bobot_panen - bobot_awal_safe)
                adg_final = round(total_gain / hari_pelihara, 2)
                
                total_pakan_safe = safe_float(data_sapi.get('Total Pakan (kg)'))
                fcr_final = round(total_pakan_safe / total_gain, 2) if total_gain > 0 else 0.0
                total_pendapatan = int(bobot_panen * harga_per_kg)
                
                st.markdown("---")
                st.markdown("##### 📊 Estimasi Hasil Panen Sapi Ini:")
                cm1, cm2 = st.columns(2)
                with cm1:
                    st.metric("Total Gain (Kenaikan)", f"{total_gain:+.1f} kg")
                    st.metric("FCR Akhir", f"{fcr_final:.2f}")
                with cm2:
                    st.metric("ADG Akhir", f"{adg_final:.2f} kg/hari")
                    st.metric("Total Pendapatan", format_rupiah(total_pendapatan))
                
                st.markdown("---")
                
                if st.button("SAH-KAN PANEN", type="primary", use_container_width=True):
                    if harga_per_kg <= 0:
                        st.error("Harga jual harus lebih besar dari Rp 0!")
                    else:
                        with st.spinner("⏳ Memproses transaksi panen..."):
                            data_panen_baru = {
                                "Kode Sapi": data_sapi.get('Kode Sapi', '-'), 
                                "RFID/Tag": data_sapi['RFID/Tag'], 
                                "Jenis Sapi": data_sapi['Jenis Sapi'], 
                                "Jenis Kelamin": data_sapi['Jenis Kelamin'], 
                                "Asal Negara": data_sapi['Asal Negara'], 
                                "Tgl Masuk": data_sapi['Tgl Masuk'], 
                                "Tgl Panen": tgl_panen.strftime("%Y-%m-%d"),
                                "Lama Pelihara (Hari)": int(hari_pelihara), 
                                "Bobot Awal (kg)": bobot_awal_safe,
                                "Bobot Panen (kg)": bobot_panen, 
                                "Total Gain (kg)": total_gain,
                                "Total Pakan (kg)": total_pakan_safe, 
                                "FCR Akhir": fcr_final,
                                "ADG Akhir (kg/hari)": adg_final, 
                                "Harga Jual /kg (Rp)": harga_per_kg,
                                "Total Pendapatan (Rp)": total_pendapatan, 
                                "Pembeli/Tujuan": pembeli
                            }
                            df_panen = pd.concat([df_panen, pd.DataFrame([data_panen_baru])], ignore_index=True)
                            write_df_to_sheet("data_panen", df_panen, cols_panen)
                            df_sapi = df_sapi.drop(idx)
                            save_data(df_sapi)
                            add_activity_log(user_name, "Panen Sapi", f"Memanen Sapi Kode {data_sapi.get('Kode Sapi', '-')} | Pendapatan: {format_rupiah(total_pendapatan)}")
                            
                        st.success(f"🎉 Sukses! Sapi RFID {selected_tag} Berhasil Dipanen.")
                        st.rerun()
                            
    with tab_riwayat:
        st.write("### 📑 Riwayat Sapi Terjual/Panen")
        if df_panen.empty: 
            st.info("Belum ada riwayat panen.")
        else:
            bobot_panen_series = pd.to_numeric(df_panen['Bobot Panen (kg)'], errors='coerce').fillna(0)
            total_pendapatan_series = pd.to_numeric(df_panen['Total Pendapatan (Rp)'], errors='coerce').fillna(0)
            
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("Total Sapi Terjual", f"{len(df_panen)} Ekor")
            col_r2.metric("Total Pendapatan Kotor", format_rupiah(total_pendapatan_series.sum()))
            col_r3.metric("Rerata Bobot Panen", f"{round(bobot_panen_series.mean(), 1)} kg")
            st.markdown("---")
            
            df_panen_tampil = df_panen.copy()
            df_panen_tampil.index = range(1, len(df_panen_tampil) + 1)
            
            if "Harga Jual /kg (Rp)" in df_panen_tampil.columns:
                df_panen_tampil["Harga Jual /kg (Rp)"] = df_panen_tampil["Harga Jual /kg (Rp)"].apply(format_rupiah)
            if "Total Pendapatan (Rp)" in df_panen_tampil.columns:
                df_panen_tampil["Total Pendapatan (Rp)"] = df_panen_tampil["Total Pendapatan (Rp)"].apply(format_rupiah)
            
            st.dataframe(df_panen_tampil, use_container_width=True)