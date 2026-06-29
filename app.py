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
from menu.master_jenis_sapi import tampilkan_menu_jenis_sapi
from menu.manajemen_pen import tampilkan_menu_pen_mutasi

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
        tampilkan_menu_pen_mutasi(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, user_role, calculate_adg, save_data, add_activity_log, user_name)
    # ==================== MENU 3: MASTER JENIS SAPI ====================
    elif menu == "🐂 Kelola Master Jenis Sapi":
        tampilkan_menu_jenis_sapi(LIST_JENIS_SAPI, save_jenis_sapi, add_activity_log, user_name)
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