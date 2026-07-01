import streamlit as st
import pandas as pd

def tampilkan_menu_edit_hapus(df_sapi, list_jenis_sapi, daftar_pen, save_data, add_activity_log, user_name):
    st.subheader("⚙️ Edit & Hapus Data Rekam Sapi")
    st.markdown("Gunakan menu ini untuk mengoreksi kesalahan input data master sapi.")

    if df_sapi.empty:
        st.warning("⚠️ Belum ada data sapi aktif di dalam database.")
        return

    # Rekonstruksi struktur hirarki dari DAFTAR_PEN global
    struktur_kandang = {}
    for item in daftar_pen:
        if " - " in item:
            blok, pen = item.split(" - ", 1)
            if blok not in struktur_kandang:
                struktur_kandang[blok] = []
            struktur_kandang[blok].append(pen)

    # Pilih Sapi sasaran
    opsi_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - {r['RFID/Tag']}", axis=1).tolist()
    sapi_terpilih = st.selectbox("Pilih Sapi Yang Akan Dikelola:", opsi_sapi)
    
    idx_sapi = opsi_sapi.index(sapi_terpilih)
    row = df_sapi.iloc[idx_sapi]

    tab_edit, tab_hapus = st.tabs(["📝 Edit Informasi Sapi", "🗑️ Hapus Sapi Dari Sistem"])

    with tab_edit:
        with st.form("form_edit_sapi_terpilih"):
            col1, col2 = st.columns(2)
            with col1:
                kode_baru = st.text_input("Kode Sapi / ID Anting", value=str(row["Kode Sapi"])).strip()
                # --- INTEGRASI: Input RFID/Tag Asal Baru ---
                rfid_asal_baru = st.text_input("RFID / Tag Asal (Asli)", value=str(row.get("RFID/Tag Asal", "-"))).strip()
                rfid_baru = st.text_input("RFID / Electronic Tag Baru", value=str(row["RFID/Tag"])).strip()
                jenis_baru = st.selectbox("Jenis Sapi", list_jenis_sapi, index=list_jenis_sapi.index(row["Jenis Sapi"]) if row["Jenis Sapi"] in list_jenis_sapi else 0)
                jk_baru = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"], index=0 if row["Jenis Kelamin"] == "Jantan" else 1)
            
            with col2:
                bobot_awal = st.number_input("Bobot Awal Masuk (kg)", value=float(row["Bobot Awal (kg)"]))
                bobot_akhir = st.number_input("Bobot Akhir Saat Ini (kg)", value=float(row["Bobot Akhir (kg)"]))
                
                # Uraikan lokasi pen saat ini untuk default selectbox
                curr_lokasi = str(row["Lokasi Pen"])
                default_blok = list(struktur_kandang.keys())[0]
                default_pen = struktur_kandang[default_blok][0]
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
                df_sapi.at[idx_sapi, "Kode Sapi"] = kode_baru
                # --- INTEGRASI: Simpan perubahan nilai RFID/Tag Asal ---
                df_sapi.at[idx_sapi, "RFID/Tag Asal"] = rfid_asal_baru
                df_sapi.at[idx_sapi, "RFID/Tag"] = rfid_baru
                df_sapi.at[idx_sapi, "Jenis Sapi"] = jenis_baru
                df_sapi.at[idx_sapi, "Jenis Kelamin"] = jk_baru
                df_sapi.at[idx_sapi, "Bobot Awal (kg)"] = bobot_awal
                df_sapi.at[idx_sapi, "Bobot Akhir (kg)"] = bobot_akhir
                df_sapi.at[idx_sapi, "Lokasi Pen"] = f"{blok_baru} - {pen_baru}"
                
                save_data(df_sapi)
                add_activity_log(user_name, "Edit Data", f"Mengubah profil Sapi {kode_baru} (Lokasi: {blok_baru} - {pen_baru})")
                st.success(f"🎉 Sukses memperbarui profil Sapi {kode_baru}!")
                st.rerun()

    with tab_hapus:
        st.warning(f"⚠️ **PERINGATAN:** Anda akan menghapus Sapi {row['Kode Sapi']} dari database secara permanen!")
        konfirmasi = st.checkbox("Saya memahami tindakan ini tidak dapat dibatalkan.")
        
        if st.button("🗑️ Eksekusi Hapus Permanen", type="primary", disabled=not konfirmasi, use_container_width=True):
            kode_deleted = row['Kode Sapi']
            df_sapi = df_sapi.drop(index=idx_sapi).reset_index(drop=True)
            save_data(df_sapi)
            add_activity_log(user_name, "Hapus Data", f"Menghapus total Sapi {kode_deleted} dari database")
            st.success(f"Otorisasi Berhasil! Sapi {kode_deleted} telah dibersihkan.")
            st.rerun()