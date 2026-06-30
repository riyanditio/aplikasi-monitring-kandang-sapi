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
    
    # --- JANGKAH DAFTAR PEN DARI STRUKTUR KANDANG ---
    daftar_pen_pakan = []
    for blok, daftar_pen_di_blok in STRUKTUR_KANDANG.items():
        for pen in daftar_pen_di_blok:
            daftar_pen_pakan.append(f"{blok} - {pen}")

    # ==================== TAB 1: INPUT PAKAN BARU ====================
    with tab1:
        st.markdown("### 📝 Form Catat Pemberian Pakan Harian")
        
        with st.form("form_input_pakan"):
            tgl_pakan = st.date_input("Tanggal Distribusi Pakan", datetime.now().date())
            pen_terpilih = st.selectbox("Pilih Target Lokasi Pen", list(daftar_pen_pakan))
            jenis_pakan = st.text_input("Jenis / Nama Formula Pakan", placeholder="Contoh: Konsentrat Hijau, Silase, Jerami Fermentasi").strip()
            jumlah_pakan = st.number_input("Total Berat Pakan Diturunkan (kg)", min_value=0.0, step=1.0, format="%.1f")
            
            submit_btn = st.form_submit_button("Simpan Pemberian Pakan", type="primary")
            
            if submit_btn:
                if not jenis_pakan or jumlah_pakan <= 0:
                    st.error("❌ Gagal Simpan! Jenis pakan wajib diisi dan berat harus lebih dari 0 kg.")
                else:
                    # Cari total populasi sapi aktif di dalam pen tersebut
                    sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == pen_terpilih]
                    jumlah_sapi = len(sapi_di_pen)
                    
                    # 1. Masukkan baris baru ke log pakan harian
                    row_pakan_baru = {
                        "Tanggal": str(tgl_pakan),
                        "Lokasi Pen": pen_terpilih,
                        "Jenis Pakan": jenis_pakan,
                        "Jumlah Pakan (kg)": jumlah_pakan,
                        "Operator": user_name
                    }
                    df_pakan = pd.concat([df_pakan, pd.DataFrame([row_pakan_baru])], ignore_index=True)
                    write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)
                    
                    # 2. Distribusikan beban pakan rata ke setiap ekor sapi di pen tersebut
                    if jumlah_sapi > 0:
                        pakan_per_ekor = round(jumlah_pakan / jumlah_sapi, 2)
                        df_sapi.loc[df_sapi["Lokasi Pen"] == pen_terpilih, "Total Pakan (kg)"] += pakan_per_ekor
                        df_sapi.loc[df_sapi["Lokasi Pen"] == pen_terpilih, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                        save_data(df_sapi)
                        detail_sukses = f"Mendistribusikan {jenis_pakan} sebanyak {jumlah_pakan} kg ke {pen_terpilih} ({jumlah_sapi} ekor, @{pakan_per_ekor} kg/ekor)"
                    else:
                        detail_sukses = f"Mencatat {jenis_pakan} sebanyak {jumlah_pakan} kg di {pen_terpilih} (Kondisi pen sedang kosong)"
                    
                    # 3. Rekam jejak audit di log aktivitas
                    add_activity_log(user_name, "Input Pakan", detail_sukses)
                    st.success(f"🎉 Berhasil! {detail_sukses}")
                    st.rerun()

    # ==================== TAB 2: EDIT / HAPUS (PASSWORD LOCKED) ====================
    with tab2:
        st.markdown("### 📋 Koreksi & Pembersihan Salah Input Pakan")
        
        if df_pakan.empty:
            st.info("ℹ️ Belum ada data riwayat pemberian pakan harian yang tercatat di database.")
        else:
            # Tampilkan list tabel pakan dengan nomor index visual agar mudah ditunjuk
            df_pakan_show = df_pakan.copy()
            df_pakan_show.insert(0, "No Urut", range(1, len(df_pakan) + 1))
            st.dataframe(df_pakan_show, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### 🔐 Panel Otorisasi Koreksi Data")
            
            # Form pemilihan baris data yang salah input
            pilihan_no = st.number_input("Masukkan 'No Urut' data pakan yang salah input", min_value=1, max_value=len(df_pakan), step=1)
            idx_pilihan = pilihan_no - 1
            row_lama = df_pakan.iloc[idx_pilihan]
            
            # Bagi layout kolom pengisian data baru vs otorisasi password
            col_form, col_auth = st.columns(2)
            
            with col_form:
                st.info(f"📍 **Data Terpilih saat ini:** Pen {row_lama['Lokasi Pen']} | {row_lama['Jenis Pakan']} | {row_lama['Jumlah Pakan (kg)']} kg")
                pen_baru = st.selectbox("Koreksi Lokasi Pen", list(daftar_pen_pakan), index=list(daftar_pen_pakan).index(row_lama["Lokasi Pen"]) if row_lama["Lokasi Pen"] in daftar_pen_pakan else 0)
                jenis_baru = st.text_input("Koreksi Jenis Pakan", value=str(row_lama["Jenis Pakan"])).strip()
                jumlah_baru = st.number_input("Koreksi Jumlah Pakan (kg)", min_value=0.0, value=float(row_lama["Jumlah Pakan (kg)"]), step=1.0, format="%.1f")
                
            with col_auth:
                st.warning("⚠️ **Perhatian:** Segala tindakan perubahan atau penghapusan riwayat pakan harian akan diverifikasi langsung menggunakan kata sandi Admin Utama Kandang.")
                pwd_input = st.text_input("Masukkan Password Otorisasi Admin", type="password", key="auth_pakan_pass")
            
            st.markdown(" ")
            btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 2])
            
            # Tarik password master admin dari rahasia st.secrets (Sama dengan app.py)
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123" # Cadangan default jika secrets belum diset

            # --- SELEKSI EKSEKUSI BUTTON EDIT ---
            if btn_col1.button("✏️ Simpan Perubahan Data", type="primary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah atau tidak terverifikasi.")
                elif not jenis_baru or jumlah_baru <= 0:
                    st.error("❌ Perubahan Gagal! Nama pakan harus valid dan berat tidak boleh nol.")
                else:
                    with st.spinner("🔄 Sedang memproses ulang kalkulasi timbangan pakan sapi..."):
                        # --- STEP 1: RESTORE / TARIK BALIK DATA LAMA ---
                        sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                        if len(sapi_pen_lama) > 0:
                            share_lama = round(float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama), 2)
                            df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= share_lama
                            # Cegah minus pakan agar data logis
                            df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)

                        # --- STEP 2: DISTRIBUSIKAN ULANG DATA KOREKSI BARU ---
                        sapi_pen_baru = df_sapi[df_sapi["Lokasi Pen"] == pen_baru]
                        if len(sapi_pen_baru) > 0:
                            share_baru = round(jumlah_baru / len(sapi_pen_baru), 2)
                            df_sapi.loc[df_sapi["Lokasi Pen"] == pen_baru, "Total Pakan (kg)"] += share_baru
                        
                        # Simpan pembaruan status master data sapi
                        save_data(df_sapi)

                        # --- STEP 3: UPDATE SHEET LOG PAKAN ---
                        df_pakan.at[idx_pilihan, "Lokasi Pen"] = pen_baru
                        df_pakan.at[idx_pilihan, "Jenis Pakan"] = jenis_baru
                        df_pakan.at[idx_pilihan, "Jumlah Pakan (kg)"] = jumlah_baru
                        df_pakan.at[idx_pilihan, "Operator"] = f"{user_name} (Edited)"
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                        # Catat ke log aktivitas audit
                        add_activity_log(user_name, "Koreksi Pakan", f"Mengubah log pakan No {pilihan_no}: Dari [{row_lama['Jenis Pakan']} - {row_lama['Jumlah Pakan (kg)']}kg] Menjadi [{jenis_baru} - {jumlah_baru}kg]")
                        
                    st.success(f"✅ Sukses! Data pakan No Urut {pilihan_no} berhasil diperbaiki dan bobot sapi disinkronisasikan.")
                    st.balloons()
                    st.rerun()

            # --- SELEKSI EKSEKUSI BUTTON HAPUS ---
            if btn_col2.button("🗑️ Hapus Data Permanen", type="secondary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin Kandang salah atau tidak terverifikasi.")
                else:
                    with st.spinner("🔄 Sedang memotong balik akumulasi pakan sapi..."):
                        # --- STEP 1: RESTORE / TARIK BALIK DATA LAMA ---
                        sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                        if len(sapi_pen_lama) > 0:
                            share_lama = round(float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama), 2)
                            df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= share_lama
                            df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)
                        
                        save_data(df_sapi)

                        # --- STEP 2: DELETE DARI DATAFRAME LOG PAKAN ---
                        df_pakan = df_pakan.drop(df_pakan.index[idx_pilihan]).reset_index(drop=True)
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)

                        # Catat ke log aktivitas audit
                        add_activity_log(user_name, "Hapus Pakan", f"Menghapus log pakan No {pilihan_no}: Terhapus data {row_lama['Jenis Pakan']} sebanyak {row_lama['Jumlah Pakan (kg)']} kg di {row_lama['Lokasi Pen']}")
                        
                    st.success(f"🗑️ Sukses! Record pakan No Urut {pilihan_no} berhasil dihapus permanen dari sistem.")
                    st.rerun()