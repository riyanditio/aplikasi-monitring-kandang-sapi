import streamlit as st
import pandas as pd
from datetime import datetime
import io
import importlib

# ==================== FUNGSI GENERATOR TEMPLATE EXCEL PAKAN ====================
def buat_template_excel_pakan(STRUKTUR_KANDANG):
    """
    Membuat file Excel template Input Pakan Harian 2 Sheet
    dilengkapi Dropdown pilihan Metode Pemberian & Jenis Pakan.
    """
    buffer = io.BytesIO()
    
    blok_default = list(STRUKTUR_KANDANG.keys())[0] if STRUKTUR_KANDANG else "Blok Karantina"
    pen_default = STRUKTUR_KANDANG[blok_default][0] if (STRUKTUR_KANDANG and STRUKTUR_KANDANG[blok_default]) else "Pen Karantina 1"

    sample_data = [
        {
            "Tanggal (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Blok Kandang": blok_default,
            "Nomor Pen": pen_default,
            "Metode Pemberian": "Serentak",
            "Kode Sapi Target (Jika Spesifik)": "-",
            "Jenis Pakan": "Konsentrat Hijau",
            "Kuantitas Pakan (kg)": 5.5
        },
        {
            "Tanggal (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Blok Kandang": blok_default,
            "Nomor Pen": pen_default,
            "Metode Pemberian": "Spesifik",
            "Kode Sapi Target (Jika Spesifik)": "S5-002",
            "Jenis Pakan": "Obat/Suplemen Khusus",
            "Kuantitas Pakan (kg)": 1.0
        }
    ]
    df_sample = pd.DataFrame(sample_data)

    panduan_data = [
        {"KOLOM": "Tanggal (YYYY-MM-DD)", "ATURAN PENGISIAN": "WAJIB DIISI. Format tanggal distribusi pakan: YYYY-MM-DD (contoh: 2026-08-04)."},
        {"KOLOM": "Blok Kandang", "ATURAN PENGISIAN": f"HARUS SAMA PERSIS DENGAN MASTER BLOK: {', '.join(list(STRUKTUR_KANDANG.keys()))}"},
        {"KOLOM": "Nomor Pen", "ATURAN PENGISIAN": "WAJIB DIISI. Nama Pen lokasi kandang (contoh: Pen Karantina 1, Pen A1)."},
        {"KOLOM": "Metode Pemberian", "ATURAN PENGISIAN": "PILIH DARI DROPDOWN EXCEL: 'Serentak' (diberikan serentak ke seluruh sapi di pen) atau 'Spesifik' (pakan khusus 1 ekor)."},
        {"KOLOM": "Kode Sapi Target (Jika Spesifik)", "ATURAN PENGISIAN": "DIISI JIKA METODE = 'Spesifik'. Ketik Kode Sapi target (contoh: S5-002). Isikan '-' jika Metode = 'Serentak'."},
        {"KOLOM": "Jenis Pakan", "ATURAN PENGISIAN": "PILIH DARI DROPDOWN EXCEL: 'Konsentrat Hijau', 'Silase', 'Jerami Fermentasi', 'Obat/Suplemen Khusus', 'TUM / Pakan Campur', 'Lain-lain'."},
        {"KOLOM": "Kuantitas Pakan (kg)", "ATURAN PENGISIAN": "WAJIB DIISI. Jika Serentak: isikan jatah kg/ekor. Jika Spesifik: isikan total kg untuk sapi tersebut."}
    ]
    df_panduan = pd.DataFrame(panduan_data)

    try:
        mod_dv = importlib.import_module("openpyxl.worksheet.datavalidation")
        DataValidation = getattr(mod_dv, "DataValidation")

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sample.to_excel(writer, sheet_name='FORM_INPUT_PAKAN_HARIAN', index=False)
            df_panduan.to_excel(writer, sheet_name='PANDUAN_PENGISIAN', index=False)
            
            wb = writer.book
            ws_input = wb['FORM_INPUT_PAKAN_HARIAN']

            # 1. Dropdown Kolom D (Metode Pemberian)
            dv_metode = DataValidation(
                type="list", 
                formula1='"Serentak, Spesifik"', 
                allow_blank=True
            )
            ws_input.add_data_validation(dv_metode)
            dv_metode.add("D2:D500")

            # 2. Dropdown Kolom F (Jenis Pakan)
            dv_pakan = DataValidation(
                type="list", 
                formula1='"Konsentrat Hijau, Silase, Jerami Fermentasi, Obat/Suplemen Khusus, TUM / Pakan Campur, Lain-lain"', 
                allow_blank=True
            )
            ws_input.add_data_validation(dv_pakan)
            dv_pakan.add("F2:F500")

        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        buffer = io.BytesIO()
        df_sample.to_csv(buffer, index=False)
        ext = "csv"
        mime = "text/csv"

    return buffer.getvalue(), ext, mime


def tampilkan_menu_pakan(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🍽️ Manajemen Pakan Harian Sapi")
    
    if "uploader_key_pakan" not in st.session_state:
        st.session_state["uploader_key_pakan"] = 0

    # Memastikan tipe data master sapi selalu terbaca float
    df_sapi["Total Pakan (kg)"] = pd.to_numeric(df_sapi["Total Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
    
    COLS_PAKAN = ["Tanggal", "Lokasi Pen", "Metode", "Target Spesifik", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"]
    
    tab1, tab2, tab3 = st.tabs(["➕ Input Pakan Baru", "⚙️ Edit / Hapus Riwayat Pakan", "📊 Rekapitulasi Realisasi Pakan"])
    
    # ==================== TAB 1: INPUT PAKAN BARU ====================
    with tab1:
        sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

        # ------------------- SUB-TAB 1: INPUT SATUAN -------------------
        with sub_satuan:
            st.markdown("### 📝 Form Catat Pemberian Pakan Harian Manual")
            
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
                opsi_pakan_default = ["Konsentrat Hijau", "Silase", "Jerami Fermentasi", "Obat/Suplemen Khusus", "TUM / Pakan Campur", "Lain-lain"]
                pakan_terpilih_dropdown = st.selectbox("4. Pilih Jenis / Nama Formula Pakan", opsi_pakan_default)
                
                if pakan_terpilih_dropdown == "Lain-lain":
                    jenis_pakan = st.text_input("📋 Masukkan Nama Formula Pakan Baru", placeholder="Contoh: Ampas Tahu").strip()
                else:
                    jenis_pakan = pakan_terpilih_dropdown
                
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
                            df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
                            if not df_pakan.empty:
                                df_pakan["Jumlah Pakan (kg)"] = pd.to_numeric(df_pakan["Jumlah Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
                            
                            if metode_pakan == "Serentak (Semua Sapi di Pen)":
                                list_rows_baru = []
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
                                
                                df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Total Pakan (kg)"] += float(pakan_per_ekor)
                                df_sapi.loc[df_sapi["Lokasi Pen"] == lokasi_pen_full, "Tgl Pakan Terakhir"] = str(tgl_pakan)
                                detail_sukses = f"Mendistribusikan Serentak {jenis_pakan} (@{pakan_per_ekor} kg/ekor) ke {lokasi_pen_full} (Dicatat individual untuk {jumlah_sapi} ekor)"
                            
                            else:
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

        # ------------------- SUB-TAB 2: UPLOAD BATCH EXCEL -------------------
        with sub_excel:
            st.markdown("### 📥 Import Distribusi Pakan Harian via File Excel")
            st.caption("Solusi cepat mencatat distribusi pakan masal ke banyak pen sekaligus dari catatan lapangan.")

            # Langkah 1: Unduh Template Excel dengan Dropdown
            st.markdown("#### 1. Unduh Template Resmi (Dilengkapi Dropdown Pilihan)")
            bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel_pakan(STRUKTUR_KANDANG)
            st.download_button(
                label=f"📥 Unduh Template Excel Distribusi Pakan (.{ext_tmpl.upper()})",
                data=bytes_tmpl,
                file_name=f"Template_Distribusi_Pakan_Harian.{ext_tmpl}",
                mime=mime_tmpl,
                type="secondary",
                help="Template ini sudah dilengkapi dropdown otomatis di kolom Metode Pemberian & Jenis Pakan."
            )

            st.markdown("---")
            # Langkah 2: Unggah File Excel
            st.markdown("#### 2. Unggah File Excel Catatan Petugas Pakan")
            uploaded_file = st.file_uploader(
                "Pilih file Excel (.xlsx / .xls / .csv) yang sudah diisi:", 
                type=["xlsx", "xls", "csv"],
                key=f"file_uploader_pakan_{st.session_state['uploader_key_pakan']}"
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file, sheet_name=0)

                    st.markdown("#### 3. Pratinjau & Validasi Data Otomatis")

                    rows_pakan_to_save = []
                    updates_sapi_dict = {}  # {(kode_sapi, rfid): additional_kg}
                    last_pakan_date_dict = {}  # pen_full or (kode, rfid) -> tgl
                    validation_errors = []

                    map_kode_to_rfid = {}
                    if not df_sapi.empty and "Kode Sapi" in df_sapi.columns and "RFID/Tag" in df_sapi.columns:
                        for _, sr in df_sapi.iterrows():
                            map_kode_to_rfid[str(sr["Kode Sapi"]).strip()] = str(sr["RFID/Tag"]).strip()

                    for idx, r in df_upload.iterrows():
                        no_baris = idx + 2

                        tgl_m = str(r.get("Tanggal (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()
                        if len(tgl_m) > 10: tgl_m = tgl_m[:10]

                        blok_k = str(r.get("Blok Kandang", "")).strip()
                        pen_k = str(r.get("Nomor Pen", "")).strip()
                        
                        if " - " in pen_k:
                            lokasi_f = pen_k
                        else:
                            lokasi_f = f"{blok_k} - {pen_k}"

                        metode = str(r.get("Metode Pemberian", "Serentak")).strip()
                        kode_target = str(r.get("Kode Sapi Target (Jika Spesifik)", "-")).strip()
                        jenis_pakan = str(r.get("Jenis Pakan", "Konsentrat Hijau")).strip()

                        try: kuantitas = float(r.get("Kuantitas Pakan (kg)", 0.0))
                        except: kuantitas = 0.0

                        err_msg = []
                        if blok_k not in STRUKTUR_KANDANG:
                            err_msg.append(f"Blok '{blok_k}' tidak terdaftar di master")
                        
                        sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == lokasi_f]
                        if sapi_di_pen.empty and "Blok" not in err_msg:
                            err_msg.append(f"Pen '{lokasi_f}' saat ini kosong / tidak ada sapi aktif")

                        if kuantitas <= 0:
                            err_msg.append("Kuantitas pakan harus > 0 kg")

                        if "Spesifik" in metode:
                            if not kode_target or kode_target in ["-", "nan", "None", ""]:
                                err_msg.append("Metode Spesifik wajib mengisi Kode Sapi Target")
                            elif kode_target not in map_kode_to_rfid:
                                err_msg.append(f"Kode Sapi Target '{kode_target}' tidak ditemukan di database master")

                        status_str = "✅ SIAP SIMPAN" if not err_msg else f"❌ ERROR: {', '.join(err_msg)}"
                        if err_msg:
                            validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")

                        # Jika valid, persiapkan baris record
                        if not err_msg:
                            if "Serentak" in metode:
                                for _, rs in sapi_di_pen.iterrows():
                                    target_str = f"{rs['Kode Sapi']} - {rs['RFID/Tag']}"
                                    rows_pakan_to_save.append({
                                        "Tanggal": tgl_m,
                                        "Lokasi Pen": lokasi_f,
                                        "Metode": "Serentak",
                                        "Target Spesifik": target_str,
                                        "Jenis Pakan": jenis_pakan,
                                        "Jumlah Pakan (kg)": kuantitas,
                                        "Operator": user_name,
                                        "Status Validasi": status_str
                                    })
                                    key_sapi = (str(rs['Kode Sapi']), str(rs['RFID/Tag']))
                                    updates_sapi_dict[key_sapi] = updates_sapi_dict.get(key_sapi, 0.0) + kuantitas
                                    last_pakan_date_dict[key_sapi] = tgl_m
                            else:
                                rfid_target = map_kode_to_rfid.get(kode_target, "-")
                                target_str = f"{kode_target} - {rfid_target}"
                                rows_pakan_to_save.append({
                                    "Tanggal": tgl_m,
                                    "Lokasi Pen": lokasi_f,
                                    "Metode": "Spesifik",
                                    "Target Spesifik": target_str,
                                    "Jenis Pakan": jenis_pakan,
                                    "Jumlah Pakan (kg)": kuantitas,
                                    "Operator": user_name,
                                    "Status Validasi": status_str
                                })
                                key_sapi = (kode_target, rfid_target)
                                updates_sapi_dict[key_sapi] = updates_sapi_dict.get(key_sapi, 0.0) + kuantitas
                                last_pakan_date_dict[key_sapi] = tgl_m
                        else:
                            rows_pakan_to_save.append({
                                "Tanggal": tgl_m,
                                "Lokasi Pen": lokasi_f,
                                "Metode": metode,
                                "Target Spesifik": kode_target,
                                "Jenis Pakan": jenis_pakan,
                                "Jumlah Pakan (kg)": kuantitas,
                                "Operator": user_name,
                                "Status Validasi": status_str
                            })

                    df_preview = pd.DataFrame(rows_pakan_to_save)
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
                        if st.button(f"🚀 Simpan {len(df_valid_only)} Log Pakan Valid ke Database", type="primary", use_container_width=True):
                            with st.spinner("💾 Mengunggah distribusi pakan harian ke database Supabase..."):
                                df_pakan_existing = read_sheet_to_df("pakan_harian", COLS_PAKAN)
                                df_baru_total = pd.concat([df_pakan_existing, df_valid_only], ignore_index=True)
                                write_df_to_sheet("pakan_harian", df_baru_total, COLS_PAKAN)

                                # Update akumulasi pakan pada master df_sapi
                                for (k_sapi, r_sapi), add_kg in updates_sapi_dict.items():
                                    mask_sp = (df_sapi["Kode Sapi"].astype(str) == k_sapi) & (df_sapi["RFID/Tag"].astype(str) == r_sapi)
                                    df_sapi.loc[mask_sp, "Total Pakan (kg)"] += float(add_kg)
                                    if (k_sapi, r_sapi) in last_pakan_date_dict:
                                        df_sapi.loc[mask_sp, "Tgl Pakan Terakhir"] = last_pakan_date_dict[(k_sapi, r_sapi)]

                                save_data(df_sapi)
                                add_activity_log(user_name, "Batch Input Pakan", f"Mengunggah {len(df_valid_only)} record pakan harian via Excel")
                            
                            st.session_state["uploader_key_pakan"] += 1
                            st.toast(f"🎉 Berhasil menyimpan {len(df_valid_only)} record pakan harian!", icon="🚀")
                            st.rerun()
                    else:
                        st.error("Tidak ada baris data yang valid untuk disimpan.")

                except Exception as e:
                    st.error(f"❌ Gagal membaca file Excel. Pastikan menggunakan template resmi! Detail Error: {e}")

    # ==================== TAB 2: EDIT / HAPUS RIWAYAT PAKAN ====================
    with tab2:
        st.markdown("### 📋 Koreksi & Pembersihan Salah Input Pakan")
        
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