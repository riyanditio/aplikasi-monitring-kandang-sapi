import streamlit as st
import pandas as pd

def tampilkan_menu_manajemen_kelompok(df_sapi, DAFTAR_PEN, user_role, save_data, add_activity_log, user_name):
    st.subheader("👥 Manajemen Kelompok / Batch Sapi")
    st.markdown("Kelola data sapi secara massal berdasarkan Kelompok (Kode Tiba/Batch) untuk mempercepat proses operasional.")

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi aktif di database. Silakan lakukan Registrasi Sapi Baru terlebih dahulu.")
        return

    # --- 🔒 OTORISASI GERBANG UTAMA UNTUK OPERATOR ---
    is_admin = str(user_role).lower() == "admin"
    
    if not is_admin:
        st.warning("🔒 **Akses Terbatas:** Menu Manajemen Kelompok Massal memerlukan otorisasi Admin Kandang.")
        password_akses = st.text_input("🔐 Silakan masukkan Password Admin untuk membuka menu ini:", type="password", key="pwd_akses_global_klp")
        
        if password_akses != "admin123":
            if password_akses: # Jika sudah mengetik tapi salah
                st.error("❌ Password Admin salah! Akses menu ditolak.")
            st.info("💡 Minta Admin Kandang untuk memasukkan password di atas agar Anda dapat melihat ringkasan dan melakukan mutasi kelompok.")
            return # Menghentikan eksekusi kode di bawahnya (menu terkunci)
        else:
            st.success("🔓 Otorisasi Berhasil! Menu kelompok terbuka untuk sesi ini.")
            # Paksa status menjadi admin khusus untuk fungsi ini agar tidak ditanya password lagi di dalam tombol
            is_admin = True 

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
                struktur_kandang["Lainnya"] = []
            struktur_kandang["Lainnya"].append(item)

    # Membuat 3 Tab Utama
    tab_ringkasan, tab_mutasi_massal, tab_koreksi_kelompok = st.tabs([
        "📊 Ringkasan Per Kelompok", 
        "🔄 Mutasi Kelompok Massal", 
        "✏️ Koreksi Kode Kelompok"
    ])

    # ==================== TAB 1: RINGKASAN PER KELOMPOK ====================
    with tab_ringkasan:
        st.markdown("### 📋 Ikhtisar Populasi Berdasarkan Kelompok (Batch)")
        
        # Agregasi data per kelompok (Kode Sapi)
        summary_data = []
        list_kelompok = df_sapi["Kode Sapi"].unique()
        
        for klp in list_kelompok:
            df_klp = df_sapi[df_sapi["Kode Sapi"] == klp]
            total_ekor = len(df_klp)
            avg_bobot_awal = df_klp["Bobot Awal (kg)"].mean()
            avg_bobot_akhir = df_klp["Bobot Akhir (kg)"].mean()
            avg_adg = df_klp["ADG (kg/hari)"].mean() if "ADG (kg/hari)" in df_klp.columns else 0.0
            total_pakan = df_klp["Total Pakan (kg)"].sum() if "Total Pakan (kg)" in df_klp.columns else 0.0
            sebaran_pen = ", ".join(df_klp["Lokasi Pen"].unique())
            jenis_sapi = ", ".join(df_klp["Jenis Sapi"].unique())
            
            summary_data.append({
                "Kode Kelompok": klp,
                "Jumlah Sapi (Ekor)": total_ekor,
                "Jenis Sapi": jenis_sapi,
                "Rerata Bobot Awal (kg)": round(avg_bobot_awal, 2),
                "Rerata Bobot Akhir (kg)": round(avg_bobot_akhir, 2),
                "Rerata ADG (kg/hari)": round(avg_adg, 2),
                "Total Pakan (kg)": round(total_pakan, 2),
                "Sebaran Pen": sebaran_pen
            })
            
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

        # Detail Viewer per Kelompok
        st.markdown("---")
        st.markdown("#### 🔍 Lihat Detail Sapi dalam Kelompok")
        kelompok_terpilih = st.selectbox("Pilih Kelompok untuk Detail:", list_kelompok, key="sb_detail_klp")
        
        df_detail_klp = df_sapi[df_sapi["Kode Sapi"] == kelompok_terpilih].reset_index(drop=True)
        st.dataframe(
            df_detail_klp[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Bobot Akhir (kg)", "Lokasi Pen"]],
            use_container_width=True
        )

    # ==================== TAB 2: MUTASI KELOMPOK MASSAL ====================
    with tab_mutasi_massal:
        st.markdown("### 🔄 Pemindahan Pen Seluruh Sapi dalam Satu Kelompok")
        st.markdown("Fitur ini memindahkan *semua sapi* yang memiliki Kode Kelompok yang sama ke Pen tujuan sekaligus.")

        list_kelompok_mutasi = df_sapi["Kode Sapi"].unique()
        klp_mutasi_terpilih = st.selectbox("Pilih Kelompok Sapi Yang Akan Dimutasi:", list_kelompok_mutasi, key="sb_mutasi_klp")
        
        df_klp_aktif = df_sapi[df_sapi["Kode Sapi"] == klp_mutasi_terpilih]
        total_mutasi = len(df_klp_aktif)
        pen_saat_ini = ", ".join(df_klp_aktif["Lokasi Pen"].unique())
        
        st.info(f"📦 **Informasi Kelompok:**\n* Kelompok Terpilih: **{klp_mutasi_terpilih}**\n* Jumlah Sapi: **{total_mutasi} Ekor**\n* Lokasi Pen Saat Ini: {pen_saat_ini}")
        
        st.markdown("#### 🎯 Tentukan Lokasi Pen Tujuan Baru Massal")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            pilihan_blok_tujuan = st.selectbox("Pilih Blok Kandang Tujuan:", list(struktur_kandang.keys()), key="klp_blok")
        with col_m2:
            pilihan_pen_tujuan = st.selectbox("Pilih Pen Tujuan:", struktur_kandang[pilihan_blok_tujuan], key="klp_pen")
            
        full_lokasi_tujuan = f"{pilihan_blok_tujuan} - {pilihan_pen_tujuan}"

        if st.button("🚀 Eksekusi Mutasi Massal Kelompok", type="primary", use_container_width=True):
            # Update lokasi pen untuk semua sapi dengan Kode Sapi tersebut
            mask = df_sapi["Kode Sapi"] == klp_mutasi_terpilih
            df_sapi.loc[mask, "Lokasi Pen"] = full_lokasi_tujuan
            
            save_data(df_sapi)
            
            detail_aksi = f"Mutasi Massal Kelompok {klp_mutasi_terpilih} ({total_mutasi} Ekor) ke [{full_lokasi_tujuan}] oleh {user_name}"
            add_activity_log(user_name, "Mutasi Kelompok Massal", detail_aksi)
            
            st.success(f"🎉 Berhasil! Seluruh sapi di kelompok {klp_mutasi_terpilih} ({total_mutasi} Ekor) telah dipindahkan ke **{full_lokasi_tujuan}**.")
            st.rerun()

    # ==================== TAB 3: KOREKSI KODE KELOMPOK ====================
    with tab_koreksi_kelompok:
        st.markdown("### ✏️ Ubah Nama/Kode Kelompok Secara Massal")
        st.markdown("Gunakan menu ini jika ada kesalahan pengetikan Kode Tiba / No. Batch pada saat registrasi awal.")

        list_kelompok_edit = df_sapi["Kode Sapi"].unique()
        klp_edit_terpilih = st.selectbox("Pilih Kelompok Yang Salah Input:", list_kelompok_edit, key="sb_edit_klp_kode")
        
        kode_baru = st.text_input("Masukkan Kode Kelompok Baru:", value=str(klp_edit_terpilih)).strip()
        
        st.warning(f"🚨 **Perhatian:** Tindakan ini akan mengubah kolom 'Kode Sapi' untuk seluruh sapi di kelompok **{klp_edit_terpilih}** menjadi **{kode_baru}**.")
        
        konfirmasi_ubah = st.checkbox("Saya benar-benar ingin mengubah kode kelompok ini secara massal.")

        if st.button("💾 Simpan Perubahan Kode Kelompok", type="primary", disabled=not konfirmasi_ubah, use_container_width=True):
            if not kode_baru:
                st.error("❌ Gagal! Kode kelompok baru tidak boleh kosong.")
            elif kode_baru == klp_edit_terpilih:
                st.info("ℹ️ Kode baru sama dengan kode lama. Tidak ada perubahan dilakukan.")
            else:
                # Update kode kelompok massal
                mask = df_sapi["Kode Sapi"] == klp_edit_terpilih
                df_sapi.loc[mask, "Kode Sapi"] = kode_baru
                
                save_data(df_sapi)
                
                detail_aksi = f"Mengubah Kode Kelompok dari {klp_edit_terpilih} menjadi {kode_baru} oleh {user_name}"
                add_activity_log(user_name, "Koreksi Kelompok", detail_aksi)
                
                st.success(f"🎉 Sukses! Kode Kelompok telah diperbarui dari {klp_edit_terpilih} menjadi **{kode_baru}**.")
                st.rerun()