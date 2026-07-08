import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import gspread
from google.oauth2.service_account import Credentials
import time

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
from menu.manajemen_kelompok import tampilkan_menu_manajemen_kelompok
from menu.karantina import tampilkan_menu_karantina  # IMPORT MENU BARU

st.set_page_config(page_title="Sistem Penggemukan Sapi", layout="wide")

@st.cache_resource(ttl=300)
def get_google_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"])
    except Exception:
        return None

sheet = get_google_sheet()

def read_sheet_to_df(worksheet_name, default_cols):
    global sheet
    if not sheet:
        if os.path.exists(f"{worksheet_name}.csv"): return pd.read_csv(f"{worksheet_name}.csv")
        return pd.DataFrame(columns=default_cols)
    for _ in range(3):
        try:
            titles = {w.title.strip().lower(): w.title for w in sheet.worksheets()}
            if worksheet_name.strip().lower() in titles:
                data = sheet.worksheet(titles[worksheet_name.strip().lower()]).get_all_records()
                return pd.DataFrame(data) if data else pd.DataFrame(columns=default_cols)
            else:
                ws = sheet.add_worksheet(title=worksheet_name, rows="1000", cols="20")
                ws.append_row(default_cols)
                return pd.DataFrame(columns=default_cols)
        except Exception: time.sleep(1)
    if os.path.exists(f"{worksheet_name}.csv"): return pd.read_csv(f"{worksheet_name}.csv")
    return pd.DataFrame(columns=default_cols)

def write_df_to_sheet(worksheet_name, df, default_cols):
    global sheet
    with st.spinner(f"💾 Sedang mengunggah data {worksheet_name.replace('_', ' ')}..."):
        df = df.reindex(columns=default_cols).fillna("")
        df.to_csv(f"{worksheet_name}.csv", index=False)
        if not sheet: return
        for _ in range(3):
            try:
                titles = {w.title.strip().lower(): w.title for w in sheet.worksheets()}
                target = worksheet_name.strip().lower()
                ws = sheet.worksheet(titles[target]) if target in titles else sheet.add_worksheet(title=worksheet_name, rows="1000", cols="20")
                ws.clear()
                ws.update(range_name='A1', values=[df.columns.values.tolist()] + df.values.tolist())
                break
            except Exception: time.sleep(1.5)

# ==================== MASTER MENU BARU (DENGAN URUTAN YANG DIMINTA) ====================
ALL_MENUS = [
    "📊 Dashboard & Tabel Monitor",
    "🚛 Timbangan Armada Truk",
    "🐂 Kelola Master Jenis Sapi",
    "➕ Registrasi Sapi Baru",
    "🏥 Karantina & Rekam Medis",
    "🏠 Manajemen Pen & Mutasi Sapi",
    "👥 Manajemen Kelompok",
    "🍽️ Input Pakan Harian",
    "⚖️ Input Timbangan Berkala",
    "📈 Analisis & Grafik Performa",
    "💰 Manajemen Panen & Penjualan",
    "⚙️ Edit & Hapus Data",
    "👥 Manajemen Akun Operator",
    "📜 Log Aktivitas Operator"
]
DEFAULT_JENIS_SAPI = ["Brahman Cross", "Simental", "Limosin", "Hereford", "Sapi Lokal (Bali)", "Sapi Lokal (Madura)", "Sapi Lokal (PO/Peranakan Ongole)", "Ex Impor"]

def add_activity_log(operator, aktivitas, detail):
    cols = ["Tanggal & Waktu", "Operator", "Aktivitas", "Detail Keterangan"]
    waktu_wib = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    df = read_sheet_to_df("log_aktivitas", cols)
    df = pd.concat([df, pd.DataFrame([{"Tanggal & Waktu": waktu_wib, "Operator": operator, "Aktivitas": aktivitas, "Detail Keterangan": detail}])], ignore_index=True)
    write_df_to_sheet("log_aktivitas", df, cols)

def load_users():
    cols = ["Username", "Password", "Role", "Menus"]
    default_admin_menus = "|".join(ALL_MENUS)
    # Menu operator disesuaikan mengikuti urutan baru
    default_op_menus = "|".join(["📊 Dashboard & Tabel Monitor", "🚛 Timbangan Armada Truk", "➕ Registrasi Sapi Baru", "🏥 Karantina & Rekam Medis", "🏠 Manajemen Pen & Mutasi Sapi", "🍽️ Input Pakan Harian", "⚖️ Input Timbangan Berkala", "📈 Analisis & Grafik Performa"])
    
    admin_pwd = st.secrets.get("ADMIN_PASSWORD", "admin123")
    operator_pwd = st.secrets.get("OPERATOR_PASSWORD", "operator123")
    
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
        current_menus = str(row["Menus"]).split("|")
        # Suntik menu baru jika belum ada di akses akun yang sudah eksis
        for w_menu in ["🏥 Karantina & Rekam Medis", "🚛 Timbangan Armada Truk", "👥 Manajemen Kelompok", "📜 Log Aktivitas Operator"]:
            if w_menu not in current_menus:
                if w_menu in ["👥 Manajemen Kelompok", "📜 Log Aktivitas Operator"] and row["Role"] != "Admin": continue
                current_menus.append(w_menu)
                file_updated = True
        if file_updated: df.at[idx, "Menus"] = "|".join(current_menus)
            
    if file_updated: write_df_to_sheet("users", df, cols)
    return df

def save_users(df): write_df_to_sheet("users", df, ["Username", "Password", "Role", "Menus"])
def load_truk_data(): return read_sheet_to_df("timbangan_truk", ["No Transaksi", "Tanggal", "Nama Lokasi Penimbangan", "No Plat / Armada", "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Daftar RFID/EarTag", "Rata-rata / Ekor (kg)", "Operator Lapangan"])
def save_truk_data(df): write_df_to_sheet("timbangan_truk", df, ["No Transaksi", "Tanggal", "Nama Lokasi Penimbangan", "No Plat / Armada", "Keterangan Muatan", "Bruto / Kotor (kg)", "Tara / Kosong (kg)", "Netto / Bersih (kg)", "Jumlah Sapi (Ekor)", "Daftar RFID/EarTag", "Rata-rata / Ekor (kg)", "Operator Lapangan"])

def load_jenis_sapi():
    df = read_sheet_to_df("jenis_sapi", ["Jenis Sapi"])
    if not df.empty: return df["Jenis Sapi"].dropna().tolist()
    write_df_to_sheet("jenis_sapi", pd.DataFrame({"Jenis Sapi": DEFAULT_JENIS_SAPI}), ["Jenis Sapi"])
    return DEFAULT_JENIS_SAPI.copy()

def save_jenis_sapi(list_jenis): write_df_to_sheet("jenis_sapi", pd.DataFrame({"Jenis Sapi": list_jenis}), ["Jenis Sapi"])

def load_master_pen():
    cols = ["Blok", "Pen"]
    df = read_sheet_to_df("master_pen", cols)
    if df.empty:
        df = pd.DataFrame([
            {"Blok": "Blok Karantina", "Pen": "Pen Karantina 1"}, {"Blok": "Blok Karantina", "Pen": "Pen Karantina 2"},
            {"Blok": "Blok Penggemukan A (Bobot < 350kg)", "Pen": "Pen A1"}, {"Blok": "Blok Penggemukan A (Bobot < 350kg)", "Pen": "Pen A2"},
            {"Blok": "Blok Penggemukan B (Bobot 350-450kg)", "Pen": "Pen B1"}, {"Blok": "Blok Penggemukan B (Bobot 350-450kg)", "Pen": "Pen B2"},
            {"Blok": "Blok Penggemukan C (Bobot > 450kg)", "Pen": "Pen C1"}, {"Blok": "Blok Penggemukan C (Bobot > 450kg)", "Pen": "Pen C2"},
            {"Blok": "Blok Isolasi & Perawatan (Sakit)", "Pen": "Pen Isolasi 1"}
        ])
        write_df_to_sheet("master_pen", df, cols)
    return df

def load_data():
    cols = ["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"]
    df = read_sheet_to_df("data_sapi", cols)
    if df.empty: return pd.DataFrame(columns=cols)
    if "Ras Sapi" in df.columns: df = df.rename(columns={"Ras Sapi": "Jenis Sapi"})
    if "Umur Sapi" in df.columns: df["Umur Masuk (Bulan)"] = 12; df = df.drop(columns=["Umur Sapi"])
    for c, v in {"Kode Sapi": "-", "RFID/Tag Asal": "-", "Jenis Kelamin": "Jantan", "Total Pakan (kg)": 0.0, "Tgl Pakan Terakhir": "-", "Lokasi Pen": "Pen Karantina 1"}.items():
        if c not in df.columns: df[c] = v
    return df.reindex(columns=cols)

def save_data(df): write_df_to_sheet("data_sapi", df, ["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"])
def load_panen_data():
    df = read_sheet_to_df("data_panen", ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"])
    if "Kode Sapi" not in df.columns and not df.empty: df["Kode Sapi"] = "-"
    return df
def save_panen_data(df): write_df_to_sheet("data_panen", df, ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"])

def calculate_adg(tgl_masuk, bobot_awal, tgl_akhir, bobot_akhir):
    try:
        t_in = tgl_masuk if isinstance(tgl_masuk, datetime) else datetime.strptime(str(tgl_masuk), "%Y-%m-%d").date()
        t_out = tgl_akhir if isinstance(tgl_akhir, datetime) else datetime.strptime(str(tgl_akhir), "%Y-%m-%d").date()
        days = (t_out - t_in).days
        if days > 0: return round((float(bobot_akhir) - float(bobot_awal)) / days, 2)
    except: pass
    return 0.0

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔒 Login Sistem Penggemukan Sapi</h2>", unsafe_allow_html=True)
    _, col_l2, _ = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login_form"):
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk Aplikasi", type="primary", use_container_width=True):
                df_users = load_users()
                u = df_users[(df_users["Username"].astype(str).str.lower() == username.lower()) & (df_users["Password"].astype(str) == password)]
                if not u.empty:
                    st.session_state.update({"logged_in": True, "username": u.iloc[0]["Username"], "role": u.iloc[0]["Role"], "allowed_menus": u.iloc[0]["Menus"].split("|")})
                    st.query_params.update({"logged_in": "true", "username": u.iloc[0]["Username"], "role": u.iloc[0]["Role"]})
                    add_activity_log(u.iloc[0]["Username"], "Login", "Berhasil masuk ke dalam sistem.")
                    st.rerun()
                else: st.error("Username atau Password salah.")

if "logged_in" not in st.session_state:
    if st.query_params.get("logged_in") == "true":
        df_u = load_users()
        u = df_u[df_u["Username"].astype(str).str.lower() == st.query_params.get("username", "").lower()]
        if not u.empty: st.session_state.update({"logged_in": True, "username": u.iloc[0]["Username"], "role": u.iloc[0]["Role"], "allowed_menus": u.iloc[0]["Menus"].split("|")})
        else: st.session_state["logged_in"] = False
    else: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]: login_page()
else:
    user_role = st.session_state["role"]
    user_name = st.session_state["username"]
    
    # Menata ulang dropdown menu agar selalu mengikuti urutan hierarki yang benar
    raw_user_menus = st.session_state.get("allowed_menus", [ALL_MENUS[0]])
    daftar_menu_user = [m for m in ALL_MENUS if m in raw_user_menus]

    st.title("🐂 Sistem Monitoring Penggemukan Sapi Impor & Lokal")
    st.sidebar.info(f"**User:** {user_name.upper()}\n\n**Hak Akses:** {user_role}")
    
    if st.sidebar.button("🚪 Keluar (Logout)", type="secondary", use_container_width=True):
        add_activity_log(user_name, "Logout", "Keluar dari sistem.")
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    menu = st.sidebar.selectbox("PILIH MENU APLIKASI", daftar_menu_user)

    with st.spinner("⏳ Menyelaraskan koneksi cloud... Sedang mengunduh seluruh database master kandang terbaru..."):
        df_sapi = load_data()
        df_panen = load_panen_data()
        df_truk = load_truk_data()
        LIST_JENIS_SAPI = load_jenis_sapi()
        
        df_pen_master = load_master_pen()
        STRUKTUR_KANDANG, DAFTAR_PEN = {}, []
        for _, row in df_pen_master.iterrows():
            b, p = str(row["Blok"]).strip(), str(row["Pen"]).strip()
            if b and p:
                STRUKTUR_KANDANG.setdefault(b, []).append(p)
                if f"{b} - {p}" not in DAFTAR_PEN: DAFTAR_PEN.append(f"{b} - {p}")

    st.markdown("---")

    # ==================== CONTROLLER MENU ROUTING ====================
    if menu == "📊 Dashboard & Tabel Monitor":
        tampilkan_dashboard(df_sapi, read_sheet_to_df)
    elif menu == "🚛 Timbangan Armada Truk":
        tampilkan_menu_timbangan_truk(df_truk, save_truk_data, add_activity_log, user_name)
    elif menu == "🐂 Kelola Master Jenis Sapi":
        tampilkan_menu_jenis_sapi(LIST_JENIS_SAPI, save_jenis_sapi, add_activity_log, user_name)
    elif menu == "➕ Registrasi Sapi Baru":
        tampilkan_menu_registrasi(df_sapi, LIST_JENIS_SAPI, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, user_role)
    elif menu == "🏥 Karantina & Rekam Medis":
        tampilkan_menu_karantina(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, user_role, read_sheet_to_df, write_df_to_sheet)
    elif menu == "🏠 Manajemen Pen & Mutasi Sapi":
        tampilkan_menu_pen_mutasi(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, user_role, calculate_adg, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet)
    elif menu == "👥 Manajemen Kelompok":
        tampilkan_menu_manajemen_kelompok(df_sapi, DAFTAR_PEN, user_role, save_data, add_activity_log, user_name)      
    elif menu == "🍽️ Input Pakan Harian":
        tampilkan_menu_pakan(df_sapi, STRUKTUR_KANDANG, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet)
    elif menu == "⚖️ Input Timbangan Berkala":
        tampilkan_menu_timbangan(df_sapi, calculate_adg, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet)
    elif menu == "📈 Analisis & Grafik Performa":
        tampilkan_menu_analisis_grafik(df_sapi, DAFTAR_PEN)
    elif menu == "💰 Manajemen Panen & Penjualan":
        tampilkan_menu_panen_penjualan(df_sapi, df_panen, save_panen_data, save_data, add_activity_log, user_name)
    elif menu == "⚙️ Edit & Hapus Data":
        tampilkan_menu_edit_hapus(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, save_data, add_activity_log, user_name)
    elif menu == "👥 Manajemen Akun Operator":
        tampilkan_menu_operator(load_users, ALL_MENUS, save_users, add_activity_log, user_name)
    elif menu == "📜 Log Aktivitas Operator":
        tampilkan_menu_log(read_sheet_to_df, write_df_to_sheet)