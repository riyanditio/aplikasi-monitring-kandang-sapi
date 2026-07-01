import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_pakan(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🍽️ Manajemen Pakan Harian Sapi")
    
    # Konfigurasi skema kolom untuk file tabel log pakan harian
    COLS_PAKAN = ["Tanggal", "Lokasi Pen", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"]
    
    # Muat log riwayat pakan harian dari Google Sheets / CSV
    df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
    
    # Membuat Tab Navigasi internal agar mempermudah operator
    tab1, tab2 = st.tabs(["➕ Input Pakan Baru", "⚙️ Edit / Hapus Riwayat Pakan"])
    
    # Jangkah daftar lengkap pen untuk kebutuhan dropdown Tab 2 (Edit)
    daftar_pen_lengkap = []
    for b, daftar_p in STRUKTUR_KANDANG.items():
        for p in daftar_p:
            daftar_pen_lengkap.append(f"{b} - {p}")

        # ==================== TAB 1: INPUT PAKAN BARU (ALUR REAKTIF ASLI) ====================
        with tab1:
            st.markdown("### 📝 Form Catat Pemberian Pakan Harian")
            
            tgl_pakan = st.date_input("Tanggal Distribusi Pakan", datetime.now().date())
            
            # 1. Pilihan Blok Kandang
            blok_terpilih = st.selectbox("1. Pilih Blok Kandang", list(STRUKTUR_KANDANG.keys()))
            
            # 2. Pilihan Pen (Otomatis tersaring berdasarkan Blok yang dipilih)
            pen_tersaring = STRUKTUR_KANDANG[blok_terpilih]
            pen_terpilih = st.selectbox("2. Pilih Pen Kandang", pen_tersaring)
            
            # Gabungkan untuk mencocokkan dengan kolom "Lokasi Pen" di database master sapi
            lokasi_pen_full = f"{blok_terpilih} - {pen_terpilih}"
            
            # Cari populasi sapi aktif di pen tersebut secara real-time
            sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == lokasi_pen_full]
            jumlah_sapi = len(sapi_di_pen)
            st.info(f"📊 Jumlah populasi sapi aktif saat ini di **{lokasi_pen_full}**: **{jumlah_sapi} Ekor**")
            
            # 3. Jenis Pakan (Sistem Dropdown Otomatis + Deteksi Dinamis)
            opsi_pakan_default = ["Konsentrat Hijau", "Silase", "Jerami Fermentasi", "Lain-lain"]
            pakan_terpilih_dropdown = st.selectbox("3. Pilih Jenis / Nama Formula Pakan", opsi_pakan_default)
            
            # Logika Kondisional: Jika memilih 'Lain-lain', buka kolom pengetikan manual baru
            if pakan_terpilih_dropdown == "Lain-lain":
                jenis_pakan = st.text_input("📋 Masukkan Nama Formula Pakan Baru", placeholder="Contoh: Ampas Tahu, Konsentrat Penggemukan B, dll").strip()
            else:
                jenis_pakan = pakan_terpilih_dropdown
            
            # 4. Input kuantiti pakan per ekor
            pakan_per_ekor = st.number_input("4. Kuantitas Pakan per Ekor (kg/ekor)", min_value=0.0, step=0.1, format="%.2f")
            
            # KUNCI UTAMA: Informasi total kuantiti pakan yang diberikan (Otomatis Terkalkulasi)
            total_pakan_terhitung = round(pakan_per_ekor * jumlah_sapi, 2)
            
            st.markdown("---")
            st.metric(
                label="⚖️ Total Kuantitas Pakan yang Akan Diturunkan (Otomatis)", 
                value=f"{total_pakan_terhitung} kg",
                delta=f"Berdasarkan hitungan: {pakan_per_ekor} kg x {jumlah_sapi} ekor" if jumlah_sapi > 0 else "Pen Kosong"
            )
            st.markdown("---")
            
            if st.button("🚀 Simpan Pemberian Pakan Baru", type="primary", use_container_width=True):
                if not jenis_pakan or pakan_per_ekor <= 0:
                    st.error("❌ Gagal Simpan! Jenis pakan wajib diisi/dipilih dan kuantiti per ekor harus lebih besar dari 0 kg.")
                else:
                    with st.spinner("⏳ Sedang memproses distribusi pakan harian..."):
                        # 1. Masukkan baris baru ke log pakan harian (yang disimpan adalah totalnya)
                        row_pakan_baru = {
                            "Tanggal": str(tgl_pakan),
                            "Lokasi Pen": lokasi_pen_full,
                            "Jenis Pakan": jenis_pakan,
                            "Jumlah Pakan (kg)": total_pakan_terhitung,
                            "Operator": user_name
                        }
                        df_pakan = pd.concat([df_pakan, pd.DataFrame([row_pakan_baru])], ignore_index=True)
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)
                        
                        # 2. Distribusikan langsung jatah per ekor ke masing-masing sapi di database master
                        if jumlah_sapi > 0:
                            df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Total Pakan (kg)"] += pakan_per_ekor
                            df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                            save_data(df_sapi)
                            detail_sukses = f"Mendistribusikan {jenis_pakan} sebanyak @{pakan_per_ekor} kg/ekor ke {lokasi_pen_full} (Total pakan diturunkan: {total_pakan_terhitung} kg untuk {jumlah_sapi} ekor)"
                        else:
                            detail_sukses = f"Mencatat log pakan {jenis_pakan} sebesar 0 kg di {lokasi_pen_full} karena kondisi pen sedang kosong"
                        
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
                
                col_form, col_auth = st.columns(2)
                
                with col_form:
                    st.info(f"📍 **Data Terpilih:** Pen {row_lama['Lokasi Pen']} | {row_lama['Jenis Pakan']} | {row_lama['Jumlah Pakan (kg)']} kg")
                    pen_baru = st.selectbox("Koreksi Tujuan Pen", list(daftar_pen_lengkap), index=list(daftar_pen_lengkap).index(row_lama["Lokasi Pen"]) if row_lama["Lokasi Pen"] in daftar_pen_lengkap else 0)
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
                            # Tarik balik data pakan lama
                            sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_lama) > 0:
                                share_lama = round(float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama), 2)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= share_lama
                                df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)

                            # Distribusikan ulang data koreksi baru
                            sapi_pen_baru = df_sapi[df_sapi["Lokasi Pen"] == pen_baru]
                            if len(sapi_pen_baru) > 0:
                                share_baru = round(jumlah_baru / len(sapi_pen_baru), 2)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == pen_baru, "Total Pakan (kg)"] += share_baru
                            
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

                # --- SELEKSI EKSEKUSI BUTTON HAPUS ---
                if btn_col2.button("🗑️ Hapus Data Permanen", type="secondary", use_container_width=True):
                    if pwd_input != correct_admin_pwd:
                        st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah.")
                    else:
                        with st.spinner("🔄 Sedang memotong balik akumulasi pakan sapi..."):
                            sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_lama) > 0:
                                share_lama = round(float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama), 2)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= share_lama
                                df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)
                            
                            save_data(df_sapi)

                            df_pakan = df_pakan.drop(df_pakan.index[idx_pilihan]).reset_index(drop=True)
                            write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                            add_activity_log(user_name, "Hapus Pakan", f"Menghapus log pakan No {pilihan_no}: Terhapus data {row_lama['Jenis Pakan']} di {row_lama['Lokasi Pen']}")
                            
                        st.success(f"🗑️ Sukses! Record pakan No Urut {pilihan_no} berhasil dihapus permanen.")
                        st.rerun()