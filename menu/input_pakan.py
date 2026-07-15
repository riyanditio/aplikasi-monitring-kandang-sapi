import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def tampilkan_menu_pakan(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🍽️ Manajemen Pakan Harian Sapi")
    
    # Memastikan tipe data master sapi selalu terbaca float
    df_sapi["Total Pakan (kg)"] = pd.to_numeric(df_sapi["Total Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
    
    # Skema kolom database pakan harian
    COLS_PAKAN = ["Tanggal", "Lokasi Pen", "Metode", "Target Spesifik", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"]
    
    # Menggunakan st.tabs untuk memisahkan menu manajemen pakan
    tab1, tab2, tab3 = st.tabs(["➕ Input Pakan Baru", "⚙️ Edit / Hapus Riwayat Pakan", "📊 Rekapitulasi Realisasi Pakan"])
    
    daftar_pen_lengkap = []
    for b, daftar_p in STRUKTUR_KANDANG.items():
        for p in daftar_p:
            daftar_pen_lengkap.append(f"{b} - {p}")

    # ==================== TAB 1: INPUT PAKAN BARU ====================
    with tab1:
        st.markdown("### 📝 Form Catat Pemberian Pakan Harian")
        
        tgl_pakan = st.date_input("Tanggal Distribusi Pakan", datetime.now().date(), key="tgl_pakan_input")
        
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            blok_terpilih = st.selectbox("1. Pilih Blok Kandang", list(STRUKTUR_KANDANG.keys()))
        with col_in2:
            pen_tersaring = STRUKTUR_KANDANG[blok_terpilih]
            pen_terpilih = st.selectbox("2. Pilih Pen Kandang", pen_tersaring)
            
        lokasi_pen_full = f"{blok_terpilih} - {pen_terpilih}"
        
        sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == lokasi_pen_full]
        jumlah_sapi = len(sapi_di_pen)
        st.info(f"📊 Jumlah populasi sapi aktif saat ini di **{lokasi_pen_full}**: **{jumlah_sapi} Ekor**")

        if jumlah_sapi == 0:
            st.warning("⚠️ Tidak bisa menginput pakan. Pen ini masih kosong.")
        else:
            st.markdown("---")
            metode_pakan = st.radio(
                "3. Pilih Metode Pemberian Pakan:",
                ["Serentak (Semua Sapi di Pen)", "Spesifik (Per Ekor/Individu)"],
                help="Gunakan 'Spesifik' untuk sapi yang sakit atau butuh perlakuan khusus (misal: Pen Isolasi)."
            )

            st.markdown("---")
            opsi_pakan_default = ["Konsentrat Hijau", "Silase", "Jerami Fermentasi", "Obat/Suplemen Khusus", "Lain-lain"]
            pakan_terpilih_dropdown = st.selectbox("4. Pilih Jenis / Nama Formula Pakan", opsi_pakan_default)
            
            if pakan_terpilih_dropdown == "Lain-lain":
                jenis_pakan = st.text_input("📋 Masukkan Nama Formula Pakan Baru", placeholder="Contoh: Ampas Tahu").strip()
            else:
                jenis_pakan = pakan_terpilih_dropdown
            
            # Pengkondisian input Kuantitas berdasarkan metode
            if metode_pakan == "Serentak (Semua Sapi di Pen)":
                pakan_per_ekor = st.number_input("5. Kuantitas Pakan per Ekor (kg/ekor)", min_value=0.0, step=0.1, format="%.2f")
                total_pakan_terhitung = round(pakan_per_ekor * jumlah_sapi, 2)
                
                st.markdown("---")
                st.metric(
                    label="⚖️ Total Kuantitas Pakan yang Akan Diturunkan (Otomatis)", 
                    value=f"{total_pakan_terhitung} kg",
                    delta=f"Berdasarkan hitungan: {pakan_per_ekor} kg x {jumlah_sapi} ekor"
                )
            else:
                opsi_sapi_spesifik = sapi_di_pen.apply(lambda r: f"{r['Kode Sapi']} - {r['RFID/Tag']}", axis=1).tolist()
                pilihan_sapi = st.selectbox("↳ Pilih Sapi Target (Individu):", opsi_sapi_spesifik)
                total_pakan_terhitung = st.number_input("5. Total Kuantitas Pakan Khusus (kg) untuk Sapi Ini", min_value=0.0, step=0.1, format="%.2f")
                pakan_per_ekor = total_pakan_terhitung
            
            st.markdown("---")
            
            if st.button("🚀 Simpan Pemberian Pakan Baru", type="primary", use_container_width=True):
                if not jenis_pakan or total_pakan_terhitung <= 0:
                    st.error("❌ Gagal Simpan! Jenis pakan wajib diisi/dipilih dan kuantiti harus lebih besar dari 0 kg.")
                else:
                    with st.spinner("⏳ Sedang memproses distribusi pakan harian..."):
                        
                        # [OPTIMASI 1]: Ambil riwayat pakan HANYA saat tombol Simpan ditekan
                        df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
                        if not df_pakan.empty:
                            df_pakan["Jumlah Pakan (kg)"] = pd.to_numeric(df_pakan["Jumlah Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
                        
                        # LOGIKA UTAMA: PEMECAHAN LOG DATA AGAR NEMPEL PADA MASING-MASING SAPI
                        if metode_pakan == "Serentak (Semua Sapi di Pen)":
                            list_rows_baru = []
                            # Iterasi/Looping setiap sapi yang ada di dalam pen saat ini
                            for _, row_sapi in sapi_di_pen.iterrows():
                                id_sapi_nempel = f"{row_sapi['Kode Sapi']} - {row_sapi['RFID/Tag']}"
                                row_pakan_baru = {
                                    "Tanggal": str(tgl_pakan),
                                    "Lokasi Pen": lokasi_pen_full,
                                    "Metode": "Serentak",
                                    "Target Spesifik": id_sapi_nempel, 
                                    "Jenis Pakan": jenis_pakan,
                                    "Jumlah Pakan (kg)": float(pakan_per_ekor), 
                                    "Operator": user_name
                                }
                                list_rows_baru.append(row_pakan_baru)
                            
                            df_pakan = pd.concat([df_pakan, pd.DataFrame(list_rows_baru)], ignore_index=True)
                            
                            # Akumulasikan ke master table utama
                            df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Total Pakan (kg)"] += float(pakan_per_ekor)
                            df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                            detail_sukses = f"Mendistribusikan Serentak {jenis_pakan} (@{pakan_per_ekor} kg/ekor) ke {lokasi_pen_full} (Dicatat individual untuk {jumlah_sapi} ekor)"
                        
                        else:
                            # Metode Spesifik Per Ekor
                            row_pakan_baru = {
                                "Tanggal": str(tgl_pakan),
                                "Lokasi Pen": lokasi_pen_full,
                                "Metode": "Spesifik",
                                "Target Spesifik": pilihan_sapi,
                                "Jenis Pakan": jenis_pakan,
                                "Jumlah Pakan (kg)": float(total_pakan_terhitung),
                                "Operator": user_name
                            }
                            df_pakan = pd.concat([df_pakan, pd.DataFrame([row_pakan_baru])], ignore_index=True)
                            
                            target_kode = pilihan_sapi.split(" - ")[0]
                            target_rfid = pilihan_sapi.split(" - ")[1]
                            mask_spesifik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_spesifik, "Total Pakan (kg)"] += float(total_pakan_terhitung)
                            df_sapi.loc[mask_spesifik, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                            detail_sukses = f"Memberikan Khusus {jenis_pakan} ({total_pakan_terhitung} kg) kepada Sapi {pilihan_sapi} di {lokasi_pen_full}"

                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)
                        save_data(df_sapi)
                        add_activity_log(user_name, "Input Pakan", detail_sukses)
                        
                    st.success(f"🎉 Berhasil! {detail_sukses}")
                    st.rerun()

    # ==================== TAB 2: EDIT / HAPUS RIWAYAT PAKAN ====================
    with tab2:
        st.markdown("### 📋 Koreksi & Pembersihan Salah Input Pakan")
        
        # [OPTIMASI 2]: Data pakan hanya di-load ketika membuka Tab Edit/Hapus ini
        df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
        if not df_pakan.empty:
            df_pakan["Jumlah Pakan (kg)"] = pd.to_numeric(df_pakan["Jumlah Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
        
        if df_pakan.empty:
            st.info("ℹ️ Belum ada data riwayat pemberian pakan harian yang tercatat di database.")
        else:
            df_pakan_show = df_pakan.copy()
            df_pakan_show.insert(0, "No Urut", range(1, len(df_pakan) + 1))
            st.dataframe(df_pakan_show, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### 🔐 Panel Otorisasi Koreksi Data")
            
            pilihan_no = st.number_input("Masukkan 'No Urut' data pakan yang salah input", min_value=1, max_value=len(df_pakan), step=1)
            idx_pilihan = pilihan_no - 1
            row_lama = df_pakan.iloc[idx_pilihan]
            
            metode_lama = row_lama.get("Metode", "Serentak")
            target_lama = row_lama.get("Target Spesifik", "-")
            
            st.info(f"📍 **Data Terpilih:** Pen {row_lama['Lokasi Pen']} | Target: **{target_lama}** | {row_lama['Jenis Pakan']} | {row_lama['Jumlah Pakan (kg)']} kg")

            col_form, col_auth = st.columns(2)
            
            with col_form:
                st.write(f"**Tujuan Pen:** {row_lama['Lokasi Pen']} (Tetap sesuai data log)")
                jenis_baru = st.text_input("Koreksi Jenis Pakan", value=str(row_lama["Jenis Pakan"])).strip()
                jumlah_baru = st.number_input("Koreksi Jumlah Pakan (kg)", min_value=0.0, value=float(row_lama["Jumlah Pakan (kg)"]), step=1.0, format="%.2f")
                
            with col_auth:
                st.warning("⚠️ **Perhatian:** Tindakan perubahan ini diawasi ketat. Masukkan Password Admin.")
                pwd_input = st.text_input("Masukkan Password Otorisasi Admin", type="password", key="auth_pakan_pass")
            
            st.markdown(" ")
            btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 2])
            
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123"

            if btn_col1.button("✏️ Simpan Perubahan Data", type="primary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah.")
                elif not jenis_baru or jumlah_baru <= 0:
                    st.error("❌ Perubahan Gagal! Nama pakan harus valid dan berat tidak boleh nol.")
                else:
                    with st.spinner("🔄 Sedang memproses ulang kalkulasi..."):
                        
                        # 1. TARIK BALIK DATA BEBAN KONSUMSI LAMA DARI SAPI
                        if target_lama != "-" and " - " in str(target_lama):
                            target_kode = str(target_lama).split(" - ")[0]
                            target_rfid = str(target_lama).split(" - ")[1]
                            mask_tarik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_tarik, "Total Pakan (kg)"] -= float(row_lama["Jumlah Pakan (kg)"])
                        else:
                            if metode_lama == "Serentak":
                                sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                                try:
                                    pop_lama = str(target_lama).strip()
                                    denom_lama = int(pop_lama) if (pop_lama != "-" and pop_lama.isdigit()) else len(sapi_pen_lama)
                                except: denom_lama = len(sapi_pen_lama)
                                if denom_lama > 0:
                                    df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= (float(row_lama["Jumlah Pakan (kg)"]) / denom_lama)
                        
                        df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)

                        # 2. MASUKKAN DATA BEBAN KONSUMSI BARU KEPADA SAPI
                        if target_lama != "-" and " - " in str(target_lama):
                            target_kode = str(target_lama).split(" - ")[0]
                            target_rfid = str(target_lama).split(" - ")[1]
                            mask_tambah = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_tambah, "Total Pakan (kg)"] += float(jumlah_baru)
                        else:
                            if metode_lama == "Serentak":
                                sapi_pen_baru = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                                if len(sapi_pen_baru) > 0:
                                    df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] += (float(jumlah_baru) / len(sapi_pen_baru))

                        save_data(df_sapi)

                        # Perbarui baris tabel log pakan
                        df_pakan.at[idx_pilihan, "Jenis Pakan"] = jenis_baru
                        df_pakan.at[idx_pilihan, "Jumlah Pakan (kg)"] = float(jumlah_baru)
                        df_pakan.at[idx_pilihan, "Operator"] = f"{user_name} (Edited)"
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                        add_activity_log(user_name, "Koreksi Pakan", f"Mengubah log pakan No {pilihan_no}")
                        
                    st.success(f"✅ Sukses! Data pakan No Urut {pilihan_no} berhasil diperbaiki.")
                    st.rerun()

            if btn_col2.button("🗑️ Hapus Data Permanen", type="secondary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah.")
                else:
                    with st.spinner("🔄 Sedang memotong balik akumulasi pakan sapi..."):
                        
                        if target_lama != "-" and " - " in str(target_lama):
                            target_kode = str(target_lama).split(" - ")[0]
                            target_rfid = str(target_lama).split(" - ")[1]
                            mask_tarik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_tarik, "Total Pakan (kg)"] -= float(row_lama["Jumlah Pakan (kg)"])
                        else:
                            if metode_lama == "Serentak":
                                sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                                try:
                                    pop_lama = str(target_lama).strip()
                                    denom_lama = int(pop_lama) if (pop_lama != "-" and pop_lama.isdigit()) else len(sapi_pen_lama)
                                except: denom_lama = len(sapi_pen_lama)
                                if denom_lama > 0:
                                    df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= (float(row_lama["Jumlah Pakan (kg)"]) / denom_lama)

                        df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)
                        save_data(df_sapi)

                        df_pakan = df_pakan.drop(df_pakan.index[idx_pilihan]).reset_index(drop=True)
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                        add_activity_log(user_name, "Hapus Pakan", f"Menghapus log pakan No {pilihan_no}")
                        
                    st.success(f"🗑️ Sukses! Record pakan No Urut {pilihan_no} berhasil dihapus.")
                    st.rerun()

    # ==================== TAB 3: REKAPITULASI REALISASI PAKAN ====================
    with tab3:
        st.markdown("### 📊 Rekapitulasi & Realisasi Konsumsi Pakan")
        
        # [OPTIMASI 3]: Data pakan hanya di-load ketika membuka Tab Rekapitulasi ini
        df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
        if not df_pakan.empty:
            df_pakan["Jumlah Pakan (kg)"] = pd.to_numeric(df_pakan["Jumlah Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
        
        if df_pakan.empty:
            st.info("Belum ada data riwayat pakan yang tercatat.")
        else:
            pen_counts = df_sapi["Lokasi Pen"].value_counts().to_dict()
            df_rekap = df_pakan.copy()
            rekap_grup = df_rekap.groupby(["Lokasi Pen", "Jenis Pakan"])["Jumlah Pakan (kg)"].sum().reset_index()
            
            def hitung_per_ekor(row):
                jml_sapi = pen_counts.get(row["Lokasi Pen"], 0)
                if jml_sapi > 0:
                    return round(row["Jumlah Pakan (kg)"] / jml_sapi, 2)
                return 0.0
            
            rekap_grup["Jumlah Sapi di Pen (Aktif)"] = rekap_grup["Lokasi Pen"].map(lambda x: pen_counts.get(x, 0))
            rekap_grup["Konsumsi Per Ekor (kg)"] = rekap_grup.apply(hitung_per_ekor, axis=1)
            rekap_grup = rekap_grup.rename(columns={"Jumlah Pakan (kg)": "Total Pakan Disalurkan (kg)"})
            
            st.dataframe(
                rekap_grup, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Total Pakan Disalurkan (kg)": st.column_config.NumberColumn(format="%.2f"),
                    "Konsumsi Per Ekor (kg)": st.column_config.NumberColumn(format="%.2f")
                }
            )