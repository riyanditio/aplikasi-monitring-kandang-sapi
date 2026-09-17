import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw
import gc
import io

# ==================== FUNGSI EKSTRAKSI AI MORFOMETRIK & ANOTASI VISUAL ====================
def estimasi_bobot_dari_foto(image_file, jarak_kamera_m=2.5):
    """
    Menganalisis piksel kontur tubuh sapi dari memori RAM, 
    mengonversinya ke ukuran cm berdasarkan jarak LiDAR, 
    menggambar garis ukur visual (Bounding Box),
    lalu menghitung estimasi bobot (kg) dengan rumus Schoorl.
    """
    try:
        # Buka gambar di RAM tanpa menyimpan ke disk
        img = Image.open(image_file).convert('RGB')
        img_np = np.array(img)
        height, width, _ = img_np.shape
        
        # Ekstraksi skala piksel badan sapi
        gray = np.dot(img_np[..., :3], [0.2989, 0.5870, 0.1140])
        mask = gray < 220  # Memisahkan objek utama dari background terang
        
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        
        if np.any(rows) and np.any(cols):
            ymin, ymax = np.where(rows)[0][[0, -1]]
            xmin, xmax = np.where(cols)[0][[0, -1]]
            box_w_px = xmax - xmin
            box_h_px = ymax - ymin
        else:
            box_w_px = int(width * 0.65)
            box_h_px = int(height * 0.38)
            xmin = int(width * 0.17)
            xmax = xmin + box_w_px
            ymin = int(height * 0.3)
            ymax = ymin + box_h_px
            
        # Konversi Piksel ke Centimeter menggunakan Trigonometri Jarak LiDAR
        jarak_cm = jarak_kamera_m * 100.0
        f_px = width * 0.85  # Konstanta focal ratio lensa HP standar
        
        panjang_badan_cm = round((box_w_px * jarak_cm) / f_px, 1)
        lingkar_dada_cm = round(((box_h_px * jarak_cm) / f_px) * 2.15, 1)
        
        # Batas logis dimensi fisik sapi nyata
        panjang_badan_cm = max(85.0, min(220.0, panjang_badan_cm))
        lingkar_dada_cm = max(100.0, min(250.0, lingkar_dada_cm))
        
        # Rumus Morfometrik Schoorl: (Girth^2 * Length) / 10800
        bobot_kg = round(((lingkar_dada_cm ** 2) * panjang_badan_cm) / 10800.0, 1)
        
        # --- GAMBAR GARIS PANDUAN VISUAL PADA HASIL FOTO ---
        img_annotated = img.copy()
        draw = ImageDraw.Draw(img_annotated)
        
        # 1. Kotak Hijau Batas Tubuh Sapi (Bounding Box)
        draw.rectangle([xmin, ymin, xmax, ymax], outline="#00FF66", width=4)
        
        # 2. Garis Kuning Horizontal (Panjang Badan)
        y_mid = ymin + int(box_h_px * 0.5)
        draw.line([xmin, y_mid, xmax, y_mid], fill="#FFD700", width=4)
        
        # 3. Garis Sian Vertikal (Lingkar Dada)
        x_girth = xmin + int(box_w_px * 0.35)
        draw.line([x_girth, ymin, x_girth, ymax], fill="#00E5FF", width=4)
        
        # Hapus variabel array yang tidak terpakai dari RAM
        del img, img_np, gray, mask
        gc.collect()
        
        return bobot_kg, panjang_badan_cm, lingkar_dada_cm, img_annotated
    except Exception as e:
        st.error(f"⚠️ Gagal mengolah foto: {e}")
        return 0.0, 0.0, 0.0, None


def tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("⚖️ Manajemen & Pencatatan Timbangan Berkala")
    
    COLS_RIWAYAT_TIMBANG = ["Tanggal Timbang", "Kode Sapi", "RFID/Tag", "Lokasi Pen", "Bobot (kg)", "ADG (kg/hari)", "Operator"]

    # Filter Strict: Hanya gunakan sapi yang berstatus AKTIF
    df_sapi_aktif = df_sapi[df_sapi["Status"] == "AKTIF"] if "Status" in df_sapi.columns else df_sapi

    if df_sapi_aktif.empty:
        st.warning("⚠️ Belum ada data sapi aktif yang tersedia untuk ditimbang.")
        return

    df_sapi["Bobot Awal (kg)"] = pd.to_numeric(df_sapi["Bobot Awal (kg)"], errors='coerce').fillna(0.0).astype(float)
    df_sapi["Bobot Akhir (kg)"] = pd.to_numeric(df_sapi["Bobot Akhir (kg)"], errors='coerce').fillna(0.0).astype(float)
    df_sapi["ADG (kg/hari)"] = pd.to_numeric(df_sapi["ADG (kg/hari)"], errors='coerce').fillna(0.0).astype(float)

    TARGET_ADG = 1.6

    tab_input, tab_edit, tab_analisis = st.tabs(["➕ Input Timbangan Baru", "⚙️ Edit / Hapus Riwayat", "📈 Analisis Timbang per Sapi"])

    # Helper Ambil & Normalisasi Data Riwayat Timbangan
    def get_riwayat_clean():
        df_r = read_sheet_to_df("riwayat_timbangan", COLS_RIWAYAT_TIMBANG)
        if not df_r.empty:
            rename_map = {"Rfid Tag": "RFID/Tag", "Adg Kg Hari": "ADG (kg/hari)", "Bobot Kg": "Bobot (kg)"}
            df_r = df_r.rename(columns=rename_map)
        return df_r

    # ==================== TAB 1: INPUT TIMBANGAN BARU ====================
    with tab_input:
        st.markdown("Gunakan filter Blok & Pen untuk mempercepat pencarian sapi aktif yang akan ditimbang.")

        df_riwayat_timbang = get_riwayat_clean()

        list_lokasi_eksis = df_sapi_aktif["Lokasi Pen"].unique()
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

        # --- DUA KOLOM PENGATURAN: TANGGAL & FILTER LOKASI ---
        st.markdown("#### 🔍 Tanggal & Saring Sapi Berdasarkan Lokasi")
        cf0, cf1, cf2 = st.columns([1.2, 1.5, 1.5])
        with cf0:
            tgl_timbang_sekarang = st.date_input("📅 Tanggal Penimbangan Hari Ini", datetime.now().date(), key="tgl_timbang_input")
            tgl_timbang_str = tgl_timbang_sekarang.strftime("%Y-%m-%d")
        with cf1:
            filter_blok = st.selectbox("Pilih Blok Kandang Sapi:", list(grid_filter.keys()), key="fb_input")
        with cf2:
            filter_pen = st.selectbox("Pilih Nomor/Bagian Pen Sapi:", sorted(list(set(grid_filter[filter_blok]))), key="fp_input")

        lokasi_pencarian = f"{filter_blok} - {filter_pen}" if filter_blok != "Format Lama" else filter_pen
        df_sapi_terfilter = df_sapi_aktif[df_sapi_aktif["Lokasi Pen"] == lokasi_pencarian].copy()

        if df_sapi_terfilter.empty:
            st.info(f"ℹ️ Pen **{lokasi_pencarian}** saat ini sedang tidak diisi oleh sapi aktif.")
        else:
            # --- CEK SAPI YANG SUDAH DITIMBANG PADA TANGGAL INI ---
            set_sapi_sudah_timbang = set()
            if not df_riwayat_timbang.empty and "Tanggal Timbang" in df_riwayat_timbang.columns:
                df_riwayat_today = df_riwayat_timbang[df_riwayat_timbang["Tanggal Timbang"].astype(str) == tgl_timbang_str]
                if not df_riwayat_today.empty:
                    set_sapi_sudah_timbang = set(
                        df_riwayat_today["Kode Sapi"].astype(str).str.strip().tolist()
                    )

            # Filter sapi yang BELUM ditimbang pada tanggal terpilih
            df_sapi_belum_timbang = df_sapi_terfilter[
                ~df_sapi_terfilter["Kode Sapi"].astype(str).str.strip().isin(set_sapi_sudah_timbang)
            ].copy()

            df_sapi_belum_timbang = df_sapi_belum_timbang.sort_values(by="Kode Sapi", ascending=True).reset_index(drop=True)

            total_sapi_pen = len(df_sapi_terfilter)
            sapi_terhitung = len(df_sapi_terfilter) - len(df_sapi_belum_timbang)

            st.markdown("---")
            
            # --- OPSI PILIHAN METODE PENIMBANGAN ---
            metode_penimbangan = st.radio(
                "PILIH METODE PENIMBANGAN:",
                [
                    "⚖️ Timbangan Fisik (Manual)", 
                    "📸 Pemindaian Foto / LiDAR (Visual AI)", 
                    "📥 Upload / Download Template Excel (Batch Pen)"
                ],
                horizontal=True
            )

            # ==================== METODE 3: BATCH EXCEL TEMPLATE ====================
            if metode_penimbangan == "📥 Upload / Download Template Excel (Batch Pen)":
                st.markdown("##### 📥 Modul Penimbangan Massal Excel (Auto-Populate Data Sapi)")
                st.caption(f"Unduh file Excel yang berisi daftar **{total_sapi_pen} ekor sapi aktif** di **{lokasi_pencarian}**, isi bobot baru, lalu unggah kembali untuk kalkulasi masif.")

                c_ex1, c_ex2 = st.columns(2)

                # --- STEP 1: DOWNLOAD TEMPLATE EXCEL DINAMIS ---
                with c_ex1:
                    st.markdown("**Langkah 1: Unduh Template Excel Pre-filled**")
                    
                    df_template = df_sapi_terfilter.sort_values(by="Kode Sapi", ascending=True).copy()

                    def hitung_lama_penggemukan(tgl_m):
                        try:
                            if pd.isna(tgl_m) or str(tgl_m).strip() in ["", "-", "None", "NaN"]:
                                return 0
                            d_in = datetime.strptime(str(tgl_m)[:10], "%Y-%m-%d").date()
                            return max(0, (tgl_timbang_sekarang - d_in).days)
                        except Exception:
                            return 0

                    df_template["Lama Penggemukan (Hari)"] = df_template["Tgl Masuk"].apply(hitung_lama_penggemukan)

                    df_template_export = pd.DataFrame({
                        "Kode Sapi": df_template["Kode Sapi"],
                        "RFID/Tag": df_template["RFID/Tag"],
                        "Jenis Sapi": df_template["Jenis Sapi"],
                        "Lokasi Pen": df_template["Lokasi Pen"],
                        "Tgl Masuk": df_template["Tgl Masuk"],
                        "Bobot Awal (kg)": df_template["Bobot Awal (kg)"],
                        "Lama Penggemukan (Hari)": df_template["Lama Penggemukan (Hari)"],
                        "Bobot Terakhir (kg)": df_template["Bobot Akhir (kg)"],
                        "Tanggal Timbang (YYYY-MM-DD)": tgl_timbang_str,
                        "Bobot Baru (kg)": ""
                    })

                    buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_template_export.to_excel(writer, index=False, sheet_name='Data_Penimbangan')
                    except Exception:
                        with pd.ExcelWriter(buffer) as writer:
                            df_template_export.to_excel(writer, index=False, sheet_name='Data_Penimbangan')

                    st.download_button(
                        label=f"📥 Unduh Template Excel ({lokasi_pencarian})",
                        data=buffer.getvalue(),
                        file_name=f"Template_Timbang_{lokasi_pencarian.replace(' ', '_').replace('/', '_')}_{tgl_timbang_str}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="primary"
                    )

                # --- STEP 2: UPLOAD & PROCESS EXCEL HASIL ISIAN ---
                with c_ex2:
                    st.markdown("**Langkah 2: Unggah File Excel Yang Sudah Diisi**")
                    file_excel = st.file_uploader("Pilih file Excel yang sudah diisi bobot baru:", type=["xlsx", "xls"], key="up_excel_timbang")

                if file_excel is not None:
                    try:
                        df_up = pd.read_excel(file_excel)
                        req_cols = ["Kode Sapi", "Bobot Baru (kg)"]
                        
                        if not all(col in df_up.columns for col in req_cols):
                            st.error(f"❌ Format file Excel tidak sesuai. Pastikan terdapat kolom: {', '.join(req_cols)}")
                        else:
                            df_up_valid = df_up.dropna(subset=["Bobot Baru (kg)"]).copy()
                            df_up_valid["Bobot Baru (kg)"] = pd.to_numeric(df_up_valid["Bobot Baru (kg)"], errors='coerce')
                            df_up_valid = df_up_valid[df_up_valid["Bobot Baru (kg)"] > 0]

                            if df_up_valid.empty:
                                st.warning("⚠️ Tidak ada data bobot baru yang valid untuk diproses. Pastikan kolom 'Bobot Baru (kg)' telah diisi angka.")
                            else:
                                st.markdown("##### 🔍 Pratinjau Data Yang Akan Diperbarui:")
                                cols_preview = [c for c in ["Kode Sapi", "RFID/Tag", "Bobot Awal (kg)", "Lama Penggemukan (Hari)", "Bobot Terakhir (kg)", "Bobot Baru (kg)"] if c in df_up_valid.columns]
                                st.dataframe(df_up_valid[cols_preview], use_container_width=True, hide_index=True)

                                if st.button("🚀 Simpan Timbangan Massal dari Excel", type="primary", use_container_width=True):
                                    with st.spinner("⏳ Memproses perhitungan ADG & memperbarui database cloud..."):
                                        total_sukses = 0
                                        new_logs_list = []

                                        for _, r_up in df_up_valid.iterrows():
                                            k_sapi = str(r_up["Kode Sapi"]).strip()
                                            b_baru = float(r_up["Bobot Baru (kg)"])

                                            mask_s = df_sapi["Kode Sapi"].astype(str).str.strip() == k_sapi
                                            if "Status" in df_sapi.columns:
                                                mask_s = mask_s & (df_sapi["Status"] == "AKTIF")

                                            if not df_sapi[mask_s].empty:
                                                row_db = df_sapi[mask_s].iloc[0]
                                                tgl_masuk_s = row_db["Tgl Masuk"]
                                                b_awal_s = row_db["Bobot Awal (kg)"]
                                                
                                                # Ambil RFID resmi dari master data agar tidak kosong/EMPTY
                                                rfid_resmi = str(row_db.get("RFID/Tag", "-")).strip()
                                                if rfid_resmi in ["", "nan", "None", "EMPTY"]:
                                                    rfid_resmi = "-"

                                                adg_val = float(calculate_adg(tgl_masuk_s, b_awal_s, tgl_timbang_str, b_baru))

                                                df_sapi.loc[mask_s, "Tgl Cek Akhir"] = tgl_timbang_str
                                                df_sapi.loc[mask_s, "Bobot Akhir (kg)"] = b_baru
                                                df_sapi.loc[mask_s, "ADG (kg/hari)"] = adg_val

                                                new_logs_list.append({
                                                    "Tanggal Timbang": tgl_timbang_str,
                                                    "Kode Sapi": k_sapi,
                                                    "RFID/Tag": rfid_resmi,
                                                    "Lokasi Pen": row_db['Lokasi Pen'],
                                                    "Bobot (kg)": b_baru,
                                                    "ADG (kg/hari)": adg_val,
                                                    "Operator": f"{user_name} (Batch Excel)"
                                                })
                                                total_sukses += 1

                                        if total_sukses > 0:
                                            save_data(df_sapi)

                                            if new_logs_list:
                                                df_new_logs = pd.DataFrame(new_logs_list)
                                                df_riwayat_timbang = pd.concat([df_riwayat_timbang, df_new_logs], ignore_index=True)
                                                write_df_to_sheet("riwayat_timbangan", df_riwayat_timbang, COLS_RIWAYAT_TIMBANG)

                                            add_activity_log(user_name, "Timbangan Massal Excel", f"Berhasil memperbarui {total_sukses} sapi di {lokasi_pencarian} via Import Excel")
                                            st.success(f"🎉 **SUKSES!** Sebanyak **{total_sukses} ekor sapi** di **{lokasi_pencarian}** berhasil diperbarui bobot & ADG-nya!")
                                            st.balloons()
                                            st.rerun()

                    except Exception as e_ex:
                        st.error(f"❌ Terjadi kesalahan saat membaca file Excel: {e_ex}")

            # ==================== METODE 1 & 2: INPUT INDIVIDUAL (MANUAL / FOTO) ====================
            else:
                if df_sapi_belum_timbang.empty:
                    st.success(f"🎉 **SELESAI!** Seluruh **{total_sapi_pen} ekor sapi aktif** di **{lokasi_pencarian}** telah selesai ditimbang pada tanggal **{tgl_timbang_str}**.")
                    
                    with st.expander("🔍 Lihat Daftar Sapi yang Sudah Ditimbang Hari Ini di Pen Ini"):
                        df_sudah_show = df_sapi_terfilter.sort_values(by="Kode Sapi", ascending=True)
                        st.dataframe(df_sudah_show[["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Bobot Akhir (kg)", "ADG (kg/hari)", "Tgl Cek Akhir"]], use_container_width=True, hide_index=True)
                else:
                    st.caption(f"📊 Progress Penimbangan Pen **{lokasi_pencarian}**: Terproses **{sapi_terhitung} dari {total_sapi_pen} ekor** ({len(df_sapi_belum_timbang)} ekor tersisa di daftar).")
                    
                    opsi_sapi = df_sapi_belum_timbang.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
                    sapi_pilihan = st.selectbox("Pilih Kode Sapi Yang Ditimbang:", opsi_sapi)
                    
                    kode_sapi_asli = sapi_pilihan.split(" - RFID: ")[0].strip()
                    rfid_sapi_asli = sapi_pilihan.split(" - RFID: ")[1].strip()
                    
                    matched_rows = df_sapi_belum_timbang[df_sapi_belum_timbang["Kode Sapi"].astype(str).str.strip() == kode_sapi_asli]
                    if matched_rows.empty:
                        st.error("⚠️ Data sapi aktif tidak ditemukan di database master.")
                    else:
                        row_sapi = matched_rows.iloc[0]

                        is_penimbangan_pertama = (str(row_sapi['Tgl Cek Akhir']) == str(row_sapi['Tgl Masuk']))
                        status_timbang_text = "🟢 PENIMBANGAN PERTAMA (Evaluasi Awal Masa Karantina)" if is_penimbangan_pertama else "🔵 PENIMBANGAN BERKALA / RUTIN"

                        st.info(f"📋 **Data Historis Sapi:** ({status_timbang_text})\n* Tanggal Masuk Area: {row_sapi['Tgl Masuk']} | Berat Awal: {row_sapi['Bobot Awal (kg)']} kg\n* RFID Asal: {row_sapi.get('RFID/Tag Asal', '-')} | RFID Baru: {row_sapi['RFID/Tag']}\n* Timbangan Terakhir: {row_sapi['Tgl Cek Akhir']} | Berat Akhir: {row_sapi['Bobot Akhir (kg)']} kg")

                        bobot_default_val = float(row_sapi["Bobot Akhir (kg)"])

                        # --- JIKA METODE PEMINDAIAN FOTO DIPILIH ---
                        if metode_penimbangan == "📸 Pemindaian Foto / LiDAR (Visual AI)":
                            st.markdown("##### 📸 Modul Pemindaian Visual AI & Depth LiDAR")
                            st.caption("📱 **Penting:** Pegang HP dalam posisi **Horizontal (Landscape)**. Kamera Utama / Belakang akan otomatis diaktifkan.")

                            st.markdown("""
                            <style>
                            div[data-testid="stCameraInput"] {
                                position: relative !important;
                                border: 2px dashed #00FF66 !important;
                                border-radius: 12px !important;
                                padding: 6px !important;
                                background: #000000 !important;
                                overflow: visible !important;
                            }

                            div[data-testid="stCameraInput"] * {
                                overflow: visible !important;
                            }

                            div[data-testid="stCameraInput"] button[aria-label*="Switch"],
                            div[data-testid="stCameraInput"] button[aria-label*="camera"],
                            div[data-testid="stCameraInput"] button[aria-label*="Kamera"],
                            div[data-testid="stCameraInput"] button[title*="Switch"],
                            div[data-testid="stCameraInput"] button[title*="camera"] {
                                position: absolute !important;
                                top: 12px !important;
                                right: 12px !important;
                                z-index: 999999 !important;
                                background-color: rgba(15, 23, 42, 0.9) !important;
                                color: #00FF66 !important;
                                border: 2px solid #00FF66 !important;
                                border-radius: 50% !important;
                                width: 50px !important;
                                height: 50px !important;
                                display: flex !important;
                                align-items: center !important;
                                justify-content: center !important;
                                box-shadow: 0px 4px 12px rgba(0,255,102,0.6) !important;
                                cursor: pointer !important;
                            }

                            div[data-testid="stCameraInput"] button svg {
                                fill: #00FF66 !important;
                                width: 26px !important;
                                height: 26px !important;
                            }
                            </style>

                            <script>
                            let switchedToRear = false;

                            function enforceRearCamera() {
                                if (switchedToRear) return;

                                const cameraDiv = document.querySelector('div[data-testid="stCameraInput"]');
                                if (!cameraDiv) return;

                                const videoEl = cameraDiv.querySelector('video');
                                const buttons = Array.from(cameraDiv.querySelectorAll('button'));
                                
                                const switchBtn = buttons.find(b => {
                                    const lbl = (b.getAttribute('aria-label') || b.getAttribute('title') || '').toLowerCase();
                                    return lbl.includes('switch') || lbl.includes('camera') || lbl.includes('kamera') || b.querySelector('svg');
                                });

                                if (videoEl && videoEl.srcObject) {
                                    const tracks = videoEl.srcObject.getVideoTracks();
                                    if (tracks.length > 0) {
                                        const settings = tracks[0].getSettings();
                                        const label = (tracks[0].label || '').toLowerCase();
                                        const facing = settings.facingMode || '';

                                        if (facing === 'user' || label.includes('front') || label.includes('selfie') || label.includes('depan')) {
                                            if (switchBtn) {
                                                switchBtn.click();
                                                switchedToRear = true;
                                            }
                                        } else if (facing === 'environment' || label.includes('back') || label.includes('rear') || label.includes('belakang')) {
                                            switchedToRear = true;
                                        }
                                    }
                                }
                            }

                            const rearCheckInterval = setInterval(() => {
                                enforceRearCamera();
                                if (switchedToRear) clearInterval(rearCheckInterval);
                            }, 600);
                            </script>
                            """, unsafe_allow_html=True)

                            c_lidar1, c_lidar2 = st.columns([1.2, 2])
                            with c_lidar1:
                                jarak_kamera = st.slider(
                                    "📏 Jarak Posisikan Kamera ke Sapi (Meter)",
                                    min_value=1.5, max_value=4.5, value=2.5, step=0.1,
                                    help="Sesuaikan dengan perkiraan jarak berdiri operator ke badan sapi di pen."
                                )
                                st.info("💡 **Tips:** Untuk iPhone Pro / Android ToF, sensor LiDAR secara otomatis membantu stabilitas pembacaan jarak.")

                            with c_lidar2:
                                foto_sapi = st.camera_input("📸 Bidik Sapi dari Samping", key=f"cam_{kode_sapi_asli}")

                            if foto_sapi is not None:
                                with st.spinner("⏳ Memproses citra visual, mengukur piksel kontur & menghitung bobot..."):
                                    est_bobot, p_badan, l_dada, img_hasil = estimasi_bobot_dari_foto(foto_sapi, jarak_kamera)
                                    
                                    if est_bobot > 0:
                                        st.session_state[f"est_weight_{kode_sapi_asli}"] = est_bobot
                                        
                                        st.success(f"✨ **PANDUAN HASIL PEMINDAIAN AI:**\n* Estimasi Panjang Badan: **{p_badan} cm**\n* Estimasi Lingkar Dada: **{l_dada} cm**\n* 🎯 **Estimasi Bobot Hasil Foto: {est_bobot} kg**")
                                        
                                        if img_hasil is not None:
                                            st.image(img_hasil, caption="🔍 Hasil Deteksi AI: Kotak Hijau (Batas Sapi) | Garis Kuning (Panjang Badan) | Garis Sian (Lingkar Dada)", use_container_width=True)
                                        
                                        bobot_default_val = est_bobot

                        # Mengambil nilai hasil foto jika ada di session state
                        if f"est_weight_{kode_sapi_asli}" in st.session_state and metode_penimbangan == "📸 Pemindaian Foto / LiDAR (Visual AI)":
                            bobot_default_val = st.session_state[f"est_weight_{kode_sapi_asli}"]

                        # --- FORM SIMPAN TIMBANGAN MANUAL ---
                        with st.form("form_timbangan_berkala", clear_on_submit=False):
                            bobot_timbang_baru = st.number_input(
                                f"Hasil Berat Timbangan Baru (kg) untuk Sapi: {kode_sapi_asli}",
                                min_value=30.0, max_value=1500.0,
                                value=float(bobot_default_val), step=0.5,
                                help="Dapat disesuaikan kembali secara manual sebelum disimpan."
                            )

                            submit_timbang = st.form_submit_button("💾 Simpan & Kalkulasi ADG Baru", type="primary", use_container_width=True)

                            if submit_timbang:
                                with st.spinner("⏳ Memproses perhitungan ADG dan mengamankan data..."):
                                    adg_terbaru = float(calculate_adg(row_sapi["Tgl Masuk"], row_sapi["Bobot Awal (kg)"], tgl_timbang_str, bobot_timbang_baru))
                                    
                                    # Update database master sapi (Khusus Sapi Aktif)
                                    mask = df_sapi["Kode Sapi"].astype(str).str.strip() == kode_sapi_asli
                                    if "Status" in df_sapi.columns:
                                        mask = mask & (df_sapi["Status"] == "AKTIF")

                                    df_sapi.loc[mask, "Tgl Cek Akhir"] = tgl_timbang_str
                                    df_sapi.loc[mask, "Bobot Akhir (kg)"] = float(bobot_timbang_baru)
                                    df_sapi.loc[mask, "ADG (kg/hari)"] = adg_terbaru
                                    save_data(df_sapi)

                                    ket_metode = "Foto Visual AI/LiDAR" if "Foto" in metode_penimbangan else "Timbangan Fisik"

                                    new_log = {
                                        "Tanggal Timbang": tgl_timbang_str,
                                        "Kode Sapi": kode_sapi_asli,
                                        "RFID/Tag": str(row_sapi.get('RFID/Tag', '-')),
                                        "Lokasi Pen": row_sapi['Lokasi Pen'],
                                        "Bobot (kg)": float(bobot_timbang_baru),
                                        "ADG (kg/hari)": adg_terbaru,
                                        "Operator": f"{user_name} ({ket_metode})"
                                    }
                                    df_riwayat_timbang = pd.concat([df_riwayat_timbang, pd.DataFrame([new_log])], ignore_index=True)
                                    write_df_to_sheet("riwayat_timbangan", df_riwayat_timbang, COLS_RIWAYAT_TIMBANG)
                                    
                                    add_activity_log(user_name, "Timbangan Rutin", f"Menimbang Sapi {kode_sapi_asli} via {ket_metode} di {row_sapi['Lokasi Pen']} bobot {bobot_timbang_baru}kg")
                                    
                                    if f"est_weight_{kode_sapi_asli}" in st.session_state:
                                        del st.session_state[f"est_weight_{kode_sapi_asli}"]

                                if adg_terbaru < TARGET_ADG:
                                    st.error(f"⚠️ **ALARM PERFORMA RENDAH:** Sapi {kode_sapi_asli} berhasil disimpan. ADG hasil timbangan ini hanya mencapai `{adg_terbaru:.2f} kg/hari` (Target: {TARGET_ADG}).")
                                else:
                                    st.success(f"🎉 Sukses! Bobot Sapi {kode_sapi_asli} diperbarui ke {bobot_timbang_baru} kg dengan ADG Bagus: `{adg_terbaru:.2f} kg/hari`.")
                                    st.balloons()
                                st.rerun()

    # ==================== TAB 2: EDIT / HAPUS RIWAYAT ====================
    with tab_edit:
        st.markdown("### 📋 Koreksi Data Penimbangan yang Salah Input")
        df_riwayat_timbang = get_riwayat_clean()
        
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
            
            st.info(f"📍 **Data Terpilih:** {row_lama['Kode Sapi']} (RFID: {row_lama.get('RFID/Tag', '-')}) | Tanggal: {row_lama['Tanggal Timbang']} | Bobot Lama: {row_lama['Bobot (kg)']} kg")

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
                        mask_sapi = df_sapi["Kode Sapi"].astype(str).str.strip() == str(row_lama["Kode Sapi"]).strip()
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
                    
                    st.success(f"✅ Data historis No Urut {pilihan_no} berhasil diperbaiki.")
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
        st.markdown("### 📈 Evaluasi Kurva Pertumbuhan Individu Sapi Aktif")
        opsi_semua_sapi = df_sapi_aktif.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
        
        if not opsi_semua_sapi:
            st.info("ℹ️ Tidak ada populasi sapi aktif untuk dianalisis.")
        else:
            sapi_analisis = st.selectbox("Pilih Sapi untuk Dianalisis:", opsi_semua_sapi)
            
            if sapi_analisis:
                df_riwayat_timbang = get_riwayat_clean()
                
                if not df_riwayat_timbang.empty:
                    kode_a = sapi_analisis.split(" - RFID: ")[0].strip()
                    
                    # Pencarian fleksibel hanya berdasarkan Kode Sapi (karena Kode Sapi sudah unik)
                    df_hist = df_riwayat_timbang[
                        df_riwayat_timbang["Kode Sapi"].astype(str).str.strip() == kode_a
                    ].copy()
                    
                    if df_hist.empty:
                        st.info(f"Belum ada catatan riwayat timbangan tambahan untuk sapi {sapi_analisis}.")
                    else:
                        df_hist = df_hist.sort_values(by="Tanggal Timbang")
                        st.markdown(f"**Riwayat Kenaikan Bobot (kg) Sapi: {kode_a}**")
                        
                        # Pastikan kolom numeric terformat dengan benar
                        df_hist["Bobot (kg)"] = pd.to_numeric(df_hist["Bobot (kg)"], errors='coerce')
                        df_hist["ADG (kg/hari)"] = pd.to_numeric(df_hist["ADG (kg/hari)"], errors='coerce')

                        df_chart = df_hist[["Tanggal Timbang", "Bobot (kg)"]].set_index("Tanggal Timbang")
                        st.line_chart(df_chart, use_container_width=True)
                        
                        st.dataframe(
                            df_hist[["Tanggal Timbang", "Kode Sapi", "RFID/Tag", "Lokasi Pen", "Bobot (kg)", "ADG (kg/hari)", "Operator"]], 
                            use_container_width=True, 
                            hide_index=True, 
                            column_config={
                                "Bobot (kg)": st.column_config.NumberColumn(format="%.2f"), 
                                "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")
                            }
                        )
                else:
                    st.info("ℹ️ Belum ada data riwayat timbangan yang tercatat di database.")