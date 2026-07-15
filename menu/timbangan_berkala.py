import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("⚖️ Manajemen & Pencatatan Timbangan Berkala")
    
    # Skema kolom untuk database riwayat timbangan
    COLS_RIWAYAT_TIMBANG = ["Tanggal Timbang", "Kode Sapi", "RFID/Tag", "Lokasi Pen", "Bobot (kg)", "ADG (kg/hari)", "Operator"]

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi aktif yang tersedia untuk ditimbang.")
        return

    # Paksa kolom numerik menjadi Float
    df_sapi["Bobot Awal (kg)"] = pd.to_numeric(df_sapi["Bobot Awal (kg)"], errors='coerce').fillna(0.0).astype(float)
    df_sapi["Bobot Akhir (kg)"] = pd.to_numeric(df_sapi["Bobot Akhir (kg)"], errors='coerce').fillna(0.0).astype(float)
    df_sapi["ADG (kg/hari)"] = pd.to_numeric(df_sapi["ADG (kg/hari)"], errors='coerce').fillna(0.0).astype(float)

    TARGET_ADG = 1.6

    tab_input, tab_edit, tab_analisis = st.tabs(["➕ Input Timbangan Baru", "⚙️ Edit / Hapus Riwayat", "📈 Analisis Timbang per Sapi"])

    # ==================== TAB 1: INPUT TIMBANGAN BARU ====================
    with tab_input:
        st.markdown("Gunakan filter Blok & Pen untuk mempercepat pencarian sapi yang sedang berada di jembatan timbang.")

        list_lokasi_eksis = df_sapi["Lokasi Pen"].unique()
        grid_filter = {}
        for item in list_lokasi_eksis:
            if " - " in str(item):
                b, p = str(item).split(" - ", 1)
                if b not in grid_filter:
                    grid_filter[b] = []
                grid_filter[b].append(p)
            else:
                if "Format Lama" not in grid_filter:
                    grid_filter["Format Lama"] = []
                grid_filter["Format Lama"].append(str(item))

        st.markdown("#### 🔍 Saring Sapi Berdasarkan Lokasi")
        cf1, cf2 = st.columns(2)
        with cf1:
            filter_blok = st.selectbox("Pilih Blok Kandang Sapi:", list(grid_filter.keys()), key="fb_input")
        with cf2:
            filter_pen = st.selectbox("Pilih Nomor/Bagian Pen Sapi:", sorted(list(set(grid_filter[filter_blok]))), key="fp_input")

        lokasi_pencarian = f"{filter_blok} - {filter_pen}" if filter_blok != "Format Lama" else filter_pen
        df_sapi_terfilter = df_sapi[df_sapi["Lokasi Pen"] == lokasi_pencarian]

        if df_sapi_terfilter.empty:
            st.info(f"ℹ️ Pen **{lokasi_pencarian}** saat ini sedang tidak diisi oleh sapi aktif.")
        else:
            opsi_sapi = df_sapi_terfilter.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
            sapi_pilihan = st.selectbox("Pilih Kode Sapi Yang Ditimbang:", opsi_sapi)
            
            kode_sapi_asli = sapi_pilihan.split(" - RFID: ")[0]
            rfid_sapi_asli = sapi_pilihan.split(" - RFID: ")[1]
            
            matched_rows = df_sapi[(df_sapi["Kode Sapi"] == kode_sapi_asli) & (df_sapi["RFID/Tag"] == rfid_sapi_asli)]
            if matched_rows.empty:
                st.error("⚠️ Data sapi tidak ditemukan di database master.")
            else:
                row_sapi = matched_rows.iloc[0]

                is_penimbangan_pertama = (str(row_sapi['Tgl Cek Akhir']) == str(row_sapi['Tgl Masuk']))
                status_timbang_text = "🟢 PENIMBANGAN PERTAMA (Evaluasi Awal Masa Karantina)" if is_penimbangan_pertama else "🔵 PENIMBANGAN BERKALA / RUTIN"

                st.info(f"📋 **Data Historis Sapi:** ({status_timbang_text})\n* Tanggal Masuk Area: {row_sapi['Tgl Masuk']} | Berat Awal: {row_sapi['Bobot Awal (kg)']} kg\n* RFID Asal: {row_sapi.get('RFID/Tag Asal', '-')} | RFID Baru: {row_sapi['RFID/Tag']}\n* Timbangan Terakhir: {row_sapi['Tgl Cek Akhir']} | Berat Akhir: {row_sapi['Bobot Akhir (kg)']} kg")

                st.markdown("---")
                with st.form("form_timbangan_berkala", clear_on_submit=True):
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        tgl_timbang_sekarang = st.date_input("Tanggal Penimbangan Hari Ini", datetime.now().date())
                    with col_t2:
                        bobot_timbang_baru = st.number_input("Hasil Berat Timbangan Baru (kg)", min_value=30.0, max_value=1500.0, value=float(row_sapi["Bobot Akhir (kg)"]), step=1.0)

                    submit_timbang = st.form_submit_button("Simpan & Kalkulasi ADG Baru", type="primary", use_container_width=True)

                    if submit_timbang:
                        with st.spinner("⏳ Memproses perhitungan ADG dan mengamankan data..."):
                            # [OPTIMASI 1]: Ambil riwayat timbangan HANYA saat tombol Simpan ditekan
                            df_riwayat_timbang = read_sheet_to_df("riwayat_timbangan", COLS_RIWAYAT_TIMBANG)
                            
                            adg_terbaru = float(calculate_adg(row_sapi["Tgl Masuk"], row_sapi["Bobot Awal (kg)"], tgl_timbang_sekarang.strftime("%Y-%m-%d"), bobot_timbang_baru))
                            
                            # Update database master sapi
                            mask = (df_sapi["Kode Sapi"] == kode_sapi_asli) & (df_sapi["RFID/Tag"] == rfid_sapi_asli)
                            df_sapi.loc[mask, "Tgl Cek Akhir"] = tgl_timbang_sekarang.strftime("%Y-%m-%d")
                            df_sapi.loc[mask, "Bobot Akhir (kg)"] = float(bobot_timbang_baru)
                            df_sapi.loc[mask, "ADG (kg/hari)"] = adg_terbaru
                            save_data(df_sapi)

                            # Tambahkan ke log riwayat timbangan
                            new_log = {
                                "Tanggal Timbang": tgl_timbang_sekarang.strftime("%Y-%m-%d"),
                                "Kode Sapi": kode_sapi_asli,
                                "RFID/Tag": rfid_sapi_asli,
                                "Lokasi Pen": row_sapi['Lokasi Pen'],
                                "Bobot (kg)": float(bobot_timbang_baru),
                                "ADG (kg/hari)": adg_terbaru,
                                "Operator": user_name
                            }
                            df_riwayat_timbang = pd.concat([df_riwayat_timbang, pd.DataFrame([new_log])], ignore_index=True)
                            write_df_to_sheet("riwayat_timbangan", df_riwayat_timbang, COLS_RIWAYAT_TIMBANG)
                            
                            add_activity_log(user_name, "Timbangan Rutin", f"Menimbang Sapi {kode_sapi_asli} di {row_sapi['Lokasi Pen']} bobot {bobot_timbang_baru}kg")
                            
                        if adg_terbaru < TARGET_ADG:
                            st.error(f"⚠️ **ALARM PERFORMA RENDAH:** Sapi {kode_sapi_asli} berhasil disimpan. ADG hasil timbangan ini hanya mencapai `{adg_terbaru:.2f} kg/hari` (Target: {TARGET_ADG}).")
                        else:
                            st.success(f"🎉 Sukses! Bobot Sapi {kode_sapi_asli} diperbarui ke {bobot_timbang_baru} kg dengan ADG Bagus: `{adg_terbaru:.2f} kg/hari`.")
                            st.balloons()
                        st.rerun()

    # ==================== TAB 2: EDIT / HAPUS RIWAYAT ====================
    with tab_edit:
        st.markdown("### 📋 Koreksi Data Penimbangan yang Salah Input")
        
        # [OPTIMASI 2]: Ambil riwayat timbangan HANYA saat tab Edit dibuka
        df_riwayat_timbang = read_sheet_to_df("riwayat_timbangan", COLS_RIWAYAT_TIMBANG)
        
        if df_riwayat_timbang.empty:
            st.info("ℹ️ Belum ada data riwayat timbangan yang tercatat.")
        else:
            df_riwayat_timbang_show = df_riwayat_timbang.copy()
            df_riwayat_timbang_show.insert(0, "No Urut", range(1, len(df_riwayat_timbang_show) + 1))
            st.dataframe(df_riwayat_timbang_show, use_container_width=True, hide_index=True, column_config={"Bobot (kg)": st.column_config.NumberColumn(format="%.2f"), "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")})
            
            st.markdown("---")
            pilihan_no = st.number_input("Masukkan 'No Urut' data timbangan yang salah input", min_value=1, max_value=len(df_riwayat_timbang), step=1)
            idx_pilihan = pilihan_no - 1
            row_lama = df_riwayat_timbang.iloc[idx_pilihan]
            
            st.info(f"📍 **Data Terpilih:** {row_lama['Kode Sapi']} (RFID: {row_lama['RFID/Tag']}) | Tanggal: {row_lama['Tanggal Timbang']} | Bobot Lama: {row_lama['Bobot (kg)']} kg")

            col_form, col_auth = st.columns(2)
            with col_form:
                bobot_baru = st.number_input("Koreksi Bobot (kg)", min_value=30.0, value=float(row_lama["Bobot (kg)"]), step=1.0)
            
            with col_auth:
                st.warning("⚠️ Perubahan ini membutuhkan Password Admin.")
                pwd_input = st.text_input("Password Otorisasi Admin", type="password", key="auth_timbang_pass")
            
            btn_col1, btn_col2 = st.columns(2)
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123"

            if btn_col1.button("✏️ Simpan Perubahan", type="primary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin salah.")
                else:
                    with st.spinner("🔄 Sedang memproses koreksi data dan hitung ulang ADG..."):
                        # Ambil bobot awal dari database master untuk re-kalkulasi ADG riwayat ini
                        mask_sapi = (df_sapi["Kode Sapi"] == row_lama["Kode Sapi"]) & (df_sapi["RFID/Tag"] == row_lama["RFID/Tag"])
                        if not df_sapi[mask_sapi].empty:
                            bobot_awal_sapi = df_sapi[mask_sapi].iloc[0]["Bobot Awal (kg)"]
                            tgl_masuk_sapi = df_sapi[mask_sapi].iloc[0]["Tgl Masuk"]
                            adg_baru = calculate_adg(tgl_masuk_sapi, bobot_awal_sapi, row_lama["Tanggal Timbang"], bobot_baru)
                        else:
                            adg_baru = 0.0

                        df_riwayat_timbang.at[idx_pilihan, "Bobot (kg)"] = bobot_baru
                        df_riwayat_timbang.at[idx_pilihan, "ADG (kg/hari)"] = adg_baru
                        df_riwayat_timbang.at[idx_pilihan, "Operator"] = f"{user_name} (Edited)"
                        
                        write_df_to_sheet("riwayat_timbangan", df_riwayat_timbang, COLS_RIWAYAT_TIMBANG)
                        
                        add_activity_log(user_name, "Koreksi Timbangan", f"Koreksi Bobot Sapi {row_lama['Kode Sapi']} dari {row_lama['Bobot (kg)']}kg menjadi {bobot_baru}kg")
                    
                    st.success(f"✅ Data historis No Urut {pilihan_no} berhasil diperbaiki. *Catatan: Jika ini adalah penimbangan terakhir, mohon perbarui juga di Menu Edit Sapi Utama.*")
                    st.rerun()

            if btn_col2.button("🗑️ Hapus Baris Permanen", type="secondary", use_container_width=True):
                if pwd_input != correct_admin_pwd:
                    st.error("❌ Otorisasi Ditolak! Password Admin salah.")
                else:
                    with st.spinner("🔄 Menghapus baris record timbangan..."):
                        df_riwayat_timbang = df_riwayat_timbang.drop(index=idx_pilihan).reset_index(drop=True)
                        write_df_to_sheet("riwayat_timbangan", df_riwayat_timbang, COLS_RIWAYAT_TIMBANG)
                        
                        add_activity_log(user_name, "Hapus Timbangan", f"Hapus log timbang {row_lama['Kode Sapi']} tanggal {row_lama['Tanggal Timbang']}")
                    
                    st.success(f"🗑️ Record timbangan No Urut {pilihan_no} berhasil dihapus permanen.")
                    st.rerun()

    # ==================== TAB 3: ANALISIS TIMBANG ====================
    with tab_analisis:
        st.markdown("### 📈 Evaluasi Kurva Pertumbuhan Individu")
        opsi_semua_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
        sapi_analisis = st.selectbox("Pilih Sapi untuk Dianalisis:", opsi_semua_sapi)
        
        if sapi_analisis:
            # [OPTIMASI 3]: Ambil riwayat timbangan HANYA saat tab Analisis dibuka
            df_riwayat_timbang = read_sheet_to_df("riwayat_timbangan", COLS_RIWAYAT_TIMBANG)
            
            if not df_riwayat_timbang.empty:
                kode_a = sapi_analisis.split(" - RFID: ")[0]
                rfid_a = sapi_analisis.split(" - RFID: ")[1]
                
                df_hist = df_riwayat_timbang[(df_riwayat_timbang["Kode Sapi"] == kode_a) & (df_riwayat_timbang["RFID/Tag"] == rfid_a)].copy()
                
                if df_hist.empty:
                    st.info(f"Belum ada catatan riwayat timbangan tambahan untuk sapi {sapi_analisis}.")
                else:
                    df_hist = df_hist.sort_values(by="Tanggal Timbang")
                    st.markdown(f"**Riwayat Kenaikan Bobot (kg) Sapi: {kode_a}**")
                    
                    # Buat chart
                    df_chart = df_hist[["Tanggal Timbang", "Bobot (kg)"]].set_index("Tanggal Timbang")
                    st.line_chart(df_chart, use_container_width=True)
                    
                    # Buat tabel desimal
                    st.dataframe(df_hist, use_container_width=True, hide_index=True, column_config={"Bobot (kg)": st.column_config.NumberColumn(format="%.2f"), "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")})
            else:
                st.info("ℹ️ Belum ada data riwayat timbangan yang tercatat di database.")