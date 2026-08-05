import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ==================== FUNGSI GENERATOR TEMPLATE EXCEL KARANTINA ====================
def buat_template_excel_karantina():
    """
    Membuat file Excel template Rekam Medis 2 Sheet lengkap dengan
    Menu Dropdown (Data Validation) pada kolom Kondisi Klinis & Tindakan Medis.
    """
    buffer = io.BytesIO()
    
    sample_data = [
        {
            "Tanggal (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Kode Sapi": "S5-001",
            "RFID / Tag Kandang": "-",  # Boleh diisi '-' agar Auto-Lookup RFID dari Master
            "Suhu Tubuh (°C)": 38.5,
            "Kondisi Klinis": "Sehat / Normal",
            "Tindakan Medis": "Injeksi Vitamin (B-Kompleks / ADE)",
            "Catatan Tambahan": "Penanganan rutin awal karantina"
        },
        {
            "Tanggal (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Kode Sapi": "S5-002",
            "RFID / Tag Kandang": "-",
            "Suhu Tubuh (°C)": 39.8,
            "Kondisi Klinis": "Sakit Ringan",
            "Tindakan Medis": "Pemberian Antibiotik",
            "Catatan Tambahan": "Suhu sedikit hangat, mata agak berair"
        }
    ]
    df_sample = pd.DataFrame(sample_data)

    panduan_data = [
        {"KOLOM": "Tanggal (YYYY-MM-DD)", "ATURAN PENGISIAN": "WAJIB DIISI. Format tanggal pemeriksaan medis: YYYY-MM-DD (contoh: 2026-08-04)."},
        {"KOLOM": "Kode Sapi", "ATURAN PENGISIAN": "WAJIB DIISI. Ketik Kode Sapi yang diperiksa (contoh: S5-001). Harus terdaftar di master sapi."},
        {"KOLOM": "RFID / Tag Kandang", "ATURAN PENGISIAN": "OPSIONAL. Nomor RFID/Tag sapi. Isikan '-' jika ingin sistem otomatis melacak RFID dari Kode Sapi."},
        {"KOLOM": "Suhu Tubuh (°C)", "ATURAN PENGISIAN": "WAJIB DIISI. Suhu hasil termometer (contoh: 38.5). Suhu normal sapi: 38.0 - 39.5 °C."},
        {"KOLOM": "Kondisi Klinis", "ATURAN PENGISIAN": "PILIH DARI DROPDOWN EXCEL: 'Sehat / Normal', 'Lesu / Kurang Nafsu Makan', 'Sakit Ringan', 'Sakit Berat', 'Pemulihan'."},
        {"KOLOM": "Tindakan Medis", "ATURAN PENGISIAN": "PILIH DARI DROPDOWN EXCEL: 'Pemberian Obat Cacing (Deworming)', 'Vaksinasi PMK', 'Vaksinasi LSD', 'Injeksi Vitamin (B-Kompleks / ADE)', 'Pemberian Antibiotik', 'Perawatan Luka / Kuku', 'Lainnya (Hanya Observasi)'."},
        {"KOLOM": "Catatan Tambahan", "ATURAN PENGISIAN": "OPSIONAL. Catatan resep, dosis, atau gejala visual (contoh: Vitamin 10ml, feses normal). Isikan '-' jika tidak ada."}
    ]
    df_panduan = pd.DataFrame(panduan_data)

    try:
        from openpyxl.worksheet.datavalidation import DataValidation

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sample.to_excel(writer, sheet_name='FORM_INPUT_REKAM_MEDIS', index=False)
            df_panduan.to_excel(writer, sheet_name='PANDUAN_PENGISIAN', index=False)
            
            wb = writer.book
            ws_input = wb['FORM_INPUT_REKAM_MEDIS']

            # Dropdown Kondisi Klinis
            dv_kondisi = DataValidation(
                type="list", 
                formula1='"Sehat / Normal, Lesu / Kurang Nafsu Makan, Sakit Ringan, Sakit Berat, Pemulihan"', 
                allow_blank=True
            )
            ws_input.add_data_validation(dv_kondisi)
            dv_kondisi.add("E2:E500")

            # Dropdown Tindakan Medis
            dv_tindakan = DataValidation(
                type="list", 
                formula1='"Pemberian Obat Cacing (Deworming), Vaksinasi PMK, Vaksinasi LSD, Injeksi Vitamin (B-Kompleks / ADE), Pemberian Antibiotik, Perawatan Luka / Kuku, Lainnya (Hanya Observasi)"', 
                allow_blank=True
            )
            ws_input.add_data_validation(dv_tindakan)
            dv_tindakan.add("F2:F500")

        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        buffer = io.BytesIO()
        df_sample.to_csv(buffer, index=False)
        ext = "csv"
        mime = "text/csv"

    return buffer.getvalue(), ext, mime


def tampilkan_menu_karantina(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, user_role, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🏥 Manajemen Karantina & Rekam Medis")
    st.markdown("Fokus pemantauan intensif, pemberian obat/vaksin, dan evaluasi *biosecurity* sapi sebelum masuk masa penggemukan utama.")

    if "uploader_key_karantina" not in st.session_state:
        st.session_state["uploader_key_karantina"] = 0

    COLS_MEDIS = ["Tanggal", "Kode Sapi", "RFID/Tag", "Suhu Tubuh (°C)", "Kondisi Klinis", "Tindakan Medis", "Catatan", "Operator"]

    # Filter Strict: Hanya gunakan populasi sapi berstatus AKTIF
    df_sapi_aktif = df_sapi[df_sapi["Status"] == "AKTIF"] if "Status" in df_sapi.columns else df_sapi

    mask_karantina = df_sapi_aktif["Lokasi Pen"].str.contains("Karantina|Isolasi", case=False, na=False)
    df_sapi_karantina = df_sapi_aktif[mask_karantina]

    struktur_karantina = {b: p for b, p in STRUKTUR_KANDANG.items() if "karantina" in b.lower() or "isolasi" in b.lower()}

    tab_status, tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Sebaran Populasi Karantina",
        "🩺 Tindakan Medis & Observasi", 
        "🚪 Mutasi Lulus Karantina", 
        "⚙️ Edit / Hapus Data Medis", 
        "📜 Riwayat & Rekam Medis"
    ])

    # ==================== TAB 0: SEBARAN POPULASI KARANTINA & ISOLASI ====================
    with tab_status:
        st.markdown("### 🏬 Peta Distribusi Sapi Karantina & Isolasi Saat Ini")
        st.caption("💡 **Legenda Warna:** 🟥 Background Merah = Sapi Sakit/Isolasi | 🟨 Background Kuning = Performa ADG Rendah (< 1.6 kg/hari)")
        
        def highlight_sapi_pen(row):
            is_sakit = "Isolasi" in str(row.get("Lokasi Pen", ""))
            if is_sakit: return ['background-color: rgba(255, 75, 75, 0.2)'] * len(row)
            try:
                adg = float(row.get("ADG (kg/hari)", 0.0))
                tgl_cek = str(row.get("Tgl Cek Akhir", ""))
                tgl_masuk = str(row.get("Tgl Masuk", ""))
                if adg < 1.6 and tgl_cek != tgl_masuk and tgl_cek != "nan":
                    return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
            except: pass
            return [''] * len(row)

        if not struktur_karantina:
            st.info("ℹ️ Tidak ada blok Karantina atau Isolasi yang terdaftar di master pen kandang.")
        else:
            for blok, pens in struktur_karantina.items():
                sapi_di_blok = df_sapi_karantina[df_sapi_karantina["Lokasi Pen"].str.startswith(blok, na=False)]
                total_sapi_blok = len(sapi_di_blok)
                 
                with st.expander(f"📂 {blok.upper()} (Total Sapi Aktif: {total_sapi_blok} Ekor)", expanded=True):
                    if total_sapi_blok == 0:
                        st.caption("ℹ️ Blok kandang ini masih kosong dari sapi aktif.")
                    else:
                        for pen in pens:
                            full_name_pen = f"{blok} - {pen}"
                            sapi_di_pen = df_sapi_karantina[df_sapi_karantina["Lokasi Pen"] == full_name_pen]
                            
                            if not sapi_di_pen.empty:
                                st.markdown(f"🔹 **{pen}** ({len(sapi_di_pen)}/25 Ekor):")
                                df_tampil = sapi_di_pen[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Bobot Akhir (kg)", "ADG (kg/hari)", "Tgl Cek Akhir", "Tgl Masuk", "Lokasi Pen"]].reset_index(drop=True)
                                
                                styled_df = df_tampil.style.apply(highlight_sapi_pen, axis=1)
                                st.dataframe(
                                    styled_df, 
                                    use_container_width=True, hide_index=True,
                                    column_config={
                                        "Lokasi Pen": None,
                                        "Bobot Akhir (kg)": st.column_config.NumberColumn(format="%.2f"),
                                        "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")
                                    }
                                )
                            else:
                                st.markdown(f"⚪ *{pen}* : (Kosong)")

    # ==================== TAB 1: TINDAKAN MEDIS ====================
    with tab1:
        sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

        # ------------------- SUB-TAB 1: INPUT SATUAN -------------------
        with sub_satuan:
            st.markdown("### 📝 Input Hasil Observasi & Penanganan Medis Manual")
            
            if df_sapi_karantina.empty:
                st.info("ℹ️ Saat ini tidak ada sapi aktif yang berada di pen Karantina atau Isolasi.")
            else:
                mode_input = st.radio(
                    "Pilih Mode Input Tindakan:",
                    ["Per Sapi Individual", "Massal Per Pen Karantina"],
                    horizontal=True
                )
                
                if mode_input == "Per Sapi Individual":
                    opsi_sapi = df_sapi_karantina.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']} (di {r['Lokasi Pen']})", axis=1).tolist()
                    sapi_terpilih = st.selectbox("Pilih Sapi Target:", opsi_sapi)
                else:
                    opsi_pen = df_sapi_karantina["Lokasi Pen"].dropna().unique().tolist()
                    pen_terpilih = st.selectbox("Pilih Pen Karantina Target (Massal):", opsi_pen)
                    jml_sapi_target = len(df_sapi_karantina[df_sapi_karantina["Lokasi Pen"] == pen_terpilih])
                    st.info(f"📢 **Rencana Tindakan Massal:** Tindakan medis akan otomatis diterapkan secara SERENTAK ke seluruh **{jml_sapi_target} ekor sapi aktif** di **{pen_terpilih}**.")
                
                with st.form("form_medis", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        tgl_medis = st.date_input("Tanggal Tindakan", datetime.now().date())
                        suhu = st.number_input("Suhu Tubuh (°C)", min_value=30.0, max_value=45.0, value=38.5, step=0.1, help="Suhu normal sapi sekitar 38.0 - 39.5 °C")
                        kondisi = st.selectbox("Kondisi Klinis", ["Sehat / Normal", "Lesu / Kurang Nafsu Makan", "Sakit Ringan", "Sakit Berat", "Pemulihan"])
                    
                    with col2:
                        tindakan = st.multiselect("Tindakan Medis / Profilaksis", [
                            "Pemberian Obat Cacing (Deworming)", 
                            "Vaksinasi PMK", 
                            "Vaksinasi LSD", 
                            "Injeksi Vitamin (B-Kompleks / ADE)", 
                            "Pemberian Antibiotik",
                            "Perawatan Luka / Kuku",
                            "Lainnya (Hanya Observasi)"
                        ])
                        catatan = st.text_area("Catatan Tambahan (Opsional)", placeholder="Cth: Mata sedikit berair, feses normal.")
                    
                    submit_medis = st.form_submit_button("Simpan Rekam Medis", type="primary", use_container_width=True)
                    
                    if submit_medis:
                        if not tindakan:
                            st.error("❌ Tindakan medis wajib diisi (Pilih minimal 'Lainnya').")
                        else:
                            if mode_input == "Per Sapi Individual":
                                kode_asli = sapi_terpilih.split(" - RFID: ")[0]
                                rfid_asli = sapi_terpilih.split(" - RFID: ")[1].split(" (di ")[0]
                                df_target = df_sapi_karantina[(df_sapi_karantina["Kode Sapi"] == kode_asli) & (df_sapi_karantina["RFID/Tag"] == rfid_asli)]
                            else:
                                df_target = df_sapi_karantina[df_sapi_karantina["Lokasi Pen"] == pen_terpilih]
                            
                            if df_target.empty:
                                st.error("❌ Gagal Simpan! Tidak ada data sapi aktif yang terdeteksi.")
                            else:
                                new_records = []
                                for _, r in df_target.iterrows():
                                    new_records.append({
                                        "Tanggal": tgl_medis.strftime("%Y-%m-%d"),
                                        "Kode Sapi": r["Kode Sapi"],
                                        "RFID/Tag": r["RFID/Tag"],
                                        "Suhu Tubuh (°C)": float(suhu),
                                        "Kondisi Klinis": kondisi,
                                        "Tindakan Medis": ", ".join(tindakan),
                                        "Catatan": catatan if catatan else "-",
                                        "Operator": user_name
                                    })
                                
                                with st.spinner("⏳ Mengamankan data rekam medis ke database..."):
                                    df_medis = read_sheet_to_df("riwayat_medis_karantina", COLS_MEDIS)
                                    df_medis = pd.concat([df_medis, pd.DataFrame(new_records)], ignore_index=True)
                                    write_df_to_sheet("riwayat_medis_karantina", df_medis, COLS_MEDIS)
                                
                                tindakan_str = ", ".join(tindakan)
                                if mode_input == "Per Sapi Individual":
                                    log_msg = f"Input kondisi {kondisi} & tindakan {tindakan_str} untuk sapi {df_target.iloc[0]['Kode Sapi']}"
                                    st.success(f"✅ Rekam medis untuk sapi {df_target.iloc[0]['Kode Sapi']} berhasil disimpan.")
                                else:
                                    log_msg = f"Input kondisi massal {kondisi} & tindakan {tindakan_str} untuk {len(new_records)} sapi di {pen_terpilih}"
                                    st.success(f"✅ Rekam medis massal untuk {len(new_records)} ekor sapi di {pen_terpilih} berhasil disimpan.")
                                    
                                add_activity_log(user_name, "Rekam Medis", log_msg)
                                st.rerun()

        # ------------------- SUB-TAB 2: UPLOAD BATCH EXCEL -------------------
        with sub_excel:
            st.markdown("### 📥 Import Rekam Medis Karantina via File Excel")
            st.caption("Unggah catatan hasil rekam medis/vaksinasi masal langsung dari file Excel.")

            st.markdown("#### 1. Unduh Template Resmi (Dilengkapi Dropdown Pilihan)")
            bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel_karantina()
            st.download_button(
                label=f"📥 Unduh Template Excel Rekam Medis (.{ext_tmpl.upper()})",
                data=bytes_tmpl,
                file_name=f"Template_Rekam_Medis_Karantina.{ext_tmpl}",
                mime=mime_tmpl,
                type="secondary",
                help="Template ini sudah dilengkapi dropdown otomatis di kolom Kondisi Klinis & Tindakan Medis."
            )

            st.markdown("---")
            st.markdown("#### 2. Unggah File Excel Catatan Petugas Medis")
            uploaded_file = st.file_uploader(
                "Pilih file Excel (.xlsx / .xls / .csv) yang sudah diisi:", 
                type=["xlsx", "xls", "csv"],
                key=f"file_uploader_karantina_{st.session_state['uploader_key_karantina']}"
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file, sheet_name=0)

                    st.markdown("#### 3. Pratinjau & Validasi Data Otomatis")

                    rows_to_save = []
                    validation_errors = []

                    map_kode_to_rfid = {}
                    if not df_sapi_aktif.empty and "Kode Sapi" in df_sapi_aktif.columns and "RFID/Tag" in df_sapi_aktif.columns:
                        for _, sr in df_sapi_aktif.iterrows():
                            map_kode_to_rfid[str(sr["Kode Sapi"]).strip()] = str(sr["RFID/Tag"]).strip()

                    for idx, r in df_upload.iterrows():
                        no_baris = idx + 2

                        tgl_m = str(r.get("Tanggal (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()
                        if len(tgl_m) > 10: tgl_m = tgl_m[:10]

                        kode_s = str(r.get("Kode Sapi", "")).strip()
                        rfid_raw = str(r.get("RFID / Tag Kandang", "-")).strip()
                        
                        if rfid_raw in ["-", "nan", "None", ""]:
                            rfid_s = map_kode_to_rfid.get(kode_s, "-")
                        else:
                            rfid_s = rfid_raw

                        try: suhu = float(r.get("Suhu Tubuh (°C)", 38.5))
                        except: suhu = 38.5

                        kondisi = str(r.get("Kondisi Klinis", "Sehat / Normal")).strip()
                        tindakan = str(r.get("Tindakan Medis", "Lainnya (Hanya Observasi)")).strip()
                        catatan = str(r.get("Catatan Tambahan", "-")).strip()

                        err_msg = []
                        if not kode_s or kode_s in ["nan", "None", ""]:
                            err_msg.append("Kode Sapi kosong")
                        elif kode_s not in map_kode_to_rfid:
                            err_msg.append(f"Kode Sapi '{kode_s}' tidak ditemukan di populasi sapi aktif")

                        if suhu < 30.0 or suhu > 45.0:
                            err_msg.append(f"Suhu {suhu}°C di luar rentang wajar (30 - 45°C)")

                        status_str = "✅ SIAP SIMPAN" if not err_msg else f"❌ ERROR: {', '.join(err_msg)}"
                        if err_msg:
                            validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")

                        rows_to_save.append({
                            "Tanggal": tgl_m,
                            "Kode Sapi": kode_s if kode_s not in ["nan", "None", ""] else "-",
                            "RFID/Tag": rfid_s,
                            "Suhu Tubuh (°C)": suhu,
                            "Kondisi Klinis": kondisi if kondisi not in ["nan", "None", ""] else "Sehat / Normal",
                            "Tindakan Medis": tindakan if tindakan not in ["nan", "None", ""] else "Lainnya (Hanya Observasi)",
                            "Catatan": catatan if catatan not in ["nan", "None", ""] else "-",
                            "Operator": user_name,
                            "Status Validasi": status_str
                        })

                    df_preview = pd.DataFrame(rows_to_save)
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)

                    if validation_errors:
                        st.error(f"⚠️ Ditemukan **{len(validation_errors)} kesalahan** pada file Excel Anda:")
                        for err in validation_errors[:10]:
                            st.write(f"* {err}")
                        if len(validation_errors) > 10:
                            st.caption(f"... dan {len(validation_errors) - 10} kesalahan lainnya.")
                        st.warning("Perbaiki file Excel Anda lalu unggah kembali, atau abaikan baris bermasalah untuk menyimpan data yang valid saja.")

                    df_valid_only = df_preview[df_preview["Status Validasi"] == "✅ SIAP SIMPAN"].drop(columns=["Status Validasi"])
                    
                    if not df_valid_only.empty:
                        if st.button(f"🚀 Simpan {len(df_valid_only)} Rekam Medis Valid ke Database", type="primary", use_container_width=True):
                            with st.spinner("💾 Mengunggah rekam medis karantina ke database Supabase..."):
                                df_medis_existing = read_sheet_to_df("riwayat_medis_karantina", COLS_MEDIS)
                                df_baru_total = pd.concat([df_medis_existing, df_valid_only], ignore_index=True)
                                write_df_to_sheet("riwayat_medis_karantina", df_baru_total, COLS_MEDIS)
                                add_activity_log(user_name, "Batch Rekam Medis", f"Mengunggah {len(df_valid_only)} data rekam medis karantina via Excel")
                            
                            st.session_state["uploader_key_karantina"] += 1
                            st.toast(f"🎉 Berhasil menyimpan {len(df_valid_only)} rekam medis karantina!", icon="🚀")
                            st.rerun()
                    else:
                        st.error("Tidak ada baris data yang valid untuk disimpan.")

                except Exception as e:
                    st.error(f"❌ Gagal membaca file Excel. Pastikan menggunakan template resmi! Detail Error: {e}")

    # ==================== TAB 2: MUTASI LULUS KARANTINA ====================
    with tab2:
        st.markdown("### 🚪 Rilis Sapi ke Pen Penggemukan")
        st.markdown("Gunakan menu ini untuk memindahkan sapi dari Pen Karantina/Isolasi ke Pen Penggemukan secara massal maupun selektif.")
        
        if df_sapi_karantina.empty:
            st.info("ℹ️ Tidak ada sapi aktif di Pen Karantina yang siap di-mutasi.")
        else:
            daftar_pen_karantina = df_sapi_karantina["Lokasi Pen"].dropna().unique().tolist()
            pen_asal = st.selectbox("Pilih Pen Karantina Asal:", daftar_pen_karantina)
            
            df_sapi_pen_asal = df_sapi_karantina[df_sapi_karantina["Lokasi Pen"] == pen_asal]
            
            st.markdown("---")
            st.markdown(f"#### 🐄 Daftar Sapi Aktif di **{pen_asal}** ({len(df_sapi_pen_asal)} Ekor)")
            
            opsi_sapi_pen = df_sapi_pen_asal.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
            
            sapi_terpilih_list = st.multiselect(
                "Pilih Sapi yang Lulus Karantina (Centang Semua = Mutasi Massal):",
                options=opsi_sapi_pen,
                default=opsi_sapi_pen,
                help="Secara otomatis semua sapi di pen ini tercentang. Hilangkan centang pada sapi tertentu jika belum lulus/masih butuh karantina."
            )
            
            st.caption(f"📊 **Status Terpilih:** {len(sapi_terpilih_list)} dari {len(df_sapi_pen_asal)} ekor sapi akan dipindahkan.")
            
            st.markdown("---")
            st.markdown("#### 🎯 Pilih Pen Penggemukan Tujuan")
            c_mut1, c_mut2 = st.columns(2)
            with c_mut1:
                blok_tujuan = st.selectbox("Blok Penggemukan:", [b for b in STRUKTUR_KANDANG.keys() if "karantina" not in b.lower() and "isolasi" not in b.lower()])
            with c_mut2:
                pen_tujuan = st.selectbox("Pen Tujuan:", STRUKTUR_KANDANG.get(blok_tujuan, [])) if blok_tujuan else None
                
            full_tujuan = f"{blok_tujuan} - {pen_tujuan}"
            
            # Hitung populasi aktif di pen tujuan
            sapi_di_pen_tujuan = len(df_sapi_aktif[df_sapi_aktif["Lokasi Pen"] == full_tujuan])
            sisa_kapasitas = 25 - sapi_di_pen_tujuan
            
            if sapi_di_pen_tujuan >= 25:
                st.error(f"⚠️ Pen **{full_tujuan}** sudah PENUH ({sapi_di_pen_tujuan}/25 Ekor Sapi Aktif). Silakan pilih pen lain.")
            else:
                st.info(f"ℹ️ Pen **{full_tujuan}** saat ini terisi {sapi_di_pen_tujuan}/25 Ekor Sapi Aktif. Sisa kapasitas: **{sisa_kapasitas} ekor**.")
            
            if st.button("🚀 Mutasikan Sapi Terpilih Keluar Karantina", type="primary", use_container_width=True):
                if not sapi_terpilih_list:
                    st.error("❌ Gagal! Pilih minimal 1 ekor sapi yang akan dimutasi.")
                elif len(sapi_terpilih_list) > sisa_kapasitas:
                    st.error(f"❌ Gagal! Kapasitas pen tujuan tidak cukup. Anda memilih {len(sapi_terpilih_list)} ekor, tetapi sisa kapasitas pen {full_tujuan} hanya {sisa_kapasitas} ekor.")
                else:
                    for item in sapi_terpilih_list:
                        kode_m = item.split(" - RFID: ")[0]
                        rfid_m = item.split(" - RFID: ")[1]
                        
                        mask = (df_sapi["Kode Sapi"] == kode_m) & (df_sapi["RFID/Tag"] == rfid_m)
                        if "Status" in df_sapi.columns:
                            mask = mask & (df_sapi["Status"] == "AKTIF")
                        df_sapi.loc[mask, "Lokasi Pen"] = full_tujuan
                    
                    save_data(df_sapi)
                    
                    log_msg = f"Mutasi lulus karantina {len(sapi_terpilih_list)} ekor sapi dari {pen_asal} ke {full_tujuan}"
                    add_activity_log(user_name, "Lulus Karantina", log_msg)
                    
                    st.success(f"🎉 Selamat! Sebanyak {len(sapi_terpilih_list)} ekor sapi dari {pen_asal} telah resmi lulus fase karantina dan dipindahkan ke {full_tujuan}.")
                    st.balloons()
                    st.rerun()

    # ==================== TAB 3: EDIT / HAPUS (OTORISASI) ====================
    with tab3:
        st.markdown("### ⚙️ Koreksi Rekam Medis")
        is_admin = str(user_role).lower() == "admin"
        
        df_medis = read_sheet_to_df("riwayat_medis_karantina", COLS_MEDIS)
        
        if df_medis.empty:
            st.info("Belum ada data rekam medis.")
        else:
            df_medis_view = df_medis.copy()
            df_medis_view.insert(0, "No Urut", range(1, len(df_medis) + 1))
            st.dataframe(df_medis_view, use_container_width=True, hide_index=True)
            
            idx_edit = st.number_input("Masukkan No Urut Data Medis yang Ingin Dihapus:", min_value=1, max_value=len(df_medis), step=1) - 1
            row_edit = df_medis.iloc[idx_edit]
            st.warning(f"Terpilih: Rekam medis Sapi {row_edit['Kode Sapi']} tanggal {row_edit['Tanggal']}.")
            
            pwd_hapus = ""
            if not is_admin:
                pwd_hapus = st.text_input("🔐 Masukkan Password Admin untuk menghapus:", type="password")
                
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123"

            if st.button("🗑️ Hapus Rekam Medis Ini", type="secondary"):
                if not is_admin and pwd_hapus != correct_admin_pwd:
                    st.error("❌ Gagal! Password Admin salah.")
                else:
                    with st.spinner("🔄 Menghapus rekam medis dari database..."):
                        df_medis = df_medis.drop(index=idx_edit).reset_index(drop=True)
                        write_df_to_sheet("riwayat_medis_karantina", df_medis, COLS_MEDIS)
                    add_activity_log(user_name, "Hapus Medis", f"Menghapus riwayat medis karantina sapi {row_edit['Kode Sapi']}")
                    st.success("✅ Data rekam medis berhasil dihapus.")
                    st.rerun()

    # ==================== TAB 4: RIWAYAT MEDIS ====================
    with tab4:
        st.markdown("### 📜 Buku Rekam Medis Karantina Sapi")
        
        df_medis = read_sheet_to_df("riwayat_medis_karantina", COLS_MEDIS)
        
        if df_medis.empty:
            st.info("Belum ada data rekam medis yang tersimpan.")
        else:
            list_sapi_medis = ["Semua Sapi"] + df_medis["Kode Sapi"].unique().tolist()
            filter_sapi = st.selectbox("Filter berdasarkan Kode Sapi:", list_sapi_medis)
            
            df_tampil = df_medis if filter_sapi == "Semua Sapi" else df_medis[df_medis["Kode Sapi"] == filter_sapi]
            
            st.dataframe(
                df_tampil.sort_values(by="Tanggal", ascending=False), 
                use_container_width=True, 
                hide_index=True,
                column_config={"Suhu Tubuh (°C)": st.column_config.NumberColumn(format="%.1f")}
            )