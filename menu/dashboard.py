import streamlit as st
import pandas as pd

def tampilkan_dashboard(df_sapi):
    st.subheader("📊 Dashboard Utama & Pemantauan Populasi Kontinu")

    if df_sapi.empty:
        st.info("👋 Selamat Datang! Database kosong. Sapi baru belum ada yang terregistrasi masuk kandang.")
        return

    # Tentukan Target ADG Standar Kandang
    TARGET_ADG = 1.6

    # Pisahkan data: Sapi Baru vs Sapi yang Sudah Pernah Ditimbang Berkala
    # Sapi baru memiliki Tgl Cek Akhir yang SAMA dengan Tgl Masuk
    df_sudah_timbang_berkala = df_sapi[df_sapi["Tgl Cek Akhir"].astype(str) != df_sapi["Tgl Masuk"].astype(str)].copy()

    # Hitung KPI Utama Global
    total_ekor = len(df_sapi)
    rata_bobot = df_sapi["Bobot Akhir (kg)"].mean()
    
    # Rata-rata ADG kandang hanya dihitung dari sapi yang sudah aktif ditimbang berkala agar akurat
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
            with st.expander("🔍 Lihat Daftar Sapi Performa Rendah"):
                st.dataframe(
                    df_underperform[["Kode Sapi", "Jenis Sapi", "Lokasi Pen", "ADG (kg/hari)", "Tgl Cek Akhir"]].sort_values(by="ADG (kg/hari)"),
                    use_container_width=True,
                    hide_index=True
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
    st.dataframe(df_sapi.drop(columns=['Blok Kandang']), use_container_width=True, hide_index=True)