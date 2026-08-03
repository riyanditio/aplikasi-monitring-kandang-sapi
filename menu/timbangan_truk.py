import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ==================== FUNGSI GENERATOR TEMPLATE EXCEL TRUK ====================
def buat_template_excel_truk():
    """
    Membuat file Excel template Timbangan Truk 2 Sheet:
    1. FORM_INPUT_TIMBANGAN_TRUK
    2. PANDUAN_PENGISIAN
    """
    buffer = io.BytesIO()
    
    # Data Contoh untuk Sheet Input
    sample_data = [
        {
            "No Transaksi": "-",  # Isikan '-' atau kosongkan agar Auto-Generate Kode
            "Tanggal (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Nama Lokasi Penimbangan": "Jembatan Timbang Utama (Kandang)",
            "No Plat / Armada": "B 9123 FDA",
            "Keterangan Status Muatan": "Sapi Masuk (Bongkar/Unloading dari Luar)",
            "Bruto / Kotor (kg)": 12500.0,
            "Tara / Kosong (kg)": 7200.0,
            "Jumlah Sapi (Ekor)": 16,
            "Daftar RFID/EarTag": "RF001, RF002, RF003"
        },
        {
            "No Transaksi": "-",
            "Tanggal (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Nama Lokasi Penimbangan": "Timbangan Digital Area Karantina",
            "No Plat / Armada": "D 8812 AB",
            "Keterangan Status Muatan": "Sapi Keluar (Muat/Loading Penjualan)",
            "Bruto / Kotor (kg)": 14200.0,
            "Tara / Kosong (kg)": 6800.0,
            "Jumlah Sapi (Ekor)": 18,
            "Daftar RFID/EarTag": "Tag 101, Tag 102"
        }
    ]
    df_sample = pd.DataFrame(sample_data)

    # Data Panduan Pengisian untuk Sheet Panduan
    panduan_data = [
        {"KOLOM": "No Transaksi", "ATURAN PENGISIAN": "OPSIONAL. Boleh diisi '-' atau dikosongkan. Sistem akan otomatis membuat No Transaksi Unik."},
        {"KOLOM": "Tanggal (YYYY-MM-DD)", "ATURAN PENGISIAN": "WAJIB DIISI. Format tanggal penimbangan: YYYY-MM-DD (contoh: 2026-08-03)."},
        {"KOLOM": "Nama Lokasi Penimbangan", "ATURAN PENGISIAN": "PILIH SALAH SATU: 'Jembatan Timbang Utama (Kandang)', 'Timbangan Digital Area Karantina', 'Jembatan Timbang Pelabuhan Dalam Negeri', 'Timbangan Luar / Pihak Ketiga'."},
        {"KOLOM": "No Plat / Armada", "ATURAN PENGISIAN": "WAJIB DIISI. Ketik nomor plat armada truk pengangkut (contoh: B 9123 FDA)."},
        {"KOLOM": "Keterangan Status Muatan", "ATURAN PENGISIAN": "PILIH SALAH SATU: 'Sapi Masuk (Bongkar/Unloading dari Luar)', 'Sapi Keluar (Muat/Loading Penjualan)', 'sapi kedatangan (pelabuhan dalam negeri)', 'sapi keberangkatan (pelabuhan negara asal)', 'Mutasi Antar Blok (Internal)', 'Pakan Ternak / Konsentrat / Hijauan', 'Logistik Umum / Muatan Lain', 'Lain-lain'."},
        {"KOLOM": "Bruto / Kotor (kg)", "ATURAN PENGISIAN": "WAJIB DIISI. Berat kotor truk beserta muatan (harus lebih besar dari 0)."},
        {"KOLOM": "Tara / Kosong (kg)", "ATURAN PENGISIAN": "WAJIB DIISI. Berat kosong truk tanpa muatan (tidak boleh melebihi Bruto)."},
        {"KOLOM": "Jumlah Sapi (Ekor)", "ATURAN PENGISIAN": "OPSIONAL. Isikan jumlah ekor sapi jika muatan berupa ternak (isikan 0 jika muatan pakan/logistik)."},
        {"KOLOM": "Daftar RFID/EarTag", "ATURAN PENGISIAN": "OPSIONAL. Daftar nomor RFID/EarTag di truk. Pisahkan dengan koma atau Enter. Isikan '-' jika tidak ada."}
    ]
    df_panduan = pd.DataFrame(panduan_data)

    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sample.to_excel(writer, sheet_name='FORM_INPUT_TIMBANGAN_TRUK', index=False)
            df_panduan.to_excel(writer, sheet_name='PANDUAN_PENGISIAN', index=False)
        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        buffer = io.BytesIO()
        df_sample.to_csv(buffer, index=False)
        ext = "csv"
        mime = "text/csv"

    return buffer.getvalue(), ext, mime


def tampilkan_menu_timbangan_truk(add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🚛 Timbangan Armada Truk (Logistik & Manifest)")
    st.markdown("Pencatatan berat jembatan timbang untuk kontrol armada logistik dan manifestasi muatan sapi.")

    # Key Reset untuk File Uploader Timbangan Truk
    if "uploader_key_truk" not in st.session_state:
        st.session_state["uploader_key_truk"] = 0

    cols_truk = [
        "No Transaksi", "Tanggal", "Nama Lokasi Penimbangan", "No Plat / Armada", 
        "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", 
        "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Daftar RFID/EarTag", 
        "Rata-rata / Ekor (kg)", "Operator Lapangan"
    ]
    
    df_truk = read_sheet_to_df("timbangan_truk", cols_truk)

    tab_input, tab_edit_hapus, tab_riwayat = st.tabs([
        "📝 Input Manifest Timbangan", 
        "⚙️ Edit / Hapus Data Timbangan", 
        "📜 Riwayat & Historis"
    ])

    # ==================== TAB 1: INPUT MANIFEST TIMBANGAN ====================
    with tab_input:
        sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

        # ------------------- SUB-TAB 1: INPUT SATUAN -------------------
        with sub_satuan:
            with st.form("form_timbangan_truk", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    no_transaksi = st.text_input("No Transaksi (Otomatis jika kosong)", placeholder="Contoh: TRK-2026-001").strip()
                    tgl_timbang = st.date_input("Tanggal Penimbangan", datetime.now().date())
                    
                    lokasi_timbang = st.selectbox("Nama Lokasi Penimbangan", [
                        "Jembatan Timbang Utama (Kandang)", 
                        "Timbangan Digital Area Karantina",
                        "Jembatan Timbang Pelabuhan Dalam Negeri",
                        "Timbangan Luar / Pihak Ketiga"
                    ])
                    
                    no_plat = st.text_input("No Plat / Armada Truk", placeholder="Contoh: B 9123 FDA").strip()
                    
                    opsi_muatan = [
                        "Sapi Masuk (Bongkar/Unloading dari Luar)",
                        "Sapi Keluar (Muat/Loading Penjualan)",
                        "sapi kedatangan (pelabuhan dalam negeri)",
                        "sapi keberangkatan (pelabuhan negara asal)",
                        "Mutasi Antar Blok (Internal)",
                        "Pakan Ternak / Konsentrat / Hijauan",
                        "Logistik Umum / Muatan Lain",
                        "Lain-lain"
                    ]
                    keterangan_muatan = st.selectbox("Keterangan Status Muatan", opsi_muatan)

                with col2:
                    bruto = st.number_input("Bruto / Berat Kotor (kg)", min_value=0.0, value=0.0, step=10.0)
                    tara = st.number_input("Tara / Berat Kosong Truk (kg)", min_value=0.0, value=0.0, step=10.0)
                    jumlah_sapi = st.number_input("Jumlah Sapi didalam Truk (Ekor)", min_value=0, value=0, step=1)
                    
                    rfid_list = st.text_area(
                        "Daftar RFID / EarTAG didalam Truk", 
                        placeholder="Scan atau ketik nomor RFID/EarTag di sini.\nGunakan tombol Enter untuk memisahkan setiap ID sapi.",
                        help="Bisa digunakan untuk memisahkan manifestasi data sapi per armada truk."
                    ).strip()

                st.markdown("---")
                submit_btn = st.form_submit_button("Simpan Manifest Timbangan Truk", type="primary", use_container_width=True)

                if submit_btn:
                    if not no_plat:
                        st.error("❌ Gagal Simpan! No Plat / Armada Truk wajib diisi.")
                        return
                    if bruto <= 0:
                        st.error("❌ Gagal Simpan! Berat bruto harus lebih besar dari 0 kg.")
                        return
                    
                    netto = bruto - tara
                    if netto < 0:
                        st.error("❌ Gagal Simpan! Berat kosong (Tara) tidak boleh melebihi berat kotor (Bruto).")
                        return

                    rata_per_ekor = round(netto / jumlah_sapi, 2) if jumlah_sapi > 0 else 0.0

                    if not no_transaksi:
                        waktu_str = datetime.now().strftime("%Y%m%d-%H%M%S")
                        no_transaksi = f"TRK-{waktu_str}"

                    new_truk_row = {
                        "No Transaksi": no_transaksi,
                        "Tanggal": tgl_timbang.strftime("%Y-%m-%d"),
                        "Nama Lokasi Penimbangan": lokasi_timbang,
                        "No Plat / Armada": no_plat,
                        "Keterangan Muatan": keterangan_muatan,
                        "Bruto / Kotor (kg)": float(bruto),
                        "Tara / Kosong (kg)": float(tara),
                        "Netto / Bersih (kg)": float(netto),
                        "Jumlah Sapi (Ekor)": int(jumlah_sapi),
                        "Daftar RFID/EarTag": rfid_list if rfid_list else "-",
                        "Rata-rata / Ekor (kg)": float(rata_per_ekor),
                        "Operator Lapangan": user_name
                    }

                    df_baru = pd.concat([df_truk, pd.DataFrame([new_truk_row])], ignore_index=True)
                    write_df_to_sheet("timbangan_truk", df_baru, cols_truk)

                    add_activity_log(user_name, "Timbangan Truk", f"Mencatat {keterangan_muatan} armada {no_plat} di {lokasi_timbang}")
                    st.success(f"🎉 Berhasil menyimpan data manifest timbangan armada {no_plat}! Bersih muatan: {netto} kg.")
                    st.balloons()
                    st.rerun()

        # ------------------- SUB-TAB 2: UPLOAD BATCH EXCEL -------------------
        with sub_excel:
            st.markdown("### 📥 Import Manifest Timbangan Truk via File Excel")
            st.caption("Solusi praktis untuk mengunggah riwayat timbangan banyak armada sekaligus.")

            # Langkah 1: Unduh Template
            st.markdown("#### 1. Unduh Template Resmi")
            bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel_truk()
            st.download_button(
                label=f"📥 Unduh Template Excel Timbangan Truk (.{ext_tmpl.upper()})",
                data=bytes_tmpl,
                file_name=f"Template_Timbangan_Armada_Truk.{ext_tmpl}",
                mime=mime_tmpl,
                type="secondary",
                help="File ini berisi format kolom standar beserta Sheet Panduan Pengisian."
            )

            st.markdown("---")
            # Langkah 2: Unggah File
            st.markdown("#### 2. Unggah File Excel Catatan Lapangan")
            uploaded_file = st.file_uploader(
                "Pilih file Excel (.xlsx / .xls / .csv) yang sudah diisi:", 
                type=["xlsx", "xls", "csv"],
                key=f"file_uploader_truk_{st.session_state['uploader_key_truk']}"
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

                    for idx, r in df_upload.iterrows():
                        no_baris = idx + 2

                        no_trx_raw = str(r.get("No Transaksi", "")).strip()
                        if not no_trx_raw or no_trx_raw in ["-", "nan", "None"]:
                            waktu_str = datetime.now().strftime("%Y%m%d")
                            no_trx = f"TRK-{waktu_str}-{idx+1:03d}"
                        else:
                            no_trx = no_trx_raw

                        tgl_m = str(r.get("Tanggal (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()
                        if len(tgl_m) > 10: tgl_m = tgl_m[:10]

                        lokasi = str(r.get("Nama Lokasi Penimbangan", "Jembatan Timbang Utama (Kandang)")).strip()
                        no_plat = str(r.get("No Plat / Armada", "")).strip()
                        ket_muatan = str(r.get("Keterangan Status Muatan", "Lain-lain")).strip()

                        try: bruto = float(r.get("Bruto / Kotor (kg)", 0.0))
                        except: bruto = 0.0

                        try: tara = float(r.get("Tara / Kosong (kg)", 0.0))
                        except: tara = 0.0

                        try: jumlah_sapi = int(r.get("Jumlah Sapi (Ekor)", 0))
                        except: jumlah_sapi = 0

                        rfid_list = str(r.get("Daftar RFID/EarTag", "-")).strip()

                        # Validasi Baris
                        err_msg = []
                        if not no_plat or no_plat in ["nan", "None", ""]:
                            err_msg.append("No Plat Armada kosong")
                        if bruto <= 0:
                            err_msg.append("Bruto harus > 0 kg")
                        if tara > bruto:
                            err_msg.append("Tara melebihi Bruto")

                        netto = max(0.0, bruto - tara)
                        rata_per_ekor = round(netto / jumlah_sapi, 2) if jumlah_sapi > 0 else 0.0

                        status_str = "✅ SIAP SIMPAN" if not err_msg else f"❌ ERROR: {', '.join(err_msg)}"
                        if err_msg:
                            validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")

                        rows_to_save.append({
                            "No Transaksi": no_trx,
                            "Tanggal": tgl_m,
                            "Nama Lokasi Penimbangan": lokasi,
                            "No Plat / Armada": no_plat if no_plat not in ["nan", "None", ""] else "-",
                            "Keterangan Muatan": ket_muatan,
                            "Bruto / Kotor (kg)": bruto,
                            "Tara / Kosong (kg)": tara,
                            "Netto / Bersih (kg)": netto,
                            "Jumlah Sapi (Ekor)": jumlah_sapi,
                            "Daftar RFID/EarTag": rfid_list if rfid_list not in ["nan", "None", ""] else "-",
                            "Rata-rata / Ekor (kg)": rata_per_ekor,
                            "Operator Lapangan": user_name,
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

                    # Tombol Eksekusi
                    df_valid_only = df_preview[df_preview["Status Validasi"] == "✅ SIAP SIMPAN"].drop(columns=["Status Validasi"])
                    
                    if not df_valid_only.empty:
                        if st.button(f"🚀 Simpan {len(df_valid_only)} Manifest Valid ke Database", type="primary", use_container_width=True):
                            with st.spinner("💾 Mengunggah manifest timbangan truk masal ke database Supabase..."):
                                df_baru_total = pd.concat([df_truk, df_valid_only], ignore_index=True)
                                write_df_to_sheet("timbangan_truk", df_baru_total, cols_truk)
                                add_activity_log(user_name, "Batch Timbangan Truk", f"Mengunggah {len(df_valid_only)} data timbangan armada via Excel")
                            
                            st.session_state["uploader_key_truk"] += 1
                            st.toast(f"🎉 Berhasil menyimpan {len(df_valid_only)} manifest timbangan truk!", icon="🚀")
                            st.rerun()
                    else:
                        st.error("Tidak ada baris data yang valid untuk disimpan.")

                except Exception as e:
                    st.error(f"❌ Gagal membaca file Excel. Pastikan menggunakan template resmi! Detail Error: {e}")

    # ==================== TAB 2: EDIT / HAPUS (OTORISASI ADMIN) ====================
    with tab_edit_hapus:
        st.markdown("### ⚙️ Otorisasi Koreksi & Penghapusan Manifest Timbangan")
        
        if df_truk.empty:
            st.info("Belum ada data timbangan truk yang tersimpan untuk dikoreksi.")
        else:
            df_truk_view = df_truk.copy()
            df_truk_view.insert(0, "No Urut", range(1, len(df_truk) + 1))
            st.dataframe(df_truk_view.sort_values(by="No Urut", ascending=True), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            idx_edit = st.number_input("Masukkan No Urut Data Timbangan yang Ingin Dikelola:", min_value=1, max_value=len(df_truk), step=1) - 1
            row_edit = df_truk.iloc[idx_edit]
            
            st.info(f"📋 **Data Terpilih:** Transaksi **{row_edit['No Transaksi']}** | Armada: **{row_edit['No Plat / Armada']}** ({row_edit['Keterangan Muatan']})")
            
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123"
                
            aksi_pilihan = st.radio("Pilih Tindakan Pengelolaan:", ["✏️ Edit / Koreksi Data", "🗑️ Hapus Permanen Data"], horizontal=True)
            
            # --- SUB ACTION: EDIT DATA ---
            if aksi_pilihan == "✏️ Edit / Koreksi Data":
                with st.form("form_edit_timbangan_truk"):
                    st.markdown("#### 📝 Form Koreksi Data Manifest")
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        st.text_input("No Transaksi (Tidak Dapat Diubah)", value=str(row_edit["No Transaksi"]), disabled=True)
                        
                        try:
                            tgl_obj = datetime.strptime(str(row_edit["Tanggal"]), "%Y-%m-%d").date()
                        except:
                            tgl_obj = datetime.now().date()
                            
                        edit_tgl_timbang = st.date_input("Tanggal Penimbangan", value=tgl_obj)
                        
                        list_lokasi = [
                            "Jembatan Timbang Utama (Kandang)", 
                            "Timbangan Digital Area Karantina",
                            "Jembatan Timbang Pelabuhan Dalam Negeri",
                            "Timbangan Luar / Pihak Ketiga"
                        ]
                        try: idx_lokasi = list_lokasi.index(str(row_edit["Nama Lokasi Penimbangan"]))
                        except: idx_lokasi = 0
                        edit_lokasi_timbang = st.selectbox("Nama Lokasi Penimbangan", list_lokasi, index=idx_lokasi)
                        
                        edit_no_plat = st.text_input("No Plat / Armada Truk", value=str(row_edit["No Plat / Armada"])).strip()
                        
                        list_muatan = [
                            "Sapi Masuk (Bongkar/Unloading dari Luar)",
                            "Sapi Keluar (Muat/Loading Penjualan)",
                            "sapi kedatangan (pelabuhan dalam negeri)",
                            "sapi keberangkatan (pelabuhan negara asal)",
                            "Mutasi Antar Blok (Internal)",
                            "Pakan Ternak / Konsentrat / Hijauan",
                            "Logistik Umum / Muatan Lain",
                            "Lain-lain"
                        ]
                        try: idx_muatan = list_muatan.index(str(row_edit["Keterangan Muatan"]))
                        except: idx_muatan = 0
                        edit_keterangan_muatan = st.selectbox("Keterangan Status Muatan", list_muatan, index=idx_muatan)

                    with col_e2:
                        edit_bruto = st.number_input("Bruto / Berat Kotor (kg)", min_value=0.0, value=float(row_edit["Bruto / Kotor (kg)"]), step=10.0)
                        edit_tara = st.number_input("Tara / Berat Kosong Truk (kg)", min_value=0.0, value=float(row_edit["Tara / Kosong (kg)"]), step=10.0)
                        edit_jumlah_sapi = st.number_input("Jumlah Sapi didalam Truk (Ekor)", min_value=0, value=int(row_edit["Jumlah Sapi (Ekor)"]), step=1)
                        edit_rfid_list = st.text_area("Daftar RFID / EarTAG didalam Truk", value=str(row_edit["Daftar RFID/EarTag"])).strip()
                    
                    st.markdown("---")
                    pwd_admin_edit = st.text_input("🔐 Masukkan Password Admin untuk Validasi Koreksi:", type="password", key="pwd_edit_truk")
                    submit_edit_btn = st.form_submit_button("💾 Simpan Perubahan Data", type="primary", use_container_width=True)
                    
                    if submit_edit_btn:
                        if pwd_admin_edit != correct_admin_pwd:
                            st.error("❌ Gagal Simpan! Password Admin salah. Otorisasi Ditolak.")
                        elif not edit_no_plat:
                            st.error("❌ Gagal Simpan! No Plat / Armada Truk wajib diisi.")
                        elif edit_bruto <= 0:
                            st.error("❌ Gagal Simpan! Berat bruto harus lebih besar dari 0 kg.")
                        else:
                            edit_netto = edit_bruto - edit_tara
                            if edit_netto < 0:
                                st.error("❌ Gagal Simpan! Berat kosong (Tara) melebihi berat kotor (Bruto).")
                                return
                                
                            edit_rata = round(edit_netto / edit_jumlah_sapi, 2) if edit_jumlah_sapi > 0 else 0.0
                            
                            df_truk.at[idx_edit, "Tanggal"] = edit_tgl_timbang.strftime("%Y-%m-%d")
                            df_truk.at[idx_edit, "Nama Lokasi Penimbangan"] = edit_lokasi_timbang
                            df_truk.at[idx_edit, "No Plat / Armada"] = edit_no_plat
                            df_truk.at[idx_edit, "Keterangan Muatan"] = edit_keterangan_muatan
                            df_truk.at[idx_edit, "Bruto / Kotor (kg)"] = float(edit_bruto)
                            df_truk.at[idx_edit, "Tara / Kosong (kg)"] = float(edit_tara)
                            df_truk.at[idx_edit, "Netto / Bersih (kg)"] = float(edit_netto)
                            df_truk.at[idx_edit, "Jumlah Sapi (Ekor)"] = int(edit_jumlah_sapi)
                            df_truk.at[idx_edit, "Daftar RFID/EarTag"] = edit_rfid_list if edit_rfid_list else "-"
                            df_truk.at[idx_edit, "Rata-rata / Ekor (kg)"] = float(edit_rata)
                            df_truk.at[idx_edit, "Operator Lapangan"] = user_name
                            
                            with st.spinner("🔄 Memperbarui manifest timbangan di Supabase..."):
                                write_df_to_sheet("timbangan_truk", df_truk, cols_truk)
                                
                            add_activity_log(user_name, "Edit Timbangan Truk", f"Mengoreksi transaksi {row_edit['No Transaksi']} armada {edit_no_plat}")
                            st.success(f"✅ Data manifest transaksi {row_edit['No Transaksi']} Berhasil diperbarui!")
                            st.rerun()
                            
            # --- SUB ACTION: HAPUS PERMANEN ---
            elif aksi_pilihan == "🗑️ Hapus Permanen Data":
                st.warning(f"⚠️ **PERINGATAN KRUSIAL:** Anda akan menghapus data transaksi **{row_edit['No Transaksi']}** secara PERMANEN dari database cloud Supabase. Tindakan ini tidak dapat dibatalkan!")
                pwd_admin_hapus = st.text_input("🔐 Masukkan Password Admin untuk Validasi Penghapusan:", type="password", key="pwd_hapus_truk")
                
                if st.button("🗑️ Eksekusi Hapus Data Permanen", type="secondary", use_container_width=True):
                    if pwd_admin_hapus != correct_admin_pwd:
                        st.error("❌ Gagal Hapus! Password Admin salah. Akses Ditolak.")
                    else:
                        with st.spinner("🔄 Menghapus baris transaksi dari Supabase..."):
                            df_truk = df_truk.drop(index=idx_edit).reset_index(drop=True)
                            write_df_to_sheet("timbangan_truk", df_truk, cols_truk)
                            
                        add_activity_log(user_name, "Hapus Timbangan Truk", f"Menghapus manifest transaksi {row_edit['No Transaksi']} armada {row_edit['No Plat / Armada']}")
                        st.success(f"🗑️ Data transaksi {row_edit['No Transaksi']} berhasil dihapus dari database.")
                        st.rerun()

    # ==================== TAB 3: RIWAYAT HISTORIS LOGISTIK ====================
    with tab_riwayat:
        st.markdown("### 📜 Riwayat Catatan Timbangan Armada Truk")
        if not df_truk.empty:
            st.dataframe(df_truk.sort_values(by="Tanggal", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat timbangan truk yang tercatat di sistem.")