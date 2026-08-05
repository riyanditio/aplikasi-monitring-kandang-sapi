import streamlit as st
import pandas as pd

def tampilkan_menu_edit_hapus(df_sapi, list_jenis_sapi, daftar_pen, save_data, add_activity_log, user_name):
    st.subheader("⚙️ Edit & Hapus Data Rekam Sapi")
    st.markdown("Gunakan menu ini untuk mengoreksi kesalahan input data master sapi dan memperbarui status populasi.")

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi di dalam database.")
        return

    # Pastikan kolom Status tersedia
    if "Status" not in df_sapi.columns:
        df_sapi["Status"] = "AKTIF"

    # Filter Kategori Status: Default memprioritaskan Sapi AKTIF
    st.markdown("#### 🔍 Filter Pencarian Sapi")
    filter_status = st.radio(
        "Pilih Kategori Status Sapi yang Ingin Dikelola:",
        ["🟢 Sapi AKTIF Kandang", "📦 Semua Status (Termasuk Panen / Afkir / Mati)"],
        horizontal=True
    )

    if filter_status == "🟢 Sapi AKTIF Kandang":
        df_sapi_target = df_sapi[df_sapi["Status"] == "AKTIF"].copy()
    else:
        df_sapi_target = df_sapi.copy()

    if df_sapi_target.empty:
        st.info("ℹ️ Tidak ada data sapi yang sesuai dengan kriteria filter status terpilih.")
        return

    # Rekonstruksi struktur hirarki dari DAFTAR_PEN global
    struktur_kandang = {}
    for item in daftar_pen:
        if " - " in item:
            blok, pen = item.split(" - ", 1)
            if blok not in struktur_kandang:
                struktur_kandang[blok] = []
            struktur_kandang[blok].append(pen)

    if not struktur_kandang:
        struktur_kandang = {"Blok Kandang": ["Pen 1"]}

    # Pilih Sapi Sasaran dari data tersaring
    opsi_sapi = df_sapi_target.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']} [{r.get('Status', 'AKTIF')}] (di {r.get('Lokasi Pen', '-')})", axis=1).tolist()
    sapi_terpilih = st.selectbox("Pilih Sapi Yang Akan Dikelola / Diperbarui:", opsi_sapi)
    
    idx_target = opsi_sapi.index(sapi_terpilih)
    row_target = df_sapi_target.iloc[idx_target]

    # Melacak indeks tepat di DataFrame utama (df_sapi) berdasarkan Kode Sapi & RFID
    mask_original = (df_sapi["Kode Sapi"].astype(str) == str(row_target["Kode Sapi"])) & (df_sapi["RFID/Tag"].astype(str) == str(row_target["RFID/Tag"]))
    real_indices = df_sapi[mask_original].index.tolist()

    if not real_indices:
        st.error("⚠️ Data sapi tidak ditemukan pada database master utama.")
        return

    real_idx = real_indices[0]
    row = df_sapi.loc[real_idx]

    tab_edit, tab_hapus = st.tabs(["📝 Edit Informasi & Status Sapi", "🗑️ Hapus Sapi Dari Sistem"])

    with tab_edit:
        with st.form("form_edit_sapi_terpilih"):
            col1, col2 = st.columns(2)
            with col1:
                kode_baru = st.text_input("Kode Sapi / ID Anting", value=str(row["Kode Sapi"])).strip()
                rfid_asal_baru = st.text_input("RFID / Tag Asal (Asli)", value=str(row.get("RFID/Tag Asal", "-"))).strip()
                rfid_baru = st.text_input("RFID / Electronic Tag Baru", value=str(row["RFID/Tag"])).strip()
                jenis_baru = st.selectbox("Jenis Sapi", list_jenis_sapi, index=list_jenis_sapi.index(row["Jenis Sapi"]) if row["Jenis Sapi"] in list_jenis_sapi else 0)
                jk_baru = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"], index=0 if str(row["Jenis Kelamin"]).lower() == "jantan" else 1)
                
                # Opsi Pembaruan Status Sapi
                opsi_status = ["AKTIF", "PANEN", "AFKIR", "MATI"]
                curr_status = str(row.get("Status", "AKTIF")).upper()
                idx_status = opsi_status.index(curr_status) if curr_status in opsi_status else 0
                status_baru = st.selectbox("Status Keberadaan Sapi", opsi_status, index=idx_status, help="Ubah status ke PANEN/AFKIR/MATI jika sapi sudah keluar kandang.")

            with col2:
                bobot_awal = st.number_input("Bobot Awal Masuk (kg)", value=float(row["Bobot Awal (kg)"]))
                bobot_akhir = st.number_input("Bobot Akhir Saat Ini (kg)", value=float(row["Bobot Akhir (kg)"]))
                
                # Uraikan lokasi pen saat ini untuk default selectbox
                curr_lokasi = str(row["Lokasi Pen"])
                default_blok = list(struktur_kandang.keys())[0]
                default_pen = struktur_kandang[default_blok][0] if struktur_kandang[default_blok] else "Pen 1"
                
                if " - " in curr_lokasi:
                    b, p = curr_lokasi.split(" - ", 1)
                    if b in struktur_kandang and p in struktur_kandang[b]:
                        default_blok = b
                        default_pen = p

                blok_baru = st.selectbox("Blok Kandang Baru", list(struktur_kandang.keys()), index=list(struktur_kandang.keys()).index(default_blok))
                pen_baru = st.selectbox("Nomor/Bagian Pen Baru", struktur_kandang[blok_baru], index=struktur_kandang[blok_baru].index(default_pen) if default_pen in struktur_kandang[blok_baru] else 0)

            st.markdown("---")
            btn_update = st.form_submit_button("Simpan Pembaruan Data Sapi", type="primary", use_container_width=True)

            if btn_update:
                df_sapi.at[real_idx, "Kode Sapi"] = kode_baru
                df_sapi.at[real_idx, "RFID/Tag Asal"] = rfid_asal_baru
                df_sapi.at[real_idx, "RFID/Tag"] = rfid_baru
                df_sapi.at[real_idx, "Jenis Sapi"] = jenis_baru
                df_sapi.at[real_idx, "Jenis Kelamin"] = jk_baru
                df_sapi.at[real_idx, "Status"] = status_baru
                df_sapi.at[real_idx, "Bobot Awal (kg)"] = bobot_awal
                df_sapi.at[real_idx, "Bobot Akhir (kg)"] = bobot_akhir
                df_sapi.at[real_idx, "Lokasi Pen"] = f"{blok_baru} - {pen_baru}"
                
                save_data(df_sapi)
                add_activity_log(user_name, "Edit Data", f"Mengubah profil Sapi {kode_baru} (Status: {status_baru}, Lokasi: {blok_baru} - {pen_baru})")
                st.success(f"🎉 Sukses memperbarui profil Sapi {kode_baru}!")
                st.rerun()

    with tab_hapus:
        st.warning(f"⚠️ **PERINGATAN HAPUS:** Anda akan menghapus Sapi **{row['Kode Sapi']}** (RFID: {row['RFID/Tag']}) dari database secara permanen!")
        konfirmasi = st.checkbox("Saya memahami tindakan ini bersifat permanen dan tidak dapat dibatalkan.")
        
        if st.button("🗑️ Eksekusi Hapus Permanen", type="primary", disabled=not konfirmasi, use_container_width=True):
            kode_deleted = row['Kode Sapi']
            df_sapi = df_sapi.drop(index=real_idx).reset_index(drop=True)
            save_data(df_sapi)
            add_activity_log(user_name, "Hapus Data", f"Menghapus total Sapi {kode_deleted} dari database")
            st.success(f"Otorisasi Berhasil! Record Sapi {kode_deleted} telah dibersihkan dari database.")
            st.rerun()