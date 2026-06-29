import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_pen_mutasi(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, user_role, calculate_adg, save_data, add_activity_log, user_name):
    st.subheader("🏠 Manajemen Stok Populasi per Pen & Mutasi Kandang")
    tab_stok, tab_pindah = st.tabs(["📊 Stok Populasi per Pen", "🔄 Mutasi (Pindah Kandang)"])
    
    with tab_stok:
        st.markdown("### 🔍 Panel Filter & Pencarian Sapi")
        with st.expander("Klik di sini untuk membuka/menutup parameter pencarian", expanded=True):
            col_f0_a, col_f0, col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1, 1, 1.2])
            
            with col_f0_a:
                search_kode = st.text_input("1. Cari Kode Sapi", placeholder="Ketik kode sapi...")
            with col_f0:
                search_rfid = st.text_input("2. Cari RFID / Tag", placeholder="Ketik nomor RFID...")
            with col_f1:
                filter_jenis = st.selectbox("3. Jenis Sapi", ["Semua"] + LIST_JENIS_SAPI)
            with col_f2:
                filter_kelamin = st.selectbox("4. Jenis Kelamin", ["Semua", "Jantan", "Betina"])
            with col_f3:
                daftar_negara = ["Semua"] + sorted(df_sapi["Asal Negara"].dropna().unique().tolist()) if not df_sapi.empty else ["Semua"]
                filter_asal = st.selectbox("5. Negara/Daerah Asal", daftar_negara)
            with col_f4:
                filter_berat = st.slider("6. Rentang Berat Akhir (kg)", min_value=0, max_value=1000, value=(0, 1000))

        df_filtered = df_sapi.copy()
        if search_kode.strip():
            df_filtered = df_filtered[df_filtered["Kode Sapi"].astype(str).str.contains(search_kode.strip(), case=False)]
        if search_rfid.strip():
            df_filtered = df_filtered[df_filtered["RFID/Tag"].astype(str).str.contains(search_rfid.strip(), case=False)]
        if filter_jenis != "Semua": 
            df_filtered = df_filtered[df_filtered["Jenis Sapi"] == filter_jenis]
        if filter_kelamin != "Semua": 
            df_filtered = df_filtered[df_filtered["Jenis Kelamin"] == filter_kelamin]
        if filter_asal != "Semua": 
            df_filtered = df_filtered[df_filtered["Asal Negara"] == filter_asal]
        if not df_filtered.empty:
            df_filtered = df_filtered[(df_filtered["Bobot Akhir (kg)"] >= filter_berat[0]) & (df_filtered["Bobot Akhir (kg)"] <= filter_berat[1])]

        st.markdown("---")
        st.write("### 📉 Ringkasan Kepadatan Pen (Hasil Filter Pencarian)")
        
        summary_pen = []
        for pen in DAFTAR_PEN:
            df_sub = df_filtered[df_filtered["Lokasi Pen"] == pen] if not df_filtered.empty else pd.DataFrame()
            populasi = len(df_sub)
            avg_bobot = round(df_sub["Bobot Akhir (kg)"].mean(), 1) if populasi > 0 else 0.0
            avg_adg = round(df_sub["ADG (kg/hari)"].mean(), 2) if populasi > 0 else 0.0
            summary_pen.append({
                "Nama Pen/Kandang": pen, 
                "Populasi Terfilter (Ekor)": populasi, 
                "Rerata Bobot Terfilter (kg)": avg_bobot, 
                "Rerata ADG Terfilter (kg/hari)": avg_adg
            })
        
        st.dataframe(pd.DataFrame(summary_pen), use_container_width=True, hide_index=True)
        st.markdown("---")
        st.write("### 📋 Detail Informasi Sapi per Pen (Hasil Filter Pencarian)")
        
        for pen in DAFTAR_PEN:
            df_filter_pen = df_filtered[df_filtered["Lokasi Pen"] == pen] if not df_filtered.empty else pd.DataFrame()
            st.markdown(f"#### 🏠 {pen} ({len(df_filter_pen)} Ekor Cocok)")
            if df_filter_pen.empty:
                st.caption("⚪ *Tidak ada sapi yang cocok dengan kriteria pencarian di pen ini.*")
            else:
                df_tabel_pen = df_filter_pen[["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)"]].copy()
                df_tabel_pen.index = range(1, len(df_tabel_pen) + 1)
                st.dataframe(df_tabel_pen, use_container_width=True)

        # PANEL KOREKSI TOTAL
        st.markdown("---")
        with st.expander("✏️ Klik di sini untuk membuka Panel Koreksi Total Data Sapi", expanded=False):
            st.markdown("### ✏️ Koreksi Total Data Sapi (Butuh Otorisasi Password Admin Utama)")
            
            if not df_sapi.empty:
                pilihan_sapi_koreksi = df_sapi["RFID/Tag"].astype(str).tolist()
                selected_tag_kor = st.selectbox("Pilih Nomor RFID Sapi yang akan Diedit Secara Menyeluruh:", pilihan_sapi_koreksi, key="sb_pop_total_edit")
                
                idx_kor = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag_kor].index[0]
                data_kor = df_sapi.loc[idx_kor]
                
                with st.form("form_pop_total_koreksi"):
                    col_k1, col_k2 = st.columns(2)
                    with col_k1:
                        new_kode = st.text_input("Koreksi Kode Sapi Baru", value=str(data_kor.get("Kode Sapi", "-")))
                        new_rfid = st.text_input("Koreksi Nomor RFID / Tag Baru", value=str(data_kor["RFID/Tag"]))
                        new_jenis = st.selectbox("Koreksi Jenis Sapi", LIST_JENIS_SAPI, index=LIST_JENIS_SAPI.index(data_kor["Jenis Sapi"]) if data_kor["Jenis Sapi"] in LIST_JENIS_SAPI else 0)
                        new_kelamin = st.selectbox("Koreksi Jenis Kelamin", ["Jantan", "Betina"], index=0 if data_kor["Jenis Kelamin"] == "Jantan" else 1)
                        new_umur = st.number_input("Koreksi Umur Masuk (Bulan)", min_value=1, value=int(data_kor["Umur Masuk (Bulan)"]) if pd.notna(data_kor["Umur Masuk (Bulan)"]) else 1)
                        new_asal = st.text_input("Koreksi Negara/Daerah Asal", value=str(data_kor["Asal Negara"]))
                        new_pen = st.selectbox("Koreksi Posisi Pen/Kandang", DAFTAR_PEN, index=DAFTAR_PEN.index(data_kor["Lokasi Pen"]) if data_kor["Lokasi Pen"] in DAFTAR_PEN else 0)
                    with col_k2:
                        try: 
                            tgl_m_curr = datetime.strptime(str(data_kor["Tgl Masuk"]), "%Y-%m-%d").date()
                        except: 
                            tgl_m_curr = datetime.now().date()
                        new_tgl_m = st.date_input("Koreksi Tanggal Masuk", value=tgl_m_curr)
                        new_bobot_awal = st.number_input("Koreksi Bobot Awal Masuk (kg)", min_value=50.0, value=float(data_kor["Bobot Awal (kg)"]) if pd.notna(data_kor["Bobot Awal (kg)"]) else 50.0)
                        
                        try: 
                            tgl_a_curr = datetime.strptime(str(data_kor["Tgl Cek Akhir"]), "%Y-%m-%d").date()
                        except: 
                            tgl_a_curr = datetime.now().date()
                        new_tgl_a = st.date_input("Koreksi Tanggal Timbangan/Cek Akhir", value=tgl_a_curr)
                        new_bobot_akhir = st.number_input("Koreksi Bobot Akhir Sekarang (kg)", min_value=50.0, value=float(data_kor["Bobot Akhir (kg)"]) if pd.notna(data_kor["Bobot Akhir (kg)"]) else 50.0)
                        new_pakan = st.number_input("Koreksi Akumulasi Pakan Terkonsumsi (kg)", min_value=0.0, value=float(data_kor["Total Pakan (kg)"]) if pd.notna(data_kor["Total Pakan (kg)"]) else 0.0)
                    
                    akses_diberikan = True
                    if user_role == "Operator":
                        try:
                            admin_pwd = st.secrets["ADMIN_PASSWORD"]
                        except Exception:
                            admin_pwd = "admin123"
                        st.markdown("⚠️ **Otorisasi Diperlukan:** Sesi Anda saat ini adalah Operator. Wajib memasukkan password akun Admin utama untuk menyimpan perubahan total.")
                        pwd_input = st.text_input("Masukkan Password Admin Utama", type="password", key="pwd_pop_total_edit")
                        if pwd_input != admin_pwd:
                            akses_diberikan = False
                            
                    if st.form_submit_button("Simpan Seluruh Perubahan Data Sapi", type="primary"):
                        if not akses_diberikan:
                            st.error("❌ Gagal Menyimpan! Password Admin salah atau tidak diisi.")
                        elif new_rfid != selected_tag_kor and new_rfid in df_sapi["RFID/Tag"].values.astype(str):
                            st.error(f"❌ Gagal Menyimpan! Nomor RFID '{new_rfid}' baru sudah digunakan oleh sapi lain.")
                        else:
                            df_sapi.at[idx_kor, "Kode Sapi"] = new_kode
                            df_sapi.at[idx_kor, "RFID/Tag"] = new_rfid
                            df_sapi.at[idx_kor, "Jenis Sapi"] = new_jenis
                            df_sapi.at[idx_kor, "Jenis Kelamin"] = new_kelamin
                            df_sapi.at[idx_kor, "Umur Masuk (Bulan)"] = int(new_umur)
                            df_sapi.at[idx_kor, "Asal Negara"] = new_asal
                            df_sapi.at[idx_kor, "Lokasi Pen"] = new_pen
                            df_sapi.at[idx_kor, "Tgl Masuk"] = new_tgl_m.strftime("%Y-%m-%d")
                            df_sapi.at[idx_kor, "Bobot Awal (kg)"] = new_bobot_awal
                            df_sapi.at[idx_kor, "Tgl Cek Akhir"] = new_tgl_a.strftime("%Y-%m-%d")
                            df_sapi.at[idx_kor, "Bobot Akhir (kg)"] = new_bobot_akhir
                            df_sapi.at[idx_kor, "Total Pakan (kg)"] = new_pakan
                            df_sapi.at[idx_kor, "ADG (kg/hari)"] = calculate_adg(new_tgl_m.strftime("%Y-%m-%d"), new_bobot_awal, new_tgl_a.strftime("%Y-%m-%d"), new_bobot_akhir)
                            
                            save_data(df_sapi)
                            add_activity_log(user_name, "Koreksi Total Sapi", f"Mengubah data Sapi Kode {new_kode}, RFID {selected_tag_kor} -> RFID baru: {new_rfid}, Pen: {new_pen}, Berat: {new_bobot_akhir}kg.")
                            st.success(f"🎉 Sukses! Data Sapi RFID {selected_tag_kor} berhasil diperbarui.")
                            st.rerun()
            else:
                st.info("Belum ada data sapi aktif.")

    with tab_pindah:
        st.write("### 🔄 Form Pemindahan (Mutasi) Kandang Sapi Bertingkat")
        if df_sapi.empty:
            st.info("Belum ada sapi aktif untuk dimutasi.")
        else:
            kandang_asal = st.selectbox("1. Pilih Kandang / Pen Asal:", DAFTAR_PEN, key="sb_kandang_asal")
            df_sapi_asal = df_sapi[df_sapi["Lokasi Pen"] == kandang_asal]
            
            if df_sapi_asal.empty:
                st.warning(f"⚠️ Tidak ada populasi sapi aktif di dalam {kandang_asal} saat ini.")
            else:
                pilihan_sapi = df_sapi_asal["RFID/Tag"].astype(str).tolist()
                selected_tag = st.selectbox(f"2. Pilih Nomor Tag / RFID Sapi (Ditemukan {len(pilihan_sapi)} Ekor):", options=pilihan_sapi, key="sb_mutasi")
                
                idx = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag].index[0]
                data_sapi = df_sapi.loc[idx]
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.info(f"""
📍 **Kondisi Sapi Saat Ini:**
* **Kode Sapi:** {data_sapi.get('Kode Sapi', '-')}
* **Nomor RFID:** {selected_tag}
* **Varietas/Jenis:** {data_sapi['Jenis Sapi']}
* **Bobot Sekarang:** {data_sapi['Bobot Akhir (kg)']} kg
* **Posisi Kandang Sekarang:** {data_sapi['Lokasi Pen']}
                    """)
                
                with col_m2:
                    pilihan_tujuan = [pen for pen in DAFTAR_PEN if pen != kandang_asal]
                    pen_tujuan = st.selectbox("3. Pilih Pen / Kandang Tujuan Baru:", pilihan_tujuan, key="sb_tujuan_pen")
                    
                    if st.button("Proses Mutasi Sapi", type="primary", use_container_width=True):
                        df_sapi.at[idx, "Lokasi Pen"] = pen_tujuan
                        save_data(df_sapi)
                        add_activity_log(user_name, "Mutasi Kandang", f"Memindahkan Sapi Kode {data_sapi.get('Kode Sapi', '-')} (RFID {selected_tag}) dari {kandang_asal} menuju {pen_tujuan}.")
                        st.success(f"🎉 Sukses! Sapi RFID {selected_tag} berhasil dipindahkan menuju {pen_tujuan}.")
                        st.rerun()