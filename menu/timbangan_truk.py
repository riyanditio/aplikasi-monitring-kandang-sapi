import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_menu_timbangan_truk(add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet):
    st.subheader("🚛 Timbangan Armada Truk (Logistik & Manifest)")
    st.markdown("Pencatatan berat jembatan timbang untuk kontrol armada logistik dan manifestasi muatan sapi.")

    # Definisi kolom tabel jembatan timbang
    cols_truk = [
        "No Transaksi", "Tanggal", "Nama Lokasi Penimbangan", "No Plat / Armada", 
        "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", 
        "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Daftar RFID/EarTag", 
        "Rata-rata / Ekor (kg)", "Operator Lapangan"
    ]
    
    # [LAZY LOADING] Menarik data hanya saat menu ini aktif dibuka oleh user
    df_truk = read_sheet_to_df("timbangan_truk", cols_truk)

    # Membuat Tabulasi Menu agar rapi seperti menu Karantina
    tab_input, tab_edit_hapus, tab_riwayat = st.tabs([
        "📝 Input Manifest Timbangan", 
        "⚙️ Edit / Hapus Data Timbangan", 
        "📜 Riwayat & Historis"
    ])

    # ==================== TAB 1: INPUT MANIFEST TIMBANGAN ====================
    with tab_input:
        with st.form("form_timbangan_truk", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                no_transaksi = st.text_input("No Transaksi (Otomatis jika kosong)", placeholder="Contoh: TRK-2026-001").strip()
                tgl_timbang = st.date_input("Tanggal Penimbangan", datetime.now().date())
                
                # Pilihan Lokasi Penimbangan Komprehensif
                lokasi_timbang = st.selectbox("Nama Lokasi Penimbangan", [
                    "Jembatan Timbang Utama (Kandang)", 
                    "Timbangan Digital Area Karantina",
                    "Jembatan Timbang Pelabuhan Dalam Negeri",
                    "Timbangan Luar / Pihak Ketiga"
                ])
                
                no_plat = st.text_input("No Plat / Armada Truk", placeholder="Contoh: B 9123 FDA").strip()
                
                # --- INTEGRASI TOTAL OPSI STATUS MUATAN ---
                opsi_muatan = [
                    "Sapi Masuk (Bongkar/Unloading dari Luar)",
                    "Sapi Keluar (Muat/Loading Penjualan)",
                    "sapi kedatangan (pelabuhan dalam negeri)",
                    "sapi keberangkatan (pelabuhan negara asal)",
                    "Mutasi Antar Blok (Internal)",
                    "Pakan Ternak / Konsentrat / Hijauan",
                    "Logistik Umum / Muatan Lain",
                    "Lain-lain"
                ]
                keterangan_muatan = st.selectbox("Keterangan Status Muatan", opsi_muatan)

            with col2:
                bruto = st.number_input("Bruto / Berat Kotor (kg)", min_value=0.0, value=0.0, step=10.0)
                tara = st.number_input("Tara / Berat Kosong Truk (kg)", min_value=0.0, value=0.0, step=10.0)
                jumlah_sapi = st.number_input("Jumlah Sapi didalam Truk (Ekor)", min_value=0, value=0, step=1)
                
                # Daftar RFID/EarTag Manifest
                rfid_list = st.text_area(
                    "Daftar RFID / EarTAG didalam Truk", 
                    placeholder="Scan atau ketik nomor RFID/EarTag di sini.\nGunakan tombol Enter untuk memisahkan setiap ID sapi.",
                    help="Bisa digunakan untuk memisahkan manifestasi data sapi per armada truk."
                ).strip()

            st.markdown("---")
            submit_btn = st.form_submit_button("Simpan Manifest Timbangan Truk", type="primary", use_container_width=True)

            if submit_btn:
                if not no_plat:
                    st.error("❌ Gagal Simpan! No Plat / Armada Truk wajib diisi.")
                    return
                if bruto <= 0:
                    st.error("❌ Gagal Simpan! Berat bruto harus lebih besar dari 0 kg.")
                    return
                
                # Hitung Netto (Berat Bersih Muatan)
                netto = bruto - tara
                if netto < 0:
                    st.error("❌ Gagal Simpan! Berat kosong (Tara) tidak boleh melebihi berat kotor (Bruto).")
                    return

                # Hitung rata-rata bobot per ekor di dalam truk
                rata_per_ekor = round(netto / jumlah_sapi, 2) if jumlah_sapi > 0 else 0.0

                # Generate otomatis No Transaksi jika dikosongkan operator
                if not no_transaksi:
                    waktu_str = datetime.now().strftime("%Y%m%d-%H%M%S")
                    no_transaksi = f"TRK-{waktu_str}"

                # Susun baris data baru sesuai struktur kolom database utama
                new_truk_row = {
                    "No Transaksi": no_transaksi,
                    "Tanggal": tgl_timbang.strftime("%Y-%m-%d"),
                    "Nama Lokasi Penimbangan": lokasi_timbang,
                    "No Plat / Armada": no_plat,
                    "Keterangan Muatan": keterangan_muatan,
                    "Bruto / Kotor (kg)": float(bruto),
                    "Tara / Kosong (kg)": float(tara),
                    "Netto / Bersih (kg)": float(netto),
                    "Jumlah Sapi (Ekor)": int(jumlah_sapi),
                    "Daftar RFID/EarTag": rfid_list if rfid_list else "-",
                    "Rata-rata / Ekor (kg)": float(rata_per_ekor),
                    "Operator Lapangan": user_name
                }

                # Gabungkan dan simpan langsung menggunakan fungsi database utama
                df_baru = pd.concat([df_truk, pd.DataFrame([new_truk_row])], ignore_index=True)
                write_df_to_sheet("timbangan_truk", df_baru, cols_truk)

                # Catat log audit aktivitas
                add_activity_log(user_name, "Timbangan Truk", f"Mencatat {keterangan_muatan} armada {no_plat} di {lokasi_timbang}")
                
                st.success(f"🎉 Berhasil menyimpan data manifest timbangan armada {no_plat}! Bersih muatan: {netto} kg.")
                st.balloons()
                st.rerun()

    # ==================== TAB 2: EDIT / HAPUS (OTORISASI ADMIN) ====================
    with tab_edit_hapus:
        st.markdown("### ⚙️ Otorisasi Koreksi & Penghapusan Manifest Timbangan")
        
        if df_truk.empty:
            st.info("Belum ada data timbangan truk yang tersimpan untuk dikoreksi.")
        else:
            # Membuat tampilan dataframe dengan No Urut pembantu agar operator mudah memilih baris
            df_truk_view = df_truk.copy()
            df_truk_view.insert(0, "No Urut", range(1, len(df_truk) + 1))
            st.dataframe(df_truk_view.sort_values(by="No Urut", ascending=True), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            idx_edit = st.number_input("Masukkan No Urut Data Timbangan yang Ingin Dikelola:", min_value=1, max_value=len(df_truk), step=1) - 1
            row_edit = df_truk.iloc[idx_edit]
            
            st.info(f"📋 **Data Terpilih:** Transaksi **{row_edit['No Transaksi']}** | Armada: **{row_edit['No Plat / Armada']}** ({row_edit['Keterangan Muatan']})")
            
            # Mengambil password admin resmi dari cloud secrets
            try:
                correct_admin_pwd = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                correct_admin_pwd = "admin123"
                
            aksi_pilihan = st.radio("Pilih Tindakan Pengelolaan:", ["✏️ Edit / Koreksi Data", "🗑️ Hapus Permanen Data"], horizontal=True)
            
            # --- SUB ACTION: EDIT DATA ---
            if aksi_pilihan == "✏️ Edit / Koreksi Data":
                with st.form("form_edit_timbangan_truk"):
                    st.markdown("#### 📝 Form Koreksi Data Manifest")
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        st.text_input("No Transaksi (Tidak Dapat Diubah)", value=str(row_edit["No Transaksi"]), disabled=True)
                        
                        # Amankan proses konversi teks tanggal ke tipe objek date streamit
                        try:
                            tgl_obj = datetime.strptime(str(row_edit["Tanggal"]), "%Y-%m-%d").date()
                        except:
                            tgl_obj = datetime.now().date()
                            
                        edit_tgl_timbang = st.date_input("Tanggal Penimbangan", value=tgl_obj)
                        
                        list_lokasi = [
                            "Jembatan Timbang Utama (Kandang)", 
                            "Timbangan Digital Area Karantina",
                            "Jembatan Timbang Pelabuhan Dalam Negeri",
                            "Timbangan Luar / Pihak Ketiga"
                        ]
                        try: idx_lokasi = list_lokasi.index(str(row_edit["Nama Lokasi Penimbangan"]))
                        except: idx_lokasi = 0
                        edit_lokasi_timbang = st.selectbox("Nama Lokasi Penimbangan", list_lokasi, index=idx_lokasi)
                        
                        edit_no_plat = st.text_input("No Plat / Armada Truk", value=str(row_edit["No Plat / Armada"])).strip()
                        
                        list_muatan = [
                            "Sapi Masuk (Bongkar/Unloading dari Luar)",
                            "Sapi Keluar (Muat/Loading Penjualan)",
                            "sapi kedatangan (pelabuhan dalam negeri)",
                            "sapi keberangkatan (pelabuhan negara asal)",
                            "Mutasi Antar Blok (Internal)",
                            "Pakan Ternak / Konsentrat / Hijauan",
                            "Logistik Umum / Muatan Lain",
                            "Lain-lain"
                        ]
                        try: idx_muatan = list_muatan.index(str(row_edit["Keterangan Muatan"]))
                        except: idx_muatan = 0
                        edit_keterangan_muatan = st.selectbox("Keterangan Status Muatan", list_muatan, index=idx_muatan)

                    with col_e2:
                        edit_bruto = st.number_input("Bruto / Berat Kotor (kg)", min_value=0.0, value=float(row_edit["Bruto / Kotor (kg)"]), step=10.0)
                        edit_tara = st.number_input("Tara / Berat Kosong Truk (kg)", min_value=0.0, value=float(row_edit["Tara / Kosong (kg)"]), step=10.0)
                        edit_jumlah_sapi = st.number_input("Jumlah Sapi didalam Truk (Ekor)", min_value=0, value=int(row_edit["Jumlah Sapi (Ekor)"]), step=1)
                        edit_rfid_list = st.text_area("Daftar RFID / EarTAG didalam Truk", value=str(row_edit["Daftar RFID/EarTag"])).strip()
                    
                    st.markdown("---")
                    pwd_admin_edit = st.text_input("🔐 Masukkan Password Admin untuk Validasi Koreksi:", type="password", key="pwd_edit_truk")
                    submit_edit_btn = st.form_submit_button("💾 Simpan Perubahan Data", type="primary", use_container_width=True)
                    
                    if submit_edit_btn:
                        if pwd_admin_edit != correct_admin_pwd:
                            st.error("❌ Gagal Simpan! Password Admin salah. Otorisasi Ditolak.")
                        elif not edit_no_plat:
                            st.error("❌ Gagal Simpan! No Plat / Armada Truk wajib diisi.")
                        elif edit_bruto <= 0:
                            st.error("❌ Gagal Simpan! Berat bruto harus lebih besar dari 0 kg.")
                        else:
                            # Hitung ulang netto & rata-rata baru hasil koreksi
                            edit_netto = edit_bruto - edit_tara
                            if edit_netto < 0:
                                st.error("❌ Gagal Simpan! Berat kosong (Tara) melebihi berat kotor (Bruto).")
                                return
                                
                            edit_rata = round(edit_netto / edit_jumlah_sapi, 2) if edit_jumlah_sapi > 0 else 0.0
                            
                            # Timpa baris data spesifik di DataFrame lokal
                            df_truk.at[idx_edit, "Tanggal"] = edit_tgl_timbang.strftime("%Y-%m-%d")
                            df_truk.at[idx_edit, "Nama Lokasi Penimbangan"] = edit_lokasi_timbang
                            df_truk.at[idx_edit, "No Plat / Armada"] = edit_no_plat
                            df_truk.at[idx_edit, "Keterangan Muatan"] = edit_keterangan_muatan
                            df_truk.at[idx_edit, "Bruto / Kotor (kg)"] = float(edit_bruto)
                            df_truk.at[idx_edit, "Tara / Kosong (kg)"] = float(edit_tara)
                            df_truk.at[idx_edit, "Netto / Bersih (kg)"] = float(edit_netto)
                            df_truk.at[idx_edit, "Jumlah Sapi (Ekor)"] = int(edit_jumlah_sapi)
                            df_truk.at[idx_edit, "Daftar RFID/EarTag"] = edit_rfid_list if edit_rfid_list else "-"
                            df_truk.at[idx_edit, "Rata-rata / Ekor (kg)"] = float(edit_rata)
                            df_truk.at[idx_edit, "Operator Lapangan"] = user_name
                            
                            with st.spinner("🔄 Memperbarui manifest timbangan di Supabase..."):
                                write_df_to_sheet("timbangan_truk", df_truk, cols_truk)
                                
                            add_activity_log(user_name, "Edit Timbangan Truk", f"Mengoreksi transaksi {row_edit['No Transaksi']} armada {edit_no_plat}")
                            st.success(f"✅ Data manifest transaksi {row_edit['No Transaksi']} Berhasil diperbarui!")
                            st.rerun()
                            
            # --- SUB ACTION: HAPUS PERMANEN ---
            elif aksi_pilihan == "🗑️ Hapus Permanen Data":
                st.warning(f"⚠️ **PERINGATAN KRUSIAL:** Anda akan menghapus data transaksi **{row_edit['No Transaksi']}** secara PERMANEN dari database cloud Supabase. Tindakan ini tidak dapat dibatalkan!")
                pwd_admin_hapus = st.text_input("🔐 Masukkan Password Admin untuk Validasi Penghapusan:", type="password", key="pwd_hapus_truk")
                
                if st.button("🗑️ Eksekusi Hapus Data Permanen", type="secondary", use_container_width=True):
                    if pwd_admin_hapus != correct_admin_pwd:
                        st.error("❌ Gagal Hapus! Password Admin salah. Akses Ditolak.")
                    else:
                        with st.spinner("🔄 Menghapus baris transaksi dari Supabase..."):
                            df_truk = df_truk.drop(index=idx_edit).reset_index(drop=True)
                            write_df_to_sheet("timbangan_truk", df_truk, cols_truk)
                            
                        add_activity_log(user_name, "Hapus Timbangan Truk", f"Menghapus manifest transaksi {row_edit['No Transaksi']} armada {row_edit['No Plat / Armada']}")
                        st.success(f"🗑️ Data transaksi {row_edit['No Transaksi']} berhasil dihapus dari database.")
                        st.rerun()

    # ==================== TAB 3: RIWAYAT HISTORIS LOGISTIK ====================
    with tab_riwayat:
        st.markdown("### 📜 Riwayat Catatan Timbangan Armada Truk")
        if not df_truk.empty:
            st.dataframe(df_truk.sort_values(by="Tanggal", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat timbangan truk yang tercatat di sistem.")