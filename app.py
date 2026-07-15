import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import time
import re
from sqlalchemy import create_engine, text

# Import sub-menu aplikasi
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
from menu.karantina import tampilkan_menu_karantina 

st.set_page_config(page_title="Sistem Penggemukan Sapi", layout="wide")

# ==================== KONEKSI DATABASE SUPABASE ====================
@st.cache_resource(ttl=300)
def get_db_engine():
    try:
        connection_string = st.secrets["supabase"]["connection_string"]
        return create_engine(connection_string)
    except Exception as e:
        st.error(f"Gagal inisialisasi database Supabase: {e}")
        return None

# Kamus Pemetaan Kolom Otomatis (App <=> Supabase Database)
DB_MAPPING = {
    "log_aktivitas": {
        "columns": {"Tanggal & Waktu": "tanggal_waktu", "Operator": "operator", "Aktivitas": "aktivitas", "Detail Keterangan": "detail_keterangan"}
    },
    "users": {
        "columns": {"Username": "username", "Password": "password", "Role": "role", "Menus": "menus"}
    },
    "timbangan_truk": {
        "columns": {
            "No Transaksi": "no_transaksi", "Tanggal": "tanggal", "Nama Lokasi Penimbangan": "nama_lokasi_penimbangan",
            "No Plat / Armada": "no_plat_armada", "Keterangan Muatan": "keterangan_muatan", "Bruto / Kotor (kg)": "bruto_kotor_kg",
            "Tara / Kosong (kg)": "tara_kosong_kg", "Netto / Bersih (kg)": "netto_bersih_kg", "Jumlah Sapi (Ekor)": "jumlah_sapi_ekor",
            "Daftar RFID/EarTag": "daftar_rfid_eartag", "Rata-rata / Ekor (kg)": "rata_rata_ekor_kg", "Operator Lapangan": "operator_lapangan"
        }
    },
    "jenis_sapi": {
        "columns": {"Jenis Sapi": "jenis_sapi"}
    },
    "master_pen": {
        "columns": {"Blok": "blok", "Pen": "pen"}
    },
    "data_sapi": {
        "columns": {
            "Kode Sapi": "kode_sapi", "RFID/Tag Asal": "rfid_tag_asal", "RFID/Tag": "rfid_tag", "Jenis Sapi": "jenis_sapi",
            "Jenis Kelamin": "jenis_kelamin", "Umur Masuk (Bulan)": "umur_masuk_bulan", "Asal Negara": "asal_negara",
            "Tgl Masuk": "tgl_masuk", "Bobot Awal (kg)": "bobot_awal", "Tgl Cek Akhir": "tgl_cek_akhir",
            "Bobot Akhir (kg)": "bobot_akhir", "ADG (kg/hari)": "adg_kg_hari", "Total Pakan (kg)": "total_pakan_kg",
            "Tgl Pakan Terakhir": "tgl_pakan_terakhir", "Lokasi Pen": "lokasi_pen"
        }
    },
    "data_panen": {
        "columns": {
            "Kode Sapi": "kode_sapi", "RFID/Tag": "rfid_tag", "Jenis Sapi": "jenis_sapi", "Jenis Kelamin": "jenis_kelamin",
            "Asal Negara": "asal_negara", "Tgl Masuk": "tgl_masuk", "Tgl Panen": "tgl_panen", "Lama Pelihara (Hari)": "lama_pelihara_hari",
            "Bobot Awal (kg)": "bobot_awal_kg", "Bobot Panen (kg)": "bobot_panen_kg", "Total Gain (kg)": "total_gain_kg",
            "Total Pakan (kg)": "total_pakan_kg", "FCR Akhir": "fcr_akhir", "ADG Akhir (kg/hari)": "adg_akhir_kg_hari",
            "Harga Jual /kg (Rp)": "harga_jual_kg_rp", "Total Pendapatan (Rp)": "total_pendapatan_rp", "Pembeli/Tujuan": "pembeli_tujuan"
        }
    },
    "riwayat_medis_karantina": {
        "columns": {
            "Tanggal": "tanggal", "Kode Sapi": "kode_sapi", "RFID/Tag": "rfid_tag", 
            "Suhu Tubuh (°C)": "suhu_tubuh_celcius", "Kondisi Klinis": "kondisi_klinis", 
            "Tindakan Medis": "tindakan_medis", "Catatan": "catatan", "Operator": "operator"
        }
    }
}

def read_sheet_to_df(worksheet_name, default_cols):
    engine = get_db_engine()
    if not engine:
        if os.path.exists(f"{worksheet_name}.csv"): return pd.read_csv(f"{worksheet_name}.csv")
        return pd.DataFrame(columns=default_cols)
    try:
        clean_name = worksheet_name.lower().strip()
        df = pd.read_sql(f"SELECT * FROM {clean_name}", engine)
        
        if df.empty and os.path.exists(f"{worksheet_name}.csv"):
            df_local = pd.read_csv(f"{worksheet_name}.csv")
            if not df_local.empty:
                for col in default_cols:
                    if col not in df_local.columns: df_local[col] = ""
                return df_local[default_cols]
            
        if "id" in df.columns: df = df.drop(columns=["id"])
            
        if worksheet_name in DB_MAPPING:
            inv_map = {v: k for k, v in DB_MAPPING[worksheet_name]["columns"].items()}
            df = df.rename(columns=inv_map)
        else:
            clean_cols = {}
            for col in df.columns:
                formatted = str(col).replace('_', ' ').title()
                if formatted.endswith(' Kg'): formatted = formatted[:-3] + ' (kg)'
                clean_cols[col] = formatted
            df = df.rename(columns=clean_cols)

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]) or any(k in str(col).lower() for k in ['tgl', 'tanggal']):
                df[col] = df[col].apply(lambda x: str(x)[:10] if pd.notnull(x) and str(x) != 'None' else "-")

        for col in default_cols:
            if col not in df.columns: df[col] = ""
        return df[default_cols]
    except Exception:
        if os.path.exists(f"{worksheet_name}.csv"): return pd.read_csv(f"{worksheet_name}.csv")
        return pd.DataFrame(columns=default_cols)

def write_df_to_sheet(worksheet_name, df, default_cols):
    engine = get_db_engine()
    worksheet_name = worksheet_name.lower().strip()
    with st.spinner(f"💾 Sinkronisasi {worksheet_name.replace('_', ' ')} ke Supabase..."):
        df = df.reindex(columns=default_cols).fillna("")
        df.to_csv(f"{worksheet_name}.csv", index=False) 
        if not engine: return
        try:
            df_db = df.copy()
            if worksheet_name in DB_MAPPING:
                df_db = df_db.rename(columns=DB_MAPPING[worksheet_name]["columns"])
                df_db = df_db[list(DB_MAPPING[worksheet_name]["columns"].values())]
            else:
                clean_columns = {}
                for col in df_db.columns:
                    c = str(col).lower().replace(' ', '_').replace('/', '_')
                    c = re.sub(r'[^a-z0-9_]', '', c)
                    clean_columns[col] = c
                df_db = df_db.rename(columns=clean_columns)

            for col in df_db.columns:
                if any(k in col for k in ['kg', 'bulan', 'hari', 'rp', 'ekor', 'bobot', 'adg', 'total', 'fcr', 'suhu']):
                    df_db[col] = pd.to_numeric(df_db[col], errors='coerce').fillna(0)
                elif any(k in col for k in ['tgl', 'tanggal']):
                    df_db[col] = df_db[col].apply(lambda x: None if str(x).strip() in ["", "None", "NaN", "-"] else str(x))

            def jalankan_penyimpanan(connection):
                connection.execute(text(f"DELETE FROM {worksheet_name}")) 
                df_db.to_sql(worksheet_name, connection, if_exists='append', index=False)

            try:
                with engine.begin() as conn: jalankan_penyimpanan(conn)
            except Exception as e_db:
                error_msg = str(e_db)
                if "does not exist" in error_msg or "UndefinedTable" in error_msg:
                    columns_sql = ",\n  ".join([f"{col} NUMERIC" if any(k in col for k in ['kg', 'bulan', 'hari', 'rp', 'ekor', 'bobot', 'adg', 'total', 'fcr', 'suhu']) else f"{col} TEXT" for col in df_db.columns])
                    sql_auto_create = f"CREATE TABLE {worksheet_name} (\n  id SERIAL PRIMARY KEY,\n  {columns_sql}\n);"
                    
                    with engine.begin() as conn_create: conn_create.execute(text(sql_auto_create))
                    with engine.begin() as conn_retry: jalankan_penyimpanan(conn_retry)
                    st.toast(f"✨ Auto-Pilot: Tabel '{worksheet_name}' sukses dibuat otomatis di Cloud!", icon="🚀")
                else:
                    raise e_db
        except Exception as e:
            st.error(f"❌ Gagal sinkronisasi data ke Supabase: {e}")

def append_df_to_db(worksheet_name, df_new_records, default_cols):
    engine = get_db_engine()
    worksheet_name = worksheet_name.lower().strip()
    with st.spinner(f"🚀 Menyisipkan data baru ke {worksheet_name.replace('_', ' ')}..."):
        df_db = df_new_records.reindex(columns=default_cols).fillna("")
        
        csv_file = f"{worksheet_name}.csv"
        file_exists = os.path.exists(csv_file)
        df_db.to_csv(csv_file, mode='a', header=not file_exists, index=False)
        
        if not engine: 
            return
        try:
            if worksheet_name in DB_MAPPING:
                df_db = df_db.rename(columns=DB_MAPPING[worksheet_name]["columns"])
                df_db = df_db[list(DB_MAPPING[worksheet_name]["columns"].values())]
            else:
                clean_columns = {}
                for col in df_db.columns:
                    c = str(col).lower().replace(' ', '_').replace('/', '_')
                    c = re.sub(r'[^a-z0-9_]', '', c)
                    clean_columns[col] = c
                df_db = df_db.rename(columns=clean_columns)

            for col in df_db.columns:
                if any(k in col for k in ['kg', 'bulan', 'hari', 'rp', 'ekor', 'bobot', 'adg', 'total', 'fcr', 'suhu']):
                    df_db[col] = pd.to_numeric(df_db[col], errors='coerce').fillna(0)
                elif any(k in col for k in ['tgl', 'tanggal']):
                    df_db[col] = df_db[col].apply(lambda x: None if str(x).strip() in ["", "None", "NaN", "-"] else str(x))

            def jalankan_append(connection):
                df_db.to_sql(worksheet_name, connection, if_exists='append', index=False)

            try:
                with engine.begin() as conn: jalankan_append(conn)
            except Exception as e_db:
                error_msg = str(e_db)
                if "does not exist" in error_msg or "UndefinedTable" in error_msg:
                    columns_sql = ",\n  ".join([f"{col} NUMERIC" if any(k in col for k in ['kg', 'bulan', 'hari', 'rp', 'ekor', 'bobot', 'adg', 'total', 'fcr', 'suhu']) else f"{col} TEXT" for col in df_db.columns])
                    sql_auto_create = f"CREATE TABLE {worksheet_name} (\n  id SERIAL PRIMARY KEY,\n  {columns_sql}\n);"
                    with engine.begin() as conn_create: conn_create.execute(text(sql_auto_create))
                    with engine.begin() as conn_retry: jalankan_append(conn_retry)
                    st.toast(f"✨ Auto-Pilot: Tabel '{worksheet_name}' sukses dibuat otomatis di Cloud!", icon="🚀")
                else:
                    raise e_db
        except Exception as e:
            st.error(f"❌ Gagal menambahkan baris baru ke Supabase: {e}")

# Pengaturan Menu Aplikasi
ALL_MENUS = [
    "📊 Dashboard & Tabel Monitor", "🚛 Timbangan Armada Truk", "🐂 Kelola Master Jenis Sapi",
    "➕ Registrasi Sapi Baru", "🏥 Karantina & Rekam Medis", "🏠 Manajemen Pen & Mutasi Sapi",
    "👥 Manajemen Kelompok", "🍽️ Input Pakan Harian", "⚖️ Input Timbangan Berkala",
    "📈 Analisis & Grafik Performa", "💰 Manajemen Panen & Penjualan", "⚙️ Edit & Hapus Data",
    "👥 Manajemen Akun Operator", "📜 Log Aktivitas Operator"
]
DEFAULT_JENIS_SAPI = ["Brahman Cross", "Simental", "Limosin", "Hereford", "Sapi Lokal (Bali)", "Sapi Lokal (Madura)", "Sapi Lokal (PO/Peranakan Ongole)", "Ex Impor"]

def add_activity_log(operator, aktivitas, detail):
    cols = ["Tanggal & Waktu", "Operator", "Aktivitas", "Detail Keterangan"]
    waktu_wib = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    df_new_log = pd.DataFrame([{"Tanggal & Waktu": waktu_wib, "Operator": operator, "Aktivitas": aktivitas, "Detail Keterangan": detail}])
    append_df_to_db("log_aktivitas", df_new_log, cols)

def load_users():
    cols = ["Username", "Password", "Role", "Menus"]
    default_admin_menus = "|".join(ALL_MENUS)
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
    return df.reindex(columns=cols)

def save_data(df): write_df_to_sheet("data_sapi", df, ["Kode Sapi", "RFID/Tag Asal", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Umur Masuk (Bulan)", "Asal Negara", "Tgl Masuk", "Bobot Awal (kg)", "Tgl Cek Akhir", "Bobot Akhir (kg)", "ADG (kg/hari)", "Total Pakan (kg)", "Tgl Pakan Terakhir", "Lokasi Pen"])
def load_panen_data(): return read_sheet_to_df("data_panen", ["Kode Sapi", "RFID/Tag", "Jenis Sapi", "Jenis Kelamin", "Asal Negara", "Tgl Masuk", "Tgl Panen", "Lama Pelihara (Hari)", "Bobot Awal (kg)", "Bobot Panen (kg)", "Total Gain (kg)", "Total Pakan (kg)", "FCR Akhir", "ADG Akhir (kg/hari)", "Harga Jual /kg (Rp)", "Total Pendapatan (Rp)", "Pembeli/Tujuan"])
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
        # [DIUBAH] Penarikan df_panen dan df_truk dihapus dari sini agar aplikasi menjadi ringan & realtime cepat!
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
        # [DIUBAH] Mengirimkan fungsi database connector (lazy loading)
        tampilkan_menu_timbangan_truk(add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet)
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
        # [DIUBAH] Mengirimkan fungsi database connector (lazy loading)
        tampilkan_menu_panen_penjualan(df_sapi, save_data, add_activity_log, user_name, read_sheet_to_df, write_df_to_sheet)
    elif menu == "⚙️ Edit & Hapus Data":
        tampilkan_menu_edit_hapus(df_sapi, LIST_JENIS_SAPI, DAFTAR_PEN, save_data, add_activity_log, user_name)
    elif menu == "👥 Manajemen Akun Operator":
        tampilkan_menu_operator(load_users, ALL_MENUS, save_users, add_activity_log, user_name)
    elif menu == "📜 Log Aktivitas Operator":
        tampilkan_menu_log(read_sheet_to_df, write_df_to_sheet)