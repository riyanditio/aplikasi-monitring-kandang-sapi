import streamlit as st
import pandas as pd
from datetime import datetime
import io
import importlib

# Fungsi Helper untuk Format Rupiah Indonesia (Pemisah Titik)
def format_rupiah(angka):
    try:
        return f"Rp {int(float(angka)):,}".replace(",", ".")
    except:
        return "Rp 0"

# Fungsi Helper untuk Konversi Nilai Numerik yang Aman dari Database/CSV
def safe_float(val, default=0.0):
    try:
        if pd.isna(val) or str(val).strip() in ["", "-", "None", "NaN"]:
            return default
        return float(val)
    except:
        return default

# ==================== FUNGSI GENERATOR TEMPLATE EXCEL PANEN ====================
def buat_template_excel_panen():
    """
    Membuat file Excel template Panen & Penjualan Sapi 2 Sheet:
    1. FORM_INPUT_PANEN_SAPI
    2. PANDUAN_PENGISIAN
    """
    buffer = io.BytesIO()

    sample_data = [
        {
            "Kode Sapi": "S5-001",
            "RFID / Tag Kandang": "-",  # Boleh diisi '-' agar Auto-Lookup RFID dari Master
            "Tanggal Panen (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Bobot Panen (kg)": 480.5,
            "Harga Jual /kg (Rp)": 52000,
            "Nama Pembeli / RPH": "RPH Cakung"
        },
        {
            "Kode Sapi": "S5-002",
            "RFID / Tag Kandang": "-",
            "Tanggal Panen (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Bobot Panen (kg)": 510.0,
            "Harga Jual /kg (Rp)": 52500,
            "Nama Pembeli / RPH": "PT Mitra Jaya"
        }
    ]
    df_sample = pd.DataFrame(sample_data)

    panduan_data = [
        {"KOLOM": "Kode Sapi", "ATURAN PENGISIAN": "WAJIB DIISI. Ketik Kode Sapi yang dipanen (contoh: S5-001). Harus sapi aktif di kandang."},
        {"KOLOM": "RFID / Tag Kandang", "ATURAN PENGISIAN": "OPSIONAL. Boleh diisi '-'. Sistem otomatis melacak RFID dari master sapi aktif."},
        {"KOLOM": "Tanggal Panen (YYYY-MM-DD)", "ATURAN PENGISIAN": "WAJIB DIISI. Format tanggal transaksi panen: YYYY-MM-DD (contoh: 2026-08-04)."},
        {"KOLOM": "Bobot Panen (kg)", "ATURAN PENGISIAN": "WAJIB DIISI. Hasil timbangan karkas/hidup sapi saat panen dalam kg (contoh: 480.5)."},
        {"KOLOM": "Harga Jual /kg (Rp)", "ATURAN PENGISIAN": "WAJIB DIISI. Harga kesepakatan per kg dalam Rupiah tanpa titik/koma (contoh: 52000)."},
        {"KOLOM": "Nama Pembeli / RPH", "ATURAN PENGISIAN": "WAJIB DIISI. Nama pembeli, pedagang, atau RPH tujuan (contoh: RPH Cakung)."}
    ]
    df_panduan = pd.DataFrame(panduan_data)

    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sample.to_excel(writer, sheet_name='FORM_INPUT_PANEN_SAPI', index=False)
            df_panduan.to_excel(writer, sheet_name='PANDUAN_PENGISIAN', index=False)

        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        buffer = io.BytesIO()
        df_sample.to_csv(buffer, index=False)
        ext = "csv"
        mime = "text/csv"

    return buffer.getvalue(), ext, mime


def tampilkan_menu_panen_penjualan(df_sapi, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("💰 Manajemen Panen & Penjualan Sapi")
    
    if "uploader_key_panen" not in st.session_state:
        st.session_state["uploader_key_panen"] = 0

    tab_form_panen, tab_riwayat = st.tabs(["🛒 Proses Panen Sapi", "📑 Riwayat Sapi Terjual/Panen"])
    
    # Definisi kolom tabel data panen
    cols_panen = [
        "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", 
        "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", 
        "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", 
        "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"
    ]
    
    df_panen = read_sheet_to_df("data_panen", cols_panen)
    
    # Filter hanya sapi dengan status AKTIF
    df_sapi_aktif = df_sapi[df_sapi["Status"] == "AKTIF"] if "Status" in df_sapi.columns else df_sapi

    # ==================== TAB 1: PROSES PANEN ====================
    with tab_form_panen:
        sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

        # ------------------- SUB-TAB 1: INPUT SATUAN -------------------
        with sub_satuan:
            if df_sapi_aktif.empty: 
                st.info("Tidak ada sapi aktif di kandang.")
            else:
                st.write("### 📝 Form Pencatatan Keluar / Panen Manual")
                pilihan_sapi = df_sapi_aktif["RFID/Tag"].astype(str).tolist()
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
* **Kode Batch:** {data_sapi.get('Kode Batch', '-')}
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
                                
                                # Pembaruan status menjadi PANEN (tanpa menghapus record)
                                df_sapi.loc[idx, "Status"] = "PANEN"
                                save_data(df_sapi)
                                
                                add_activity_log(user_name, "Panen Sapi", f"Memanen Sapi Kode {data_sapi.get('Kode Sapi', '-')} [Batch: {data_sapi.get('Kode Batch', '-')}] | Pendapatan: {format_rupiah(total_pendapatan)}")
                                
                            st.success(f"🎉 Sukses! Sapi RFID {selected_tag} Berhasil Dipanen.")
                            st.rerun()

        # ------------------- SUB-TAB 2: UPLOAD BATCH EXCEL -------------------
        with sub_excel:
            st.markdown("### 📥 Import Transaksi Panen via File Excel")
            st.caption("Solusi cepat untuk memproses transaksi penjualan masal puluhan ekor sapi sekaligus.")

            # Langkah 1: Unduh Template Excel
            st.markdown("#### 1. Unduh Template Resmi")
            bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel_panen()
            st.download_button(
                label=f"📥 Unduh Template Excel Panen Sapi (.{ext_tmpl.upper()})",
                data=bytes_tmpl,
                file_name=f"Template_Panen_Penjualan_Sapi.{ext_tmpl}",
                mime=mime_tmpl,
                type="secondary",
                help="File ini berisi format kolom standar beserta Sheet Panduan Pengisian."
            )

            st.markdown("---")
            # Langkah 2: Unggah File Excel
            st.markdown("#### 2. Unggah File Excel Transaksi Penjualan")
            uploaded_file = st.file_uploader(
                "Pilih file Excel (.xlsx / .xls / .csv) yang sudah diisi:", 
                type=["xlsx", "xls", "csv"],
                key=f"file_uploader_panen_{st.session_state['uploader_key_panen']}"
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file, sheet_name=0)

                    st.markdown("#### 3. Pratinjau & Validasi Data Otomatis")

                    rows_panen_to_save = []
                    kodes_to_panen = []
                    validation_errors = []

                    # Pemeta data sapi aktif
                    map_sapi_aktif = {}
                    if not df_sapi_aktif.empty:
                        for idx_s, sr in df_sapi_aktif.iterrows():
                            k_sapi = str(sr.get("Kode Sapi", "")).strip()
                            if k_sapi and k_sapi not in ["nan", "None", "-"]:
                                map_sapi_aktif[k_sapi] = (idx_s, sr)

                    for idx, r in df_upload.iterrows():
                        no_baris = idx + 2

                        kode_s = str(r.get("Kode Sapi", "")).strip()
                        tgl_p = str(r.get("Tanggal Panen (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()
                        if len(tgl_p) > 10: tgl_p = tgl_p[:10]

                        try: bobot_p = float(r.get("Bobot Panen (kg)", 0.0))
                        except: bobot_p = 0.0

                        try: harga_p = float(r.get("Harga Jual /kg (Rp)", 0.0))
                        except: harga_p = 0.0

                        pembeli = str(r.get("Nama Pembeli / RPH", "Umum")).strip()

                        err_msg = []
                        if not kode_s or kode_s in ["nan", "None", ""]:
                            err_msg.append("Kode Sapi kosong")
                        elif kode_s not in map_sapi_aktif:
                            err_msg.append(f"Kode Sapi '{kode_s}' tidak ditemukan di populasi sapi aktif")

                        if bobot_p <= 0:
                            err_msg.append("Bobot panen harus > 0 kg")
                        if harga_p <= 0:
                            err_msg.append("Harga jual harus > Rp 0")

                        if not err_msg:
                            idx_sapi_orig, sr_sapi = map_sapi_aktif[kode_s]
                            rfid_tag = str(sr_sapi.get("RFID/Tag", "-"))
                            jenis_s = str(sr_sapi.get("Jenis Sapi", "-"))
                            jk_s = str(sr_sapi.get("Jenis Kelamin", "Jantan"))
                            asal_s = str(sr_sapi.get("Asal Negara", "Lokal"))
                            tgl_m = str(sr_sapi.get("Tgl Masuk", tgl_p))

                            try:
                                hari_pelihara = (datetime.strptime(tgl_p, "%Y-%m-%d").date() - datetime.strptime(tgl_m, "%Y-%m-%d").date()).days
                            except:
                                hari_pelihara = 1
                            if hari_pelihara <= 0: hari_pelihara = 1

                            bobot_awal_safe = safe_float(sr_sapi.get("Bobot Awal (kg)", 300.0))
                            total_gain = float(bobot_p - bobot_awal_safe)
                            adg_final = round(total_gain / hari_pelihara, 2)

                            total_pakan_safe = safe_float(sr_sapi.get("Total Pakan (kg)", 0.0))
                            fcr_final = round(total_pakan_safe / total_gain, 2) if total_gain > 0 else 0.0
                            total_pendapatan = int(bobot_p * harga_p)

                            rows_panen_to_save.append({
                                "Kode Sapi": kode_s,
                                "RFID/Tag": rfid_tag,
                                "Jenis Sapi": jenis_s,
                                "Jenis Kelamin": jk_s,
                                "Asal Negara": asal_s,
                                "Tgl Masuk": tgl_m,
                                "Tgl Panen": tgl_p,
                                "Lama Pelihara (Hari)": int(hari_pelihara),
                                "Bobot Awal (kg)": bobot_awal_safe,
                                "Bobot Panen (kg)": bobot_p,
                                "Total Gain (kg)": total_gain,
                                "Total Pakan (kg)": total_pakan_safe,
                                "FCR Akhir": fcr_final,
                                "ADG Akhir (kg/hari)": adg_final,
                                "Harga Jual /kg (Rp)": harga_p,
                                "Total Pendapatan (Rp)": total_pendapatan,
                                "Pembeli/Tujuan": pembeli if pembeli not in ["nan", "None", ""] else "Umum",
                                "Status Validasi": "✅ SIAP SIMPAN"
                            })
                            kodes_to_panen.append(kode_s)
                        else:
                            validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")
                            rows_panen_to_save.append({
                                "Kode Sapi": kode_s if kode_s not in ["nan", "None", ""] else "-",
                                "RFID/Tag": "-",
                                "Jenis Sapi": "-",
                                "Jenis Kelamin": "-",
                                "Asal Negara": "-",
                                "Tgl Masuk": "-",
                                "Tgl Panen": tgl_p,
                                "Lama Pelihara (Hari)": 0,
                                "Bobot Awal (kg)": 0.0,
                                "Bobot Panen (kg)": bobot_p,
                                "Total Gain (kg)": 0.0,
                                "Total Pakan (kg)": 0.0,
                                "FCR Akhir": 0.0,
                                "ADG Akhir (kg/hari)": 0.0,
                                "Harga Jual /kg (Rp)": harga_p,
                                "Total Pendapatan (Rp)": int(bobot_p * harga_p),
                                "Pembeli/Tujuan": pembeli,
                                "Status Validasi": f"❌ ERROR: {', '.join(err_msg)}"
                            })

                    df_preview = pd.DataFrame(rows_panen_to_save)
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
                        total_omset = df_valid_only["Total Pendapatan (Rp)"].sum()
                        if st.button(f"🚀 Sah-kan Panen {len(df_valid_only)} Sapi Valid ({format_rupiah(total_omset)})", type="primary", use_container_width=True):
                            with st.spinner("💾 Mengunggah data panen & mengupdate status populasi sapi..."):
                                # 1. Simpan ke riwayat data_panen
                                df_panen_existing = read_sheet_to_df("data_panen", cols_panen)
                                df_panen_total = pd.concat([df_panen_existing, df_valid_only], ignore_index=True)
                                write_df_to_sheet("data_panen", df_panen_total, cols_panen)

                                # 2. Ubah status sapi terpilih menjadi 'PANEN' di df_sapi
                                mask_panen = df_sapi["Kode Sapi"].astype(str).isin(kodes_to_panen)
                                df_sapi.loc[mask_panen, "Status"] = "PANEN"
                                save_data(df_sapi)

                                add_activity_log(user_name, "Batch Panen Sapi", f"Memanen {len(df_valid_only)} ekor sapi via Excel | Total Omset: {format_rupiah(total_omset)}")

                            st.session_state["uploader_key_panen"] += 1
                            st.toast(f"🎉 Berhasil memanen {len(df_valid_only)} ekor sapi! Omset: {format_rupiah(total_omset)}", icon="🚀")
                            st.balloons()
                            st.rerun()
                    else:
                        st.error("Tidak ada baris data panen yang valid untuk disimpan.")

                except Exception as e:
                    st.error(f"❌ Gagal membaca file Excel. Pastikan menggunakan template resmi! Detail Error: {e}")

    # ==================== TAB 2: RIWAYAT PANEN ====================
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