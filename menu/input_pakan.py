import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_pakan(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🍽️ Manajemen Pakan Harian Sapi")
    
    # Konfigurasi skema kolom untuk file tabel log pakan harian
    # DITAMBAHKAN KOLOM: 'Metode' dan 'Target Spesifik'
    COLS_PAKAN = ["Tanggal", "Lokasi Pen", "Metode", "Target Spesifik", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"]
    
    # Muat log riwayat pakan harian dari Google Sheets / CSV
    df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
    
    # Membuat Tab Navigasi internal agar mempermudah operator
    tab1, tab2, tab3 = st.tabs(["➕ Input Pakan Baru", "⚙️ Edit / Hapus Riwayat Pakan", "📊 Rekapitulasi Realisasi Pakan"])
    
    # Jangkah daftar lengkap pen untuk kebutuhan dropdown Tab 2 (Edit)
    daftar_pen_lengkap = []
    for b, daftar_p in STRUKTUR_KANDANG.items():
        for p in daftar_p:
            daftar_pen_lengkap.append(f"{b} - {p}")

    # ==================== TAB 1: INPUT PAKAN BARU ====================
    with tab1:
        st.markdown("### 📝 Form Catat Pemberian Pakan Harian")
        
        tgl_pakan = st.date_input("Tanggal Distribusi Pakan", datetime.now().date(), key="tgl_pakan_input")
        
        # 1. Pilihan Blok Kandang
        blok_terpilih = st.selectbox("1. Pilih Blok Kandang", list(STRUKTUR_KANDANG.keys()))
        
        # 2. Pilihan Pen (Otomatis tersaring berdasarkan Blok yang dipilih)
        pen_tersaring = STRUKTUR_KANDANG[blok_terpilih]
        pen_terpilih = st.selectbox("2. Pilih Pen Kandang", pen_tersaring)
        
        lokasi_pen_full = f"{blok_terpilih} - {pen_terpilih}"
        
        # Cari populasi sapi aktif di pen tersebut secara real-time
        sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == lokasi_pen_full]
        jumlah_sapi = len(sapi_di_pen)
        st.info(f"📊 Jumlah populasi sapi aktif saat ini di **{lokasi_pen_full}**: **{jumlah_sapi} Ekor**")

        if jumlah_sapi == 0:
            st.warning("⚠️ Tidak bisa menginput pakan. Pen ini masih kosong.")
        else:
            # 3. FITUR BARU: Metode Pemberian
            st.markdown("---")
            metode_pakan = st.radio(
                "3. Pilih Metode Pemberian Pakan:",
                ["Serentak (Semua Sapi di Pen)", "Spesifik (Per Ekor/Individu)"],
                help="Gunakan 'Spesifik' untuk sapi yang sakit atau butuh perlakuan khusus (misal: Pen Isolasi)."
            )

            target_spesifik_val = "-"
            opsi_sapi_spesifik = []

            if metode_pakan == "Spesifik (Per Ekor/Individu)":
                # Ambil daftar sapi di pen tersebut untuk dipilih
                opsi_sapi_spesifik = sapi_di_pen.apply(lambda r: f"{r['Kode Sapi']} - {r['RFID/Tag']}", axis=1).tolist()
                pilihan_sapi = st.selectbox("↳ Pilih Sapi Target (Individu):", opsi_sapi_spesifik)
                target_spesifik_val = pilihan_sapi # Simpan RFID/Kode Sapi target
            
            st.markdown("---")
            
            # 4. Jenis Pakan (Sistem Dropdown Otomatis + Deteksi Dinamis)
            opsi_pakan_default = ["Konsentrat Hijau", "Silase", "Jerami Fermentasi", "Obat/Suplemen Khusus", "Lain-lain"]
            pakan_terpilih_dropdown = st.selectbox("4. Pilih Jenis / Nama Formula Pakan", opsi_pakan_default)
            
            # Logika Kondisional: Jika memilih 'Lain-lain', buka kolom pengetikan manual baru
            if pakan_terpilih_dropdown == "Lain-lain":
                jenis_pakan = st.text_input("📋 Masukkan Nama Formula Pakan Baru", placeholder="Contoh: Ampas Tahu, Konsentrat Penggemukan B, dll").strip()
            else:
                jenis_pakan = pakan_terpilih_dropdown
            
            # 5. Input kuantiti pakan
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
                total_pakan_terhitung = st.number_input("5. Total Kuantitas Pakan Khusus (kg) untuk Sapi Ini", min_value=0.0, step=0.1, format="%.2f")
                pakan_per_ekor = total_pakan_terhitung # Untuk metode spesifik, total = pakan per ekor
            
            st.markdown("---")
            
            if st.button("🚀 Simpan Pemberian Pakan Baru", type="primary", use_container_width=True):
                if not jenis_pakan or total_pakan_terhitung <= 0:
                    st.error("❌ Gagal Simpan! Jenis pakan wajib diisi/dipilih dan kuantiti harus lebih besar dari 0 kg.")
                else:
                    with st.spinner("⏳ Sedang memproses distribusi pakan harian..."):
                        # 1. Masukkan baris baru ke log pakan harian
                        row_pakan_baru = {
                            "Tanggal": str(tgl_pakan),
                            "Lokasi Pen": lokasi_pen_full,
                            "Metode": "Serentak" if metode_pakan == "Serentak (Semua Sapi di Pen)" else "Spesifik",
                            "Target Spesifik": target_spesifik_val,
                            "Jenis Pakan": jenis_pakan,
                            "Jumlah Pakan (kg)": total_pakan_terhitung,
                            "Operator": user_name
                        }
                        df_pakan = pd.concat([df_pakan, pd.DataFrame([row_pakan_baru])], ignore_index=True)
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)
                        
                        # 2. Distribusikan jatah
                        if metode_pakan == "Serentak (Semua Sapi di Pen)":
                            df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Total Pakan (kg)"] += pakan_per_ekor
                            df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                            detail_sukses = f"Mendistribusikan Serentak {jenis_pakan} (@{pakan_per_ekor} kg/ekor) ke {lokasi_pen_full} (Total: {total_pakan_terhitung} kg untuk {jumlah_sapi} ekor)"
                        else:
                            # Ekstrak Kode/RFID target
                            target_kode = target_spesifik_val.split(" - ")[0]
                            target_rfid = target_spesifik_val.split(" - ")[1]
                            
                            mask_spesifik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_spesifik, "Total Pakan (kg)"] += total_pakan_terhitung
                            df_sapi.loc[mask_spesifik, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                            detail_sukses = f"Memberikan Khusus {jenis_pakan} ({total_pakan_terhitung} kg) kepada Sapi {target_spesifik_val} di {lokasi_pen_full}"

                        save_data(df_sapi)
                        
                        # 3. Rekam audit log
                        add_activity_log(user_name, "Input Pakan", detail_sukses)
                        
                    st.success(f"🎉 Berhasil! {detail_sukses}")
                    st.balloons()
                    st.rerun()

    # ==================== TAB 2: EDIT / HAPUS (PASSWORD LOCKED) ====================
    with tab2:
        st.markdown("### 📋 Koreksi & Pembersihan Salah Input Pakan")
        
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
            
            # Ekstrak detail row lama
            metode_lama = row_lama.get("Metode", "Serentak") # Backward compatibility
            target_lama = row_lama.get("Target Spesifik", "-")
            
            st.info(f"📍 **Data Terpilih:** Pen {row_lama['Lokasi Pen']} | Metode: **{metode_lama}** {f'({target_lama})' if metode_lama == 'Spesifik' else ''} | {row_lama['Jenis Pakan']} | {row_lama['Jumlah Pakan (kg)']} kg")

            col_form, col_auth = st.columns(2)
            
            with col_form:
                # Hanya izinkan ganti Pen jika metodenya serentak. Jika spesifik, ganti pen bisa berisiko salah target sapi
                if metode_lama == "Serentak":
                    pen_baru = st.selectbox("Koreksi Tujuan Pen", list(daftar_pen_lengkap), index=list(daftar_pen_lengkap).index(row_lama["Lokasi Pen"]) if row_lama["Lokasi Pen"] in daftar_pen_lengkap else 0)
                else:
                    st.write(f"**Tujuan Pen:** {row_lama['Lokasi Pen']} (Tidak bisa diubah karena spesifik per sapi)")
                    pen_baru = row_lama["Lokasi Pen"]
                
                jenis_baru = st.text_input("Koreksi Jenis Pakan", value=str(row_lama["Jenis Pakan"])).strip()
                jumlah_baru = st.number_input("Koreksi Total Jumlah Pakan (kg)", min_value=0.0, value=float(row_lama["Jumlah Pakan (kg)"]), step=1.0, format="%.1f")
                
            with col_auth:
                st.warning("⚠️ **Perhatian:** Tindakan perubahan atau penghapusan riwayat pakan harian akan diverifikasi langsung menggunakan kata sandi Admin.")
                pwd_input = st.text_input("Masukkan Password Otorisasi Admin", type="password", key="auth_pakan_pass")
            
            st.markdown(" ")
            btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 2])
            
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123"

            # --- SELEKSI EKSEKUSI BUTTON EDIT ---
            if btn_col1.button("✏️ Simpan Perubahan Data", type="primary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah.")
                elif not jenis_baru or jumlah_baru <= 0:
                    st.error("❌ Perubahan Gagal! Nama pakan harus valid dan berat tidak boleh nol.")
                else:
                    with st.spinner("🔄 Sedang memproses ulang kalkulasi timbangan pakan sapi..."):
                        
                        # 1. TARIK BALIK DATA LAMA
                        if metode_lama == "Serentak":
                            sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_lama) > 0:
                                share_lama = round(float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama), 2)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= share_lama
                        else: # Spesifik
                            if target_lama != "-":
                                target_kode = target_lama.split(" - ")[0]
                                target_rfid = target_lama.split(" - ")[1]
                                mask_tarik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                                df_sapi.loc[mask_tarik, "Total Pakan (kg)"] -= float(row_lama["Jumlah Pakan (kg)"])
                        
                        df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)

                        # 2. DISTRIBUSIKAN DATA BARU
                        if metode_lama == "Serentak":
                            sapi_pen_baru = df_sapi[df_sapi["Lokasi Pen"] == pen_baru]
                            if len(sapi_pen_baru) > 0:
                                share_baru = round(jumlah_baru / len(sapi_pen_baru), 2)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == pen_baru, "Total Pakan (kg)"] += share_baru
                        else: # Spesifik (Hanya jumlah yang berubah, target tetap)
                            if target_lama != "-":
                                target_kode = target_lama.split(" - ")[0]
                                target_rfid = target_lama.split(" - ")[1]
                                mask_tambah = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                                df_sapi.loc[mask_tambah, "Total Pakan (kg)"] += jumlah_baru

                        save_data(df_sapi)

                        # Update sheet log pakan
                        df_pakan.at[idx_pilihan, "Lokasi Pen"] = pen_baru
                        df_pakan.at[idx_pilihan, "Jenis Pakan"] = jenis_baru
                        df_pakan.at[idx_pilihan, "Jumlah Pakan (kg)"] = jumlah_baru
                        df_pakan.at[idx_pilihan, "Operator"] = f"{user_name} (Edited)"
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                        add_activity_log(user_name, "Koreksi Pakan", f"Mengubah log pakan No {pilihan_no}: Dari [{row_lama['Jenis Pakan']} - {row_lama['Jumlah Pakan (kg)']}kg] Menjadi [{jenis_baru} - {jumlah_baru}kg]")
                        
                    st.success(f"✅ Sukses! Data pakan No Urut {pilihan_no} berhasil diperbaiki.")
                    st.rerun()

# ==================== TAB 3: REKAPITULASI PAKAN ====================
    with tab3:
        st.markdown("### 📊 Rekapitulasi & Realisasi Konsumsi Pakan")
        
        if df_pakan.empty:
            st.info("Belum ada data riwayat pakan yang tercatat.")
        else:
            # 1. Hitung jumlah sapi per pen saat ini dari master data sapi
            pen_counts = df_sapi["Lokasi Pen"].value_counts().to_dict()
            
            # 2. Siapkan data rekap pakan
            df_rekap = df_pakan.copy()
            df_rekap["Jumlah Pakan (kg)"] = pd.to_numeric(df_rekap["Jumlah Pakan (kg)"], errors="coerce").fillna(0)
            
            # 3. Kelompokkan berdasarkan Lokasi Pen dan Jenis Pakan
            rekap_grup = df_rekap.groupby(["Lokasi Pen", "Jenis Pakan"])["Jumlah Pakan (kg)"].sum().reset_index()
            
            # 4. Tambahkan kalkulasi konsumsi per ekor
            def hitung_per_ekor(row):
                jml_sapi = pen_counts.get(row["Lokasi Pen"], 0)
                if jml_sapi > 0:
                    return round(row["Jumlah Pakan (kg)"] / jml_sapi, 2)
                return 0.0
            
            rekap_grup["Jumlah Sapi di Pen"] = rekap_grup["Lokasi Pen"].map(lambda x: pen_counts.get(x, 0))
            rekap_grup["Konsumsi Per Ekor (kg)"] = rekap_grup.apply(hitung_per_ekor, axis=1)
            
            # Ganti nama kolom agar enak dibaca di tabel
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
            
            # --- SELEKSI EKSEKUSI BUTTON HAPUS ---
            if btn_col2.button("🗑️ Hapus Data Permanen", type="secondary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah.")
                else:
                    with st.spinner("🔄 Sedang memotong balik akumulasi pakan sapi..."):
                        
                        # TARIK BALIK DATA LAMA
                        if metode_lama == "Serentak":
                            sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_lama) > 0:
                                share_lama = round(float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama), 2)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= share_lama
                        else: # Spesifik
                            if target_lama != "-":
                                target_kode = target_lama.split(" - ")[0]
                                target_rfid = target_lama.split(" - ")[1]
                                mask_tarik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                                df_sapi.loc[mask_tarik, "Total Pakan (kg)"] -= float(row_lama["Jumlah Pakan (kg)"])

                        df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)
                        
                        save_data(df_sapi)

                        df_pakan = df_pakan.drop(df_pakan.index[idx_pilihan]).reset_index(drop=True)
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                        add_activity_log(user_name, "Hapus Pakan", f"Menghapus log pakan No {pilihan_no}: Terhapus data {row_lama['Jenis Pakan']} ({metode_lama}) di {row_lama['Lokasi Pen']}")
                        
                    st.success(f"🗑️ Sukses! Record pakan No Urut {pilihan_no} berhasil dihapus permanen.")
                    st.rerun()