import streamlit as st
import pandas as pd
from datetime import datetime
import io
import importlib

# ==================== GENERATOR TEMPLATE EXCEL REGISTRASI ====================
def buat_template_excel_registrasi(STRUKTUR_KANDANG, LIST_JENIS_SAPI):
    """Membuat template Excel Registrasi Sapi Baru 2 Sheet lengkap dengan Data Validation."""
    buffer = io.BytesIO()
    
    blok_default = list(STRUKTUR_KANDANG.keys())[0] if STRUKTUR_KANDANG else "Blok Karantina"
    pen_default = STRUKTUR_KANDANG[blok_default][0] if (STRUKTUR_KANDANG and STRUKTUR_KANDANG[blok_default]) else "Pen Karantina 1"
    jenis_default = LIST_JENIS_SAPI[0] if LIST_JENIS_SAPI else "Brahman Cross"
    batch_default = f"BATCH-{datetime.now().strftime('%Y-%m')}"

    sample_data = [
        {
            "Kode Batch (Opsional)": batch_default,
            "Kode Sapi": "S5-001",
            "RFID / EarTag Asal": "RF-882001",
            "RFID / EarTag Kandang": "RF-882001",
            "Jenis Sapi": jenis_default,
            "Jenis Kelamin": "Jantan",
            "Asal Negara": "Australia",
            "Tanggal Masuk (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Bobot Awal (kg)": 320.5,
            "Blok Kandang": blok_default,
            "Nomor Pen": pen_default
        }
    ]
    df_sample = pd.DataFrame(sample_data)

    panduan_data = [
        {"KOLOM": "Kode Batch (Opsional)", "ATURAN PENGISIAN": "OPSIONAL. Jika dikosongkan, sistem otomatis membuatkan Kode Batch (contoh: BATCH-2026-08)."},
        {"KOLOM": "Kode Sapi", "ATURAN PENGISIAN": "WAJIB DIISI & UNIK. Kode identitas internal sapi (contoh: S5-001)."},
        {"KOLOM": "RFID / EarTag Asal", "ATURAN PENGISIAN": "OPSIONAL. Tag fisik dari supplier/importer. Isikan '-' jika tidak ada."},
        {"KOLOM": "RFID / EarTag Kandang", "ATURAN PENGISIAN": "WAJIB DIISI. Tag RFID resmi kandang yang ditempel di telinga sapi."},
        {"KOLOM": "Jenis Sapi", "ATURAN PENGISIAN": f"PILIH DARI DROPDOWN EXCEL: {', '.join(LIST_JENIS_SAPI[:8])}"},
        {"KOLOM": "Jenis Kelamin", "ATURAN PENGISIAN": "PILIH DARI DROPDOWN EXCEL: 'Jantan' atau 'Betina'."},
        {"KOLOM": "Asal Negara", "ATURAN PENGISIAN": "PILIH DARI DROPDOWN EXCEL: 'Australia', 'Indonesia (Lokal)', 'Selandia Baru', 'Lain-lain'."},
        {"KOLOM": "Tanggal Masuk (YYYY-MM-DD)", "ATURAN PENGISIAN": "WAJIB DIISI. Format YYYY-MM-DD (contoh: 2026-08-04)."},
        {"KOLOM": "Bobot Awal (kg)", "ATURAN PENGISIAN": "WAJIB DIISI. Berat timbangan saat pertama masuk kandang (contoh: 320.5)."},
        {"KOLOM": "Blok Kandang", "ATURAN PENGISIAN": f"HARUS SAMA PERSIS MASTER: {', '.join(list(STRUKTUR_KANDANG.keys()))}"},
        {"KOLOM": "Nomor Pen", "ATURAN PENGISIAN": "WAJIB DIISI. Nama Pen penempatan awal karantina/penggemukan."}
    ]
    df_panduan = pd.DataFrame(panduan_data)

    try:
        mod_dv = importlib.import_module("openpyxl.worksheet.datavalidation")
        DataValidation = getattr(mod_dv, "DataValidation")

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sample.to_excel(writer, sheet_name='FORM_REGISTRASI_SAPI', index=False)
            df_panduan.to_excel(writer, sheet_name='PANDUAN_PENGISIAN', index=False)
            
            wb = writer.book
            ws_input = wb['FORM_REGISTRASI_SAPI']

            # Dropdown Jenis Sapi
            dv_jenis = DataValidation(type="list", formula1=f'"{", ".join(LIST_JENIS_SAPI[:12])}"', allow_blank=True)
            ws_input.add_data_validation(dv_jenis)
            dv_jenis.add("E2:E500")

            # Dropdown Gender
            dv_gender = DataValidation(type="list", formula1='"Jantan, Betina"', allow_blank=True)
            ws_input.add_data_validation(dv_gender)
            dv_gender.add("F2:F500")

            # Dropdown Asal
            dv_asal = DataValidation(type="list", formula1='"Australia, Indonesia (Lokal), Selandia Baru, Lain-lain"', allow_blank=True)
            ws_input.add_data_validation(dv_asal)
            dv_asal.add("G2:G500")

        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        buffer = io.BytesIO()
        df_sample.to_csv(buffer, index=False)
        ext = "csv"
        mime = "text/csv"

    return buffer.getvalue(), ext, mime


def tampilkan_menu_registrasi(df_sapi, LIST_JENIS_SAPI, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, user_role):
    st.subheader("➕ Registrasi & Penerimaan Sapi Baru")
    st.markdown("Pendaftaran sapi baru ke dalam sistem master data kandang lengkap dengan penandaan **Kode Batch**.")

    if "uploader_key_registrasi" not in st.session_state:
        st.session_state["uploader_key_registrasi"] = 0

    batch_default_auto = f"BATCH-{datetime.now().strftime('%Y-%m')}"

    sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

    # ==================== SUB-TAB 1: FORM INPUT SATUAN ====================
    with sub_satuan:
        st.markdown("### 📝 Form Pendaftaran Sapi Baru (Manual)")
        
        with st.form("form_registrasi_sapi", clear_on_submit=True):
            st.markdown("#### 📦 1. Identitas Pembelian & Batch")
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                kode_batch_in = st.text_input(
                    "Kode Batch / Lot Pembelian (Otomatis Terisi Jika Dikosongkan)", 
                    value=batch_default_auto, 
                    help="Boleh dikosongkan/diubah. Jika kosong, sistem otomatis memakai format BATCH-YYYY-MM"
                ).strip()
            with c_b2:
                asal_negara_in = st.selectbox("Asal Negara / Daerah", ["Australia", "Indonesia (Lokal)", "Selandia Baru", "Lain-lain"])

            st.markdown("---")
            st.markdown("#### 🏷️ 2. Identitas Sapi & Tag Fisik")
            c_i1, c_i2, c_i3 = st.columns(3)
            with c_i1:
                kode_sapi_in = st.text_input("Kode Sapi (Internal Kandang)*", placeholder="Contoh: S5-001").strip()
            with c_i2:
                rfid_asal_in = st.text_input("RFID / EarTag Asal (Supplier)", value="-").strip()
            with c_i3:
                rfid_kandang_in = st.text_input("RFID / EarTag Resmi Kandang*", placeholder="Contoh: RF-882001").strip()

            c_i4, c_i5, c_i6 = st.columns(3)
            with c_i4:
                jenis_sapi_in = st.selectbox("Jenis Sapi*", LIST_JENIS_SAPI)
            with c_i5:
                jenis_kelamin_in = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"])
            with c_i6:
                tgl_masuk_in = st.date_input("Tanggal Masuk Kandang", datetime.now().date())

            st.markdown("---")
            st.markdown("#### ⚖️ 3. Penimbangan Awal & Penempatan Kandang")
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                bobot_awal_in = st.number_input("Bobot Awal Masuk (kg)*", min_value=1.0, value=300.0, step=1.0, format="%.2f")
            with c_p2:
                blok_terpilih = st.selectbox("Pilih Blok Kandang Awal", list(STRUKTUR_KANDANG.keys()))
            with c_p3:
                pen_tersaring = STRUKTUR_KANDANG.get(blok_terpilih, [])
                pen_terpilih = st.selectbox("Pilih Pen Kandang Awal", pen_tersaring)

            lokasi_pen_full = f"{blok_terpilih} - {pen_terpilih}"
            
            sapi_aktif_di_pen = df_sapi[(df_sapi["Lokasi Pen"] == lokasi_pen_full) & (df_sapi["Status"] == "AKTIF")]
            st.info(f"📊 Populasi Sapi Aktif di **{lokasi_pen_full}**: **{len(sapi_aktif_di_pen)} / 25 Ekor**")

            submit_reg = st.form_submit_button("🚀 Daftarkan Sapi Baru", type="primary", use_container_width=True)

            if submit_reg:
                # Penanganan otomatis jika Kode Batch dikosongkan pengguna
                kode_batch_final = kode_batch_in if kode_batch_in else batch_default_auto

                # Validasi Keunikan Sapi (Khusus Sapi Aktif)
                sapi_aktif_existing = df_sapi[df_sapi["Status"] == "AKTIF"]
                kode_exist = not sapi_aktif_existing[sapi_aktif_existing["Kode Sapi"].astype(str).str.upper() == kode_sapi_in.upper()].empty
                rfid_exist = not sapi_aktif_existing[sapi_aktif_existing["RFID/Tag"].astype(str).str.upper() == rfid_kandang_in.upper()].empty

                if not kode_sapi_in or not rfid_kandang_in:
                    st.error("❌ Gagal Registrasi! Kode Sapi dan RFID Kandang wajib diisi.")
                elif kode_exist:
                    st.error(f"❌ Gagal Registrasi! Kode Sapi '{kode_sapi_in}' sudah terdaftar pada populasi aktif.")
                elif rfid_exist:
                    st.error(f"❌ Gagal Registrasi! RFID Kandang '{rfid_kandang_in}' sedang digunakan oleh sapi aktif lain.")
                elif len(sapi_aktif_di_pen) >= 25:
                    st.error(f"❌ Gagal Registrasi! Pen **{lokasi_pen_full}** sudah penuh (25/25 Ekor).")
                else:
                    new_row = {
                        "Kode Batch": kode_batch_final,
                        "Kode Sapi": kode_sapi_in,
                        "RFID/Tag Asal": rfid_asal_in if rfid_asal_in else "-",
                        "RFID/Tag": rfid_kandang_in,
                        "Jenis Sapi": jenis_sapi_in,
                        "Jenis Kelamin": jenis_kelamin_in,
                        "Asal Negara": asal_negara_in,
                        "Tgl Masuk": str(tgl_masuk_in),
                        "Bobot Awal (kg)": float(bobot_awal_in),
                        "Tgl Cek Akhir": str(tgl_masuk_in),
                        "Bobot Akhir (kg)": float(bobot_awal_in),
                        "ADG (kg/hari)": 0.0,
                        "Total Pakan (kg)": 0.0,
                        "Tgl Pakan Terakhir": "-",
                        "Lokasi Pen": lokasi_pen_full,
                        "Status": "AKTIF"
                    }

                    with st.spinner("💾 Menyimpan registrasi sapi baru..."):
                        df_sapi = pd.concat([df_sapi, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df_sapi)
                        add_activity_log(user_name, "Registrasi Sapi", f"Mendaftarkan sapi {kode_sapi_in} ({rfid_kandang_in}) ke {lokasi_pen_full} [Batch: {kode_batch_final}]")

                    st.success(f"🎉 Berhasil mendaftarkan Sapi **{kode_sapi_in}** ke **{lokasi_pen_full}** [Batch: {kode_batch_final}]!")
                    st.rerun()

    # ==================== SUB-TAB 2: UPLOAD BATCH EXCEL ====================
    with sub_excel:
        st.markdown("### 📥 Import Registrasi Sapi Masal via File Excel")
        
        bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel_registrasi(STRUKTUR_KANDANG, LIST_JENIS_SAPI)
        st.download_button(
            label=f"📥 Unduh Template Excel Registrasi Sapi (.{ext_tmpl.upper()})",
            data=bytes_tmpl,
            file_name=f"Template_Registrasi_Sapi_Baru.{ext_tmpl}",
            mime=mime_tmpl,
            type="secondary"
        )

        st.markdown("---")
        uploaded_file = st.file_uploader(
            "Pilih file Excel (.xlsx / .xls / .csv) yang sudah diisi:", 
            type=["xlsx", "xls", "csv"],
            key=f"file_uploader_registrasi_{st.session_state['uploader_key_registrasi']}"
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file, sheet_name=0)

                st.markdown("#### Pratinjau & Validasi Data Upload")
                rows_to_save = []
                validation_errors = []

                sapi_aktif_existing = df_sapi[df_sapi["Status"] == "AKTIF"]
                set_kode_aktif = set(sapi_aktif_existing["Kode Sapi"].astype(str).str.upper())
                set_rfid_aktif = set(sapi_aktif_existing["RFID/Tag"].astype(str).str.upper())

                for idx, r in df_upload.iterrows():
                    no_baris = idx + 2
                    
                    # Dukung pembacaan kolom dengan nama lama maupun baru
                    batch_k = str(r.get("Kode Batch (Opsional)", r.get("Kode Batch", ""))).strip()
                    batch_final = batch_k if batch_k and batch_k not in ["nan", "None", ""] else batch_default_auto

                    kode_s = str(r.get("Kode Sapi", "")).strip()
                    rfid_a = str(r.get("RFID / EarTag Asal", "-")).strip()
                    rfid_k = str(r.get("RFID / EarTag Kandang", "")).strip()
                    jenis_s = str(r.get("Jenis Sapi", "Brahman Cross")).strip()
                    gender_s = str(r.get("Jenis Kelamin", "Jantan")).strip()
                    asal_n = str(r.get("Asal Negara", "Australia")).strip()
                    tgl_m = str(r.get("Tanggal Masuk (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()[:10]

                    try: bobot_a = float(r.get("Bobot Awal (kg)", 300.0))
                    except: bobot_a = 0.0

                    blok_k = str(r.get("Blok Kandang", "")).strip()
                    pen_k = str(r.get("Nomor Pen", "")).strip()
                    lokasi_f = pen_k if " - " in pen_k else f"{blok_k} - {pen_k}"

                    err_msg = []
                    if not kode_s or kode_s in ["nan", "None", ""]: err_msg.append("Kode Sapi kosong")
                    elif kode_s.upper() in set_kode_aktif: err_msg.append(f"Kode Sapi '{kode_s}' sudah terdaftar")

                    if not rfid_k or rfid_k in ["nan", "None", ""]: err_msg.append("RFID Kandang kosong")
                    elif rfid_k.upper() in set_rfid_aktif: err_msg.append(f"RFID '{rfid_k}' sedang digunakan")

                    if bobot_a <= 0: err_msg.append("Bobot awal harus > 0 kg")
                    if blok_k not in STRUKTUR_KANDANG: err_msg.append(f"Blok '{blok_k}' tidak terdaftar")

                    status_str = "✅ SIAP SIMPAN" if not err_msg else f"❌ ERROR: {', '.join(err_msg)}"
                    if err_msg: validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")

                    if not err_msg:
                        set_kode_aktif.add(kode_s.upper())
                        set_rfid_aktif.add(rfid_k.upper())

                    rows_to_save.append({
                        "Kode Batch": batch_final,
                        "Kode Sapi": kode_s, "RFID/Tag Asal": rfid_a if rfid_a not in ["nan", "None", ""] else "-",
                        "RFID/Tag": rfid_k, "Jenis Sapi": jenis_s, "Jenis Kelamin": gender_s, "Asal Negara": asal_n,
                        "Tgl Masuk": tgl_m, "Bobot Awal (kg)": bobot_a, "Tgl Cek Akhir": tgl_m, "Bobot Akhir (kg)": bobot_a,
                        "ADG (kg/hari)": 0.0, "Total Pakan (kg)": 0.0, "Tgl Pakan Terakhir": "-",
                        "Lokasi Pen": lokasi_f, "Status": "AKTIF", "Status Validasi": status_str
                    })

                df_preview = pd.DataFrame(rows_to_save)
                st.dataframe(df_preview, use_container_width=True, hide_index=True)

                df_valid_only = df_preview[df_preview["Status Validasi"] == "✅ SIAP SIMPAN"].drop(columns=["Status Validasi"])
                if not df_valid_only.empty:
                    if st.button(f"🚀 Simpan {len(df_valid_only)} Sapi Baru Valid", type="primary", use_container_width=True):
                        with st.spinner("💾 Menyimpan registrasi massal..."):
                            df_sapi = pd.concat([df_sapi, df_valid_only], ignore_index=True)
                            save_data(df_sapi)
                            add_activity_log(user_name, "Batch Registrasi Sapi", f"Mendaftarkan {len(df_valid_only)} ekor sapi baru via Excel")

                        st.session_state["uploader_key_registrasi"] += 1
                        st.toast("🎉 Berhasil mendaftarkan sapi baru!", icon="🚀")
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Error upload file: {e}")