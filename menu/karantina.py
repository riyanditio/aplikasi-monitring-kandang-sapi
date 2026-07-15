import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_karantina(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, user_role, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🏥 Manajemen Karantina & Rekam Medis")
    st.markdown("Fokus pemantauan intensif, pemberian obat/vaksin, dan evaluasi *biosecurity* sapi sebelum masuk masa penggemukan utama.")

    # Skema kolom untuk database rekam medis
    COLS_MEDIS = ["Tanggal", "Kode Sapi", "RFID/Tag", "Suhu Tubuh (°C)", "Kondisi Klinis", "Tindakan Medis", "Catatan", "Operator"]

    # Hanya menyaring sapi yang lokasinya mengandung kata "Karantina" atau "Isolasi"
    mask_karantina = df_sapi["Lokasi Pen"].str.contains("Karantina|Isolasi", case=False, na=False)
    df_sapi_karantina = df_sapi[mask_karantina]

    # Ambil struktur pen khusus Karantina & Isolasi
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
                 
                with st.expander(f"📂 {blok.upper()} (Total: {total_sapi_blok} Ekor)", expanded=True):
                    if total_sapi_blok == 0:
                        st.caption("ℹ️ Blok kandang ini masih kosong.")
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
        st.markdown("### 📝 Input Hasil Observasi & Penanganan Medis")
        
        if df_sapi_karantina.empty:
            st.info("ℹ️ Saat ini tidak ada sapi yang berada di pen Karantina atau Isolasi.")
        else:
            opsi_sapi = df_sapi_karantina.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']} (di {r['Lokasi Pen']})", axis=1).tolist()
            sapi_terpilih = st.selectbox("Pilih Sapi Target:", opsi_sapi)
            
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
                        kode_asli = sapi_terpilih.split(" - RFID: ")[0]
                        rfid_asli = sapi_terpilih.split(" - RFID: ")[1].split(" (di ")[0]
                        
                        row_medis = {
                            "Tanggal": tgl_medis.strftime("%Y-%m-%d"),
                            "Kode Sapi": kode_asli,
                            "RFID/Tag": rfid_asli,
                            "Suhu Tubuh (°C)": float(suhu),
                            "Kondisi Klinis": kondisi,
                            "Tindakan Medis": ", ".join(tindakan),
                            "Catatan": catatan if catatan else "-",
                            "Operator": user_name
                        }
                        
                        with st.spinner("⏳ Mengamankan data rekam medis ke database..."):
                            # [OPTIMASI 1]: Ambil riwayat medis HANYA saat tombol Simpan diklik
                            df_medis = read_sheet_to_df("riwayat_medis_karantina", COLS_MEDIS)
                            df_medis = pd.concat([df_medis, pd.DataFrame([row_medis])], ignore_index=True)
                            write_df_to_sheet("riwayat_medis_karantina", df_medis, COLS_MEDIS)
                        
                        add_activity_log(user_name, "Rekam Medis", f"Input kondisi {kondisi} & tindakan {row_medis['Tindakan Medis']} untuk sapi {kode_asli}")
                        st.success(f"✅ Rekam medis untuk sapi {kode_asli} berhasil disimpan.")
                        st.rerun()

    # ==================== TAB 2: MUTASI LULUS KARANTINA ====================
    with tab2:
        st.markdown("### 🚪 Rilis Sapi ke Pen Penggemukan")
        st.markdown("Gunakan menu ini jika masa observasi karantina sudah selesai dan sapi siap digemukkan.")
        
        if df_sapi_karantina.empty:
            st.info("ℹ️ Tidak ada sapi di Pen Karantina yang siap di-mutasi.")
        else:
            opsi_mutasi = df_sapi_karantina.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']} (Lokasi: {r['Lokasi Pen']})", axis=1).tolist()
            sapi_mutasi = st.selectbox("Pilih Sapi yang Lulus Karantina:", opsi_mutasi)
            
            kode_m = sapi_mutasi.split(" - RFID: ")[0]
            rfid_m = sapi_mutasi.split(" - RFID: ")[1].split(" (Lokasi:")[0]
            lokasi_awal = sapi_mutasi.split("(Lokasi: ")[1].replace(")", "")
            
            st.markdown("#### 🎯 Pilih Pen Penggemukan Tujuan")
            c_mut1, c_mut2 = st.columns(2)
            with c_mut1:
                blok_tujuan = st.selectbox("Blok Penggemukan:", [b for b in STRUKTUR_KANDANG.keys() if "karantina" not in b.lower() and "isolasi" not in b.lower()])
            with c_mut2:
                pen_tujuan = st.selectbox("Pen Tujuan:", STRUKTUR_KANDANG.get(blok_tujuan, [])) if blok_tujuan else None
                
            full_tujuan = f"{blok_tujuan} - {pen_tujuan}"
            
            if st.button("🚀 Mutasikan Keluar Karantina", type="primary", use_container_width=True):
                sapi_di_pen_tujuan = len(df_sapi[df_sapi["Lokasi Pen"] == full_tujuan])
                if sapi_di_pen_tujuan >= 25:
                    st.error(f"❌ Pen **{full_tujuan}** sudah penuh (Maks 25 ekor). Silakan pilih pen lain.")
                else:
                    mask = (df_sapi["Kode Sapi"] == kode_m) & (df_sapi["RFID/Tag"] == rfid_m)
                    df_sapi.loc[mask, "Lokasi Pen"] = full_tujuan
                    save_data(df_sapi)
                    
                    add_activity_log(user_name, "Lulus Karantina", f"Sapi {kode_m} lulus karantina. Pindah dari {lokasi_awal} ke {full_tujuan}")
                    st.success(f"🎉 Selamat! Sapi {kode_m} telah resmi lulus fase karantina dan dipindahkan ke {full_tujuan}.")
                    st.balloons()
                    st.rerun()

    # ==================== TAB 3: EDIT / HAPUS (OTORISASI) ====================
    with tab3:
        st.markdown("### ⚙️ Koreksi Rekam Medis")
        is_admin = str(user_role).lower() == "admin"
        
        # [OPTIMASI 2]: Ambil riwayat medis HANYA jika tab Edit/Hapus dibuka
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
        
        # [OPTIMASI 3]: Ambil riwayat medis HANYA jika tab Riwayat dibuka
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