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
from menu.dashboard import tampilkan_dashboard

# --- 1. PERBAIKAN: set_page_config HARUS DI PALING ATAS ---
st.set_page_config(page_title="Sistem Penggemukan Sapi", layout="wide")

# GLOBAL VARIABLE UNTUK KONEKSI
sheet = None

# --- KONEKSI GOOGLE SHEETS MENGGUNAKAN GSPREAD ---
@st.cache_resource
def get_google_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet_id = st.secrets["spreadsheet_id"]
        return client.open_by_key(sheet_id)
    except Exception as e:
        return None

# --- FUNGSI PEMBANTU BACA & TULIS SPREADSHEET TABS ---
def read_sheet_to_df(worksheet_name, default_cols):
    global sheet
    if not sheet:
        file_name = f"{worksheet_name}.csv"
        if os.path.exists(file_name): return pd.read_csv(file_name)
        return pd.DataFrame(columns=default_cols)
        
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
                time.sleep(1)
                continue
            else:
                st.warning(f"⚠️ Koneksi Google Sheets sibuk sesaat. Menggunakan data cadangan lokal.")
                file_name = f"{worksheet_name}.csv"
                if os.path.exists(file_name): return pd.read_csv(file_name)
                return pd.DataFrame(columns=default_cols)

def write_df_to_sheet(worksheet_name, df, default_cols):
    global sheet
    df = df.reindex(columns=default_cols).fillna("")
    df.to_csv(f"{worksheet_name}.csv", index=False)
    if not sheet: return
    
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
            break
        except Exception as e:
            if percobaan < 2:
                time.sleep(1.5)
                continue
            else:
                st.error(f"❌ Gagal sinkronisasi data ke Google Sheets ({worksheet_name}). Data tetap aman tersimpan di komputer kandang.")

# Master Data Konfigurasi Aplikasi
DAFTAR_PEN = ["Pen Karantina", "Pen A (Bobot < 350kg)", "Pen B (Bobot 350-450kg)", "Pen C (Bobot > 450kg)", "Pen D (Khusus/Isolasi Sakit)"]
DEFAULT_JENIS_SAPI = ["Brahman Cross", "Simental", "Limosin", "Hereford", "Sapi Lokal (Bali)", "Sapi Lokal (Madura)", "Sapi Lokal (PO/Peranakan Ongole)", "Ex Impor"]
ALL_MENUS = ["📊 Dashboard & Tabel Monitor", "🏠 Manajemen Pen & Mutasi Sapi", "🐂 Kelola Master Jenis Sapi", "👥 Manajemen Akun Operator", "🚛 Timbangan Armada Truk", "➕ Registrasi Sapi Baru", "🍽️ Input Pakan Harian", "⚖️ Input Timbangan Berkala", "📈 Analisis & Grafik Performa", "💰 Manajemen Panen & Penjualan", "⚙️ Edit & Hapus Data", "📜 Log Aktivitas Operator"]

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

# --- FUNGSI UTAMA UNTUK MANAJEMEN AKUN ---
def load_users():
    cols = ["Username", "Password", "Role", "Menus"]
    default_admin_menus = "|".join(ALL_MENUS)
    default_op_menus = "|".join(["📊 Dashboard & Tabel Monitor", "🏠 Manajemen Pen & Mutasi Sapi", "🚛 Timbangan Armada Truk", "➕ Registrasi Sapi Baru", "🍽️ Input Pakan Harian", "⚖️ Input Timbangan Berkala", "📈 Analisis & Grafik Performa"])
    
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

# --- DATA LOADER FUNCTIONS ---
def load_truk_data():
    cols = ["No Transaksi", "Tanggal", "No Plat / Armada", "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Rata-rata / Ekor (kg)", "Operator Lapangan"]
    return read_sheet_to_df("timbangan_truk", cols)

def save_truk_data(df):
    cols = ["No Transaksi", "Tanggal", "No Plat / Armada", "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Rata-rata / Ekor (kg)", "Operator Lapangan"]
    write_df_to_sheet("timbangan_truk", df, cols)

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

def load_data():
    cols = ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"]
    df = read_sheet_to_df("data_sapi", cols)
    
    if df.empty: return pd.DataFrame(columns=cols)
    if "Ras Sapi" in df.columns: df = df.rename(columns={"Ras Sapi": "Jenis Sapi"})
    if "Umur Sapi" in df.columns:
        df["Umur Masuk (Bulan)"] = 12
        df = df.drop(columns=["Umur Sapi"])
    if "Kode Sapi" not in df.columns: df["Kode Sapi"] = "-"
    if "Jenis Kelamin" not in df.columns: df["Jenis Kelamin"] = "Jantan"
    if "Total Pakan (kg)" not in df.columns: df["Total Pakan (kg)"] = 0.0
    if "Tgl Pakan Terakhir" not in df.columns: df["Tgl Pakan Terakhir"] = "-"
    if "Lokasi Pen" not in df.columns: df["Lokasi Pen"] = "Pen Karantina"
        
    return df.reindex(columns=cols)

def save_data(df):
    cols = ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"]
    write_df_to_sheet("data_sapi", df, cols)

def load_panen_data():
    cols = ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"]
    df = read_sheet_to_df("data_panen", cols)
    if "Kode Sapi" not in df.columns and not df.empty: df["Kode Sapi"] = "-"
    return df

def save_panen_data(df):
    cols = ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"]
    write_df_to_sheet("data_panen", df, cols)

def calculate_adg(tgl_masuk, bobot_awal, tgl_akhir, bobot_akhir):
    try:
        if isinstance(tgl_masuk, str): tgl_masuk = datetime.strptime(tgl_masuk, "%Y-%m-%d").date()
        if isinstance(tgl_akhir, str): tgl_akhir = datetime.strptime(tgl_akhir, "%Y-%m-%d").date()
        selisih_hari = (tgl_akhir - tgl_masuk).days
        if selisih_hari > 0: return round((bobot_akhir - bobot_awal) / selisih_hari, 2)
    except: pass
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

# --- ROUTING LOGIC & SESSION INITIALIZATION ---
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

# --- KONDISI BELUM LOGIN ---
if not st.session_state["logged_in"]:
    login_page()

# --- KONDISI SUDAH LOGIN (PERBAIKAN PERFORMA DI SINI) ---
else:
    # 1. Hubungkan ke Google Sheets secara global (Hanya saat sudah masuk aplikasi)
    sheet = get_google_sheet()
    
    # 2. Ambil data dari Sheets / CSV (Hanya dipanggil setelah operator terverifikasi)
    df_sapi = load_data()
    df_panen = load_panen_data()
    df_truk = load_truk_data()
    LIST_JENIS_SAPI = load_jenis_sapi()

    # --- TAMPILAN HALAMAN UTAMA KANDANG ---
    st.title("🐂 Sistem Monitoring Penggemukan Sapi Impor & Lokal")
    
    # Tampilkan banner status koneksi secara elegan setelah login berhasil
    if sheet:
        st.success("Aplikasi ini sekarang terhubung online dengan Google Sheets! 🚀")
    else:
        st.warning("⚠️ Aplikasi berjalan dalam mode LOKAL (Gagal terhubung ke Google Sheets).")
    st.markdown("---")

    user_role = st.session_state["role"]
    user_name = st.session_state["username"]
    daftar_menu_user = st.session_state.get("allowed_menus", [ALL_MENUS[0]])

    # SIDEBAR PANEL CONTROL
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

    # ==================== CONTROLLER MENU ROUTING ====================
    if menu == "📊 Dashboard & Tabel Monitor":
        tampilkan_dashboard(df_sapi)
    elif menu == "🏠 Manajemen Pen & Mutasi Sapi":
        tampilkan_menu_pen_mutasi(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, user_role, calculate_adg, save_data, add_activity_log, user_name)
    elif menu == "🐂 Kelola Master Jenis Sapi":
        tampilkan_menu_jenis_sapi(LIST_JENIS_SAPI, save_jenis_sapi, add_activity_log, user_name)
    elif menu == "👥 Manajemen Akun Operator":
        tampilkan_menu_operator(load_users, ALL_MENUS, save_users, add_activity_log, user_name)
    elif menu == "🚛 Timbangan Armada Truk":
        tampilkan_menu_timbangan_truk(df_truk, save_truk_data, add_activity_log, user_name)
    elif menu == "➕ Registrasi Sapi Baru":
        tampilkan_menu_registrasi(df_sapi, LIST_JENIS_SAPI, save_data, add_activity_log, user_name)
    elif menu == "🍽️ Input Pakan Harian":
        tampilkan_menu_pakan(df_sapi, save_data, add_activity_log, user_name)
    elif menu == "⚖️ Input Timbangan Berkala":
        tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name)
    elif menu == "📈 Analisis & Grafik Performa":
        tampilkan_menu_analisis_grafik(df_sapi, DAFTAR_PEN)
    elif menu == "💰 Manajemen Panen & Penjualan":
        tampilkan_menu_panen_penjualan(df_sapi, df_panen, save_panen_data, save_data, add_activity_log, user_name)
    elif menu == "⚙️ Edit & Hapus Data":
        tampilkan_menu_edit_hapus(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, save_data, add_activity_log, user_name)
    elif menu == "📜 Log Aktivitas Operator":
        tampilkan_menu_log(read_sheet_to_df, write_df_to_sheet)