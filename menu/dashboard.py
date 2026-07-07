import streamlit as st
import pandas as pd

def tampilkan_dashboard(df_sapi):
    st.subheader("📊 Dashboard Utama & Pemantauan Populasi Berkala")

    if df_sapi.empty:
        st.info("👋 Selamat Datang! Database kosong. Sapi baru belum ada yang terregistrasi masuk kandang.")
        return

    # Tentukan Target ADG Standar Kandang
    TARGET_ADG = 1.6

    # Pisahkan data: Sapi Baru vs Sapi yang Sudah Pernah Ditimbang Berkala
    df_sudah_timbang_berkala = df_sapi[df_sapi["Tgl Cek Akhir"].astype(str) != df_sapi["Tgl Masuk"].astype(str)].copy()

    # Hitung KPI Utama Global
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
    m2.metric("⚖️ Rata-rata Bobot Sapi", f"{rata_bobot:.1f} kg")
    m3.metric("📈 Rata-rata ADG Kandang Tracked", f"{rata_adg:.2f} kg/hari", delta=status_adg if rata_adg > 0 else None)

    # --- FITUR PERINGATAN: MENAMPILKAN RFID ---
    st.markdown("---")
    if not df_sudah_timbang_berkala.empty:
        df_sudah_timbang_berkala["ADG (kg/hari)"] = df_sudah_timbang_berkala["ADG (kg/hari)"].astype(float)
        df_underperform = df_sudah_timbang_berkala[df_sudah_timbang_berkala["ADG (kg/hari)"] < TARGET_ADG]

        if not df_underperform.empty:
            st.warning(f"⚠️ **PERINGATAN DETEKSI PERFORMA:** Ditemukan **{len(df_underperform)} ekor** sapi dalam masa penggemukan aktif dengan pertumbuhan di bawah target ({TARGET_ADG} kg/hari). Perlu evaluasi pakan atau kesehatan!")
            
            df_underperform_view = df_underperform.copy()
            rename_underperform = {}
            if "Kode Sapi" in df_underperform_view.columns:
                rename_underperform["Kode Sapi"] = "Kode Tiba"
            if "RFID/Tag" in df_underperform_view.columns:
                rename_underperform["RFID/Tag"] = "RFID/Tag Kandang"
            df_underperform_view = df_underperform_view.rename(columns=rename_underperform)
            
            with st.expander("🔍 Lihat Daftar Sapi Performa Rendah"):
                # Menambahkan 'RFID/Tag Kandang' pada daftar kolom agar bisa diidentifikasi
                st.dataframe(
                    df_underperform_view[["Kode Tiba", "RFID/Tag Kandang", "Jenis Sapi", "Lokasi Pen", "ADG (kg/hari)", "Tgl Cek Akhir"]].sort_values(by="ADG (kg/hari)"),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Kode Tiba": st.column_config.TextColumn("Kode Tiba"),
                        "RFID/Tag Kandang": st.column_config.TextColumn("RFID Kandang"),
                        "Jenis Sapi": st.column_config.TextColumn("Jenis Sapi"),
                        "Lokasi Pen": st.column_config.TextColumn("Lokasi Pen"),
                        "ADG (kg/hari)": st.column_config.NumberColumn("ADG (kg/hari)", format="%.2f"),
                        "Tgl Cek Akhir": st.column_config.TextColumn("Tgl Cek Akhir")
                    }
                )
        else:
            st.success(f"✅ **Kondisi Bagus:** Semua sapi yang sudah ditimbang berkala berhasil mencapai atau melewati target pertumbuhan {TARGET_ADG} kg/hari!")
    else:
        st.info("ℹ️ **Informasi:** Seluruh populasi saat ini masih dalam masa awal masuk / karantina. Peringatan ADG akan aktif otomatis setelah penimbangan rutin bulan depan dilakukan.")

    st.markdown("---")
    st.markdown("### 🏢 Ringkasan Kinerja per Blok Kandang")

    # Ekstrak nama Blok Kandang
    df_sapi['Blok Kandang'] = df_sapi['Lokasi Pen'].apply(lambda x: str(x).split(' - ')[0] if ' - ' in str(x) else 'Format Lama')
    
    df_summary_blok = df_sapi.groupby('Blok Kandang').agg(
        Pop=( 'Kode Sapi', 'count'),
        Adg_Blok=('ADG (kg/hari)', 'mean')
    ).reset_index()

    # Tampilkan Grid Dinamis Metric per Blok Kandang
    cols_blok = st.columns(len(df_summary_blok))
    for i, row_b in df_summary_blok.iterrows():
        with cols_blok[i]:
            st.metric(
                label=f"🏢 {row_b['Blok Kandang'].upper()}", 
                value=f"{row_b['Pop']} Ekor", 
                delta=f"{row_b['Adg_Blok']:.2f} kg/hari ADG" if row_b['Adg_Blok'] > 0 else None
            )

    st.markdown("---")
    
    tab_grafik, tab_tabel = st.tabs(["📊 Grafik Analisis Performa", "📋 Tabel Monitor Seluruh Sapi"])
    
    with tab_grafik:
        st.markdown("#### 🎯 Analisis Visual Populasi Kandang")
        cg1, cg2 = st.columns(2)
        
        with cg1:
            st.markdown("**📈 Rata-rata Pertumbuhan (ADG) per Blok Kandang**")
            df_chart_adg = df_sapi.groupby("Blok Kandang")["ADG (kg/hari)"].mean().reset_index()
            df_chart_adg = df_chart_adg.set_index("Blok Kandang")
            st.bar_chart(df_chart_adg["ADG (kg/hari)"], color="#2670e8", use_container_width=True)
            st.caption("💡 *Gunakan grafik ini untuk melihat blok mana yang pertumbuhannya paling agresif atau tertinggal.*")
            
        with cg2:
            st.markdown("**🐂 Distribusi Komposisi Jenis/Rumpun Sapi**")
            df_chart_jenis = df_sapi["Jenis Sapi"].value_counts().reset_index()
            df_chart_jenis.columns = ["Jenis Sapi", "Jumlah (Ekor)"]
            df_chart_jenis = df_chart_jenis.set_index("Jenis Sapi")
            st.bar_chart(df_chart_jenis["Jumlah (Ekor)"], color="#ff9800", use_container_width=True)
            st.caption("💡 *Representasi volume populasi berdasarkan varietas ras sapi yang masuk kandang.*")

    with tab_tabel:
        st.markdown("💡 **Legenda Warna:** 🟥 Merah = Pen Isolasi/Sakit | 🟨 Kuning = Performa Rendah (ADG < Target)")
        
        # --- FUNGSI PEWARNAAN TABEL DASHBOARD ---
        def style_monitor_kandang(row):
            lokasi = str(row.get("Lokasi Pen", ""))
            if "Isolasi" in lokasi:
                return ['background-color: rgba(255, 75, 75, 0.2)'] * len(row)
            
            try:
                adg = float(row.get("ADG (kg/hari)", 0.0))
                tgl_cek = str(row.get("Tgl Cek Akhir", ""))
                tgl_masuk = str(row.get("Tgl Masuk", ""))
                if adg < 1.6 and tgl_cek != tgl_masuk and tgl_cek != "nan":
                    return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
            except:
                pass
            return [''] * len(row)

        df_monitor = df_sapi.drop(columns=['Blok Kandang']).copy()
        
        rename_main = {}
        if "Kode Sapi" in df_monitor.columns:
            rename_main["Kode Sapi"] = "Kode Tiba"
        if "RFID/Tag" in df_monitor.columns:
            rename_main["RFID/Tag"] = "RFID/Tag Kandang"
        df_monitor = df_monitor.rename(columns=rename_main)
        
        if "RFID/Tag Asal" not in df_monitor.columns:
            df_monitor["RFID/Tag Asal"] = "-"
            
        cols_order = list(df_monitor.columns)
        if "Kode Tiba" in cols_order and "RFID/Tag Asal" in cols_order:
            cols_order.remove("RFID/Tag Asal")
            idx_kode_tiba = cols_order.index("Kode Tiba")
            cols_order.insert(idx_kode_tiba + 1, "RFID/Tag Asal")
            df_monitor = df_monitor[cols_order]

        styled_monitor_df = df_monitor.style.apply(style_monitor_kandang, axis=1)

        st.dataframe(
            styled_monitor_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Kode Tiba": st.column_config.TextColumn("Kode Tiba"),
                "RFID/Tag Asal": st.column_config.TextColumn("RFID/Tag Asal"),
                "RFID/Tag Kandang": st.column_config.TextColumn("RFID/Tag Kandang"),
                "Jenis Sapi": st.column_config.TextColumn("Jenis Sapi"),
                "Lokasi Pen": st.column_config.TextColumn("Lokasi Pen"),
                "Bobot Awal (kg)": st.column_config.NumberColumn("Bobot Awal (kg)", format="%d"),
                "Bobot Akhir (kg)": st.column_config.NumberColumn("Bobot Akhir (kg)", format="%d"),
                "ADG (kg/hari)": st.column_config.NumberColumn("ADG (kg/hari)", format="%.2f"),
                "Total Pakan (kg)": st.column_config.NumberColumn("Total Pakan (kg)", format="%.2f"),
                "Tgl Masuk": st.column_config.TextColumn("Tgl Masuk"),
                "Tgl Cek Akhir": st.column_config.TextColumn("Tgl Cek Akhir"),
                "Tgl Pakan Terakhir": st.column_config.TextColumn("Tgl Pakan Terakhir"),
            }
        )