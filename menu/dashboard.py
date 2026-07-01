import streamlit as st
import pandas as pd

def tampilkan_dashboard(df_sapi):
    # --- PERUBAHAN JUDUL: Mengganti Kontinu menjadi Berkala ---
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

    # --- FITUR PERINGATAN: HANYA UNTUK SAPI YANG SUDAH DITIMBANG KE-2 DST ---
    st.markdown("---")
    if not df_sudah_timbang_berkala.empty:
        df_sudah_timbang_berkala["ADG (kg/hari)"] = df_sudah_timbang_berkala["ADG (kg/hari)"].astype(float)
        df_underperform = df_sudah_timbang_berkala[df_sudah_timbang_berkala["ADG (kg/hari)"] < TARGET_ADG]

        if not df_underperform.empty:
            st.warning(f"⚠️ **PERINGATAN DETEKSI PERFORMA:** Ditemukan **{len(df_underperform)} ekor** sapi dalam masa penggemukan aktif dengan pertumbuhan di bawah target ({TARGET_ADG} kg/hari). Perlu evaluasi pakan atau kesehatan!")
            
            # Koreksi visualisasi header pada tabel peringatan performa rendah
            df_underperform_view = df_underperform.copy()
            rename_underperform = {}
            if "Kode Sapi" in df_underperform_view.columns:
                rename_underperform["Kode Sapi"] = "Kode Tiba"
            if "RFID/Tag" in df_underperform_view.columns:
                rename_underperform["RFID/Tag"] = "RFID/Tag Kandang"
            df_underperform_view = df_underperform_view.rename(columns=rename_underperform)
            
            with st.expander("🔍 Lihat Daftar Sapi Performa Rendah"):
                # FIX: Menghapus parameter width statis agar tabel auto-size sempurna
                st.dataframe(
                    df_underperform_view[["Kode Tiba", "Jenis Sapi", "Lokasi Pen", "ADG (kg/hari)", "Tgl Cek Akhir"]].sort_values(by="ADG (kg/hari)"),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Kode Tiba": st.column_config.TextColumn("Kode Tiba"),
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
    st.markdown("### 📋 Tabel Monitor Seluruh Sapi di Area")
    
    # ==================== PROSES ADAPTASI STRUKTUR TABEL BARU ====================
    df_monitor = df_sapi.drop(columns=['Blok Kandang']).copy()
    
    # 1. Ganti judul kolom Lama ke Baru
    rename_main = {}
    if "Kode Sapi" in df_monitor.columns:
        rename_main["Kode Sapi"] = "Kode Tiba"
    if "RFID/Tag" in df_monitor.columns:
        rename_main["RFID/Tag"] = "RFID/Tag Kandang"
    df_monitor = df_monitor.rename(columns=rename_main)
    
    # 2. Sisipkan Kolom 'RFID/Tag Asal' tepat setelah 'Kode Tiba'
    if "RFID/Tag Asal" not in df_monitor.columns:
        df_monitor["RFID/Tag Asal"] = "-"  # Penanda default strip sebelum database di-migrasi
        
    cols_order = list(df_monitor.columns)
    if "Kode Tiba" in cols_order and "RFID/Tag Asal" in cols_order:
        cols_order.remove("RFID/Tag Asal")
        idx_kode_tiba = cols_order.index("Kode Tiba")
        cols_order.insert(idx_kode_tiba + 1, "RFID/Tag Asal")
        df_monitor = df_monitor[cols_order]

    # FIX: Seluruh batasan width kaku di bawah ini dihapus agar tabel melebar otomatis mengikuti layar
    st.dataframe(
        df_monitor, 
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