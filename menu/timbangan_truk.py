import streamlit as st
import pandas as pd
from datetime import datetime  # <-- WAJIB ADA untuk penomoran transaksi otomatis & tanggal timbang

def tampilkan_menu_timbangan_truk(df_truk, save_truk_data, add_activity_log, user_name):
    st.subheader("Summary Jembatan Timbang Kendaraan & Armada Sapi")
    tab_truk_input, tab_truk_histori = st.tabs(["➕ Input Timbangan Truk Baru", "📜 Riwayat Jembatan Timbang"])
    
    with tab_truk_input:
        st.write("### 📝 Form Pencatatan Timbangan Truk (Real-Time Kalkulasi)")
        with st.form("form_timbangan_truk"):
            col_tr1, col_tr2 = st.columns(2)
            with col_tr1:
                plat_nomor = st.text_input("1. Nomor Plat Kendaraan / No Lambung", placeholder="Contoh: B 9123 TAA").strip()
                tgl_timbang = st.date_input("2. Tanggal Penimbangan", datetime.now())
                ket_muatan = st.selectbox("3. Keterangan Status Muatan", [
                    "Sapi Masuk (Bongkar/Unloading dari Luar)", 
                    "Sapi Keluar (Muat/Loading Penjualan)", 
                    "Mutasi Antar Blok (Internal)", 
                    "Lain-lain"
                ])
                jml_sapi_truk = st.number_input("4. Jumlah Sapi di Dalam Truk (Ekor)", min_value=1, step=1, value=10)
            with col_tr2:
                bruto_kg = st.number_input("5. Berat Kotor / Bruto dalam kg", min_value=0.0, step=10.0, value=7500.0)
                tara_kg = st.number_input("6. Berat Kosong / Tara dalam kg", min_value=0.0, step=10.0, value=4000.0)
                
                netto_kg = bruto_kg - tara_kg
                if netto_kg < 0: 
                    netto_kg = 0.0
                avg_per_sapi = round(netto_kg / jml_sapi_truk, 1) if jml_sapi_truk > 0 else 0.0
                
                st.markdown("#### 📊 Hasil Kalkulasi Timbangan:")
                st.info(f"""
* **Berat Bersih Sapi (Netto):** {netto_kg:,} kg
* **Estimasi Rerata Berat / Ekor:** {avg_per_sapi:,} kg
                """)
                
            st.markdown("---")
            if st.form_submit_button("Simpan Log Timbangan Armada", type="primary"):
                if not plat_nomor:
                    st.error("❌ Gagal! Nomor Plat wajib diisi.")
                elif bruto_kg <= tara_kg:
                    st.error("❌ Gagal! Bruto harus lebih besar dari Tara.")
                else:
                    no_transaksi = f"TRK-{datetime.now().strftime('%d%H%M%S')}"
                    new_log_truk = {
                        "No Transaksi": no_transaksi, "Tanggal": tgl_timbang.strftime("%Y-%m-%d"),
                        "No Plat / Armada": plat_nomor.upper(), "Keterangan Muatan": ket_muatan,
                        "Bruto / Kotor (kg)": bruto_kg, "Tara / Kosong (kg)": tara_kg,
                        "Netto / Bersih (kg)": netto_kg, "Jumlah Sapi (Ekor)": int(jml_sapi_truk),
                        "Rata-rata / Ekor (kg)": avg_per_sapi, "Operator Lapangan": user_name
                    }
                    df_truk = pd.concat([df_truk, pd.DataFrame([new_log_truk])], ignore_index=True)
                    save_truk_data(df_truk)
                    add_activity_log(user_name, "Timbangan Truk", f"Pencatatan jembatan timbang No {no_transaksi} | Netto: {netto_kg} kg.")
                    st.success(f"🎉 Berhasil Disimpan! Transaksi {no_transaksi} tercatat.")
                    st.rerun()
                    
    with tab_truk_histori:
        st.write("### 📜 Riwayat Bongkar Muat Kendaraan")
        if df_truk.empty:
            st.info("Belum ada log penimbangan armada truk.")
        else:
            col_st1, col_st2, col_st3 = st.columns(3)
            col_st1.metric("Total Kendaraan Ditimbang", f"{len(df_truk)} Armada")
            col_st2.metric("Total Tonase Bersih", f"{df_truk['Netto / Bersih (kg)'].sum():,} kg")
            col_st3.metric("Total Sapi Termobilisasi", f"{int(df_truk['Jumlah Sapi (Ekor)'].sum())} Ekor")
            st.markdown("---")
            df_truk_tampil = df_truk.copy()
            df_truk_tampil.index = range(1, len(df_truk_tampil) + 1)
            st.dataframe(df_truk_tampil, use_container_width=True)