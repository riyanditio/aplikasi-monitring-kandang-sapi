import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import importlib

# ==================== FUNGSI HELPER KELOMPOK PAKAN ====================
def kelompokkan_jenis_pakan(nama_pakan):
    """
    Mengkategorikan nama pakan dari database ke 5 kelompok utama
    sesuai draft format rekapitulasi pakan.
    """
    nama = str(nama_pakan).lower().strip()
    if "konsentrat" in nama:
        return "Konsentrat (kg)"
    elif "hijauan" in nama or "rumput" in nama or "odot" in nama:
        return "Hijauan (kg)"
    elif "jerami" in nama:
        return "Jerami (kg)"
    elif "silase" in nama:
        return "Silase (kg)"
    else:
        return "Lainnya / Suplemen (kg)"

# ==================== GENERATOR EXCEL REKAPITULASI DRAFT ====================
def buat_excel_rekapitulasi_pakan(df_rekap_pivoted, summary_data):
    """
    Membuat file Excel Rekapitulasi Pakan dengan Header Bertingkat (Merged)
    persis seperti 'Draff tampilan rekapitulasi pakan di web monitoring.xlsx'.
    """
    buffer = io.BytesIO()
    try:
        openpyxl = importlib.import_module("openpyxl")
        Font = openpyxl.styles.Font
        Alignment = openpyxl.styles.Alignment
        PatternFill = openpyxl.styles.PatternFill
        Border = openpyxl.styles.Border
        Side = openpyxl.styles.Side

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"

        # Styling Warna & Font
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        sub_header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
        header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        data_font = Font(name="Calibri", size=10)
        total_font = Font(name="Calibri", size=10, bold=True)

        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        # Header Row 1
        ws.cell(row=1, column=1, value="No")
        ws.cell(row=1, column=2, value="Tanggal")
        ws.cell(row=1, column=3, value="Lokasi kandang / Pan")
        ws.cell(row=1, column=4, value="Metode Pakan")
        ws.cell(row=1, column=5, value="Jenis Pakan (Kuantiti Pemberian Pakan Kg)")
        ws.cell(row=1, column=10, value="Total Pakan (Kg)")
        ws.cell(row=1, column=11, value="Jumlah Sapi")
        ws.cell(row=1, column=12, value="Konsumsi per ekor (Kg)")

        # Merging Cells
        ws.merge_cells("A1:A2")
        ws.merge_cells("B1:B2")
        ws.merge_cells("C1:C2")
        ws.merge_cells("D1:D2")
        ws.merge_cells("E1:I1")
        ws.merge_cells("J1:J2")
        ws.merge_cells("K1:K2")
        ws.merge_cells("L1:L2")

        # Header Row 2 (Sub-Kolom Pakan)
        ws.cell(row=2, column=5, value="Konsentrat (Kg)")
        ws.cell(row=2, column=6, value="Hijauan (Kg)")
        ws.cell(row=2, column=7, value="Jerami (Kg)")
        ws.cell(row=2, column=8, value="Silase (Kg)")
        ws.cell(row=2, column=9, value="Lainnya / Suplemen (Kg)")

        for r in [1, 2]:
            for c in range(1, 13):
                cell = ws.cell(row=r, column=c)
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.fill = header_fill if r == 1 else sub_header_fill
                cell.border = thin_border

        curr_row = 3
        for idx, r in df_rekap_pivoted.iterrows():
            ws.cell(row=curr_row, column=1, value=idx + 1).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=str(r["Tanggal"])).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=3, value=str(r["Lokasi Kandang / Pen"])).alignment = Alignment(horizontal="left")
            ws.cell(row=curr_row, column=4, value=str(r["Metode Pakan"])).alignment = Alignment(horizontal="center")

            ws.cell(row=curr_row, column=5, value=float(r["Konsentrat (kg)"])).number_format = '#,##0.00'
            ws.cell(row=curr_row, column=6, value=float(r["Hijauan (kg)"])).number_format = '#,##0.00'
            ws.cell(row=curr_row, column=7, value=float(r["Jerami (kg)"])).number_format = '#,##0.00'
            ws.cell(row=curr_row, column=8, value=float(r["Silase (kg)"])).number_format = '#,##0.00'
            ws.cell(row=curr_row, column=9, value=float(r["Lainnya / Suplemen (kg)"])).number_format = '#,##0.00'

            ws.cell(row=curr_row, column=10, value=float(r["Total Pakan (kg)"])).number_format = '#,##0.00'
            ws.cell(row=curr_row, column=11, value=int(r["Jumlah Sapi"])).number_format = '#,##0'
            ws.cell(row=curr_row, column=12, value=float(r["Konsumsi per Ekor (kg)"])).number_format = '#,##0.00'

            for c in range(1, 13):
                cell = ws.cell(row=curr_row, column=c)
                cell.font = data_font
                cell.border = thin_border
            curr_row += 1

        # Row TOTAL
        ws.cell(row=curr_row, column=1, value="TOTAL").alignment = Alignment(horizontal="center")
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)

        ws.cell(row=curr_row, column=5, value=float(summary_data["tot_konsentrat"])).number_format = '#,##0.00'
        ws.cell(row=curr_row, column=6, value=float(summary_data["tot_hijauan"])).number_format = '#,##0.00'
        ws.cell(row=curr_row, column=7, value=float(summary_data["tot_jerami"])).number_format = '#,##0.00'
        ws.cell(row=curr_row, column=8, value=float(summary_data["tot_silase"])).number_format = '#,##0.00'
        ws.cell(row=curr_row, column=9, value=float(summary_data["tot_lainnya"])).number_format = '#,##0.00'

        ws.cell(row=curr_row, column=10, value=float(summary_data["tot_semua"])).number_format = '#,##0.00'
        ws.cell(row=curr_row, column=11, value=int(summary_data["tot_sapi"])).number_format = '#,##0'
        ws.cell(row=curr_row, column=12, value=float(summary_data["rerata_per_ekor"])).number_format = '#,##0.00'

        total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        for c in range(1, 13):
            cell = ws.cell(row=curr_row, column=c)
            cell.font = total_font
            cell.fill = total_fill
            cell.border = thin_border

        wb.save(buffer)
        return buffer.getvalue(), "xlsx"
    except Exception:
        df_rekap_pivoted.to_csv(buffer, index=False)
        return buffer.getvalue(), "csv"


# ==================== FUNGSI GENERATOR TEMPLATE UPLOAD PAKAN ====================
def buat_template_excel_pakan(STRUKTUR_KANDANG):
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

            dv_metode = DataValidation(type="list", formula1='"Serentak, Spesifik"', allow_blank=True)
            ws_input.add_data_validation(dv_metode)
            dv_metode.add("D2:D500")

            dv_pakan = DataValidation(type="list", formula1='"Konsentrat Hijau, Silase, Jerami Fermentasi, Obat/Suplemen Khusus, TUM / Pakan Campur, Lain-lain"', allow_blank=True)
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

    df_sapi["Total Pakan (kg)"] = pd.to_numeric(df_sapi["Total Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
    COLS_PAKAN = ["Tanggal", "Lokasi Pen", "Metode", "Target Spesifik", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"]
    
    tab1, tab2, tab3 = st.tabs(["➕ Input Pakan Baru", "⚙️ Edit / Hapus Riwayat Pakan", "📊 Rekapitulasi Realisasi Pakan"])
    
    # ==================== TAB 1: INPUT PAKAN BARU ====================
    with tab1:
        sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

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
                        label="秤 Total Kuantitas Pakan yang Akan Diturunkan (Otomatis)", 
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

        with sub_excel:
            st.markdown("### 📥 Import Distribusi Pakan Harian via File Excel")
            bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel_pakan(STRUKTUR_KANDANG)
            st.download_button(
                label=f"📥 Unduh Template Excel Distribusi Pakan (.{ext_tmpl.upper()})",
                data=bytes_tmpl,
                file_name=f"Template_Distribusi_Pakan_Harian.{ext_tmpl}",
                mime=mime_tmpl,
                type="secondary"
            )

            st.markdown("---")
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

                    st.markdown("#### Pratinjau Data Upload")
                    rows_pakan_to_save = []
                    updates_sapi_dict = {}
                    last_pakan_date_dict = {}
                    validation_errors = []

                    map_kode_to_rfid = {}
                    if not df_sapi.empty and "Kode Sapi" in df_sapi.columns and "RFID/Tag" in df_sapi.columns:
                        for _, sr in df_sapi.iterrows():
                            map_kode_to_rfid[str(sr["Kode Sapi"]).strip()] = str(sr["RFID/Tag"]).strip()

                    for idx, r in df_upload.iterrows():
                        no_baris = idx + 2
                        tgl_m = str(r.get("Tanggal (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()[:10]
                        blok_k = str(r.get("Blok Kandang", "")).strip()
                        pen_k = str(r.get("Nomor Pen", "")).strip()
                        lokasi_f = pen_k if " - " in pen_k else f"{blok_k} - {pen_k}"
                        metode = str(r.get("Metode Pemberian", "Serentak")).strip()
                        kode_target = str(r.get("Kode Sapi Target (Jika Spesifik)", "-")).strip()
                        jenis_pakan = str(r.get("Jenis Pakan", "Konsentrat Hijau")).strip()

                        try: kuantitas = float(r.get("Kuantitas Pakan (kg)", 0.0))
                        except: kuantitas = 0.0

                        err_msg = []
                        if blok_k not in STRUKTUR_KANDANG: err_msg.append(f"Blok '{blok_k}' tidak terdaftar")
                        sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == lokasi_f]
                        if sapi_di_pen.empty and "Blok" not in err_msg: err_msg.append(f"Pen '{lokasi_f}' kosong")
                        if kuantitas <= 0: err_msg.append("Kuantitas pakan harus > 0 kg")

                        status_str = "✅ SIAP SIMPAN" if not err_msg else f"❌ ERROR: {', '.join(err_msg)}"
                        if err_msg: validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")

                        if not err_msg:
                            if "Serentak" in metode:
                                for _, rs in sapi_di_pen.iterrows():
                                    target_str = f"{rs['Kode Sapi']} - {rs['RFID/Tag']}"
                                    rows_pakan_to_save.append({
                                        "Tanggal": tgl_m, "Lokasi Pen": lokasi_f, "Metode": "Serentak",
                                        "Target Spesifik": target_str, "Jenis Pakan": jenis_pakan,
                                        "Jumlah Pakan (kg)": kuantitas, "Operator": user_name, "Status Validasi": status_str
                                    })
                                    key_sapi = (str(rs['Kode Sapi']), str(rs['RFID/Tag']))
                                    updates_sapi_dict[key_sapi] = updates_sapi_dict.get(key_sapi, 0.0) + kuantitas
                                    last_pakan_date_dict[key_sapi] = tgl_m
                            else:
                                rfid_target = map_kode_to_rfid.get(kode_target, "-")
                                target_str = f"{kode_target} - {rfid_target}"
                                rows_pakan_to_save.append({
                                    "Tanggal": tgl_m, "Lokasi Pen": lokasi_f, "Metode": "Spesifik",
                                    "Target Spesifik": target_str, "Jenis Pakan": jenis_pakan,
                                    "Jumlah Pakan (kg)": kuantitas, "Operator": user_name, "Status Validasi": status_str
                                })
                                key_sapi = (kode_target, rfid_target)
                                updates_sapi_dict[key_sapi] = updates_sapi_dict.get(key_sapi, 0.0) + kuantitas
                                last_pakan_date_dict[key_sapi] = tgl_m

                    df_preview = pd.DataFrame(rows_pakan_to_save)
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)

                    df_valid_only = df_preview[df_preview["Status Validasi"] == "✅ SIAP SIMPAN"].drop(columns=["Status Validasi"])
                    if not df_valid_only.empty:
                        if st.button(f"🚀 Simpan {len(df_valid_only)} Log Pakan Valid", type="primary", use_container_width=True):
                            with st.spinner("💾 Mengunggah ke database..."):
                                df_pakan_existing = read_sheet_to_df("pakan_harian", COLS_PAKAN)
                                df_baru_total = pd.concat([df_pakan_existing, df_valid_only], ignore_index=True)
                                write_df_to_sheet("pakan_harian", df_baru_total, COLS_PAKAN)

                                for (k_sapi, r_sapi), add_kg in updates_sapi_dict.items():
                                    mask_sp = (df_sapi["Kode Sapi"].astype(str) == k_sapi) & (df_sapi["RFID/Tag"].astype(str) == r_sapi)
                                    df_sapi.loc[mask_sp, "Total Pakan (kg)"] += float(add_kg)
                                    if (k_sapi, r_sapi) in last_pakan_date_dict:
                                        df_sapi.loc[mask_sp, "Tgl Pakan Terakhir"] = last_pakan_date_dict[(k_sapi, r_sapi)]

                                save_data(df_sapi)
                                add_activity_log(user_name, "Batch Input Pakan", f"Mengunggah {len(df_valid_only)} record pakan")
                            
                            st.session_state["uploader_key_pakan"] += 1
                            st.toast("🎉 Berhasil menyimpan pakan!", icon="🚀")
                            st.rerun()
                except Exception as e:
                    st.error(f"❌ Error upload file: {e}")

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
            pilihan_no = st.number_input("Masukkan 'No Urut' data pakan yang salah input", min_value=1, max_value=len(df_pakan), step=1)
            idx_pilihan = pilihan_no - 1
            row_lama = df_pakan.iloc[idx_pilihan]
            
            metode_lama = row_lama.get("Metode", "Serentak")
            target_lama = row_lama.get("Target Spesifik", "-")
            
            st.info(f"📍 **Data Terpilih:** Pen {row_lama['Lokasi Pen']} | Target: **{target_lama}** | {row_lama['Jenis Pakan']} | {row_lama['Jumlah Pakan (kg)']} kg")

            col_form, col_auth = st.columns(2)
            with col_form:
                jenis_baru = st.text_input("Koreksi Jenis Pakan", value=str(row_lama["Jenis Pakan"])).strip()
                jumlah_baru = st.number_input("Koreksi Jumlah Pakan (kg)", min_value=0.0, value=float(row_lama["Jumlah Pakan (kg)"]), step=1.0, format="%.2f")
            with col_auth:
                pwd_input = st.text_input("Masukkan Password Otorisasi Admin", type="password", key="auth_pakan_pass")
            
            try: correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except: correct_admin_pwd = "admin123"

            btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 2])
            if btn_col1.button("✏️ Simpan Perubahan Data", type="primary", use_container_width=True):
                if pwd_input != correct_admin_pwd: st.error("❌ Password Admin salah.")
                elif not jenis_baru or jumlah_baru <= 0: st.error("❌ Nama & berat pakan harus valid.")
                else:
                    with st.spinner("🔄 Memproses kalkulasi ulang..."):
                        if target_lama != "-" and " - " in str(target_lama):
                            target_kode = str(target_lama).split(" - ")[0]
                            target_rfid = str(target_lama).split(" - ")[1]
                            mask_tarik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_tarik, "Total Pakan (kg)"] -= float(row_lama["Jumlah Pakan (kg)"])
                        else:
                            sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_lama) > 0:
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= (float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama))
                        
                        df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)

                        if target_lama != "-" and " - " in str(target_lama):
                            target_kode = str(target_lama).split(" - ")[0]
                            target_rfid = str(target_lama).split(" - ")[1]
                            mask_tambah = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_tambah, "Total Pakan (kg)"] += float(jumlah_baru)
                        else:
                            sapi_pen_baru = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_baru) > 0:
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] += (float(jumlah_baru) / len(sapi_pen_baru))

                        save_data(df_sapi)
                        df_pakan.at[idx_pilihan, "Jenis Pakan"] = jenis_baru
                        df_pakan.at[idx_pilihan, "Jumlah Pakan (kg)"] = float(jumlah_baru)
                        df_pakan.at[idx_pilihan, "Operator"] = f"{user_name} (Edited)"
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)
                        add_activity_log(user_name, "Koreksi Pakan", f"Mengubah log pakan No {pilihan_no}")
                    st.success("✅ Perubahan berhasil disimpan!")
                    st.rerun()

            if btn_col2.button("🗑️ Hapus Data Permanen", type="secondary", use_container_width=True):
                if pwd_input != correct_admin_pwd: st.error("❌ Password Admin salah.")
                else:
                    with st.spinner("🔄 Menghapus record pakan..."):
                        if target_lama != "-" and " - " in str(target_lama):
                            target_kode = str(target_lama).split(" - ")[0]
                            target_rfid = str(target_lama).split(" - ")[1]
                            mask_tarik = (df_sapi["Kode Sapi"] == target_kode) & (df_sapi["RFID/Tag"] == target_rfid)
                            df_sapi.loc[mask_tarik, "Total Pakan (kg)"] -= float(row_lama["Jumlah Pakan (kg)"])
                        else:
                            sapi_pen_lama = df_sapi[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"]]
                            if len(sapi_pen_lama) > 0:
                                df_sapi.loc[df_sapi["Lokasi Pen"] == row_lama["Lokasi Pen"], "Total Pakan (kg)"] -= (float(row_lama["Jumlah Pakan (kg)"]) / len(sapi_pen_lama))

                        df_sapi["Total Pakan (kg)"] = df_sapi["Total Pakan (kg)"].clip(lower=0.0)
                        save_data(df_sapi)

                        df_pakan = df_pakan.drop(df_pakan.index[idx_pilihan]).reset_index(drop=True)
                        write_df_to_sheet("pakan_harian", df_pakan, COLS_PAKAN)
                        add_activity_log(user_name, "Hapus Pakan", f"Menghapus log pakan No {pilihan_no}")
                    st.success("🗑️ Record berhasil dihapus!")
                    st.rerun()

    # ==================== TAB 3: REKAPITULASI REALISASI PAKAN (FORMAT DRAFT) ====================
    with tab3:
        st.markdown("### 📊 Laporan Progres Realisasi Pemberian Pakan")
        
        df_pakan = read_sheet_to_df("pakan_harian", COLS_PAKAN)
        if not df_pakan.empty:
            df_pakan["Jumlah Pakan (kg)"] = pd.to_numeric(df_pakan["Jumlah Pakan (kg)"], errors='coerce').fillna(0.0).astype(float)
        
        if df_pakan.empty:
            st.info("Belum ada data riwayat pakan yang tercatat di database.")
        else:
            # --- PANEL FILTER ---
            f_col1, f_col2 = st.columns([1.5, 2])
            with f_col1:
                opsi_blok = ["Semua Blok Kandang"] + list(STRUKTUR_KANDANG.keys())
                blok_pilihan_filter = st.selectbox("🔍 Filter Blok Kandang:", opsi_blok)
            with f_col2:
                filter_periode = st.radio(
                    "📅 Filter Periode Tanggal:",
                    ["Semua Tanggal", "Hari Ini", "7 Hari Terakhir", "Bulan Ini"],
                    horizontal=True
                )

            # Terapkan Filter Tanggal
            df_f = df_pakan.copy()
            df_f["Tanggal_dt"] = pd.to_datetime(df_f["Tanggal"], errors='coerce')
            today = datetime.now().date()

            if filter_periode == "Hari Ini":
                df_f = df_f[df_f["Tanggal_dt"].dt.date == today]
            elif filter_periode == "7 Hari Terakhir":
                seven_days_ago = today - timedelta(days=7)
                df_f = df_f[df_f["Tanggal_dt"].dt.date >= seven_days_ago]
            elif filter_periode == "Bulan Ini":
                df_f = df_f[(df_f["Tanggal_dt"].dt.month == today.month) & (df_f["Tanggal_dt"].dt.year == today.year)]

            # Terapkan Filter Blok Kandang
            if blok_pilihan_filter != "Semua Blok Kandang":
                df_f = df_f[df_f["Lokasi Pen"].astype(str).str.startswith(f"{blok_pilihan_filter} -")]

            if df_f.empty:
                st.warning(" Tidak ada data transaksi pakan pada filter periode / blok kandang terpilih.")
            else:
                # 1. Kelompokkan Jenis Pakan ke 5 Kategori Standar
                df_f["Kategori Pakan"] = df_f["Jenis Pakan"].apply(kelompokkan_jenis_pakan)

                # 2. Hitung Jumlah Populasi Sapi per Pen
                pen_counts = df_sapi["Lokasi Pen"].value_counts().to_dict()

                # 3. Pivot Matriks Pakan per Pen per Tanggal per Metode
                pivot_df = df_f.pivot_table(
                    index=["Tanggal", "Lokasi Pen", "Metode"],
                    columns="Kategori Pakan",
                    values="Jumlah Pakan (kg)",
                    aggfunc="sum",
                    fill_value=0.0
                ).reset_index()

                # Pastikan seluruh 5 kolom kategori pakan selalu ada
                kategori_cols = ["Konsentrat (kg)", "Hijauan (kg)", "Jerami (kg)", "Silase (kg)", "Lainnya / Suplemen (kg)"]
                for col in kategori_cols:
                    if col not in pivot_df.columns:
                        pivot_df[col] = 0.0

                pivot_df["Total Pakan (kg)"] = pivot_df[kategori_cols].sum(axis=1)
                
                def get_populasi_pen(row_pen):
                    jml = pen_counts.get(row_pen, 0)
                    return jml if jml > 0 else 1

                pivot_df["Jumlah Sapi"] = pivot_df["Lokasi Pen"].map(get_populasi_pen)
                pivot_df["Konsumsi per Ekor (kg)"] = (pivot_df["Total Pakan (kg)"] / pivot_df["Jumlah Sapi"]).round(2)

                pivot_df = pivot_df.rename(columns={
                    "Lokasi Pen": "Lokasi Kandang / Pen",
                    "Metode": "Metode Pakan"
                })

                cols_final = ["Tanggal", "Lokasi Kandang / Pen", "Metode Pakan"] + kategori_cols + ["Total Pakan (kg)", "Jumlah Sapi", "Konsumsi per Ekor (kg)"]
                pivot_df = pivot_df[cols_final].sort_values(by=["Tanggal", "Lokasi Kandang / Pen"], ascending=[False, True]).reset_index(drop=True)

                # --- HITUNG AKUMULASI RINGKASAN ---
                tot_konsentrat = pivot_df["Konsentrat (kg)"].sum()
                tot_hijauan = pivot_df["Hijauan (kg)"].sum()
                tot_jerami = pivot_df["Jerami (kg)"].sum()
                tot_silase = pivot_df["Silase (kg)"].sum()
                tot_lainnya = pivot_df["Lainnya / Suplemen (kg)"].sum()
                tot_semua = pivot_df["Total Pakan (kg)"].sum()
                tot_sapi = pivot_df["Jumlah Sapi"].sum()
                rerata_per_ekor = round(tot_semua / tot_sapi, 2) if tot_sapi > 0 else 0.0

                st.markdown("---")
                st.markdown("#### 📊 Akumulasi Total Pemberian Pakan (Periode Terpilih)")
                
                m_c1, m_c2, m_c3, m_c4, m_c5, m_c6 = st.columns(6)
                m_c1.metric("🌾 Konsentrat", f"{tot_konsentrat:.1f} kg")
                m_c2.metric("🌿 Hijauan", f"{tot_hijauan:.1f} kg")
                m_c3.metric("🌾 Jerami", f"{tot_jerami:.1f} kg")
                m_c4.metric("🌽 Silase", f"{tot_silase:.1f} kg")
                m_c5.metric("🧪 Suplemen/Lain", f"{tot_lainnya:.1f} kg")
                m_c6.metric("⚖️ TOTAL PAKAN", f"{tot_semua:.1f} kg", delta=f"Rerata {rerata_per_ekor} kg/ekor")

                st.markdown("---")
                col_title, col_dl = st.columns([3, 1.2])
                with col_title:
                    st.markdown("#### 📑 Tabel Matriks Realisasi Pakan Harian")
                with col_dl:
                    summary_dict = {
                        "tot_konsentrat": tot_konsentrat, "tot_hijauan": tot_hijauan,
                        "tot_jerami": tot_jerami, "tot_silase": tot_silase,
                        "tot_lainnya": tot_lainnya, "tot_semua": tot_semua,
                        "tot_sapi": tot_sapi, "rerata_per_ekor": rerata_per_ekor
                    }
                    bytes_excel_rekap, ext_rekap = buat_excel_rekapitulasi_pakan(pivot_df, summary_dict)
                    st.download_button(
                        label=f"📥 Download Excel Realisasi (.XLSX)",
                        data=bytes_excel_rekap,
                        file_name=f"Realisasi_Pemberian_Pakan_{datetime.now().strftime('%Y%m%d')}.{ext_rekap}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )

                # BUAT TABEL DENGAN BARIS TOTAL
                df_tampil_web = pivot_df.copy()
                df_tampil_web.insert(0, "No", range(1, len(df_tampil_web) + 1))

                row_total_web = {
                    "No": "TOTAL",
                    "Tanggal": "-",
                    "Lokasi Kandang / Pen": "AKUMULASI TOTAL",
                    "Metode Pakan": "-",
                    "Konsentrat (kg)": tot_konsentrat,
                    "Hijauan (kg)": tot_hijauan,
                    "Jerami (kg)": tot_jerami,
                    "Silase (kg)": tot_silase,
                    "Lainnya / Suplemen (kg)": tot_lainnya,
                    "Total Pakan (kg)": tot_semua,
                    "Jumlah Sapi": tot_sapi,
                    "Konsumsi per Ekor (kg)": rerata_per_ekor
                }
                df_tampil_web = pd.concat([df_tampil_web, pd.DataFrame([row_total_web])], ignore_index=True)

                st.dataframe(
                    df_tampil_web,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Konsentrat (kg)": st.column_config.NumberColumn(format="%.2f"),
                        "Hijauan (kg)": st.column_config.NumberColumn(format="%.2f"),
                        "Jerami (kg)": st.column_config.NumberColumn(format="%.2f"),
                        "Silase (kg)": st.column_config.NumberColumn(format="%.2f"),
                        "Lainnya / Suplemen (kg)": st.column_config.NumberColumn(format="%.2f"),
                        "Total Pakan (kg)": st.column_config.NumberColumn(format="%.2f"),
                        "Jumlah Sapi": st.column_config.NumberColumn(format="%d Ekor"),
                        "Konsumsi per Ekor (kg)": st.column_config.NumberColumn(format="%.2f kg")
                    }
                )