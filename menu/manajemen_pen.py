import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

def tampilkan_menu_pen_mutasi(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, user_role, calculate_adg, save_data, add_activity_log, user_name):
    st.subheader("🏠 Manajemen Blok Kandang & Mutasi Pen Sapi")
    st.markdown("Kelola perpindahan lokasi sapi antar Blok Kandang dan Pen secara terstruktur sesuai fase pemeliharaan.")

    # Ambil tanggal hari ini (WIB)
    zona_wib = timezone(timedelta(hours=7))
    tgl_hari_ini = datetime.now(zona_wib).strftime("%Y-%m-%d")

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi aktif di dalam kandang. Silakan lakukan Registrasi Sapi Baru terlebih dahulu.")
        return

    # --- REKONSTRUKSI STRUKTUR HIRARKI DARI DAFTAR_PEN ---
    struktur_kandang = {}
    for item in DAFTAR_PEN:
        if " - " in item:
            blok, pen = item.split(" - ", 1)
            if blok not in struktur_kandang:
                struktur_kandang[blok] = []
            struktur_kandang[blok].append(pen)
        else:
            if "Lainnya" not in struktur_kandang:
                struktur_kandang["Lainnya"] = []  # FIX TYPO VS CODE: shortcut_kandang diganti menjadi struktur_kandang
            struktur_kandang["Lainnya"].append(item)

    # Pemisahan Halaman Menjadi 2 Tab Utama
    tab_status, tab_mutasi = st.tabs(["📊 Sebaran Populasi per Blok & Pen", "🔄 Jalankan Mutasi Sapi"])

    # ==================== TAB 1: SEBARAN POPULASI ====================
    with tab_status:
        st.markdown("### 🏬 Peta Distribusi Sapi Saat Ini")
        
        sapi_terpetakan_idx = []
        for blok, pens in struktur_kandang.items():
            sapi_di_blok = df_sapi[df_sapi["Lokasi Pen"].str.startswith(blok, na=False)]
            total_sapi_blok = len(sapi_di_blok)
            sapi_terpetakan_idx.extend(sapi_di_blok.index.tolist())
            
            with st.expander(f"📂 {blok.upper()} (Total: {total_sapi_blok} Ekor)", expanded=True):
                if total_sapi_blok == 0:
                    st.caption("ℹ️ Blok kandang ini masih kosong.")
                else:
                    for pen in pens:
                        full_name_pen = f"{blok} - {pen}"
                        sapi_di_pen = df_sapi[df_sapi["Lokasi Pen"] == full_name_pen]
                        
                        if not sapi_di_pen.empty:
                            st.markdown(f"🔹 **{pen}** ({len(sapi_di_pen)} Ekor):")
                            # --- INTEGRASI: Menampilkan RFID/Tag Asal di Dataframe Map Pen ---
                            df_tampil = sapi_di_pen[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Bobot Akhir (kg)", "Tgl Masuk"]].reset_index(drop=True)
                            st.dataframe(df_tampil, use_container_width=True)
                        else:
                            st.markdown(f"⚪ *{pen}* : (Kosong)")

        # ANTISIPASI DATA FORMAT LAMA (BACKWARD COMPATIBILITY)
        sapi_format_lama = df_sapi.drop(index=sapi_terpetakan_idx, errors='ignore')
        if not sapi_format_lama.empty:
            st.markdown("---")
            with st.expander("⚠️ Data Pen Format Lama / Perlu Penyesuaian", expanded=True):
                st.warning("Sapi di bawah ini terdeteksi masih menggunakan format pen lama. Segera lakukan mutasi pen ke struktur blok yang baru di Tab sebelah.")
                # --- INTEGRASI: Menampilkan RFID/Tag Asal di Format Lama ---
                st.dataframe(sapi_format_lama[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Lokasi Pen", "Bobot Akhir (kg)"]].reset_index(drop=True), use_container_width=True)

    # ==================== TAB 2: EKSEKUSI MUTASI PEN ====================
    with tab_mutasi:
        st.markdown("### 🔄 Form Pemindahan (Mutasi) Pen Sapi")
        
        opsi_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - {r['RFID/Tag']} (Sekarang di: {r['Lokasi Pen']})", axis=1).tolist()
        sapi_terpilih = st.selectbox("Pilih Sapi Yang Akan Dimutasi:", opsi_sapi)
        
        # FIX JAMINAN SINKRON: Pecah string opsi untuk mengambil Kode Sapi DAN RFID secara spesifik
        bagian_depan = sapi_terpilih.split(" (Sekarang di:")[0]
        kode_sapi_asli = bagian_depan.split(" - ")[0]
        rfid_sapi_asli = bagian_depan.split(" - ")[1]
        
        # FIX ABSOLUT: Proteksi baris data menggunakan kombinasi .iloc[0] agar tidak salah sasaran karena bug indeks duplikat
        matched_rows = df_sapi[(df_sapi["Kode Sapi"] == kode_sapi_asli) & (df_sapi["RFID/Tag"] == rfid_sapi_asli)]
        if matched_rows.empty:
            st.error("⚠️ Data sapi tidak ditemukan di database master.")
            return
        sapi_row = matched_rows.iloc[0]
        
        # --- INTEGRASI: Tampilkan info RFID/Tag Asal di lembar info mutasi ---
        st.info(f"📋 **Detail Sapi Terpilih:**\n* Kode Sapi: {sapi_row['Kode Sapi']} | RFID Asal: {sapi_row.get('RFID/Tag Asal', '-')}\n* RFID Baru: {sapi_row['RFID/Tag']} | Jenis: {sapi_row['Jenis Sapi']} | Bobot Terakhir: {sapi_row['Bobot Akhir (kg)']} kg\n* Lokasi Sekarang: **{sapi_row['Lokasi Pen']}**")
        
        st.markdown("#### 🎯 Tentukan Tujuan Perpindahan Baru")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            pilihan_blok_tujuan = st.selectbox("Pilih Blok Kandang Tujuan:", list(struktur_kandang.keys()))
        with col_m2:
            pilihan_pen_tujuan = st.selectbox("Pilih Pen Tujuan:", struktur_kandang[pilihan_blok_tujuan])
            
        full_lokasi_tujuan = f"{pilihan_blok_tujuan} - {pilihan_pen_tujuan}"
        
        if full_lokasi_tujuan == sapi_row["Lokasi Pen"]:
            st.warning(f"⚠️ Sapi saat ini sudah berada di {full_lokasi_tujuan}. Silakan ganti lokasi tujuan yang berbeda.")
            tombol_siap = False
        else:
            tombol_siap = True
            
        if st.button("🚀 Eksekusi Pemindahan Sapi", type="primary", use_container_width=True, disabled=not tombol_siap):
            lokasi_asal = sapi_row["Lokasi Pen"]
            
            # FIX ABSOLUT: Gunakan Boolean Mask (.loc[mask]) untuk mengunci baris mutasi secara rigid dan akurat
            mask = (df_sapi["Kode Sapi"] == kode_sapi_asli) & (df_sapi["RFID/Tag"] == rfid_sapi_asli)
            df_sapi.loc[mask, "Lokasi Pen"] = full_lokasi_tujuan
            save_data(df_sapi)
            
            detail_aksi = f"Memindahkan Sapi Kode {sapi_row['Kode Sapi']} (RFID Baru: {sapi_row['RFID/Tag']} | RFID Asal: {sapi_row.get('RFID/Tag Asal', '-')}) dari [{lokasi_asal}] ke [{full_lokasi_tujuan}]"
            add_activity_log(user_name, "Mutasi Kandang", detail_aksi)
            
            st.success(f"🎉 Sukses! Sapi {sapi_row['Kode Sapi']} berhasil dipindahkan menuju **{full_lokasi_tujuan}**.")
            st.rerun()