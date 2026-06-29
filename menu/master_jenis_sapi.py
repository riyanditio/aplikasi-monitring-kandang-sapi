import streamlit as st
import pandas as pd

def tampilkan_menu_jenis_sapi(LIST_JENIS_SAPI, save_jenis_sapi, add_activity_log, user_name):
    st.subheader("🐂 Kelola Master Pilihan Jenis Sapi")
    tab_lihat, tab_tambah, tab_edit, tab_hapus = st.tabs(["📋 Daftar Jenis Sapi", "➕ Tambah Jenis Baru", "✏️ Edit Jenis", "❌ Hapus Jenis"])
    
    with tab_lihat:
        st.dataframe(
            pd.DataFrame({"No": range(1, len(LIST_JENIS_SAPI) + 1), "Nama Jenis Sapi": LIST_JENIS_SAPI}), 
            use_container_width=True, 
            hide_index=True
        )
        
    with tab_tambah:
        with st.form("form_tambah_jenis"):
            input_jenis_baru = st.text_input("Nama Jenis Sapi Baru")
            if st.form_submit_button("Simpan", type="primary") and input_jenis_baru.strip():
                LIST_JENIS_SAPI.append(input_jenis_baru.strip())
                save_jenis_sapi(LIST_JENIS_SAPI)
                add_activity_log(user_name, "Tambah Jenis Sapi", f"Menambahkan varietas jenis sapi baru: {input_jenis_baru.strip()}")
                st.success("Sukses!")
                st.rerun()
                
    with tab_edit:
        if not LIST_JENIS_SAPI:
            st.info("Belum ada jenis sapi yang terdaftar.")
        else:
            jenis_diubah = st.selectbox("Pilih Jenis Sapi", LIST_JENIS_SAPI, key="sb_edit_j")
            nama_baru = st.text_input("Nama Baru", value=jenis_diubah)
            if st.button("Simpan Perubahan"):
                idx_j = LIST_JENIS_SAPI.index(jenis_diubah)
                LIST_JENIS_SAPI[idx_j] = nama_baru.strip()
                save_jenis_sapi(LIST_JENIS_SAPI)
                add_activity_log(user_name, "Edit Jenis Sapi", f"Mengubah nama jenis sapi dari '{jenis_diubah}' menjadi '{nama_baru.strip()}'.")
                st.success("Berhasil diubah!")
                st.rerun()
                
    with tab_hapus:
        if not LIST_JENIS_SAPI:
            st.info("Belum ada jenis sapi yang bisa dihapus.")
        else:
            jenis_dihapus = st.selectbox("Pilih Jenis Sapi yang Dihapus", LIST_JENIS_SAPI, key="sb_hapus_j")
            if st.button("Hapus Permanen", type="primary"):
                if jenis_dihapus in LIST_JENIS_SAPI:
                    LIST_JENIS_SAPI.remove(jenis_dihapus)
                    save_jenis_sapi(LIST_JENIS_SAPI)
                    add_activity_log(user_name, "Hapus Jenis Sapi", f"Menghapus varietas jenis sapi: {jenis_dihapus}")
                    st.success("Terhapus!")
                    st.rerun()