import streamlit as st
import pandas as pd
from datetime import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
import time  # Ditambahkan untuk memberi jeda otomatis jika Google Sheets sibuk
from menu.log_operator import tampilkan_menu_log
from menu.edit_hapus import tampilkan_menu_edit_hapus
from menu.panen_penjualan import tampilkan_menu_panen_penjualan
from menu.analisis_grafik import tampilkan_menu_analisis_grafik
from menu.timbangan_berkala import tampilkan_menu_timbangan
from menu.input_pakan import tampilkan_menu_pakan
from menu.registrasi_sapi import tampilkan_menu_registrasi
from menu.timbangan_truk import tampilkan_menu_timbangan_truk
from menu.manajemen_operator import tampilkan_menu_operator

# --- 1. PERBAIKAN: set_page_config HARUS DI PALING ATAS ---
st.set_page_config(page_title="Sistem Penggemukan Sapi", layout="wide")

# --- KONEKSI GOOGLE SHEETS MENGGUNAKAN GSPREAD ---
@st.cache_resource
def get_google_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        # Mengambil kredensial akun robot dari secrets.toml
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scopes
        )
        client = gspread.authorize(creds)
        # Mengambil ID spreadsheet dari secrets.toml
        sheet_id = st.secrets["spreadsheet_id"]
        sheet = client.open_by_key(sheet_id)
        return sheet
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        return None

# Hubungkan ke Google Sheets secara global
sheet = get_google_sheet()

if sheet:
    st.success("Aplikasi ini sekarang terhubung online dengan Google Sheets! 🚀")
else:
    st.warning("⚠️ Aplikasi berjalan dalam mode LOKAL (Gagal terhubung ke Google Sheets).")

# --- FUNGSI PEMBANTU BACA & TULIS SPREADSHEET TABS ---
def read_sheet_to_df(worksheet_name, default_cols):
    if not sheet:
        file_name = f"{worksheet_name}.csv"
        if os.path.exists(file_name): return pd.read_csv(file_name)
        return pd.DataFrame(columns=default_cols)
        
    # Mencoba ulang otomatis sampai 3 kali jika Google Sheets mendadak sibuk
    for percobaan in range(3):
        try:
            worksheet_list = sheet.worksheets()
            existing_titles = {w.title.strip().lower(): w.title for w in worksheet_list}
            target_title = worksheet_name.strip().lower()
            
            if target_title in existing_titles:
                worksheet = sheet.worksheet(existing_titles[target_title])
            else:
                worksheet = sheet.add_worksheet(title=worksheet_name, rows="1000", cols="20")
                worksheet.append_row(default_cols)
                return pd.DataFrame(columns=default_cols)
                
            data = worksheet.get_all_records()
            if not data: return pd.DataFrame(columns=default_cols)
            return pd.DataFrame(data)
            
        except Exception as e:
            if percobaan < 2:
                time.sleep(1) # Tunggu 1 detik lalu coba lagi secara otomatis
                continue
            else:
                # Jika sudah 3 kali gagal, gunakan database cadangan lokal (.csv) agar tidak macet
                st.warning(f"⚠️ Koneksi Google Sheets sibuk sesaat. Menggunakan data cadangan lokal.")
                file_name = f"{worksheet_name}.csv"
                if os.path.exists(file_name): return pd.read_csv(file_name)
                return pd.DataFrame(columns=default_cols)

def write_df_to_sheet(worksheet_name, df, default_cols):
    df = df.reindex(columns=default_cols).fillna("")
    df.to_csv(f"{worksheet_name}.csv", index=False) # Selalu buat cadangan lokal demi keamanan data
    if not sheet: return
    
    # Mencoba menyimpan ulang otomatis sampai 3 kali jika Google Sheets mendadak sibuk
    for percobaan in range(3):
        try:
            worksheet_list = sheet.worksheets()
            existing_titles = {w.title.strip().lower(): w.title for w in worksheet_list}
            target_title = worksheet_name.strip().lower()
            
            if target_title in existing_titles:
                worksheet = sheet.worksheet(existing_titles[target_title])
            else:
                worksheet = sheet.add_worksheet(title=worksheet_name, rows="1000", cols="20")
                
            worksheet.clear()
            worksheet.update(range_name='A1', values=[df.columns.values.tolist()] + df.values.tolist())
            break # Keluar jika pengiriman data sukses
        except Exception as e:
            if percobaan < 2:
                time.sleep(1.5) # Beri jeda 1.5 detik sebelum mencoba menulis ulang
                continue
            else:
                st.error(f"❌ Gagal sinkronisasi data ke Google Sheets ({worksheet_name}). Data tetap aman tersimpan di komputer kandang.")

# Master Daftar Pen/Kandang
DAFTAR_PEN = [
    "Pen Karantina", 
    "Pen A (Bobot < 350kg)", 
    "Pen B (Bobot 350-450kg)", 
    "Pen C (Bobot > 450kg)",
    "Pen D (Khusus/Isolasi Sakit)"
]

# Master Jenis Sapi Bawaan (Default)
DEFAULT_JENIS_SAPI = [
    "Brahman Cross", "Simental", "Limosin", "Hereford", 
    "Sapi Lokal (Bali)", "Sapi Lokal (Madura)", "Sapi Lokal (PO/Peranakan Ongole)", 
    "Ex Impor"
]

# Master Seluruh Menu Aplikasi
ALL_MENUS = [
    "📊 Dashboard & Tabel Monitor", 
    "🏠 Manajemen Pen & Mutasi Sapi", 
    "🐂 Kelola Master Jenis Sapi", 
    "👥 Manajemen Akun Operator", 
    "🚛 Timbangan Armada Truk",
    "➕ Registrasi Sapi Baru", 
    "🍽️ Input Pakan Harian", 
    "⚖️ Input Timbangan Berkala", 
    "📈 Analisis & Grafik Performa",
    "💰 Manajemen Panen & Penjualan",
    "⚙️ Edit & Hapus Data",
    "📜 Log Aktivitas Operator"
]

# --- FUNGSI MENCATAT LOG RIWAYAT AKTIVITAS ---
def add_activity_log(operator, aktivitas, detail):
    cols = ["Tanggal & Waktu", "Operator", "Aktivitas", "Detail Keterangan"]
    new_log = {
        "Tanggal & Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Operator": operator,
        "Aktivitas": aktivitas,
        "Detail Keterangan": detail
    }
    df = read_sheet_to_df("log_aktivitas", cols)
    df = pd.concat([df, pd.DataFrame([new_log])], ignore_index=True)
    write_df_to_sheet("log_aktivitas", df, cols)

# --- FUNGSI UTAMA UNTUK MANAJEMEN AKUN (DATABASE USERS) ---
def load_users():
    cols = ["Username", "Password", "Role", "Menus"]
    default_admin_menus = "|".join(ALL_MENUS)
    default_op_menus = "|".join([
        "📊 Dashboard & Tabel Monitor", 
        "🏠 Manajemen Pen & Mutasi Sapi", 
        "🚛 Timbangan Armada Truk",
        "➕ Registrasi Sapi Baru", 
        "🍽️ Input Pakan Harian", 
        "⚖️ Input Timbangan Berkala", 
        "📈 Analisis & Grafik Performa"
    ])
    
    try:
        admin_pwd = st.secrets["ADMIN_PASSWORD"]
        operator_pwd = st.secrets["OPERATOR_PASSWORD"]
    except Exception:
        admin_pwd = "admin123"
        operator_pwd = "operator123"
    
    df = read_sheet_to_df("users", cols)
    
    if df.empty:
        df = pd.DataFrame([
            {"Username": "admin", "Password": admin_pwd, "Role": "Admin", "Menus": default_admin_menus},
            {"Username": "operator", "Password": operator_pwd, "Role": "Operator", "Menus": default_op_menus}
        ])
        write_df_to_sheet("users", df, cols)
        return df

    if "Menus" not in df.columns:
        df["Menus"] = df["Role"].apply(lambda r: default_admin_menus if r == "Admin" else default_op_menus)
        write_df_to_sheet("users", df, cols)
        
    file_updated = False
    for idx, row in df.iterrows():
        row_updated = False
        current_menus = str(row["Menus"]).split("|")
        if "🚛 Timbangan Armada Truk" not in current_menus:
            current_menus.append("🚛 Timbangan Armada Truk")
            row_updated = True
        if "📜 Log Aktivitas Operator" not in current_menus and row["Role"] == "Admin":
            current_menus.append("📜 Log Aktivitas Operator")
            row_updated = True
            
        if row_updated:
            df.at[idx, "Menus"] = "|".join(current_menus)
            file_updated = True
            
    if file_updated:
        write_df_to_sheet("users", df, cols)
        
    return df

def save_users(df):
    cols = ["Username", "Password", "Role", "Menus"]
    write_df_to_sheet("users", df, cols)

# --- FUNGSI MUAT DATA TIMBANGAN TRUK ---
def load_truk_data():
    cols = [
        "No Transaksi", "Tanggal", "No Plat / Armada", "Keterangan Muatan", 
        "Bruto / Kotor (kg)", "Tara / Kosong (kg)", "Netto / Bersih (kg)", 
        "Jumlah Sapi (Ekor)", "Rata-rata / Ekor (kg)", "Operator Lapangan"
    ]
    return read_sheet_to_df("timbangan_truk", cols)

def save_truk_data(df):
    cols = [
        "No Transaksi", "Tanggal", "No Plat / Armada", "Keterangan Muatan", 
        "Bruto / Kotor (kg)", "Tara / Kosong (kg)", "Netto / Bersih (kg)", 
        "Jumlah Sapi (Ekor)", "Rata-rata / Ekor (kg)", "Operator Lapangan"
    ]
    write_df_to_sheet("timbangan_truk", df, cols)

# --- FUNGSI UTAMA UNTUK MASTER JENIS SAPI ---
def load_jenis_sapi():
    cols = ["Jenis Sapi"]
    df = read_sheet_to_df("jenis_sapi", cols)
    if not df.empty:
        return df["Jenis Sapi"].dropna().tolist()
    else:
        df = pd.DataFrame({"Jenis Sapi": DEFAULT_JENIS_SAPI})
        write_df_to_sheet("jenis_sapi", df, cols)
        return DEFAULT_JENIS_SAPI.copy()

def save_jenis_sapi(list_jenis):
    cols = ["Jenis Sapi"]
    df = pd.DataFrame({"Jenis Sapi": list_jenis})
    write_df_to_sheet("jenis_sapi", df, cols)

# --- FUNGSI MUAT DATA SAPI AKTIF ---
def load_data():
    cols = [
        "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", 
        "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)",
        "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"
    ]
    df = read_sheet_to_df("data_sapi", cols)
    
    if df.empty:
        return pd.DataFrame(columns=cols)
        
    if "Ras Sapi" in df.columns:
        df = df.rename(columns={"Ras Sapi": "Jenis Sapi"})
    if "Umur Sapi" in df.columns:
        df["Umur Masuk (Bulan)"] = 12
        df = df.drop(columns=["Umur Sapi"])
    
    # Toleransi untuk data lama yang belum punya kolom 'Kode Sapi'
    if "Kode Sapi" not in df.columns:
        df["Kode Sapi"] = "-"
        
    if "Jenis Kelamin" not in df.columns:
        df["Jenis Kelamin"] = "Jantan"
    if "Total Pakan (kg)" not in df.columns:
        df["Total Pakan (kg)"] = 0.0
    if "Tgl Pakan Terakhir" not in df.columns:
        df["Tgl Pakan Terakhir"] = "-"
    if "Lokasi Pen" not in df.columns:
        df["Lokasi Pen"] = "Pen Karantina"
        
    df = df.reindex(columns=cols)
    return df

def save_data(df):
    cols = [
        "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", 
        "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)",
        "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"
    ]
    write_df_to_sheet("data_sapi", df, cols)

# --- FUNGSI MUAT DATA PANEN ---
def load_panen_data():
    cols = [
        "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen",
        "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)",
        "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"
    ]
    df = read_sheet_to_df("data_panen", cols)
    if "Kode Sapi" not in df.columns and not df.empty:
        df["Kode Sapi"] = "-"
    return df

def save_panen_data(df):
    cols = [
        "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen",
        "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)",
        "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"
    ]
    write_df_to_sheet("data_panen", df, cols)

def calculate_adg(tgl_masuk, bobot_awal, tgl_akhir, bobot_akhir):
    try:
        if isinstance(tgl_masuk, str):
            tgl_masuk = datetime.strptime(tgl_masuk, "%Y-%m-%d").date()
        if isinstance(tgl_akhir, str):
            tgl_akhir = datetime.strptime(tgl_akhir, "%Y-%m-%d").date()
        
        selisih_hari = (tgl_akhir - tgl_masuk).days
        if selisih_hari > 0:
            return round((bobot_akhir - bobot_awal) / selisih_hari, 2)
    except:
        pass
    return 0.0

# --- FUNGSI HALAMAN LOGIN ---
def login_page():
    st.markdown("<h2 style='text-align: center;'>🔒 Login Sistem Penggemukan Sapi</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Silakan masukkan akun Anda untuk mengakses sistem</p>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Masukkan username Anda").strip()
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            submit = st.form_submit_button("Masuk Aplikasi", type="primary", use_container_width=True)
            
            if submit:
                df_users = load_users()
                user_match = df_users[(df_users["Username"].astype(str).str.lower() == username.lower()) & (df_users["Password"].astype(str) == password)]
                
                if not user_match.empty:
                    role_user = user_match.iloc[0]["Role"]
                    actual_username = user_match.iloc[0]["Username"]
                    menus_user = user_match.iloc[0]["Menus"]
                    
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = actual_username
                    st.session_state["role"] = role_user
                    st.session_state["allowed_menus"] = menus_user.split("|")
                    
                    st.query_params["logged_in"] = "true"
                    st.query_params["username"] = actual_username
                    st.query_params["role"] = role_user
                    
                    add_activity_log(actual_username, "Login", "Berhasil masuk ke dalam sistem.")
                    st.success(f"Login Berhasil! Selamat datang {actual_username}")
                    st.rerun()
                else:
                    st.error("Username atau Password salah. Silakan hubungi Admin Kandang.")

if "logged_in" not in st.session_state:
    if "logged_in" in st.query_params and st.query_params["logged_in"] == "true":
        username_ref = st.query_params.get("username", "user")
        df_u = load_users()
        u_match = df_u[df_u["Username"].astype(str).str.lower() == username_ref.lower()]
        
        if not u_match.empty:
            st.session_state["logged_in"] = True
            st.session_state["username"] = u_match.iloc[0]["Username"]
            st.session_state["role"] = u_match.iloc[0]["Role"]
            st.session_state["allowed_menus"] = u_match.iloc[0]["Menus"].split("|")
        else:
            st.session_state["logged_in"] = False
    else:
        st.session_state["logged_in"] = False

# Inisialisasi Data Global
df_sapi = load_data()
df_panen = load_panen_data()
df_truk = load_truk_data()
LIST_JENIS_SAPI = load_jenis_sapi()

if not st.session_state["logged_in"]:
    login_page()
else:
    st.title("🐂 Sistem Monitoring Penggemukan Sapi Impor & Lokal")
    st.markdown("---")

    user_role = st.session_state["role"]
    user_name = st.session_state["username"]
    daftar_menu_user = st.session_state.get("allowed_menus", [ALL_MENUS[0]])

    st.sidebar.markdown("### 👤 Pengguna Aktif")
    st.sidebar.info(f"**User:** {user_name.upper()}\n\n**Hak Akses:** {user_role}")
    
    if st.sidebar.button("🚪 Keluar (Logout)", type="secondary", use_container_width=True):
        add_activity_log(user_name, "Logout", "Keluar dari sistem.")
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.session_state["allowed_menus"] = []
        st.query_params.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    menu = st.sidebar.selectbox("PILIH MENU APLIKASI", daftar_menu_user)

    # ==================== MENU 1: DASHBOARD ====================
    if menu == "📊 Dashboard & Tabel Monitor":
        st.subheader("📊 Ringkasan Populasi & Performa Kelompok")
        if not df_sapi.empty:
            df_tampil = df_sapi.copy()
            tgl_m = pd.to_datetime(df_tampil["Tgl Masuk"])
            tgl_a = pd.to_datetime(df_tampil["Tgl Cek Akhir"])
            
            df_tampil["Lama Peliharaan (Hari)"] = (tgl_a - tgl_m).dt.days
            df_tampil["Umur Sekarang (Bulan)"] = (df_tampil["Umur Masuk (Bulan)"] + (df_tampil["Lama Peliharaan (Hari)"].fillna(0) / 30.4)).round(0).astype(int)
            df_tampil["Total Gain (kg)"] = df_tampil["Bobot Akhir (kg)"] - df_tampil["Bobot Awal (kg)"]
            
            df_tampil["FCR"] = df_tampil.apply(
                lambda row: round(row["Total Pakan (kg)"] / row["Total Gain (kg)"], 2) if row["Total Gain (kg)"] > 0 else 0.0, 
                axis=1
            )
            
            kolom_rapi = [
                "Kode Sapi", "RFID/Tag", "Jenis Sapi", "Lokasi Pen", "Jenis Kelamin", "Umur Masuk (Bulan)", "Umur Sekarang (Bulan)",
                "Asal Negara", "Tgl Masuk", "Lama Peliharaan (Hari)", "Bobot Awal (kg)", "Bobot Akhir (kg)", 
                "Total Gain (kg)", "Total Pakan (kg)", "FCR", "ADG (kg/hari)"
            ]
            df_tampil = df_tampil.reindex(columns=kolom_rapi)
            df_tampil.index = range(1, len(df_tampil) + 1)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Populasi Sapi Aktif", len(df_tampil))
            col2.metric("Rata-rata Bobot Saat Ini", f"{round(df_tampil['Bobot Akhir (kg)'].mean(), 2)} kg")
            col3.metric("Rata-rata ADG Kelompok", f"{round(df_tampil['ADG (kg/hari)'].mean(), 2)} kg/hari")
            
            fcr_aktif = df_tampil[df_tampil["FCR"] > 0]["FCR"]
            avg_fcr = round(fcr_aktif.mean(), 2) if not fcr_aktif.empty else 0.0
            col4.metric("Rata-rata FCR Kandang", f"{avg_fcr}")
            
            st.write("### 📋 Tabel Monitoring Sapi Keseluruhan (Real-Time)")
            st.dataframe(df_tampil, use_container_width=True)
        else:
            st.info("Belum ada data sapi aktif. Silakan daftarkan di menu registrasi.")

    # ==================== MENU 2: MANAJEMEN PEN & MUTASI SAPI ====================
    elif menu == "🏠 Manajemen Pen & Mutasi Sapi":
        st.subheader("🏠 Manajemen Stok Populasi per Pen & Mutasi Kandang")
        tab_stok, tab_pindah = st.tabs(["📊 Stok Populasi per Pen", "🔄 Mutasi (Pindah Kandang)"])
        
        with tab_stok:
            st.markdown("### 🔍 Panel Filter & Pencarian Sapi")
            with st.expander("Klik di sini untuk membuka/menutup parameter pencarian", expanded=True):
                col_f0_a, col_f0, col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1, 1, 1.2])
                
                with col_f0_a:
                    search_kode = st.text_input("1. Cari Kode Sapi", placeholder="Ketik kode sapi...")
                with col_f0:
                    search_rfid = st.text_input("2. Cari RFID / Tag", placeholder="Ketik nomor RFID...")
                with col_f1:
                    filter_jenis = st.selectbox("3. Jenis Sapi", ["Semua"] + LIST_JENIS_SAPI)
                with col_f2:
                    filter_kelamin = st.selectbox("4. Jenis Kelamin", ["Semua", "Jantan", "Betina"])
                with col_f3:
                    daftar_negara = ["Semua"] + sorted(df_sapi["Asal Negara"].dropna().unique().tolist())
                    filter_asal = st.selectbox("5. Negara/Daerah Asal", daftar_negara)
                with col_f4:
                    filter_berat = st.slider("6. Rentang Berat Akhir (kg)", min_value=0, max_value=1000, value=(0, 1000))

            df_filtered = df_sapi.copy()
            if search_kode.strip():
                df_filtered = df_filtered[df_filtered["Kode Sapi"].astype(str).str.contains(search_kode.strip(), case=False)]
            if search_rfid.strip():
                df_filtered = df_filtered[df_filtered["RFID/Tag"].astype(str).str.contains(search_rfid.strip(), case=False)]
            if filter_jenis != "Semua": df_filtered = df_filtered[df_filtered["Jenis Sapi"] == filter_jenis]
            if filter_kelamin != "Semua": df_filtered = df_filtered[df_filtered["Jenis Kelamin"] == filter_kelamin]
            if filter_asal != "Semua": df_filtered = df_filtered[df_filtered["Asal Negara"] == filter_asal]
            if not df_filtered.empty:
                df_filtered = df_filtered[(df_filtered["Bobot Akhir (kg)"] >= filter_berat[0]) & (df_filtered["Bobot Akhir (kg)"] <= filter_berat[1])]

            st.markdown("---")
            st.write("### 📉 Ringkasan Kepadatan Pen (Hasil Filter Pencarian)")
            
            summary_pen = []
            for pen in DAFTAR_PEN:
                df_sub = df_filtered[df_filtered["Lokasi Pen"] == pen] if not df_filtered.empty else pd.DataFrame()
                populasi = len(df_sub)
                avg_bobot = round(df_sub["Bobot Akhir (kg)"].mean(), 1) if populasi > 0 else 0.0
                avg_adg = round(df_sub["ADG (kg/hari)"].mean(), 2) if populasi > 0 else 0.0
                summary_pen.append({"Nama Pen/Kandang": pen, "Populasi Terfilter (Ekor)": populasi, "Rerata Bobot Terfilter (kg)": avg_bobot, "Rerata ADG Terfilter (kg/hari)": avg_adg})
            
            st.dataframe(pd.DataFrame(summary_pen), use_container_width=True, hide_index=True)
            st.markdown("---")
            st.write("### 📋 Detail Informasi Sapi per Pen (Hasil Filter Pencarian)")
            
            for pen in DAFTAR_PEN:
                df_filter_pen = df_filtered[df_filtered["Lokasi Pen"] == pen] if not df_filtered.empty else pd.DataFrame()
                st.markdown(f"#### 🏠 {pen} ({len(df_filter_pen)} Ekor Cocok)")
                if df_filter_pen.empty:
                    st.caption("⚪ *Tidak ada sapi yang cocok dengan kriteria pencarian di pen ini.*")
                else:
                    df_tabel_pen = df_filter_pen[["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)"]].copy()
                    df_tabel_pen.index = range(1, len(df_tabel_pen) + 1)
                    st.dataframe(df_tabel_pen, use_container_width=True)

            # PANEL KOREKSI TOTAL
            st.markdown("---")
            with st.expander("✏️ Klik di sini untuk membuka Panel Koreksi Total Data Sapi", expanded=False):
                st.markdown("### ✏️ Koreksi Total Data Sapi (Butuh Otorisasi Password Admin Utama)")
                
                if not df_sapi.empty:
                    pilihan_sapi_koreksi = df_sapi["RFID/Tag"].astype(str).tolist()
                    selected_tag_kor = st.selectbox("Pilih Nomor RFID Sapi yang akan Diedit Secara Menyeluruh:", pilihan_sapi_koreksi, key="sb_pop_total_edit")
                    
                    idx_kor = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag_kor].index[0]
                    data_kor = df_sapi.loc[idx_kor]
                    
                    with st.form("form_pop_total_koreksi"):
                        col_k1, col_k2 = st.columns(2)
                        with col_k1:
                            new_kode = st.text_input("Koreksi Kode Sapi Baru", value=str(data_kor.get("Kode Sapi", "-")))
                            new_rfid = st.text_input("Koreksi Nomor RFID / Tag Baru", value=str(data_kor["RFID/Tag"]))
                            new_jenis = st.selectbox("Koreksi Jenis Sapi", LIST_JENIS_SAPI, index=LIST_JENIS_SAPI.index(data_kor["Jenis Sapi"]) if data_kor["Jenis Sapi"] in LIST_JENIS_SAPI else 0)
                            new_kelamin = st.selectbox("Koreksi Jenis Kelamin", ["Jantan", "Betina"], index=0 if data_kor["Jenis Kelamin"] == "Jantan" else 1)
                            new_umur = st.number_input("Koreksi Umur Masuk (Bulan)", min_value=1, value=int(data_kor["Umur Masuk (Bulan)"]) if pd.notna(data_kor["Umur Masuk (Bulan)"]) else 1)
                            new_asal = st.text_input("Koreksi Negara/Daerah Asal", value=str(data_kor["Asal Negara"]))
                            new_pen = st.selectbox("Koreksi Posisi Pen/Kandang", DAFTAR_PEN, index=DAFTAR_PEN.index(data_kor["Lokasi Pen"]) if data_kor["Lokasi Pen"] in DAFTAR_PEN else 0)
                        with col_k2:
                            try: tgl_m_curr = datetime.strptime(str(data_kor["Tgl Masuk"]), "%Y-%m-%d").date()
                            except: tgl_m_curr = datetime.now().date()
                            new_tgl_m = st.date_input("Koreksi Tanggal Masuk", value=tgl_m_curr)
                            new_bobot_awal = st.number_input("Koreksi Bobot Awal Masuk (kg)", min_value=50.0, value=float(data_kor["Bobot Awal (kg)"]) if pd.notna(data_kor["Bobot Awal (kg)"]) else 50.0)
                            
                            try: tgl_a_curr = datetime.strptime(str(data_kor["Tgl Cek Akhir"]), "%Y-%m-%d").date()
                            except: tgl_a_curr = datetime.now().date()
                            new_tgl_a = st.date_input("Koreksi Tanggal Timbangan/Cek Akhir", value=tgl_a_curr)
                            new_bobot_akhir = st.number_input("Koreksi Bobot Akhir Sekarang (kg)", min_value=50.0, value=float(data_kor["Bobot Akhir (kg)"]) if pd.notna(data_kor["Bobot Akhir (kg)"]) else 50.0)
                            new_pakan = st.number_input("Koreksi Akumulasi Pakan Terkonsumsi (kg)", min_value=0.0, value=float(data_kor["Total Pakan (kg)"]) if pd.notna(data_kor["Total Pakan (kg)"]) else 0.0)
                        
                        akses_diberikan = True
                        if user_role == "Operator":
                            try:
                                admin_pwd = st.secrets["ADMIN_PASSWORD"]
                            except Exception:
                                admin_pwd = "admin123"
                            st.markdown("⚠️ **Otorisasi Diperlukan:** Sesi Anda saat ini adalah Operator. Wajib memasukkan password akun Admin utama untuk menyimpan perubahan total.")
                            pwd_input = st.text_input("Masukkan Password Admin Utama", type="password", key="pwd_pop_total_edit")
                            if pwd_input != admin_pwd:
                                akses_diberikan = False
                                
                        if st.form_submit_button("Simpan Seluruh Perubahan Data Sapi", type="primary"):
                            if not akses_diberikan:
                                st.error("❌ Gagal Menyimpan! Password Admin salah atau tidak diisi.")
                            elif new_rfid != selected_tag_kor and new_rfid in df_sapi["RFID/Tag"].values.astype(str):
                                st.error(f"❌ Gagal Menyimpan! Nomor RFID '{new_rfid}' baru sudah digunakan oleh sapi lain.")
                            else:
                                df_sapi.at[idx_kor, "Kode Sapi"] = new_kode
                                df_sapi.at[idx_kor, "RFID/Tag"] = new_rfid
                                df_sapi.at[idx_kor, "Jenis Sapi"] = new_jenis
                                df_sapi.at[idx_kor, "Jenis Kelamin"] = new_kelamin
                                df_sapi.at[idx_kor, "Umur Masuk (Bulan)"] = int(new_umur)
                                df_sapi.at[idx_kor, "Asal Negara"] = new_asal
                                df_sapi.at[idx_kor, "Lokasi Pen"] = new_pen
                                df_sapi.at[idx_kor, "Tgl Masuk"] = new_tgl_m.strftime("%Y-%m-%d")
                                df_sapi.at[idx_kor, "Bobot Awal (kg)"] = new_bobot_awal
                                df_sapi.at[idx_kor, "Tgl Cek Akhir"] = new_tgl_a.strftime("%Y-%m-%d")
                                df_sapi.at[idx_kor, "Bobot Akhir (kg)"] = new_bobot_akhir
                                df_sapi.at[idx_kor, "Total Pakan (kg)"] = new_pakan
                                df_sapi.at[idx_kor, "ADG (kg/hari)"] = calculate_adg(new_tgl_m.strftime("%Y-%m-%d"), new_bobot_awal, new_tgl_a.strftime("%Y-%m-%d"), new_bobot_akhir)
                                
                                save_data(df_sapi)
                                add_activity_log(user_name, "Koreksi Total Sapi", f"Mengubah data Sapi Kode {new_kode}, RFID {selected_tag_kor} -> RFID baru: {new_rfid}, Pen: {new_pen}, Berat: {new_bobot_akhir}kg.")
                                st.success(f"🎉 Sukses! Data Sapi RFID {selected_tag_kor} berhasil diperbarui.")
                                st.rerun()
                else:
                    st.info("Belum ada data sapi aktif.")

        with tab_pindah:
            st.write("### 🔄 Form Pemindahan (Mutasi) Kandang Sapi Bertingkat")
            if df_sapi.empty:
                st.info("Belum ada sapi aktif untuk dimutasi.")
            else:
                kandang_asal = st.selectbox("1. Pilih Kandang / Pen Asal:", DAFTAR_PEN, key="sb_kandang_asal")
                df_sapi_asal = df_sapi[df_sapi["Lokasi Pen"] == kandang_asal]
                
                if df_sapi_asal.empty:
                    st.warning(f"⚠️ Tidak ada populasi sapi aktif di dalam {kandang_asal} saat ini.")
                else:
                    pilihan_sapi = df_sapi_asal["RFID/Tag"].astype(str).tolist()
                    selected_tag = st.selectbox(f"2. Pilih Nomor Tag / RFID Sapi (Ditemukan {len(pilihan_sapi)} Ekor):", options=pilihan_sapi, key="sb_mutasi")
                    
                    idx = df_sapi[df_sapi["RFID/Tag"].astype(str) == selected_tag].index[0]
                    data_sapi = df_sapi.loc[idx]
                    
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.info(f"""
                        📍 **Kondisi Sapi Saat Ini:**
                        * **Kode Sapi:** {data_sapi.get('Kode Sapi', '-')}
                        * **Nomor RFID:** {selected_tag}
                        * **Varietas/Jenis:** {data_sapi['Jenis Sapi']}
                        * **Bobot Sekarang:** {data_sapi['Bobot Akhir (kg)']} kg
                        * **Posisi Kandang Sekarang:** {data_sapi['Lokasi Pen']}
                        """)
                    
                    with col_m2:
                        pilihan_tujuan = [pen for pen in DAFTAR_PEN if pen != kandang_asal]
                        pen_tujuan = st.selectbox("3. Pilih Pen / Kandang Tujuan Baru:", pilihan_tujuan, key="sb_tujuan_pen")
                        
                        if st.button("Proses Mutasi Sapi", type="primary", use_container_width=True):
                            df_sapi.at[idx, "Lokasi Pen"] = pen_tujuan
                            save_data(df_sapi)
                            add_activity_log(user_name, "Mutasi Kandang", f"Memindahkan Sapi Kode {data_sapi.get('Kode Sapi', '-')} (RFID {selected_tag}) dari {kandang_asal} menuju {pen_tujuan}.")
                            st.success(f"🎉 Sukses! Sapi RFID {selected_tag} berhasil dipindahkan menuju {pen_tujuan}.")
                            st.rerun()

    # ==================== MENU 3: MASTER JENIS SAPI ====================
    elif menu == "🐂 Kelola Master Jenis Sapi":
        st.subheader("🐂 Kelola Master Pilihan Jenis Sapi")
        tab_lihat, tab_tambah, tab_edit, tab_hapus = st.tabs(["📋 Daftar Jenis Sapi", "➕ Tambah Jenis Baru", "✏️ Edit Jenis", "❌ Hapus Jenis"])
        
        with tab_lihat:
            st.dataframe(pd.DataFrame({"No": range(1, len(LIST_JENIS_SAPI) + 1), "Nama Jenis Sapi": LIST_JENIS_SAPI}), use_container_width=True, hide_index=True)
        with tab_tambah:
            with st.form("form_tambah_jenis"):
                input_jenis_baru = st.text_input("Nama Jenis Sapi Baru")
                if st.form_submit_button("Simpan", type="primary") and input_jenis_baru.strip():
                    LIST_JENIS_SAPI.append(input_jenis_baru.strip())
                    save_jenis_sapi(LIST_JENIS_SAPI)
                    add_activity_log(user_name, "Tambah Jenis Sapi", f"Menambahkan varietas jenis sapi baru: {input_jenis_baru.strip()}")
                    st.success("Sukses!"); st.rerun()
        with tab_edit:
            jenis_diubah = st.selectbox("Pilih Jenis Sapi", LIST_JENIS_SAPI, key="sb_edit_j")
            nama_baru = st.text_input("Nama Baru", value=jenis_diubah)
            if st.button("Simpan Perubahan"):
                idx_j = LIST_JENIS_SAPI.index(jenis_diubah)
                LIST_JENIS_SAPI[idx_j] = nama_baru.strip()
                save_jenis_sapi(LIST_JENIS_SAPI)
                add_activity_log(user_name, "Edit Jenis Sapi", f"Mengubah nama jenis sapi dari '{jenis_diubah}' menjadi '{nama_baru.strip()}'.")
                st.success("Berhasil diubah!"); st.rerun()
        with tab_hapus:
            jenis_dihapus = st.selectbox("Pilih Jenis Sapi yang Dihapus", LIST_JENIS_SAPI, key="sb_hapus_j")
            if st.button("Hapus Permanen", type="primary"):
                if jenis_dihapus in LIST_JENIS_SAPI:
                    LIST_JENIS_SAPI.remove(jenis_dihapus)
                    save_jenis_sapi(LIST_JENIS_SAPI)
                    add_activity_log(user_name, "Hapus Jenis Sapi", f"Menghapus varietas jenis sapi: {jenis_dihapus}")
                    st.success("Terhapus!"); st.rerun()

    # ==================== MENU 4: MANAJEMEN AKUN OPERATOR ====================
    elif menu == "👥 Manajemen Akun Operator":
        tampilkan_menu_operator(load_users, ALL_MENUS, save_users, add_activity_log, user_name)
    # ==================== MENU 5: TIMBANGAN ARMADA TRUK ====================
    elif menu == "🚛 Timbangan Armada Truk":
        tampilkan_menu_timbangan_truk(df_truk, save_truk_data, add_activity_log, user_name)
    # ==================== MENU 6: REGISTRASI SAPI BARU ====================
    elif menu == "➕ Registrasi Sapi Baru":
        tampilkan_menu_registrasi(df_sapi, LIST_JENIS_SAPI, save_data, add_activity_log, user_name)
    # ==================== MENU 7: INPUT PAKAN HARIAN ====================
    elif menu == "🍽️ Input Pakan Harian":
        tampilkan_menu_pakan(df_sapi, save_data, add_activity_log, user_name)
    # ==================== MENU 8: INPUT TIMBANGAN BERKALA ====================
    elif menu == "⚖️ Input Timbangan Berkala":
        tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name)
    # ==================== MENU 9: ANALISIS & GRAFIK PERFORMA ====================
    elif menu == "📈 Analisis & Grafik Performa":
        tampilkan_menu_analisis_grafik(df_sapi, DAFTAR_PEN)
    # ==================== MENU 10: MANAJEMEN PANEN & PENJUALAN ====================
    elif menu == "💰 Manajemen Panen & Penjualan":
        tampilkan_menu_panen_penjualan(df_sapi, df_panen, save_panen_data, save_data, add_activity_log, user_name)
    # ==================== MENU 11: EDIT & HAPUS DATA SAPI ====================
    elif menu == "⚙️ Edit & Hapus Data":
        tampilkan_menu_edit_hapus(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, save_data, add_activity_log, user_name)
    # ==================== MENU 12: LOG AKTIVITAS OPERATOR ====================
    elif menu == "📜 Log Aktivitas Operator":
        tampilkan_menu_log(read_sheet_to_df, write_df_to_sheet)