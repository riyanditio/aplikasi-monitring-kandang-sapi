import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ==================== FUNGSI GENERATOR TEMPLATE EXCEL DINAMIS ====================
def buat_template_excel(list_jenis_sapi, struktur_kandang):
    """
    Membuat file Excel template yang berisi Sheet Input Data dan Sheet Panduan Pengisian
    yang otomatis tersinkronisasi dengan Master Jenis Sapi & Struktur Kandang aktif.
    """
    buffer = io.BytesIO()
    
    # Data Contoh untuk Sheet Input
    blok_default = list(struktur_kandang.keys())[0] if struktur_kandang else "Blok Karantina"
    jenis_default = list_jenis_sapi[0] if list_jenis_sapi else "Brahman Cross"

    sample_data = [
        {
            "Kode Tiba / No Batch": "BATCH-01",
            "RFID Asal": "90001",
            "RFID Kandang": "RF1001",
            "Jenis Sapi": jenis_default,
            "Jenis Kelamin": "Jantan",
            "Umur Masuk (Bulan)": 12,
            "Asal Negara": "Australia",
            "Tgl Masuk (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Bobot Awal (kg)": 320.5,
            "Blok Kandang": blok_default,
            "Nomor Pen": "-"  # Dikosongkan/Diisi '-' agar terisi otomatis
        },
        {
            "Kode Tiba / No Batch": "BATCH-01",
            "RFID Asal": "90002",
            "RFID Kandang": "RF1002",
            "Jenis Sapi": list_jenis_sapi[1] if len(list_jenis_sapi) > 1 else jenis_default,
            "Jenis Kelamin": "Jantan",
            "Umur Masuk (Bulan)": 14,
            "Asal Negara": "Australia",
            "Tgl Masuk (YYYY-MM-DD)": datetime.now().strftime("%Y-%m-%d"),
            "Bobot Awal (kg)": 340.0,
            "Blok Kandang": blok_default,
            "Nomor Pen": "-"  # Dikosongkan/Diisi '-' agar terisi otomatis
        }
    ]
    df_sample = pd.DataFrame(sample_data)

    # Data Panduan Pengisian untuk Sheet Panduan
    panduan_data = [
        {"KOLOM": "Kode Tiba / No Batch", "ATURAN PENGISIAN": "WAJIB DIISI. Boleh sama untuk satu kelompok/truk kedatangan (contoh: BATCH-01, S2, B05)."},
        {"KOLOM": "RFID Asal", "ATURAN PENGISIAN": "OPSIONAL. Nomor RFID bawaan asal supplier. Isikan '-' jika tidak ada."},
        {"KOLOM": "RFID Kandang", "ATURAN PENGISIAN": "OPSIONAL. Nomor RFID internal kandang. HARUS UNIK (tidak boleh sama dengan sapi lain). Isikan '-' jika belum dipasang."},
        {"KOLOM": "Jenis Sapi", "ATURAN PENGISIAN": f"PILIH SALAH SATU DARI MASTER: {', '.join(list_jenis_sapi)}"},
        {"KOLOM": "Jenis Kelamin", "ATURAN PENGISIAN": "Ketik persis: Jantan atau Betina"},
        {"KOLOM": "Umur Masuk (Bulan)", "ATURAN PENGISIAN": "Angka estimasi umur sapi saat masuk (contoh: 12, 18, 24)."},
        {"KOLOM": "Asal Negara", "ATURAN PENGISIAN": "Contoh: Australia, Lokal, Bali, NTB, Lampung."},
        {"KOLOM": "Tgl Masuk (YYYY-MM-DD)", "ATURAN PENGISIAN": "Format tanggal: YYYY-MM-DD (contoh: 2026-07-29)."},
        {"KOLOM": "Bobot Awal (kg)", "ATURAN PENGISIAN": "Angka bobot timbangan awal masuk (contoh: 320.5)."},
        {"KOLOM": "Blok Kandang", "ATURAN PENGISIAN": f"HARUS SAMA PERSIS DENGAN MASTER BLOK: {', '.join(list(struktur_kandang.keys()))}"},
        {"KOLOM": "Nomor Pen", "ATURAN PENGISIAN": "BISA DIKOSONGKAN / ISI '-'. Sistem akan OTOMATIS membagikan sapi ke Pen yang masih berkuota (< 25 ekor) di Blok tersebut."}
    ]
    df_panduan = pd.DataFrame(panduan_data)

    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sample.to_excel(writer, sheet_name='FORM_INPUT_SAPI', index=False)
            df_panduan.to_excel(writer, sheet_name='PANDUAN_PENGISIAN', index=False)
        ext = "xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception:
        buffer = io.BytesIO()
        df_sample.to_csv(buffer, index=False)
        ext = "csv"
        mime = "text/csv"

    return buffer.getvalue(), ext, mime


def tampilkan_menu_registrasi(df_sapi, list_jenis_sapi, struktur_kandang, save_data, add_activity_log, user_name, user_role="operator"):
    st.subheader("📝 Manajemen & Registrasi Sapi Baru")
    
    tab_registrasi, tab_edit_hapus = st.tabs(["➕ Registrasi Sapi Baru", "⚙️ Edit / Hapus Data Registrasi"])

    # ==================== TAB 1: FORM REGISTRASI ====================
    with tab_registrasi:
        sub_satuan, sub_excel = st.tabs(["📝 Form Input Satuan", "📥 Upload Batch File Excel"])

        # ------------------- SUB-TAB 1: INPUT SATUAN -------------------
        with sub_satuan:
            st.markdown("Silakan masukkan data batch sapi baru secara manual satu per satu.")

            with st.form("form_registrasi_sapi", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    kode_tiba = st.text_input("Kode Tiba / No. Batch Kedatangan", placeholder="Contoh: S2").strip()
                    rfid_tag_asal = st.text_input("RFID / Tag Asal (Opsional)", placeholder="Scan/ketik RFID bawaan asal supplier").strip()
                    rfid_tag_kandang = st.text_input("RFID / Tag Kandang (Opsional)", placeholder="Scan/ketik nomor RFID internal kandang").strip()
                    
                    st.markdown("---")
                    jenis_sapi = st.selectbox("Jenis / Ras Sapi", list_jenis_sapi, key="reg_jenis")
                    jenis_kelamin = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"], key="reg_jk")

                with col2:
                    umur_masuk = st.number_input("Estimasi Umur Masuk (Bulan)", min_value=1, max_value=120, value=12, key="reg_umur")
                    asal_negara = st.text_input("Asal Negara / Daerah", placeholder="Contoh: Australia / Bali").strip()
                    tgl_masuk = st.date_input("Tanggal Masuk Kandang", datetime.now().date(), key="reg_tgl")
                    bobot_awal = st.number_input("Bobot Awal Masuk (kg)", min_value=50.0, max_value=1500.0, value=300.0, step=1.0, key="reg_bobot")
                    
                    st.markdown("---")
                    pilihan_blok = st.selectbox("Pilih Blok Kandang", list(struktur_kandang.keys()), key="reg_blok")
                    daftar_pen_tersedia = struktur_kandang[pilihan_blok]
                    pilihan_pen = st.selectbox("Pilih Nomor/Bagian Pen", daftar_pen_tersedia, key="reg_pen")

                st.markdown("---")
                submit_btn = st.form_submit_button("Simpan Data Sapi Baru", type="primary", use_container_width=True)

                if submit_btn:
                    if not kode_tiba:
                        st.error("❌ Gagal Simpan! 'Kode Tiba / No. Batch Kedatangan' wajib diisi.")
                        return

                    if rfid_tag_kandang and rfid_tag_kandang != "-":
                        if not df_sapi.empty and "RFID/Tag" in df_sapi.columns:
                            if rfid_tag_kandang.lower() in df_sapi["RFID/Tag"].astype(str).str.lower().values:
                                st.error(f"❌ Gagal Simpan! RFID Kandang '{rfid_tag_kandang}' sudah digunakan oleh sapi lain.")
                                return

                    lokasi_pen_final = f"{pilihan_blok} - {pilihan_pen}"

                    # CEK KAPASITAS PEN (MAKS 25 EKOR)
                    sapi_di_pen = len(df_sapi[df_sapi["Lokasi Pen"] == lokasi_pen_final])
                    if sapi_di_pen >= 25:
                        pen_rekomendasi = []
                        for b, pens in struktur_kandang.items():
                            for p in pens:
                                nama_full = f"{b} - {p}"
                                isi = len(df_sapi[df_sapi["Lokasi Pen"] == nama_full])
                                if isi < 25:
                                    pen_rekomendasi.append(f"{nama_full} (Isi: {isi}/25)")
                        
                        saran_teks = "\n* ".join(pen_rekomendasi[:5])
                        st.error(f"❌ Gagal Registrasi! Pen **{lokasi_pen_final}** sudah penuh (Maksimal 25 ekor). Saat ini berisi {sapi_di_pen} ekor.")
                        if pen_rekomendasi:
                            st.info(f"💡 **Saran Pen yang Masih Tersedia:**\n* {saran_teks}")
                        else:
                            st.warning("⚠️ Semua pen di kandang saat ini sudah penuh!")
                        return

                    new_cow = {
                        "Kode Sapi": kode_tiba, 
                        "RFID/Tag Asal": rfid_tag_asal if rfid_tag_asal else "-",
                        "RFID/Tag": rfid_tag_kandang if rfid_tag_kandang else "-",
                        "Jenis Sapi": jenis_sapi,
                        "Jenis Kelamin": jenis_kelamin,
                        "Umur Masuk (Bulan)": int(umur_masuk),
                        "Asal Negara": asal_negara if asal_negara else "Lokal",
                        "Tgl Masuk": tgl_masuk.strftime("%Y-%m-%d"),
                        "Bobot Awal (kg)": float(bobot_awal),
                        "Tgl Cek Akhir": tgl_masuk.strftime("%Y-%m-%d"),
                        "Bobot Akhir (kg)": float(bobot_awal),
                        "ADG (kg/hari)": 0.0,
                        "Total Pakan (kg)": 0.0,
                        "Tgl Pakan Terakhir": "-",
                        "Lokasi Pen": lokasi_pen_final
                    }

                    df_baru = pd.concat([df_sapi, pd.DataFrame([new_cow])], ignore_index=True)
                    save_data(df_baru)
                    add_activity_log(user_name, "Registrasi Sapi", f"Mendaftarkan Sapi Kelompok {kode_tiba} di {lokasi_pen_final}")
                    st.success(f"🎉 Berhasil! Sapi dengan Kode Tiba {kode_tiba} telah terdaftar.")
                    st.rerun()

        # ------------------- SUB-TAB 2: UPLOAD BATCH EXCEL -------------------
        with sub_excel:
            st.markdown("### 📥 Registrasi Masal via Unggah File Excel")
            st.caption("Solusi cepat untuk memproses puluhan/ratusan sapi sekaligus dari catatan petugas lapangan.")

            # Langkah 1: Unduh Template Excel
            st.markdown("#### 1. Unduh Template Resmi")
            bytes_tmpl, ext_tmpl, mime_tmpl = buat_template_excel(list_jenis_sapi, struktur_kandang)
            st.download_button(
                label=f"📥 Unduh Template Excel Registrasi Sapi (.{ext_tmpl.upper()})",
                data=bytes_tmpl,
                file_name=f"Template_Registrasi_Sapi_Kandang.{ext_tmpl}",
                mime=mime_tmpl,
                type="secondary",
                help="File ini berisi format kolom yang pas dan Sheet Panduan Pengisian."
            )

            st.markdown("---")
            # Langkah 2: Unggah File
            st.markdown("#### 2. Unggah File Excel Catatan Lapangan")
            uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls / .csv) yang sudah diisi:", type=["xlsx", "xls", "csv"])

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file, sheet_name=0)

                    st.markdown("#### 3. Pratinjau & Validasi Data Otomatis")
                    
                    rfid_eksis = set(df_sapi["RFID/Tag"].astype(str).str.lower().tolist()) if not df_sapi.empty and "RFID/Tag" in df_sapi.columns else set()
                    
                    # Hitung kapasitas awal pen saat ini
                    pen_counts = df_sapi["Lokasi Pen"].value_counts().to_dict() if not df_sapi.empty and "Lokasi Pen" in df_sapi.columns else {}

                    rows_to_save = []
                    validation_errors = []

                    for idx, r in df_upload.iterrows():
                        no_baris = idx + 2
                        
                        kode_t = str(r.get("Kode Tiba / No Batch", "")).strip()
                        rfid_a = str(r.get("RFID Asal", "-")).strip()
                        rfid_k = str(r.get("RFID Kandang", "-")).strip()
                        jenis = str(r.get("Jenis Sapi", list_jenis_sapi[0])).strip()
                        jk = str(r.get("Jenis Kelamin", "Jantan")).strip()
                        
                        try: umur = int(r.get("Umur Masuk (Bulan)", 12))
                        except: umur = 12
                        
                        asal = str(r.get("Asal Negara", "Lokal")).strip()
                        
                        tgl_m = str(r.get("Tgl Masuk (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))).strip()
                        if len(tgl_m) > 10: tgl_m = tgl_m[:10]
                        
                        try: bobot = float(r.get("Bobot Awal (kg)", 300.0))
                        except: bobot = 300.0
                        
                        blok_k = str(r.get("Blok Kandang", "")).strip()
                        pen_k = str(r.get("Nomor Pen", "-")).strip()
                        
                        err_msg = []
                        lokasi_f = "-"

                        if not kode_t or kode_t == "nan":
                            err_msg.append("Kode Tiba kosong")

                        if rfid_k != "-" and rfid_k.lower() in rfid_eksis:
                            err_msg.append(f"RFID Kandang '{rfid_k}' sudah terdaftar")

                        if blok_k not in struktur_kandang:
                            err_msg.append(f"Blok Kandang '{blok_k}' tidak ditemukan di master")
                        else:
                            # --- FITUR AUTO-PILOT PEMBAGIAN PEN ---
                            if pen_k in ["-", "nan", "None", "", "Otomatis"]:
                                pen_terpilih = None
                                list_pen_di_blok = struktur_kandang.get(blok_k, [])
                                
                                for p_cand in list_pen_di_blok:
                                    cand_full = f"{blok_k} - {p_cand}"
                                    isi_cand = pen_counts.get(cand_full, 0)
                                    if isi_cand < 25:
                                        pen_terpilih = p_cand
                                        lokasi_f = cand_full
                                        pen_counts[cand_full] = isi_cand + 1
                                        break
                                
                                if not pen_terpilih:
                                    err_msg.append(f"Semua Pen di '{blok_k}' sudah penuh (Maksimal 25 ekor per Pen)")
                            else:
                                # Input Pen secara manual dari Excel
                                lokasi_f = f"{blok_k} - {pen_k}"
                                if pen_k not in struktur_kandang.get(blok_k, []):
                                    err_msg.append(f"Nomor Pen '{pen_k}' tidak ada di {blok_k}")
                                else:
                                    isi_pen = pen_counts.get(lokasi_f, 0)
                                    if isi_pen >= 25:
                                        err_msg.append(f"Pen '{lokasi_f}' sudah penuh (25 ekor)")
                                    else:
                                        pen_counts[lokasi_f] = isi_pen + 1

                        status_str = "✅ SIAP SIMPAN" if not err_msg else f"❌ ERROR: {', '.join(err_msg)}"
                        
                        if err_msg:
                            validation_errors.append(f"Baris #{no_baris}: {', '.join(err_msg)}")

                        rows_to_save.append({
                            "Kode Sapi": kode_t if kode_t != "nan" else "-",
                            "RFID/Tag Asal": rfid_a if rfid_a != "nan" else "-",
                            "RFID/Tag": rfid_k if rfid_k != "nan" else "-",
                            "Jenis Sapi": jenis,
                            "Jenis Kelamin": jk,
                            "Umur Masuk (Bulan)": umur,
                            "Asal Negara": asal,
                            "Tgl Masuk": tgl_m,
                            "Bobot Awal (kg)": bobot,
                            "Tgl Cek Akhir": tgl_m,
                            "Bobot Akhir (kg)": bobot,
                            "ADG (kg/hari)": 0.0,
                            "Total Pakan (kg)": 0.0,
                            "Tgl Pakan Terakhir": "-",
                            "Lokasi Pen": lokasi_f,
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
                        if st.button(f"🚀 Simpan {len(df_valid_only)} Sapi Valid ke Database", type="primary", use_container_width=True):
                            with st.spinner("💾 Mengunggah data registrasi masal ke database Supabase..."):
                                df_baru_total = pd.concat([df_sapi, df_valid_only], ignore_index=True)
                                save_data(df_baru_total)
                                add_activity_log(user_name, "Registrasi Batch Excel", f"Mengunggah {len(df_valid_only)} ekor sapi baru via Excel")
                            st.success(f"🎉 Berhasil mendaftarkan **{len(df_valid_only)} ekor sapi baru** sekaligus!")
                            st.balloons()
                            st.rerun()
                    else:
                        st.error("Tidak ada baris data yang valid untuk disimpan.")

                except Exception as e:
                    st.error(f"❌ Gagal membaca file Excel. Pastikan menggunakan template resmi! Detail Error: {e}")

    # ==================== TAB 2: EDIT / HAPUS ====================
    with tab_edit_hapus:
        st.markdown("### ⚙️ Panel Koreksi Data Registrasi")
        
        if df_sapi.empty:
            st.info("Belum ada data sapi aktif di database untuk diedit.")
            return

        opsi_sapi = df_sapi.apply(lambda r: f"No. {r.name + 1} | Kelompok: {r['Kode Sapi']} | RFID: {r['RFID/Tag']} | Pen: {r['Lokasi Pen']}", axis=1).tolist()
        sapi_terpilih = st.selectbox("Pilih Sapi Yang Akan Di-Koreksi/Hapus:", opsi_sapi)
        
        idx_target = opsi_sapi.index(sapi_terpilih)
        row_sapi = df_sapi.iloc[idx_target]

        sub_tab_edit, sub_tab_hapus = st.tabs(["📝 Edit Data Sapi", "🗑️ Hapus Sapi"])
        is_admin = str(user_role).lower() == "admin"

        # --- SUB-TAB: EDIT DATA ---
        with sub_tab_edit:
            with st.form("form_edit_registrasi"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_kode_tiba = st.text_input("Kode Tiba / No. Batch", value=str(row_sapi["Kode Sapi"])).strip()
                    e_rfid_asal = st.text_input("RFID / Tag Asal", value=str(row_sapi.get("RFID/Tag Asal", "-"))).strip()
                    e_rfid_kandang = st.text_input("RFID / Tag Kandang", value=str(row_sapi["RFID/Tag"])).strip()
                    e_jenis = st.selectbox("Jenis Sapi", list_jenis_sapi, index=list_jenis_sapi.index(row_sapi["Jenis Sapi"]) if row_sapi["Jenis Sapi"] in list_jenis_sapi else 0)
                with col_e2:
                    e_jk = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"], index=0 if row_sapi["Jenis Kelamin"] == "Jantan" else 1)
                    e_umur = st.number_input("Estimasi Umur (Bulan)", min_value=1, value=int(row_sapi.get("Umur Masuk (Bulan)", 12)))
                    e_asal = st.text_input("Asal Negara", value=str(row_sapi["Asal Negara"])).strip()
                    e_bobot = st.number_input("Bobot Awal Masuk (kg)", value=float(row_sapi["Bobot Awal (kg)"]))

                st.markdown("---")
                
                password_edit = ""
                if not is_admin:
                    password_edit = st.text_input("🔐 Operator wajib memasukkan Password Admin untuk menyimpan:", type="password", help="Minta bantuan admin untuk memasukkan password konfirmasi")

                btn_simpan_edit = st.form_submit_button("Simpan Perubahan Data", type="primary", use_container_width=True)
                
                if btn_simpan_edit:
                    if not is_admin and password_edit != "admin123":
                        st.error("❌ Gagal Simpan! Password Admin salah atau belum diisi.")
                    else:
                        df_sapi.at[idx_target, "Kode Sapi"] = e_kode_tiba
                        df_sapi.at[idx_target, "RFID/Tag Asal"] = e_rfid_asal
                        df_sapi.at[idx_target, "RFID/Tag"] = e_rfid_kandang
                        df_sapi.at[idx_target, "Jenis Sapi"] = e_jenis
                        df_sapi.at[idx_target, "Jenis Kelamin"] = e_jk
                        df_sapi.at[idx_target, "Umur Masuk (Bulan)"] = e_umur
                        df_sapi.at[idx_target, "Asal Negara"] = e_asal
                        df_sapi.at[idx_target, "Bobot Awal (kg)"] = e_bobot
                        
                        save_data(df_sapi)
                        add_activity_log(user_name, "Edit Registrasi", f"Mengubah data sapi baris {idx_target + 1} oleh {user_name}")
                        st.success("🎉 Sukses memperbarui data registrasi!")
                        st.rerun()

        # --- SUB-TAB: HAPUS DATA ---
        with sub_tab_hapus:
            st.markdown(f"🚨 **Perhatian:** Tindakan ini akan menghapus data sapi kelompok **{row_sapi['Kode Sapi']}** pada baris ke-{idx_target + 1} secara permanen.")
            konfirmasi_hapus = st.checkbox("Saya benar-benar ingin menghapus data sapi ini.")
            
            password_hapus = ""
            if not is_admin and konfirmasi_hapus:
                password_hapus = st.text_input("🔐 Operator wajib memasukkan Password Admin untuk menghapus:", type="password", key="pwd_hapus")

            if st.button("🗑️ Hapus Sapi Secara Permanen", type="primary", disabled=not konfirmasi_hapus, use_container_width=True):
                if not is_admin and password_hapus != "admin123":
                    st.error("❌ Gagal Hapus! Password Admin salah atau belum diisi.")
                else:
                    df_sapi = df_sapi.drop(index=idx_target).reset_index(drop=True)
                    save_data(df_sapi)
                    add_activity_log(user_name, "Hapus Registrasi", f"Menghapus sapi baris {idx_target + 1} dari Kelompok {row_sapi['Kode Sapi']}")
                    st.success("💥 Data berhasil dihapus dari database!")
                    st.rerun()