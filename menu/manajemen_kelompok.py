import streamlit as st
import pandas as pd

def tampilkan_menu_manajemen_kelompok(df_sapi, DAFTAR_PEN, user_role, save_data, add_activity_log, user_name):
    st.subheader("👥 Manajemen Kelompok / Batch Sapi")
    st.markdown("Kelola data sapi secara massal berdasarkan **Kelompok / Batch (Kode Tiba)** atau **Pen / Kandang** untuk mempercepat proses operasional.")

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
            is_admin = True 

    # --- EKSTRAKSI KODE KELOMPOK / BATCH UTAMA ---
    # Mengambil prefix sebelum tanda '-' (Contoh: S1-001 -> S1) agar grouping kelompok tetap utuh
    df_sapi_work = df_sapi.copy()
    df_sapi_work["Kode Kelompok / Batch"] = df_sapi_work["Kode Sapi"].apply(
        lambda x: str(x).split("-")[0].strip() if "-" in str(x) else str(x).strip()
    )

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
        
        # Agregasi data per Kode Kelompok / Batch
        summary_data = []
        list_batch = df_sapi_work["Kode Kelompok / Batch"].unique()
        
        for batch in list_batch:
            df_klp = df_sapi_work[df_sapi_work["Kode Kelompok / Batch"] == batch]
            total_ekor = len(df_klp)
            avg_bobot_awal = df_klp["Bobot Awal (kg)"].mean() if "Bobot Awal (kg)" in df_klp.columns else 0.0
            avg_bobot_akhir = df_klp["Bobot Akhir (kg)"].mean() if "Bobot Akhir (kg)" in df_klp.columns else 0.0
            avg_adg = df_klp["ADG (kg/hari)"].mean() if "ADG (kg/hari)" in df_klp.columns else 0.0
            total_pakan = df_klp["Total Pakan (kg)"].sum() if "Total Pakan (kg)" in df_klp.columns else 0.0
            sebaran_pen = ", ".join(df_klp["Lokasi Pen"].dropna().unique())
            jenis_sapi = ", ".join(df_klp["Jenis Sapi"].dropna().unique())
            
            summary_data.append({
                "Kode Kelompok (Batch)": batch,
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
        batch_terpilih = st.selectbox("Pilih Kelompok (Batch) untuk Detail:", list_batch, key="sb_detail_klp")
        
        df_detail_klp = df_sapi_work[df_sapi_work["Kode Kelompok / Batch"] == batch_terpilih].reset_index(drop=True)
        st.dataframe(
            df_detail_klp[["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Bobot Akhir (kg)", "ADG (kg/hari)", "Lokasi Pen"]],
            use_container_width=True,
            hide_index=True
        )

    # ==================== TAB 2: MUTASI KELOMPOK MASSAL ====================
    with tab_mutasi_massal:
        st.markdown("### 🔄 Pemindahan Pen Massal (Per Batch / Per Pen)")
        st.markdown("Pindahkan sapi secara serentak berdasarkan **Kode Kelompok/Batch** atau **Pen/Kandang** asal.")

        mode_mutasi = st.radio(
            "Pilih Dasar Pemindahan Massal:",
            ["📦 Berdasarkan Kelompok / Batch (Cth: S1, S2)", "🏠 Berdasarkan Pen / Kandang Asal"],
            horizontal=True
        )

        df_target_mutasi = pd.DataFrame()
        label_sumber = ""

        if "Kelompok" in mode_mutasi:
            list_batch_mutasi = df_sapi_work["Kode Kelompok / Batch"].unique().tolist()
            batch_pilihan = st.selectbox("Pilih Kelompok (Batch) Sapi Yang Akan Dimutasi:", list_batch_mutasi, key="sb_mutasi_batch")
            df_target_mutasi = df_sapi_work[df_sapi_work["Kode Kelompok / Batch"] == batch_pilihan]
            label_sumber = f"Kelompok {batch_pilihan}"
        else:
            list_pen_mutasi = df_sapi_work["Lokasi Pen"].dropna().unique().tolist()
            pen_pilihan = st.selectbox("Pilih Pen / Kandang Asal Yang Akan Dimutasi:", list_pen_mutasi, key="sb_mutasi_pen")
            df_target_mutasi = df_sapi_work[df_sapi_work["Lokasi Pen"] == pen_pilihan]
            label_sumber = f"Pen {pen_pilihan}"

        if not df_target_mutasi.empty:
            st.markdown("---")
            st.markdown(f"#### 🐄 Sapi Terdeteksi di **{label_sumber}** ({len(df_target_mutasi)} Ekor)")

            # Opsi Filter Bobot Tambahan
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_bobot_min = st.number_input("Filter Bobot Minimal (kg) - *Isi 0 untuk Semua*", min_value=0.0, value=0.0, step=10.0)
            
            df_filtered = df_target_mutasi.copy()
            if filter_bobot_min > 0:
                df_filtered = df_filtered[df_filtered["Bobot Akhir (kg)"].astype(float) >= filter_bobot_min]
                st.caption(f"💡 Ditemukan **{len(df_filtered)} ekor** sapi dengan bobot ≥ {filter_bobot_min} kg.")

            # Multiselect sapi target (Default Checked ALL)
            opsi_sapi_mutasi = df_filtered.apply(
                lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']} (Bobot: {r['Bobot Akhir (kg)']} kg | Lokasi: {r['Lokasi Pen']})", axis=1
            ).tolist()

            sapi_terpilih_mutasi = st.multiselect(
                "Pilih Sapi Yang Akan Dipindahkan (Default: Tercentang Semua):",
                options=opsi_sapi_mutasi,
                default=opsi_sapi_mutasi,
                key="ms_mutasi_sapi"
            )

            st.caption(f"📊 **Status Terpilih:** {len(sapi_terpilih_mutasi)} dari {len(df_filtered)} ekor sapi akan dipindahkan.")

            st.markdown("---")
            st.markdown("#### 🎯 Tentukan Lokasi Pen Tujuan Baru Massal")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                pilihan_blok_tujuan = st.selectbox("Pilih Blok Kandang Tujuan:", list(struktur_kandang.keys()), key="klp_blok")
            with col_m2:
                pilihan_pen_tujuan = st.selectbox("Pilih Pen Tujuan:", struktur_kandang[pilihan_blok_tujuan], key="klp_pen")
                
            full_lokasi_tujuan = f"{pilihan_blok_tujuan} - {pilihan_pen_tujuan}"

            # Cek Kapasitas Pen Tujuan
            sapi_di_pen_tujuan = len(df_sapi[df_sapi["Lokasi Pen"] == full_lokasi_tujuan])
            sisa_kapasitas = 25 - sapi_di_pen_tujuan

            if sapi_di_pen_tujuan >= 25:
                st.error(f"⚠️ Pen **{full_lokasi_tujuan}** sudah PENUH ({sapi_di_pen_tujuan}/25 Ekor). Silakan pilih pen lain.")
            else:
                st.info(f"ℹ️ Pen **{full_lokasi_tujuan}** saat ini terisi {sapi_di_pen_tujuan}/25 Ekor. Sisa kapasitas: **{sisa_kapasitas} ekor**.")

            if st.button("🚀 Eksekusi Mutasi Massal", type="primary", use_container_width=True):
                if not sapi_terpilih_mutasi:
                    st.error("❌ Gagal! Pilih minimal 1 ekor sapi yang akan dimutasi.")
                elif len(sapi_terpilih_mutasi) > sisa_kapasitas:
                    st.error(f"❌ Gagal! Kapasitas pen tujuan tidak cukup. Anda memilih {len(sapi_terpilih_mutasi)} ekor, tetapi sisa kapasitas pen {full_lokasi_tujuan} hanya {sisa_kapasitas} ekor.")
                else:
                    # Ambil daftar Kode Sapi dari item tercentang
                    list_kode_sapi_mutasi = []
                    for item in sapi_terpilih_mutasi:
                        kode_item = item.split(" - RFID: ")[0]
                        list_kode_sapi_mutasi.append(kode_item)

                    # Update lokasi pen di df_sapi utama
                    mask = df_sapi["Kode Sapi"].isin(list_kode_sapi_mutasi)
                    df_sapi.loc[mask, "Lokasi Pen"] = full_lokasi_tujuan
                    
                    save_data(df_sapi)
                    
                    detail_aksi = f"Mutasi Massal {len(list_kode_sapi_mutasi)} Ekor sapi dari {label_sumber} ke [{full_lokasi_tujuan}] oleh {user_name}"
                    add_activity_log(user_name, "Mutasi Kelompok Massal", detail_aksi)
                    
                    st.success(f"🎉 Berhasil! Sebanyak {len(list_kode_sapi_mutasi)} ekor sapi telah dipindahkan ke **{full_lokasi_tujuan}**.")
                    st.balloons()
                    st.rerun()

    # ==================== TAB 3: KOREKSI KODE KELOMPOK ====================
    with tab_koreksi_kelompok:
        st.markdown("### ✏️ Ubah Nama/Kode Kelompok (Batch) Secara Massal")
        st.markdown("Gunakan menu ini jika ingin mengganti awalan Kode Kelompok/Batch (misalnya mengubah awalan `S1` menjadi `S1-NEW` pada seluruh `S1-001`, `S1-002`, dst).")

        list_batch_edit = df_sapi_work["Kode Kelompok / Batch"].unique().tolist()
        batch_edit_terpilih = st.selectbox("Pilih Kelompok (Batch) Yang Ingin Diubah:", list_batch_edit, key="sb_edit_klp_kode")
        
        kode_baru_prefix = st.text_input("Masukkan Prefix Kode Kelompok Baru (Cth: S2 atau BATCH-A):", value=str(batch_edit_terpilih)).strip()
        
        df_edit_target = df_sapi_work[df_sapi_work["Kode Kelompok / Batch"] == batch_edit_terpilih]
        st.warning(f"🚨 **Perhatian:** Tindakan ini akan memperbarui **{len(df_edit_target)} ekor sapi** pada kelompok **{batch_edit_terpilih}** menjadi berawalan **{kode_baru_prefix}**.")
        
        konfirmasi_ubah = st.checkbox("Saya benar-benar ingin mengubah kode kelompok ini secara massal.")

        if st.button("💾 Simpan Perubahan Kode Kelompok", type="primary", disabled=not konfirmasi_ubah, use_container_width=True):
            if not kode_baru_prefix:
                st.error("❌ Gagal! Kode kelompok baru tidak boleh kosong.")
            elif kode_baru_prefix == batch_edit_terpilih:
                st.info("ℹ️ Kode baru sama dengan kode lama. Tidak ada perubahan dilakukan.")
            else:
                # Update kode kelompok massal (mempertahankan akhiran -001, -002 jika ada)
                mask = df_sapi_work["Kode Kelompok / Batch"] == batch_edit_terpilih
                
                for idx in df_sapi[mask].index:
                    kode_lama = str(df_sapi.loc[idx, "Kode Sapi"])
                    if "-" in kode_lama:
                        suffix = kode_lama.split("-", 1)[1]
                        df_sapi.loc[idx, "Kode Sapi"] = f"{kode_baru_prefix}-{suffix}"
                    else:
                        df_sapi.loc[idx, "Kode Sapi"] = kode_baru_prefix
                
                save_data(df_sapi)
                
                detail_aksi = f"Mengubah Kode Kelompok Batch dari {batch_edit_terpilih} menjadi {kode_baru_prefix} oleh {user_name}"
                add_activity_log(user_name, "Koreksi Kelompok", detail_aksi)
                
                st.success(f"🎉 Sukses! Kode Kelompok (Batch) telah diperbarui dari {batch_edit_terpilih} menjadi **{kode_baru_prefix}**.")
                st.rerun()