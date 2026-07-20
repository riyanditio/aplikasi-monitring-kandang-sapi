import streamlit as st
import pandas as pd

def tampilkan_menu_log(read_sheet_to_df, write_df_to_sheet):
    st.subheader("📜 Log Riwayat Aktivitas Harian Operator")
    
    # Skema lengkap di database audit_ip_logs
    cols_audit = ["Tanggal & Waktu", "Operator", "Aktivitas", "Detail Keterangan", "IP Address", "Perangkat", "User Agent"]
    
    # Skema khusus tampilan layar operator (IP & Perangkat disembunyikan)
    cols_tampil = ["Tanggal & Waktu", "Operator", "Aktivitas", "Detail Keterangan"]
    
    # Membaca data langsung dari tabel tunggal audit_ip_logs
    df_logs = read_sheet_to_df("audit_ip_logs", cols_audit)
    
    if df_logs.empty: 
        st.info("Belum ada log aktivitas.")
    else:
        col_log1, col_log2, col_log3 = st.columns(3)
        with col_log1:
            filter_op = st.selectbox("Filter Operator", ["Semua"] + sorted(df_logs["Operator"].dropna().unique().tolist()))
        with col_log2:
            filter_act = st.selectbox("Filter Aktivitas", ["Semua"] + sorted(df_logs["Aktivitas"].dropna().unique().tolist()))
        with col_log3:
            search_detail = st.text_input("Cari Kata Kunci Detail")

        df_logs_filtered = df_logs.copy()
        if filter_op != "Semua": df_logs_filtered = df_logs_filtered[df_logs_filtered["Operator"] == filter_op]
        if filter_act != "Semua": df_logs_filtered = df_logs_filtered[df_logs_filtered["Aktivitas"] == filter_act]
        if search_detail.strip(): df_logs_filtered = df_logs_filtered[df_logs_filtered["Detail Keterangan"].astype(str).str.contains(search_detail.strip(), case=False)]

        if not df_logs_filtered.empty:
            df_logs_filtered = df_logs_filtered.iloc[::-1].reset_index(drop=True)
            df_logs_filtered.index = range(1, len(df_logs_filtered) + 1)
            
            # Hanya menampilkan kolom umum ke operator
            st.dataframe(df_logs_filtered[cols_tampil], use_container_width=True)
        else:
            st.info("Log tidak ditemukan berdasarkan kriteria filter.")
        
        st.markdown("---")
        if st.button("🗑️ Bersihkan Semua Log Aktivitas", type="secondary"):
            if st.session_state["role"] == "Admin":
                write_df_to_sheet("audit_ip_logs", pd.DataFrame(columns=cols_audit), cols_audit)
                st.success("Log berhasil dibersihkan!")
                st.rerun()
            else: 
                st.error("❌ Hanya Admin yang bisa menghapus log.")