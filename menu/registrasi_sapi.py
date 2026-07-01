import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_registrasi(df_sapi, list_jenis_sapi, struktur_kandang, save_data, add_activity_log, user_name, user_role="operator"):
    st.subheader("📝 Manajemen & Registrasi Sapi Baru")
    
    # Membuat 2 Tab utama
    tab_registrasi, tab_edit_hapus = st.tabs(["➕ Registrasi Sapi Baru", "⚙️ Edit / Hapus Data Registrasi"])

    # ==================== TAB 1: FORM REGISTRASI ====================
    with tab_registrasi:
        st.markdown("Silakan masukkan data batch sapi baru. **Kode Tiba** bisa diisi sama untuk kuantiti sapi yang banyak.")

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

                new_cow = {
                    "Kode Tiba": kode_tiba,
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

    # ==================== TAB 2: EDIT / HAPUS (KOREKSI DULU BARU OTORISASI) ====================
    with tab_edit_hapus:
        st.markdown("### ⚙️ Panel Koreksi Data Registrasi")
        
        if df_sapi.empty:
            st.info("Belum ada data sapi aktif di database untuk diedit.")
            return

        # Pilihan sapi selalu muncul langsung tanpa dihalangi password
        opsi_sapi = df_sapi.apply(lambda r: f"No. {r.name + 1} | Kelompok: {r['Kode Tiba']} | RFID: {r['RFID/Tag']} | Pen: {r['Lokasi Pen']}", axis=1).tolist()
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
                    e_kode_tiba = st.text_input("Kode Tiba / No. Batch", value=str(row_sapi["Kode Tiba"])).strip()
                    e_rfid_asal = st.text_input("RFID / Tag Asal", value=str(row_sapi.get("RFID/Tag Asal", "-"))).strip()
                    e_rfid_kandang = st.text_input("RFID / Tag Kandang", value=str(row_sapi["RFID/Tag"])).strip()
                    e_jenis = st.selectbox("Jenis Sapi", list_jenis_sapi, index=list_jenis_sapi.index(row_sapi["Jenis Sapi"]) if row_sapi["Jenis Sapi"] in list_jenis_sapi else 0)
                with col_e2:
                    e_jk = st.selectbox("Jenis Kelamin", ["Jantan", "Betina"], index=0 if row_sapi["Jenis Kelamin"] == "Jantan" else 1)
                    e_umur = st.number_input("Estimasi Umur (Bulan)", min_value=1, value=int(row_sapi.get("Umur Masuk (Bulan)", 12)))
                    e_asal = st.text_input("Asal Negara", value=str(row_sapi["Asal Negara"])).strip()
                    e_bobot = st.number_input("Bobot Awal Masuk (kg)", value=float(row_sapi["Bobot Awal (kg)"]))

                st.markdown("---")
                
                # Input password dimasukkan di bagian bawah form (hanya muncul untuk operator)
                password_edit = ""
                if not is_admin:
                    password_edit = st.text_input("🔐 Operator wajib memasukkan Password Admin untuk menyimpan:", type="password", help="Minta bantuan admin untuk memasukkan password konfirmasi")

                btn_simpan_edit = st.form_submit_button("Simpan Perubahan Data", type="primary", use_container_width=True)
                
                if btn_simpan_edit:
                    # Validasi password di akhir klik tombol
                    if not is_admin and password_edit != "admin123":
                        st.error("❌ Gagal Simpan! Password Admin salah atau belum diisi.")
                    else:
                        df_sapi.at[idx_target, "Kode Tiba"] = e_kode_tiba
                        df_sapi.at[idx_target, "Kode Sapi"] = e_kode_tiba  # Menjaga sinkronisasi
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
            st.markdown(f"🚨 **Perhatian:** Tindakan ini akan menghapus data sapi kelompok **{row_sapi['Kode Tiba']}** pada baris ke-{idx_target + 1} secara permanen.")
            konfirmasi_hapus = st.checkbox("Saya benar-benar ingin menghapus data sapi ini.")
            
            # Input password hapus ditaruh setelah checkbox dicentang (hanya untuk operator)
            password_hapus = ""
            if not is_admin and konfirmasi_hapus:
                password_hapus = st.text_input("🔐 Operator wajib memasukkan Password Admin untuk menghapus:", type="password", key="pwd_hapus")

            if st.button("🗑️ Hapus Sapi Secara Permanen", type="primary", disabled=not konfirmasi_hapus, use_container_width=True):
                # Validasi password di akhir klik tombol hapus
                if not is_admin and password_hapus != "admin123":
                    st.error("❌ Gagal Hapus! Password Admin salah atau belum diisi.")
                else:
                    df_sapi = df_sapi.drop(index=idx_target).reset_index(drop=True)
                    save_data(df_sapi)
                    add_activity_log(user_name, "Hapus Registrasi", f"Menghapus sapi baris {idx_target + 1} dari Kelompok {row_sapi['Kode Tiba']}")
                    st.success("💥 Data berhasil dihapus dari database!")
                    st.rerun()