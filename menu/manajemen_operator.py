import streamlit as st
import pandas as pd

def tampilkan_menu_operator(load_users, ALL_MENUS, save_users, add_activity_log, user_name):
    st.subheader("👥 Manajemen Akun Pengguna & Pengaturan Hak Akses Menu")
    df_users = load_users()
    
    # 🌟 SEKARANG MENJADI 4 TAB: Menyelipkan Tab Edit di antara Tambah dan Hapus
    tab_user_lihat, tab_user_tambah, tab_user_edit, tab_user_hapus = st.tabs([
        "📋 Daftar Anggota Aktif", 
        "➕ Tambah Operator & Atur Menu", 
        "✏️ Edit Hak Akses & Akun", 
        "❌ Hapus Akun"
    ])
    
    # ==================== TAB 1: DAFTAR ANGGOTA AKTIF ====================
    with tab_user_lihat:
        st.write("### Daftar Pengguna & Akses Menu Lapangan")
        df_users_tampil = df_users.copy()
        df_users_tampil["Password"] = "******"
        df_users_tampil.index = range(1, len(df_users_tampil) + 1)
        st.dataframe(df_users_tampil, use_container_width=True)
        
    # ==================== TAB 2: TAMBAH OPERATOR BARU ====================
    with tab_user_tambah:
        st.write("### Buat Akun Anggota Baru & Pilih Menunya")
        with st.form("form_tambah_operator"):
            new_username = st.text_input("Username Baru", placeholder="Contoh: ahmad_kandang").strip()
            new_password = st.text_input("Password Baru", type="password", placeholder="Masukkan password").strip()
            new_role = st.selectbox("Tingkat Akun (Role)", ["Operator", "Admin"])
            chosen_menus = st.multiselect("Pilih Hak Akses Menu", ALL_MENUS)
            
            submit_tambah = st.form_submit_button("➕ Buat Akun Baru", type="primary", use_container_width=True)
            
            if submit_tambah:
                if not new_username or not new_password:
                    st.error("❌ Username dan Password wajib diisi!")
                elif new_username in df_users["Username"].astype(str).values:
                    st.error(f"❌ Username '{new_username}' sudah terdaftar.")
                else:
                    menus_str = "|".join(chosen_menus)
                    new_account = pd.DataFrame([{"Username": new_username, "Password": new_password, "Role": new_role, "Menus": menus_str}])
                    df_users = pd.concat([df_users, new_account], ignore_index=True)
                    save_users(df_users)
                    add_activity_log(user_name, "Tambah Operator", f"Membuat akun pengguna baru '{new_username}' dengan hak akses {new_role}.")
                    st.success(f"🎉 Sukses! Akun '{new_username}' berhasil aktif.")
                    st.rerun()

    # ==================== TAB 3: EDIT HAK AKSES & AKUN (FITUR BARU COLO-COLO) ====================
    with tab_user_edit:
        st.write("### ✏️ Edit Hak Akses Menu & Informasi Akun Terdaftar")
        list_users = df_users["Username"].tolist()
        
        if not list_users:
            st.info("Belum ada akun pengguna yang terdaftar di database.")
        else:
            user_terpilih = st.selectbox("Pilih Akun Operator/Admin Yang Akan Diubah:", list_users, key="sb_edit_user_pilih")
            
            # Ambil detail baris data user terpilih
            idx_user = df_users[df_users["Username"] == user_terpilih].index[0]
            user_row = df_users.loc[idx_user]
            
            # Parse daftar menu bawaan saat ini yang dipisah tanda pipa |
            menu_sekarang = str(user_row["Menus"]).split("|") if pd.notna(user_row["Menus"]) else []
            # Amankan filter agar hanya mengambil menu yang valid di dalam list ALL_MENUS global
            menu_default = [m for m in menu_sekarang if m in ALL_MENUS]
            
            with st.form("form_edit_hak_akses_operator"):
                edit_password = st.text_input("Password Akun", value=str(user_row["Password"]), type="password")
                
                # Menentukan index pilihan default untuk Role saat ini
                role_options = ["Operator", "Admin"]
                current_role = str(user_row["Role"])
                default_role_idx = role_options.index(current_role) if current_role in role_options else 0
                
                edit_role = st.selectbox("Tingkat Akun (Role)", role_options, index=default_role_idx)
                
                # Tampilkan multiselect dengan isian menu lama operator tersebut sebagai nilai default-nya
                edit_chosen_menus = st.multiselect("Sesuaikan Hak Akses Menu Lapangan:", options=ALL_MENUS, default=menu_default)
                
                submit_edit = st.form_submit_button("💾 Simpan Perubahan Hak Akses", type="primary", use_container_width=True)
                
                if submit_edit:
                    if not edit_password.strip():
                        st.error("❌ Password tidak boleh dikosongkan!")
                    else:
                        # Satukan list menu kembali menjadi string yang dipisah pipa |
                        menus_str_baru = "|".join(edit_chosen_menus)
                        
                        # Tulis balik perubahan langsung ke DataFrame di index yang tepat
                        df_users.at[idx_user, "Password"] = edit_password.strip()
                        df_users.at[idx_user, "Role"] = edit_role
                        df_users.at[idx_user, "Menus"] = menus_str_baru
                        
                        # Simpan ke Google Sheets atau CSV lokal melalui callback bawaan aplikasi
                        save_users(df_users)
                        
                        # Catat ke log audit aktivitas harian kandang
                        add_activity_log(user_name, "Edit Operator", f"Mengubah hak akses menu / profil akun '{user_terpilih}' (Role: {edit_role}).")
                        
                        st.success(f"🎉 Berhasil memperbarui konfigurasi akun '{user_terpilih}'!")
                        st.rerun()
                    
    # ==================== TAB 4: HAPUS AKSES AKUN ====================
    with tab_user_hapus:
        st.write("### Hapus Akses Akun")
        list_hapus = df_users[df_users["Username"].astype(str).str.lower() != "admin"]["Username"].tolist()
        if not list_hapus:
            st.info("Tidak ada akun operator tambahan yang bisa dihapus.")
        else:
            user_yang_dihapus = st.selectbox("Pilih Akun yang Akan Dihapus Aksesnya:", list_hapus, key="sb_hapus_user_pilih")
            if st.button("Hapus Akun Selamanya", type="primary", use_container_width=True):
                df_users = df_users[df_users["Username"] != user_yang_dihapus]
                save_users(df_users)
                add_activity_log(user_name, "Hapus Operator", f"Menghapus akun pengguna '{user_yang_dihapus}' dari sistem.")
                st.success(f"🗑️ Akun '{user_yang_dihapus}' berhasil dihapus secara permanen!")
                st.rerun()