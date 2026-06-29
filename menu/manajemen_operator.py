import streamlit as st
import pandas as pd

def tampilkan_menu_operator(load_users, ALL_MENUS, save_users, add_activity_log, user_name):
    st.subheader("👥 Manajemen Akun Pengguna & Pengaturan Hak Akses Menu")
    df_users = load_users()
    tab_user_lihat, tab_user_tambah, tab_user_hapus = st.tabs(["📋 Daftar Anggota Aktif", "➕ Tambah Operator & Atur Menu", "❌ Hapus Akun"])
    
    with tab_user_lihat:
        st.write("### Daftar Pengguna & Akses Menu Lapangan")
        df_users_tampil = df_users.copy()
        df_users_tampil["Password"] = "******"
        df_users_tampil.index = range(1, len(df_users_tampil) + 1)
        st.dataframe(df_users_tampil, use_container_width=True)
        
    with tab_user_tambah:
        st.write("### Buat Akun Anggota Baru & Pilih Menunya")
        with st.form("form_tambah_operator"):
            new_username = st.text_input("Username Baru", placeholder="Contoh: ahmad_kandang").strip()
            new_password = st.text_input("Password Baru", type="password", placeholder="Masukkan password").strip()
            new_role = st.selectbox("Tingkat Akun (Role)", ["Operator", "Admin"])
            
            st.markdown("---")
            st.markdown("##### 🔑 Pilih Menu yang Boleh Diakses Akun Ini:")
            chosen_menus = st.multiselect(
                "Centang menu yang diberikan izin:", 
                options=ALL_MENUS, 
                default=[ALL_MENUS[0], ALL_MENUS[1], ALL_MENUS[4], ALL_MENUS[5]]
            )
            
            if st.form_submit_button("Daftarkan Akun", type="primary"):
                if not new_username or not new_password:
                    st.error("❌ Username dan Password tidak boleh kosong!")
                elif not chosen_menus:
                    st.error("❌ Operator harus diberikan minimal 1 pilihan hak akses menu!")
                elif new_username.lower() in df_users["Username"].astype(str).str.lower().values:
                    st.error(f"❌ Username '{new_username}' sudah terdaftar.")
                else:
                    menus_str = "|".join(chosen_menus)
                    new_account = pd.DataFrame([{"Username": new_username, "Password": new_password, "Role": new_role, "Menus": menus_str}])
                    df_users = pd.concat([df_users, new_account], ignore_index=True)
                    save_users(df_users)
                    add_activity_log(user_name, "Tambah Operator", f"Membuat akun pengguna baru '{new_username}' dengan hak akses {new_role}.")
                    st.success(f"🎉 Sukses! Akun '{new_username}' berhasil aktif.")
                    st.rerun()
                    
    with tab_user_hapus:
        st.write("### Hapus Akses Akun")
        list_hapus = df_users[df_users["Username"].astype(str).str.lower() != "admin"]["Username"].tolist()
        if not list_hapus:
            st.info("Tidak ada akun operator tambahan yang bisa dihapus.")
        else:
            user_yang_dihapus = st.selectbox("Pilih Akun yang Akan Dihapus Aksesnya:", list_hapus)
            if st.button("Hapus Akun Selamanya", type="primary"):
                df_users = df_users[df_users["Username"] != user_yang_dihapus]
                save_users(df_users)
                add_activity_log(user_name, "Hapus Operator", f"Menghapus/menonaktifkan akun pengguna: {user_yang_dihapus}")
                st.success(f"🗑️ Akun '{user_yang_dihapus}' berhasil dinonaktifkan.")
                st.rerun()