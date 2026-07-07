import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

def tampilkan_menu_pen_mutasi(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, user_role, calculate_adg, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🏠 Manajemen Blok Kandang & Mutasi Pen Sapi")
    st.markdown("Kelola perpindahan lokasi sapi antar Blok Kandang dan Pen secara terstruktur sesuai fase pemeliharaan.")

    zona_wib = timezone(timedelta(hours=7))
    tgl_hari_ini = datetime.now(zona_wib).strftime("%Y-%m-%d")

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi aktif di dalam kandang. Silakan lakukan Registrasi Sapi Baru terlebih dahulu.")
        return

    struktur_kandang = {}
    for item in DAFTAR_PEN:
        if " - " in item:
            blok, pen = item.split(" - ", 1)
            if blok not in struktur_kandang:
                struktur_kandang[blok] = []
            struktur_kandang[blok].append(pen)
        else:
            if "Lainnya" not in struktur_kandang:
                struktur_kandang["Lainnya"] = []
            struktur_kandang["Lainnya"].append(item)

    if user_role == "Admin":
        tab_status, tab_mutasi, tab_pengaturan = st.tabs([
            "📊 Sebaran Populasi per Blok & Pen", 
            "🔄 Jalankan Mutasi Sapi", 
            "🛠️ Kelola Blok & Pen Baru"
        ])
    else:
        tab_status, tab_mutasi = st.tabs([
            "📊 Sebaran Populasi per Blok & Pen", 
            "🔄 Jalankan Mutasi Sapi"
        ])

    # ==================== TAB 1: SEBARAN POPULASI ====================
    with tab_status:
        # --- TAMBAHAN FITUR: PENCARIAN RIWAYAT SAPI DI TAB MUTASI ---
        with st.expander("🔍 Cari Profil & Riwayat Sapi Lengkap", expanded=False):
            opsi_cari_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
            sapi_dicari = st.selectbox("Pilih Sapi untuk melihat detail (Timbangan & Pakan):", ["-- Silakan Pilih Sapi --"] + opsi_cari_sapi, key="cari_mutasi")
            
            if sapi_dicari != "-- Silakan Pilih Sapi --":
                k_cari = sapi_dicari.split(" - RFID: ")[0]
                r_cari = sapi_dicari.split(" - RFID: ")[1]
                inf = df_sapi[(df_sapi["Kode Sapi"] == k_cari) & (df_sapi["RFID/Tag"] == r_cari)].iloc[0]
                
                st.info(f"**Posisi Saat Ini:** {inf['Lokasi Pen']} | **Bobot Terakhir:** {float(inf['Bobot Akhir (kg)']):.2f} kg | **Total Pakan Masuk:** {float(inf['Total Pakan (kg)']):.2f} kg")
                
                cc1, cc2 = st.columns(2)
                with cc1:
                    df_r_timbang = read_sheet_to_df("riwayat_timbangan", ["Tanggal Timbang", "Kode Sapi", "RFID/Tag", "Lokasi Pen", "Bobot (kg)", "ADG (kg/hari)", "Operator"])
                    df_r_timbang = df_r_timbang[(df_r_timbang["Kode Sapi"] == k_cari) & (df_r_timbang["RFID/Tag"] == r_cari)]
                    if not df_r_timbang.empty:
                        st.dataframe(df_r_timbang[["Tanggal Timbang", "Bobot (kg)", "ADG (kg/hari)"]].sort_values("Tanggal Timbang", ascending=False), hide_index=True, column_config={"Bobot (kg)": st.column_config.NumberColumn(format="%.2f"), "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")}, use_container_width=True)
                    else:
                        st.caption("Belum ada riwayat timbangan")
                with cc2:
                    df_r_pakan = read_sheet_to_df("pakan_harian", ["Tanggal", "Lokasi Pen", "Metode", "Target Spesifik", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"])
                    df_r_pakan_spesifik = df_r_pakan[(df_r_pakan["Metode"] == "Spesifik") & (df_r_pakan["Target Spesifik"] == f"{k_cari} - {r_cari}")]
                    if not df_r_pakan_spesifik.empty:
                        st.dataframe(df_r_pakan_spesifik[["Tanggal", "Jenis Pakan", "Jumlah Pakan (kg)"]].sort_values("Tanggal", ascending=False), hide_index=True, column_config={"Jumlah Pakan (kg)": st.column_config.NumberColumn(format="%.2f")}, use_container_width=True)
                    else:
                        st.caption("Belum ada riwayat pakan medis/individu.")

        st.markdown("---")
        st.markdown("### 🏬 Peta Distribusi Sapi Saat Ini")
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
                            st.markdown(f"🔹 **{pen}** ({len(sapi_di_pen)}/25 Ekor):")
                            df_tampil = sapi_di_pen[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Bobot Akhir (kg)", "ADG (kg/hari)", "Tgl Cek Akhir", "Tgl Masuk", "Lokasi Pen"]].reset_index(drop=True)
                            
                            styled_df = df_tampil.style.apply(highlight_sapi_pen, axis=1)
                            st.dataframe(
                                styled_df, 
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "Lokasi Pen": None, # Sembunyikan kolom
                                    "Bobot Akhir (kg)": st.column_config.NumberColumn(format="%.2f"),
                                    "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")
                                }
                            )
                        else:
                            st.markdown(f"⚪ *{pen}* : (Kosong)")

        sapi_format_lama = df_sapi.drop(index=sapi_terpetakan_idx, errors='ignore')
        if not sapi_format_lama.empty:
            st.markdown("---")
            with st.expander("⚠️ Data Pen Format Lama / Perlu Penyesuaian", expanded=True):
                st.warning("Sapi di bawah ini terdeteksi masih menggunakan format pen lama.")
                st.dataframe(sapi_format_lama[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Lokasi Pen", "Bobot Akhir (kg)"]].reset_index(drop=True), use_container_width=True)

    # ==================== TAB 2: EKSEKUSI MUTASI PEN ====================
    with tab_mutasi:
        st.markdown("### 🔄 Form Pemindahan (Mutasi) Pen Sapi")
        opsi_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - {r['RFID/Tag']} (Sekarang di: {r['Lokasi Pen']})", axis=1).tolist()
        if not opsi_sapi:
            st.info("Tidak ada data sapi untuk dimutasi.")
            return
            
        sapi_terpilih = st.selectbox("Pilih Sapi Yang Akan Dimutasi:", opsi_sapi)
        kode_sapi_asli = sapi_terpilih.split(" - ")[0]
        rfid_sapi_asli = sapi_terpilih.split(" (Sekarang di:")[0].split(" - ")[1]
        
        matched_rows = df_sapi[(df_sapi["Kode Sapi"] == kode_sapi_asli) & (df_sapi["RFID/Tag"] == rfid_sapi_asli)]
        if matched_rows.empty:
            st.error("⚠️ Data sapi tidak ditemukan di database master.")
            return
            
        sapi_row = matched_rows.iloc[0]
        st.info(f"📋 **Detail Sapi Terpilih:**\n* Kode Sapi: {sapi_row['Kode Sapi']} | RFID Baru: {sapi_row['RFID/Tag']}\n* Jenis: {sapi_row['Jenis Sapi']} | Bobot Terakhir: {float(sapi_row['Bobot Akhir (kg)']):.2f} kg\n* Lokasi Sekarang: **{sapi_row['Lokasi Pen']}**")
        
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
            sapi_di_pen_tujuan = len(df_sapi[df_sapi["Lokasi Pen"] == full_lokasi_tujuan])
            if sapi_di_pen_tujuan >= 25:
                pen_rekomendasi = [f"{b} - {p} (Isi: {len(df_sapi[df_sapi['Lokasi Pen'] == f'{b} - {p}'])}/25)" for b, pens in struktur_kandang.items() for p in pens if len(df_sapi[df_sapi["Lokasi Pen"] == f"{b} - {p}"]) < 25]
                st.error(f"❌ Mutasi Gagal! Pen **{full_lokasi_tujuan}** sudah penuh (Maksimal 25 ekor).")
                if pen_rekomendasi: st.info(f"💡 **Saran Pen Tujuan Lain:**\n* " + "\n* ".join(pen_rekomendasi[:5]))
                return

            lokasi_asal = sapi_row["Lokasi Pen"]
            mask = (df_sapi["Kode Sapi"] == kode_sapi_asli) & (df_sapi["RFID/Tag"] == rfid_sapi_asli)
            df_sapi.loc[mask, "Lokasi Pen"] = full_lokasi_tujuan
            save_data(df_sapi)
            
            add_activity_log(user_name, "Mutasi Kandang", f"Memindahkan Sapi {sapi_row['Kode Sapi']} dari [{lokasi_asal}] ke [{full_lokasi_tujuan}]")
            st.success(f"🎉 Sukses! Sapi {sapi_row['Kode Sapi']} berhasil dipindahkan menuju **{full_lokasi_tujuan}**.")
            st.rerun()

    # ==================== TAB 3: PENGATURAN BLOK & PEN (ADMIN ONLY) ====================
    if user_role == "Admin":
        with tab_pengaturan:
            st.markdown("### 🛠️ Tambah Blok & Pen Kandang Baru")
            df_pen_db = read_sheet_to_df("master_pen", ["Blok", "Pen"])
            blok_existing = sorted(df_pen_db["Blok"].dropna().unique().tolist()) if not df_pen_db.empty else []
            
            pilih_blok_input = st.selectbox("Pilih Opsi Kategori Blok Kandang:", ["+ Buat Blok Baru Baru"] + blok_existing)
            nama_blok = st.text_input("Masukkan Nama Blok Baru Anda:", placeholder="Contoh: Blok Penggemukan D").strip() if pilih_blok_input == "+ Buat Blok Baru Baru" else pilih_blok_input
            nama_pen = st.text_input("Masukkan Nama Pen Kandang Baru:", placeholder="Contoh: Pen D1").strip()
            
            if st.button("➕ Daftarkan Pen Baru Ke Google Sheets", type="primary"):
                if not nama_blok or not nama_pen:
                    st.error("⚠️ Nama Blok dan Nama Pen tidak diperbolehkan kosong!")
                elif not df_pen_db[(df_pen_db["Blok"].str.lower() == nama_blok.lower()) & (df_pen_db["Pen"].str.lower() == nama_pen.lower())].empty:
                    st.warning(f"⚠️ Pen '{nama_pen}' pada '{nama_blok}' sudah ada di database.")
                else:
                    df_pen_db = pd.concat([df_pen_db, pd.DataFrame([{"Blok": nama_blok, "Pen": nama_pen}])], ignore_index=True)
                    write_df_to_sheet("master_pen", df_pen_db, ["Blok", "Pen"])
                    add_activity_log(user_name, "Tambah Master Pen", f"Menambahkan Pen baru: {nama_blok} - {nama_pen}")
                    st.success(f"🎉 Sukses menambahkan pen kandang: **{nama_blok} - {nama_pen}**")
                    st.rerun()
                        
            st.markdown("---")
            st.markdown("### 🗑️ Hapus Pen Kandang")
            if not df_pen_db.empty:
                pen_dihapus = st.selectbox("Pilih Lokasi Pen yang Ingin Dihapus:", sorted(df_pen_db.apply(lambda r: f"{r['Blok']} - {r['Pen']}", axis=1).tolist()))
                
                if st.button("🗑️ Hapus Pen Terpilih", type="secondary"):
                    b_hapus, p_hapus = pen_dihapus.split(" - ", 1)
                    if not df_sapi[df_sapi["Lokasi Pen"] == pen_dihapus].empty:
                        st.error(f"❌ Tidak bisa menghapus! Masih ada sapi aktif di {pen_dihapus}. Mutasi sapinya terlebih dahulu.")
                    else:
                        df_pen_db = df_pen_db[~((df_pen_db["Blok"] == b_hapus) & (df_pen_db["Pen"] == p_hapus))]
                        write_df_to_sheet("master_pen", df_pen_db, ["Blok", "Pen"])
                        add_activity_log(user_name, "Hapus Master Pen", f"Menghapus Pen: {pen_dihapus}")
                        st.success(f"🗑️ Lokasi Pen **{pen_dihapus}** sukses dihapus dari database.")
                        st.rerun()