import streamlit as st
import pandas as pd

def tampilkan_dashboard(df_sapi, read_sheet_to_df):
    st.subheader("📊 Dashboard Utama & Pemantauan Populasi Berkala")

    if df_sapi.empty:
        st.info("👋 Selamat Datang! Database kosong. Sapi baru belum ada yang terregistrasi masuk kandang.")
        return

    TARGET_ADG = 1.6

    df_sudah_timbang_berkala = df_sapi[df_sapi["Tgl Cek Akhir"].astype(str) != df_sapi["Tgl Masuk"].astype(str)].copy()

    total_ekor = len(df_sapi)
    rata_bobot = df_sapi["Bobot Akhir (kg)"].mean()
    
    if not df_sudah_timbang_berkala.empty:
        rata_adg = df_sudah_timbang_berkala["ADG (kg/hari)"].mean()
        status_adg = f"{rata_adg - TARGET_ADG:+.2f} dari target"
    else:
        rata_adg = 0.0
        status_adg = "Belum ada data penimbangan berkala"

    m1, m2, m3 = st.columns(3)
    m1.metric("📦 Total Populasi Aktif", f"{total_ekor} Ekor")
    m2.metric("⚖️ Rata-rata Bobot Sapi", f"{rata_bobot:.2f} kg")
    m3.metric("📈 Rata-rata ADG Kandang Tracked", f"{rata_adg:.2f} kg/hari", delta=status_adg if rata_adg > 0 else None)

    st.markdown("---")
    if not df_sudah_timbang_berkala.empty:
        df_sudah_timbang_berkala["ADG (kg/hari)"] = df_sudah_timbang_berkala["ADG (kg/hari)"].astype(float)
        df_underperform = df_sudah_timbang_berkala[df_sudah_timbang_berkala["ADG (kg/hari)"] < TARGET_ADG]

        if not df_underperform.empty:
            st.warning(f"⚠️ **PERINGATAN DETEKSI PERFORMA:** Ditemukan **{len(df_underperform)} ekor** sapi dengan pertumbuhan di bawah target ({TARGET_ADG} kg/hari).")
            
            df_underperform_view = df_underperform.copy()
            rename_underperform = {"Kode Sapi": "Kode Tiba", "RFID/Tag": "RFID/Tag Kandang"}
            df_underperform_view = df_underperform_view.rename(columns=rename_underperform)
            
            with st.expander("🔍 Lihat Daftar Sapi Performa Rendah"):
                st.dataframe(
                    df_underperform_view[["Kode Tiba", "RFID/Tag Kandang", "Jenis Sapi", "Lokasi Pen", "ADG (kg/hari)", "Tgl Cek Akhir"]].sort_values(by="ADG (kg/hari)"),
                    use_container_width=True, hide_index=True,
                    column_config={"ADG (kg/hari)": st.column_config.NumberColumn("ADG (kg/hari)", format="%.2f")}
                )
        else:
            st.success(f"✅ **Kondisi Bagus:** Semua sapi yang sudah ditimbang berkala berhasil mencapai atau melewati target pertumbuhan {TARGET_ADG} kg/hari!")
    else:
        st.info("ℹ️ **Informasi:** Seluruh populasi saat ini masih dalam masa awal masuk / karantina.")

    st.markdown("---")
    st.markdown("### 🏢 Ringkasan Kinerja per Blok Kandang")
    df_sapi['Blok Kandang'] = df_sapi['Lokasi Pen'].apply(lambda x: str(x).split(' - ')[0] if ' - ' in str(x) else 'Format Lama')
    
    df_summary_blok = df_sapi.groupby('Blok Kandang').agg(Pop=('Kode Sapi', 'count'), Adg_Blok=('ADG (kg/hari)', 'mean')).reset_index()

    cols_blok = st.columns(len(df_summary_blok))
    for i, row_b in df_summary_blok.iterrows():
        with cols_blok[i]:
            st.metric(label=f"🏢 {row_b['Blok Kandang'].upper()}", value=f"{row_b['Pop']} Ekor", delta=f"{row_b['Adg_Blok']:.2f} kg/hari ADG" if row_b['Adg_Blok'] > 0 else None)

    st.markdown("---")
    tab_grafik, tab_tabel = st.tabs(["📊 Grafik Analisis Performa", "📋 Tabel Monitor Seluruh Sapi"])
    
    with tab_grafik:
        cg1, cg2 = st.columns(2)
        with cg1:
            st.markdown("**📈 Rata-rata Pertumbuhan (ADG) per Blok Kandang**")
            df_chart_adg = df_sapi.groupby("Blok Kandang")["ADG (kg/hari)"].mean().reset_index().set_index("Blok Kandang")
            st.bar_chart(df_chart_adg["ADG (kg/hari)"], color="#2670e8")
        with cg2:
            st.markdown("**🐂 Distribusi Komposisi Jenis/Rumpun Sapi**")
            df_chart_jenis = df_sapi["Jenis Sapi"].value_counts().reset_index()
            df_chart_jenis.columns = ["Jenis Sapi", "Jumlah (Ekor)"]
            st.bar_chart(df_chart_jenis.set_index("Jenis Sapi")["Jumlah (Ekor)"], color="#ff9800")

    with tab_tabel:
        st.markdown("💡 **Legenda Warna:** 🟥 Merah = Pen Isolasi/Sakit | 🟨 Kuning = Performa Rendah (ADG < Target)")
        
        def style_monitor_kandang(row):
            lokasi = str(row.get("Lokasi Pen", ""))
            if "Isolasi" in lokasi: return ['background-color: rgba(255, 75, 75, 0.2)'] * len(row)
            try:
                adg = float(row.get("ADG (kg/hari)", 0.0))
                tgl_cek = str(row.get("Tgl Cek Akhir", ""))
                tgl_masuk = str(row.get("Tgl Masuk", ""))
                if adg < 1.6 and tgl_cek != tgl_masuk and tgl_cek != "nan":
                    return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
            except: pass
            return [''] * len(row)

        df_monitor = df_sapi.drop(columns=['Blok Kandang']).copy()
        df_monitor = df_monitor.rename(columns={"Kode Sapi": "Kode Tiba", "RFID/Tag": "RFID/Tag Kandang"})
        if "RFID/Tag Asal" not in df_monitor.columns: df_monitor["RFID/Tag Asal"] = "-"
        
        cols_order = list(df_monitor.columns)
        if "Kode Tiba" in cols_order and "RFID/Tag Asal" in cols_order:
            cols_order.remove("RFID/Tag Asal")
            cols_order.insert(cols_order.index("Kode Tiba") + 1, "RFID/Tag Asal")
            df_monitor = df_monitor[cols_order]

        st.dataframe(
            df_monitor.style.apply(style_monitor_kandang, axis=1), 
            use_container_width=True, hide_index=True,
            column_config={
                "Bobot Awal (kg)": st.column_config.NumberColumn("Bobot Awal (kg)", format="%.2f"),
                "Bobot Akhir (kg)": st.column_config.NumberColumn("Bobot Akhir (kg)", format="%.2f"),
                "ADG (kg/hari)": st.column_config.NumberColumn("ADG (kg/hari)", format="%.2f"),
                "Total Pakan (kg)": st.column_config.NumberColumn("Total Pakan (kg)", format="%.2f")
            }
        )

    # ==================== FITUR PENCARIAN PROFIL SAPI ====================
    st.markdown("---")
    st.markdown("### 🔍 Pencarian Riwayat & Profil Lengkap Sapi")
    
    opsi_cari_sapi = df_sapi.apply(lambda r: f"{r['Kode Sapi']} - RFID: {r['RFID/Tag']}", axis=1).tolist()
    sapi_dicari = st.selectbox("Pilih / Ketik Nomor Sapi untuk melihat detail perjalanan:", ["-- Silakan Pilih Sapi --"] + opsi_cari_sapi)

    if sapi_dicari != "-- Silakan Pilih Sapi --":
        kode_cari = sapi_dicari.split(" - RFID: ")[0]
        rfid_cari = sapi_dicari.split(" - RFID: ")[1]
        
        info_sapi = df_sapi[(df_sapi["Kode Sapi"] == kode_cari) & (df_sapi["RFID/Tag"] == rfid_cari)].iloc[0]
        
        st.info(f"**Profil Sapi:** Jenis {info_sapi['Jenis Sapi']} | Kelamin {info_sapi['Jenis Kelamin']} | Masuk: {info_sapi['Tgl Masuk']} | Posisi Saat Ini: **{info_sapi['Lokasi Pen']}**")
        
        cl_hist1, cl_hist2 = st.columns(2)
        
        with cl_hist1:
            st.markdown("📊 **Riwayat Penimbangan**")
            df_r_timbang = read_sheet_to_df("riwayat_timbangan", ["Tanggal Timbang", "Kode Sapi", "RFID/Tag", "Lokasi Pen", "Bobot (kg)", "ADG (kg/hari)", "Operator"])
            df_r_timbang = df_r_timbang[(df_r_timbang["Kode Sapi"] == kode_cari) & (df_r_timbang["RFID/Tag"] == rfid_cari)]
            if not df_r_timbang.empty:
                st.dataframe(df_r_timbang[["Tanggal Timbang", "Bobot (kg)", "ADG (kg/hari)"]].sort_values("Tanggal Timbang", ascending=False), use_container_width=True, hide_index=True, column_config={"Bobot (kg)": st.column_config.NumberColumn(format="%.2f"), "ADG (kg/hari)": st.column_config.NumberColumn(format="%.2f")})
            else:
                st.write("*Belum ada riwayat timbangan berkala.*")

        with cl_hist2:
            st.markdown("🍽️ **Riwayat Pemberian Pakan (Spesifik/Medis)**")
            st.caption(f"*Total pakan terakumulasi selama di kandang: **{info_sapi['Total Pakan (kg)']:.2f} kg***")
            df_r_pakan = read_sheet_to_df("pakan_harian", ["Tanggal", "Lokasi Pen", "Metode", "Target Spesifik", "Jenis Pakan", "Jumlah Pakan (kg)", "Operator"])
            
            target_id = f"{kode_cari} - {rfid_cari}"
            df_r_pakan_spesifik = df_r_pakan[(df_r_pakan["Metode"] == "Spesifik") & (df_r_pakan["Target Spesifik"] == target_id)]
            
            if not df_r_pakan_spesifik.empty:
                st.dataframe(df_r_pakan_spesifik[["Tanggal", "Jenis Pakan", "Jumlah Pakan (kg)"]].sort_values("Tanggal", ascending=False), use_container_width=True, hide_index=True, column_config={"Jumlah Pakan (kg)": st.column_config.NumberColumn(format="%.2f")})
            else:
                st.write("*Belum ada riwayat pakan yang diinput secara individu/spesifik untuk sapi ini. Sapi mendapatkan pakan serentak harian di pen.*")