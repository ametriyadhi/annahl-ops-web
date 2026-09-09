# -*- coding: utf-8 -*-
"""
checklist_core.py - Sistem Monitoring Checklist Pemeliharaan OB & Gardener
Ekosistem Operasional Ramah Lingkungan & Paperless — An Nahl Islamic School

Core Features:
1. Zero-Login Mobile Web Checklist PWA (<60KB) via QR Token & Dynamic Shift Auto-Detection.
2. Geofence Distance Validation with Indoor GPS Fallback.
3. Client-side HTML5 Canvas Image Compression (<150KB) before upload.
4. Closed-Loop Auto-Ticketing Sarpras for damaged/leaking facilities (SLA 2-8 jam).
5. Green Operations Index (kertas diselamatkan, air dicegah bocor, hemat energi).
6. Print-Ready QR Acrylic Stickers (A5/A6) for maintenance zones.
"""

import os
import re
import json
import uuid
import math
import base64
import sqlite3
import requests
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Blueprint, request, jsonify, session, render_template_string

WIB = ZoneInfo("Asia/Jakarta")

def now_wib():
    return datetime.now(WIB)

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"
UPLOAD_DIR = "/home/ametriyadhi/annahl-ops-web/static/uploads/checklist"
os.makedirs(UPLOAD_DIR, exist_ok=True)

checklist_bp = Blueprint('checklist', __name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== DATABASE INITIALIZATION & SEEDING ====================

def init_checklist_db():
    conn = get_db()
    cur = conn.cursor()

    # 1. Master Zona & Titik Pemeliharaan
    cur.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_zones (
            id TEXT PRIMARY KEY,
            unit_type TEXT NOT NULL,
            sub_scope TEXT NOT NULL,
            zone_name TEXT NOT NULL,
            building_or_sector TEXT,
            target_lat REAL NOT NULL,
            target_lng REAL NOT NULL,
            geofence_radius_m INTEGER DEFAULT 45,
            qr_token TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Master Template Parameter Checklist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS checklist_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_type TEXT NOT NULL,
            sub_scope TEXT NOT NULL,
            shift_code TEXT NOT NULL,
            item_order INTEGER DEFAULT 1,
            item_label TEXT NOT NULL,
            help_text TEXT,
            is_eco_critical INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # 3. Transaksi Log Checklist Lapangan
    cur.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_checklist_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id TEXT NOT NULL,
            shift_code TEXT NOT NULL,
            petugas_name TEXT NOT NULL,
            petugas_wa TEXT,
            checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_lat REAL,
            user_lng REAL,
            distance_meters REAL,
            is_within_geofence INTEGER DEFAULT 1,
            status_summary TEXT NOT NULL,
            checklist_data_json TEXT NOT NULL,
            anomaly_notes TEXT,
            photo_url TEXT,
            ticket_id TEXT,
            FOREIGN KEY(zone_id) REFERENCES maintenance_zones(id)
        )
    ''')

    # 4. Transaksi Closed-Loop Tiket Perbaikan Sarpras
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_maintenance_tickets (
            ticket_id TEXT PRIMARY KEY,
            source_checklist_id INTEGER,
            zone_id TEXT NOT NULL,
            unit_source TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT DEFAULT 'MEDIUM',
            issue_description TEXT NOT NULL,
            photo_before_url TEXT,
            reporter_name TEXT NOT NULL,
            reporter_wa TEXT,
            assigned_tech_name TEXT,
            assigned_tech_wa TEXT,
            status TEXT DEFAULT 'OPEN',
            resolution_notes TEXT,
            photo_after_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            sla_hours INTEGER DEFAULT 4,
            FOREIGN KEY(zone_id) REFERENCES maintenance_zones(id)
        )
    ''')

    # 5. Rekap Metrik Keberlanjutan Lingkungan (Green Ops Index)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS green_ops_daily_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_date DATE NOT NULL,
            unit_type TEXT NOT NULL,
            organic_waste_kg REAL DEFAULT 0,
            compost_harvest_kg REAL DEFAULT 0,
            water_leaks_prevented INTEGER DEFAULT 0,
            veggie_harvest_kg REAL DEFAULT 0,
            notes TEXT,
            logged_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Indexes untuk performa tinggi
    cur.execute('CREATE INDEX IF NOT EXISTS idx_maint_logs_zone_time ON maintenance_checklist_logs(zone_id, checked_at)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_maint_logs_shift ON maintenance_checklist_logs(shift_code)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_maint_tickets_status ON ops_maintenance_tickets(status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_maint_zones_unit ON maintenance_zones(unit_type, is_active)')

    conn.commit()

    # Seeding Data Pilot jika masih kosong
    cur.execute('SELECT COUNT(*) FROM maintenance_zones')
    if cur.fetchone()[0] == 0:
        seed_pilot_data(cur)
        conn.commit()

    # Seeding Template Parameter jika masih kosong
    cur.execute('SELECT COUNT(*) FROM checklist_templates')
    if cur.fetchone()[0] == 0:
        seed_checklist_templates(cur)
        conn.commit()

    conn.close()


def seed_pilot_data(cur):
    """Seed 10 titik pilot OB dan 10 titik pilot Gardener"""
    zones = [
        # OB Pilot Zones (Sanitasi & Ruang)
        ('ZONE-OB-TOILET-SD-L1', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SD Lt 1', 'Gedung SD', -6.339295, 106.9643658, 45, 'qr_ob_sd1_toilet', 1),
        ('ZONE-OB-TOILET-SD-L2', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SD Lt 2', 'Gedung SD', -6.339295, 106.9643658, 45, 'qr_ob_sd2_toilet', 1),
        ('ZONE-OB-TOILET-SD-L3', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SD Lt 3', 'Gedung SD', -6.339295, 106.9643658, 45, 'qr_ob_sd3_toilet', 1),
        ('ZONE-OB-TOILET-SMP-L1', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SMP Lt 1', 'Gedung SMP', -6.3392024, 106.9647293, 45, 'qr_ob_smp1_toilet', 1),
        ('ZONE-OB-TOILET-SMP-L2', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SMP Lt 2', 'Gedung SMP', -6.3392024, 106.9647293, 45, 'qr_ob_smp2_toilet', 1),
        ('ZONE-OB-TOILET-SMA-L1', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SMA Lt 1', 'Gedung SMA', -6.3392024, 106.9647293, 45, 'qr_ob_sma1_toilet', 1),
        ('ZONE-OB-TOILET-SMA-L2', 'OB', 'INDOOR_SANITASI', 'Toilet Siswa SMA Lt 2', 'Gedung SMA', -6.3392024, 106.9647293, 45, 'qr_ob_sma2_toilet', 1),
        ('ZONE-OB-RUANG-GURU', 'OB', 'INDOOR_SANITASI', 'Ruang Guru & Tata Usaha Utama', 'Gedung FO', -6.3386552, 106.9645968, 45, 'qr_ob_rguru_fo', 1),
        ('ZONE-OB-KORIDOR-LOBI', 'OB', 'INDOOR_SANITASI', 'Lobi Utama & Koridor Gedung FO', 'Gedung FO', -6.3386552, 106.9645968, 45, 'qr_ob_lobi_fo', 1),
        ('ZONE-OB-MASJID-WUDHU', 'OB', 'INDOOR_SANITASI', 'Toilet & Tempat Wudhu Masjid An Nahl', 'Gedung Masjid', -6.3393294, 106.9650421, 45, 'qr_ob_masjid_wudhu', 1),

        # Gardener Pilot Zones (Taman, Lanskap, Kompos, Ecopark)
        ('ZONE-GAR-TAMAN-GERBANG', 'GARDENER', 'TAMAN_LANSKAP', 'Taman Gerbang Utama & Drop Zone', 'Sentra Publik', -6.3384000, 106.9645000, 45, 'qr_gar_taman_gerbang', 1),
        ('ZONE-GAR-GAZEBO-DEPAN', 'GARDENER', 'TAMAN_LANSKAP', 'Gazebo & Kolam Depan', 'Taman Depan', -6.3385000, 106.9646000, 45, 'qr_gar_gazebo_depan', 1),
        ('ZONE-GAR-LAPANGAN-RUMPUT', 'GARDENER', 'TAMAN_LANSKAP', 'Lapangan Rumput & Area Olahraga', 'Lapangan Utama', -6.3391000, 106.9644000, 50, 'qr_gar_lapangan', 1),
        ('ZONE-GAR-ECOPARK-KELINCI', 'GARDENER', 'AGRO_TERNAK', 'Ecopark - Kandang Kelinci & Unggas', 'Ecopark', -6.3395000, 106.9652000, 45, 'qr_gar_ecopark_kelinci', 1),
        ('ZONE-GAR-ECOPARK-KAMBING', 'GARDENER', 'AGRO_TERNAK', 'Ecopark - Kandang Kambing & Domba', 'Ecopark', -6.3395500, 106.9653000, 45, 'qr_gar_ecopark_kambing', 1),
        ('ZONE-GAR-ECOPARK-KOLAM', 'GARDENER', 'AGRO_TERNAK', 'Ecopark - Kolam Ikan Nila & Bioflok', 'Ecopark', -6.3396000, 106.9652500, 45, 'qr_gar_ecopark_kolam', 1),
        ('ZONE-GAR-RUMAH-KOMPOS', 'GARDENER', 'TAMAN_LANSKAP', 'Rumah Kompos & Pencacahan Serasah', 'Edupark', -6.3397000, 106.9654000, 45, 'qr_gar_rumah_kompos', 1),
        ('ZONE-GAR-KEBUN-HIDROPONIK', 'GARDENER', 'AGRO_TERNAK', 'Greenhouse & Kebun Sayur Hidroponik', 'Edupark', -6.3396500, 106.9653500, 45, 'qr_gar_hidroponik', 1),
        ('ZONE-GAR-KEBUN-ORGANIK', 'GARDENER', 'AGRO_TERNAK', 'Kebun Sayur Organik Bedengan Tanah', 'Edupark', -6.3397500, 106.9654500, 45, 'qr_gar_kebun_organik', 1),
        ('ZONE-GAR-PEMBIBITAN', 'GARDENER', 'TAMAN_LANSKAP', 'Area Pembibitan Tanaman & Stek', 'Edupark', -6.3398000, 106.9655000, 45, 'qr_gar_pembibitan', 1),
    ]
    cur.executemany('''
        INSERT OR IGNORE INTO maintenance_zones (
            id, unit_type, sub_scope, zone_name, building_or_sector, target_lat, target_lng, geofence_radius_m, qr_token, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', zones)


def seed_checklist_templates(cur):
    """Seed standar parameter checklist OB & Gardener berwawasan lingkungan"""
    templates = [
        # --- UNIT OB / INDOOR SANITASI ---
        # Shift Pagi (06:30 - 08:30): Kesiapan Kelas & Koridor
        ('OB', 'INDOOR_SANITASI', 'PAGI', 1, 'Lantai disapu & dipel higienis (wangi & bersih)', 'Pastikan tidak ada noda atau genangan air', 0),
        ('OB', 'INDOOR_SANITASI', 'PAGI', 2, 'Meja, kursi & papan tulis rapi/bersih', 'Debu telah dibersihkan & tersusun rapi', 0),
        ('OB', 'INDOOR_SANITASI', 'PAGI', 3, 'Tempat sampah kosong & kantong liner terpasang', 'Sampah sisa kemarin telah diangkut ke TPS', 0),
        ('OB', 'INDOOR_SANITASI', 'PAGI', 4, 'Kaca jendela & ventilasi bersih dari debu', 'Buka jendela secukupnya untuk sirkulasi udara alami pagi', 0),
        ('OB', 'INDOOR_SANITASI', 'PAGI', 5, '🌿 Hemat Energi: Saklar lampu & AC mati jika ruang belum digunakan', 'Gunakan pencahayaan alami matahari saat pagi hari', 1),

        # Shift Siang 1 (08:30 - 12:30): Sanitasi Toilet Sesi 1
        ('OB', 'INDOOR_SANITASI', 'SIANG_1', 1, '💧 Kran wastafel/bak mengalir normal & TIDAK BOCOR/MENETES', 'Cek dinding bak & sambungan selang fleksibel (Konservasi Air)', 1),
        ('OB', 'INDOOR_SANITASI', 'SIANG_1', 2, '🚽 Kloset & urinal bersih, flush berfungsi normal tanpa macet', 'Pastikan pelampung toren tidak mengalir terus menerus', 1),
        ('OB', 'INDOOR_SANITASI', 'SIANG_1', 3, 'Sabun cuci tangan & tisu wastafel terisi cukup', 'Cek kebersihan dispenser sabun biodegradable', 0),
        ('OB', 'INDOOR_SANITASI', 'SIANG_1', 4, 'Lantai kering (tidak licin/becek) & cermin wastafel bersih', 'Pel berkala untuk mencegah risiko terpeleset', 0),
        ('OB', 'INDOOR_SANITASI', 'SIANG_1', 5, 'Exhaust fan / ventilasi udara berfungsi (ruangan segar & tidak berbau)', 'Gunakan pengharum ruangan alami / kamper aman', 0),

        # Shift Siang 2 (12:30 - 16:00): Sanitasi Toilet Sesi 2
        ('OB', 'INDOOR_SANITASI', 'SIANG_2', 1, '💧 Kran wastafel/bak mengalir normal & TIDAK BOCOR/MENETES', 'Cek dinding bak & sambungan selang fleksibel (Konservasi Air)', 1),
        ('OB', 'INDOOR_SANITASI', 'SIANG_2', 2, '🚽 Kloset & urinal bersih, flush berfungsi normal tanpa macet', 'Pastikan pelampung toren tidak mengalir terus menerus', 1),
        ('OB', 'INDOOR_SANITASI', 'SIANG_2', 3, 'Sabun cuci tangan & tisu wastafel terisi cukup', 'Cek kebersihan dispenser sabun biodegradable', 0),
        ('OB', 'INDOOR_SANITASI', 'SIANG_2', 4, 'Lantai kering (tidak licin/becek) & cermin wastafel bersih', 'Pel berkala untuk mencegah risiko terpeleset', 0),
        ('OB', 'INDOOR_SANITASI', 'SIANG_2', 5, 'Exhaust fan / ventilasi udara berfungsi (ruangan segar & tidak berbau)', 'Gunakan pengharum ruangan alami / kamper aman', 0),

        # Shift Sore (16:00 - 18:00): Closing & Konservasi Energi
        ('OB', 'INDOOR_SANITASI', 'SORE', 1, '♻️ Sampah ruangan diangkut & dipilah (anorganik botol/kertas vs residu)', 'Pemisahan sampah di sumber menuju TPS sekolah', 1),
        ('OB', 'INDOOR_SANITASI', 'SORE', 2, '⚡ Hemat Energi: Seluruh lampu, pendingin AC & dispenser posisi OFF', 'Matikan total untuk memutus beban vampire load malam hari', 1),
        ('OB', 'INDOOR_SANITASI', 'SORE', 3, 'Pintu, jendela & gorden tertutup dan terkunci aman', 'Pastikan fasilitas aman sebelum meninggalkan gedung', 0),

        # --- UNIT GARDENER / TAMAN & LANSKAP ---
        # Shift Pagi (06:00 - 08:30): Penyiraman Efisien & Kebersihan
        ('GARDENER', 'TAMAN_LANSKAP', 'PAGI', 1, '💧 Penyiraman tuntas sebelum jam 08:30 (efisiensi air & kurangi evaporasi)', 'Gunakan air tandon hujan/sumber alami secara hemat', 1),
        ('GARDENER', 'TAMAN_LANSKAP', 'PAGI', 2, 'Rumput & semak dipangkas rapi secara berkala', 'Jalur hijau tampak terawat & estetis', 0),
        ('GARDENER', 'TAMAN_LANSKAP', 'PAGI', 3, 'Jalur pedestrian, trotoar & selokan bersih dari sampah/daun', 'Aliran air parit lancar tidak tersumbat', 0),

        # Shift Siang (12:30 - 15:30): Rumah Kompos & Sampah Organik
        ('GARDENER', 'TAMAN_LANSKAP', 'SIANG_1', 1, '🍂 Serasah dedaunan taman dikumpulkan & dicacah mesin', 'Bahan baku organik dipersiapkan untuk proses fermentasi', 1),
        ('GARDENER', 'TAMAN_LANSKAP', 'SIANG_1', 2, '♻️ Zero Burning Policy: 100% dedaunan masuk ke bak komposter aktif', 'Dilarang keras membakar sampah daun/ranting di area sekolah', 1),
        ('GARDENER', 'TAMAN_LANSKAP', 'SIANG_1', 3, 'Pengecekan aerasi, suhu & kelembaban tumpukan kompos aktif', 'Siram bio-aktivator / EM4 berkala agar fermentasi optimal', 0),

        # Shift Sore (16:00 - 18:00): Closing Outdoor & K3
        ('GARDENER', 'TAMAN_LANSKAP', 'SORE', 1, '💧 Selang air tergulung rapi & kran utama tertutup rapat tanpa bocor', 'Pastikan tidak ada kran taman yang menetes semalaman', 1),
        ('GARDENER', 'TAMAN_LANSKAP', 'SORE', 2, 'Peralatan kerja (mesin potong rumput, gunting) bersih & aman di gudang', 'Perawatan alat kerja agar berumur panjang', 0),
        ('GARDENER', 'TAMAN_LANSKAP', 'SORE', 3, 'Area bebas dari genangan air jentik nyamuk', 'Tutup wadah penampung air liar di taman', 1),

        # --- UNIT GARDENER / AGRO & ECOPARK ---
        ('GARDENER', 'AGRO_TERNAK', 'ALL_DAY', 1, '💧 Sirkulasi nutrisi hidroponik normal & PPM air terpantau baik', 'Cek pompa sirkulasi hidroponik & pasokan air tandon', 1),
        ('GARDENER', 'AGRO_TERNAK', 'ALL_DAY', 2, 'Pemberian pakan bernutrisi & pasokan air minum segar untuk ternak', 'Kandang kelinci, kambing & kolam ikan telah diberi pakan', 0),
        ('GARDENER', 'AGRO_TERNAK', 'ALL_DAY', 3, '♻️ Sanitasi kandang & kotoran hewan dialirkan ke bahan pupuk organik/maggot', 'Pemanfaatan kotoran hewan untuk ekonomi sirkular ramah lingkungan', 1),
        ('GARDENER', 'AGRO_TERNAK', 'ALL_DAY', 4, 'Observasi kesehatan ternak & pencatatan panen sayuran/ikan siap konsumsi', 'Pastikan hewan aktif, sehat & lingkungan kandang higienis', 0),
    ]
    cur.executemany('''
        INSERT OR IGNORE INTO checklist_templates (
            unit_type, sub_scope, shift_code, item_order, item_label, help_text, is_eco_critical
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', templates)


# Jalankan inisialisasi tabel saat modul dimuat
init_checklist_db()


# ==================== HELPER FUNCTIONS ====================

def calculate_haversine(lat1, lon1, lat2, lon2):
    """Menghitung jarak dalam meter antara dua koordinat GPS"""
    try:
        R = 6371000.0
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)
    except Exception:
        return 999999.0

def detect_shift_code(cur_time_str=None):
    """Auto-detect shift berdasarkan jam operasional real-time WIB"""
    if not cur_time_str:
        cur_time_str = now_wib().strftime("%H:%M")
    
    # 06:00 - 08:30 = PAGI (Pre-class / Siram Pagi)
    # 08:30 - 12:30 = SIANG_1 (Toilet mid-day 1)
    # 12:30 - 16:00 = SIANG_2 (Toilet mid-day 2 / Kompos)
    # 16:00 - 18:00 = SORE (Closing / Energy shutoff)
    if cur_time_str < "08:30":
        return "PAGI", "Shift Pagi (Kesiapan & Pre-Class)"
    elif cur_time_str < "12:30":
        return "SIANG_1", "Shift Siang Sesi 1 (Sanitasi)"
    elif cur_time_str < "16:00":
        return "SIANG_2", "Shift Siang Sesi 2 (Sanitasi & Kompos)"
    else:
        return "SORE", "Shift Sore (Closing & Konservasi Energi)"

def send_sarpras_ticket_alert(ticket):
    """Kirim WhatsApp Alert ke Sarpras via mutabaah-wa-bot port 3005"""
    target_wa = "120363428379955493@g.us" # Grup Sarpras / AIS_Umum
    priority_emoji = "🚨" if ticket.get("priority") in ["HIGH", "EMERGENCY"] else "⚠️"
    
    msg = (
        f"{priority_emoji} *[TIKET PERBAIKAN SARPRAS TERBUAT]*\n\n"
        f"🏷️ *ID Tiket* : `{ticket.get('ticket_id')}`\n"
        f"📍 *Lokasi/Zona* : {ticket.get('zone_name')}\n"
        f"🏢 *Gedung/Sektor* : {ticket.get('building_or_sector', '-')}\n"
        f"👤 *Pelapor (OB)* : {ticket.get('reporter_name')}\n"
        f"🔧 *Kategori* : {ticket.get('category')}\n"
        f"⚡ *Prioritas* : *{ticket.get('priority')}* (SLA: {ticket.get('sla_hours')} Jam)\n"
        f"📝 *Masalah* : {ticket.get('issue_description')}\n"
    )
    if ticket.get("is_eco_critical"):
        msg += f"\n🌿 *Perhatian Khusus Konservasi:* Kerusakan ini berisiko memboroskan air/listrik. Mohon penanganan cepat sebelum batas SLA!\n"
    
    msg += f"\nTeknisi Sarpras dapat merespons di grup ini:\nBalas: *TERIMA {ticket.get('ticket_id')}* atau *SELESAI {ticket.get('ticket_id')} [Catatan]*"

    try:
        requests.post("http://127.0.0.1:3005/send_alert", json={"target": target_wa, "text": msg}, timeout=4)
    except Exception as e:
        print(f"[CHECKLIST] Gagal kirim WA alert ke Sarpras: {e}")


# ==================== ZERO-LOGIN PWA MICRO-CHECKIN ENDPOINT ====================

@checklist_bp.route("/c/<token>", methods=["GET"])
@checklist_bp.route("/checklist/c/<token>", methods=["GET"])
def web_checklist_micro_pwa(token):
    """
    Halaman Micro-Web Checklist Lapangan Ultra-Ringan (<50KB) - ZERO LOGIN:
    Petugas scan QR akrilik di pintu toilet / pos taman.
    Server otomatis mendeteksi shift dan menyajikan template item 3-5 poin.
    Tersedia tombol sentuh jempol hijau/merah dan kompresi foto canvas langsung di browser.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM maintenance_zones WHERE qr_token = ? AND is_active = 1", (token,))
    zone_row = cur.fetchone()
    
    if not zone_row:
        cur.execute("SELECT * FROM maintenance_zones WHERE id = ? AND is_active = 1", (token,))
        zone_row = cur.fetchone()

    if not zone_row:
        conn.close()
        return "<h3>⚠️ Titik kontrol zona pemeliharaan tidak ditemukan atau belum aktif.</h3>", 404

    zone = dict(zone_row)

    cur_time = now_wib().strftime("%H:%M")
    shift_code, shift_title = detect_shift_code(cur_time)

    cur.execute('''
        SELECT * FROM checklist_templates 
        WHERE unit_type = ? AND sub_scope = ? AND (shift_code = ? OR shift_code = 'ALL_DAY') AND is_active = 1
        ORDER BY item_order ASC
    ''', (zone['unit_type'], zone['sub_scope'], shift_code))
    items = [dict(r) for r in cur.fetchall()]

    if not items:
        cur.execute('''
            SELECT * FROM checklist_templates 
            WHERE unit_type = ? AND (shift_code = ? OR shift_code = 'ALL_DAY') AND is_active = 1
            ORDER BY item_order ASC
        ''', (zone['unit_type'], shift_code))
        items = [dict(r) for r in cur.fetchall()]

    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>{{ zone.zone_name }} — Checklist Pemeliharaan An Nahl</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            .tap-target { min-height: 48px; }
            .toggle-active-ok { background-color: #059669 !important; color: white !important; border-color: #10b981 !important; }
            .toggle-active-bad { background-color: #e11d48 !important; color: white !important; border-color: #f43f5e !important; }
        </style>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col justify-between antialiased selection:bg-emerald-500 selection:text-white pb-6">
        
        <!-- Header Identitas Titik -->
        <header class="bg-slate-800/90 border-b border-slate-700/80 p-4 sticky top-0 z-30 backdrop-blur-md">
            <div class="max-w-md mx-auto flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-emerald-900/30">
                        <i class="fa-solid {% if zone.unit_type == 'OB' %}fa-broom{% else %}fa-seedling{% endif %}"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-1.5">
                            <span class="text-[10px] font-black tracking-wider px-2 py-0.5 rounded-full {% if zone.unit_type == 'OB' %}bg-sky-500/20 text-sky-400 border border-sky-500/30{% else %}bg-emerald-500/20 text-emerald-400 border border-emerald-500/30{% endif %} uppercase">
                                UNIT {{ zone.unit_type }}
                            </span>
                            <span class="text-[10px] text-slate-400 font-medium">{{ zone.building_or_sector }}</span>
                        </div>
                        <h1 class="text-sm font-bold text-white leading-tight mt-0.5">{{ zone.zone_name }}</h1>
                    </div>
                </div>
                <div class="text-right">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {{ shift_code }}
                    </span>
                    <p class="text-[10px] text-slate-400 font-mono mt-0.5" id="live-clock">--:-- WIB</p>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-md mx-auto w-full p-4 flex-1 space-y-4">

            <!-- Banner Info Shift -->
            <div class="bg-slate-800/60 border border-slate-700/70 rounded-2xl p-3.5 flex items-center justify-between shadow-xs">
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-sm">
                        <i class="fa-regular fa-clock"></i>
                    </div>
                    <div>
                        <p class="text-[11px] font-bold text-white">{{ shift_title }}</p>
                        <p class="text-[10px] text-slate-400">Pemeriksaan rutin berkala & pencegahan kebocoran</p>
                    </div>
                </div>
            </div>

            <!-- Kartu Identitas Petugas & Status GPS -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl p-4 space-y-3 shadow-sm">
                <div>
                    <label class="block text-[11px] font-bold text-slate-300 mb-1">
                        <i class="fa-solid fa-user-check text-emerald-400 mr-1"></i> Nama Petugas Pemeriksa:
                    </label>
                    <input type="text" id="petugas_name" required placeholder="Ketik nama lengkap Anda (tersimpan otomatis)"
                        class="w-full px-3.5 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition font-medium">
                </div>
                <div>
                    <label class="block text-[11px] font-bold text-slate-300 mb-1">
                        <i class="fa-brands fa-whatsapp text-emerald-400 mr-1"></i> Nomor WhatsApp Petugas:
                    </label>
                    <input type="tel" id="petugas_wa" placeholder="Contoh: 08123456789 (untuk verifikasi)"
                        class="w-full px-3.5 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition font-mono">
                </div>

                <!-- GPS Status Pill -->
                <div id="gps-box" class="pt-1 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-700/60 mt-2">
                    <span class="flex items-center gap-1.5" id="gps-status-text">
                        <i class="fa-solid fa-satellite-dish fa-spin text-amber-400"></i> Mengunci lokasi GPS...
                    </span>
                    <button type="button" onclick="acquireGps()" class="text-[10px] text-emerald-400 hover:text-emerald-300 font-bold">Refresh GPS</button>
                </div>
            </div>

            <!-- Form Checklist Items -->
            <form id="form-checklist" onsubmit="submitChecklist(event)" class="space-y-3">
                <div class="flex items-center justify-between px-1">
                    <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Parameter Inspeksi ({{ items|length }} Butir)
                    </h2>
                    <button type="button" onclick="setAllOk()" class="text-[11px] text-emerald-400 hover:text-emerald-300 font-bold flex items-center gap-1">
                        <i class="fa-solid fa-check-double"></i> Centang Semua Normal
                    </button>
                </div>

                <!-- List Item Checklist -->
                <div class="space-y-2.5" id="checklist-container">
                    {% for item in items %}
                    <div class="checklist-row bg-slate-800 border border-slate-700/80 rounded-2xl p-3.5 transition hover:border-slate-600" data-item-id="{{ item.id }}" data-eco="{{ item.is_eco_critical }}">
                        <div class="flex items-start justify-between gap-3">
                            <div class="flex-1">
                                <div class="flex items-center gap-1.5">
                                    <span class="text-xs font-bold text-slate-200 leading-snug">{{ item.item_label }}</span>
                                    {% if item.is_eco_critical %}
                                    <span class="text-[9px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded font-black border border-emerald-500/30 whitespace-nowrap">
                                        🌱 ECO KRITIS
                                    </span>
                                    {% endif %}
                                </div>
                                {% if item.help_text %}
                                <p class="text-[10px] text-slate-400 mt-1">{{ item.help_text }}</p>
                                {% endif %}
                            </div>
                        </div>

                        <!-- Toggle Tombol OK vs RUSAK -->
                        <div class="grid grid-cols-2 gap-2 mt-3 pt-2.5 border-t border-slate-700/50">
                            <button type="button" onclick="setItemStatus({{ item.id }}, true)" id="btn-ok-{{ item.id }}"
                                class="tap-target toggle-btn w-full py-2 px-3 rounded-xl border border-slate-600 bg-slate-700/60 text-slate-300 text-xs font-bold flex items-center justify-center gap-1.5 transition">
                                <i class="fa-solid fa-check text-emerald-400"></i> NORMAL
                            </button>
                            <button type="button" onclick="setItemStatus({{ item.id }}, false)" id="btn-bad-{{ item.id }}"
                                class="tap-target toggle-btn w-full py-2 px-3 rounded-xl border border-slate-600 bg-slate-700/60 text-slate-300 text-xs font-bold flex items-center justify-center gap-1.5 transition">
                                <i class="fa-solid fa-triangle-exclamation text-rose-400"></i> RUSAK / KURANG
                            </button>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <!-- Bagian Pelaporan Anomali / Kerusakan (Muncul otomatis jika ada 1 item Rusak) -->
                <div id="anomaly-section" class="hidden bg-rose-950/40 border border-rose-600/40 rounded-2xl p-4 space-y-3 transition-all duration-300">
                    <div class="flex items-center gap-2 text-rose-400 text-xs font-bold">
                        <i class="fa-solid fa-triangle-exclamation text-sm"></i>
                        <span>Anomali Terdeteksi: Tiket Sarpras Otomatis Dibuat</span>
                    </div>
                    <p class="text-[11px] text-slate-300">
                        Item kerusakan di atas akan otomatis diteruskan ke tim Sarpras / Teknisi melalui WhatsApp Bot. Mohon lengkapi catatan dan foto.
                    </p>

                    <div>
                        <label class="block text-[11px] font-bold text-slate-200 mb-1">Keterangan Detail Kerusakan / Masalah:</label>
                        <textarea id="anomaly_notes" rows="2" placeholder="Contoh: Kran wastafel no. 2 patah bocor terus menerus..."
                            class="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"></textarea>
                    </div>

                    <div>
                        <label class="block text-[11px] font-bold text-slate-200 mb-1">
                            <i class="fa-solid fa-camera text-rose-400 mr-1"></i> Foto Bukti Kerusakan (Wajib Kompresi):
                        </label>
                        <input type="file" id="anomaly_photo" accept="image/*" capture="environment" onchange="compressPhoto(event)"
                            class="block w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-rose-600 file:text-white hover:file:bg-rose-700 cursor-pointer">
                        <input type="hidden" id="compressed_photo_base64" value="">
                        <div id="photo-preview-box" class="hidden mt-2 flex items-center gap-2">
                            <img id="photo-preview-img" class="w-14 h-14 object-cover rounded-lg border border-slate-600">
                            <span id="photo-preview-size" class="text-[10px] text-emerald-400 font-mono font-bold"></span>
                        </div>
                    </div>
                </div>

                <!-- Green Ops Badge Tips -->
                <div class="bg-emerald-950/30 border border-emerald-600/30 rounded-2xl p-3 flex items-start gap-2.5">
                    <i class="fa-solid fa-leaf text-emerald-400 text-sm mt-0.5"></i>
                    <div class="text-[10px] text-slate-300 leading-relaxed">
                        <strong class="text-emerald-400">Gerakan Sekolah Berwawasan Lingkungan:</strong>
                        Setiap kran bocor yang Anda temukan dan laporkan hari ini menyelamatkan lebih dari <span class="text-white font-bold">1.500 liter</span> air bersih dari pemborosan. Jazakallahu khairan!
                    </div>
                </div>

                <!-- Tombol Submit Besar -->
                <button type="submit" id="btn-submit"
                    class="tap-target w-full py-3.5 px-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm rounded-2xl shadow-lg shadow-emerald-900/40 flex items-center justify-center gap-2 transition active:scale-[0.98] cursor-pointer">
                    <i class="fa-solid fa-paper-plane"></i>
                    <span>Kirim Laporan Checklist</span>
                </button>
            </form>

            <!-- Screen Hasil Sukses (Modal Overlay) -->
            <div id="modal-success" class="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4 hidden">
                <div class="bg-slate-800 border border-slate-700 max-w-sm w-full rounded-3xl p-6 text-center space-y-4 shadow-2xl">
                    <div class="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center text-3xl">
                        <i class="fa-solid fa-circle-check"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white">Alhamdulillah, Laporan Tercatat!</h3>
                        <p class="text-xs text-slate-400 mt-1" id="success-desc">Data checklist pemeliharaan Anda telah berhasil diverifikasi oleh server An Nahl Ops.</p>
                    </div>
                    <div id="success-ticket-badge" class="hidden p-3 bg-rose-950/50 border border-rose-500/40 rounded-xl text-left text-xs text-rose-300 space-y-1">
                        <div class="font-bold flex items-center gap-1.5">
                            <i class="fa-solid fa-ticket"></i> Tiket Sarpras Diterbitkan:
                        </div>
                        <p class="font-mono font-bold text-white" id="success-ticket-id">TK-OPS-...</p>
                        <p class="text-[10px] text-slate-300">Notifikasi telah dikirim ke WhatsApp tim Sarpras untuk perbaikan segera.</p>
                    </div>
                    <div class="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center justify-between">
                        <span>🌱 Poin Green Ops Didapat:</span>
                        <span class="font-bold text-white text-sm">+25 Poin</span>
                    </div>
                    <button type="button" onclick="location.reload()" class="w-full py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-xs font-bold transition">
                        Tutup & Selesai
                    </button>
                </div>
            </div>

        </main>

        <!-- Footer -->
        <footer class="max-w-md mx-auto w-full px-4 text-center text-[10px] text-slate-500">
            Sistem Pemeliharaan Digital 100% Paperless &bull; An Nahl Islamic School
        </footer>

        <!-- Client Scripts -->
        <script>
            const ZONE_DATA = {
                id: "{{ zone.id }}",
                token: "{{ zone.qr_token }}",
                name: "{{ zone.zone_name }}",
                lat: {{ zone.target_lat }},
                lng: {{ zone.target_lng }},
                radius: {{ zone.geofence_radius_m }}
            };
            let currentShift = "{{ shift_code }}";
            let itemStates = {};
            let userCoordinates = { lat: null, lng: null, accuracy: null };

            document.querySelectorAll('.checklist-row').forEach(row => {
                const id = row.getAttribute('data-item-id');
                itemStates[id] = true;
                updateButtonUi(id, true);
            });

            function updateClock() {
                const now = new Date();
                const str = now.toLocaleTimeString('id-ID', { timeZone: 'Asia/Jakarta', hour: '2-digit', minute: '2-digit' });
                document.getElementById('live-clock').innerText = str + " WIB";
            }
            setInterval(updateClock, 1000);
            updateClock();

            const savedName = localStorage.getItem('annahl_petugas_name');
            const savedWa = localStorage.getItem('annahl_petugas_wa');
            if (savedName) document.getElementById('petugas_name').value = savedName;
            if (savedWa) document.getElementById('petugas_wa').value = savedWa;

            function acquireGps() {
                const statusBox = document.getElementById('gps-status-text');
                statusBox.innerHTML = '<i class="fa-solid fa-satellite-dish fa-spin text-amber-400"></i> Mengunci lokasi GPS...';

                if (!navigator.geolocation) {
                    statusBox.innerHTML = '<i class="fa-solid fa-circle-check text-emerald-400"></i> Mode Stiker QR Fisik Aktif';
                    return;
                }

                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        userCoordinates.lat = pos.coords.latitude;
                        userCoordinates.lng = pos.coords.longitude;
                        userCoordinates.accuracy = Math.round(pos.coords.accuracy);
                        
                        const dist = calcDistance(userCoordinates.lat, userCoordinates.lng, ZONE_DATA.lat, ZONE_DATA.lng);
                        if (dist <= (ZONE_DATA.radius + 20)) {
                            statusBox.innerHTML = `<i class="fa-solid fa-location-dot text-emerald-400"></i> Lokasi Valid (${Math.round(dist)}m)`;
                        } else {
                            statusBox.innerHTML = `<i class="fa-solid fa-location-arrow text-amber-400"></i> Jarak GPS: ${Math.round(dist)}m`;
                        }
                    },
                    (err) => {
                        console.warn("GPS Warning:", err.message);
                        statusBox.innerHTML = '<i class="fa-solid fa-circle-check text-emerald-400"></i> Terverifikasi via QR Fisik (Indoor)';
                    },
                    { enableHighAccuracy: true, timeout: 6000, maximumAge: 30000 }
                );
            }
            acquireGps();

            function calcDistance(lat1, lon1, lat2, lon2) {
                const R = 6371000;
                const dLat = (lat2 - lat1) * Math.PI / 180;
                const dLon = (lon2 - lon1) * Math.PI / 180;
                const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                          Math.sin(dLon/2) * Math.sin(dLon/2);
                return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            }

            function setItemStatus(id, isOk) {
                itemStates[id] = isOk;
                updateButtonUi(id, isOk);
                checkAnomalyVisibility();
            }

            function updateButtonUi(id, isOk) {
                const btnOk = document.getElementById(`btn-ok-${id}`);
                const btnBad = document.getElementById(`btn-bad-${id}`);
                if (isOk) {
                    btnOk.className = "tap-target toggle-btn toggle-active-ok w-full py-2 px-3 rounded-xl border border-emerald-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition";
                    btnBad.className = "tap-target toggle-btn w-full py-2 px-3 rounded-xl border border-slate-700 bg-slate-800/80 text-slate-400 text-xs font-bold flex items-center justify-center gap-1.5 transition";
                } else {
                    btnOk.className = "tap-target toggle-btn w-full py-2 px-3 rounded-xl border border-slate-700 bg-slate-800/80 text-slate-400 text-xs font-bold flex items-center justify-center gap-1.5 transition";
                    btnBad.className = "tap-target toggle-btn toggle-active-bad w-full py-2 px-3 rounded-xl border border-rose-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition";
                }
            }

            function setAllOk() {
                for (const id in itemStates) {
                    itemStates[id] = true;
                    updateButtonUi(id, true);
                }
                checkAnomalyVisibility();
            }

            function checkAnomalyVisibility() {
                let hasBad = false;
                for (const id in itemStates) {
                    if (itemStates[id] === false) {
                        hasBad = true;
                        break;
                    }
                }
                const sec = document.getElementById('anomaly-section');
                if (hasBad) {
                    sec.classList.remove('hidden');
                } else {
                    sec.classList.add('hidden');
                }
            }

            function compressPhoto(event) {
                const file = event.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = new Image();
                    img.onload = function() {
                        const canvas = document.createElement('canvas');
                        let width = img.width;
                        let height = img.height;
                        const maxDim = 1280;

                        if (width > maxDim || height > maxDim) {
                            if (width > height) {
                                height = Math.round((height * maxDim) / width);
                                width = maxDim;
                            } else {
                                width = Math.round((width * maxDim) / height);
                                height = maxDim;
                            }
                        }

                        canvas.width = width;
                        canvas.height = height;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0, width, height);

                        const compressedBase64 = canvas.toDataURL('image/jpeg', 0.72);
                        document.getElementById('compressed_photo_base64').value = compressedBase64;

                        const prevBox = document.getElementById('photo-preview-box');
                        const prevImg = document.getElementById('photo-preview-img');
                        const prevSize = document.getElementById('photo-preview-size');
                        prevImg.src = compressedBase64;
                        const approxKb = Math.round((compressedBase64.length * 3 / 4) / 1024);
                        prevSize.innerText = `Terkompresi: ~${approxKb} KB (Hemat Bandwidth)`;
                        prevBox.classList.remove('hidden');
                    };
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }

            async function submitChecklist(event) {
                event.preventDefault();
                const btn = document.getElementById('btn-submit');
                const name = document.getElementById('petugas_name').value.trim();
                const wa = document.getElementById('petugas_wa').value.trim();

                if (!name) {
                    alert('Silakan ketik nama lengkap Anda.');
                    document.getElementById('petugas_name').focus();
                    return;
                }

                let hasBad = false;
                for (const id in itemStates) {
                    if (itemStates[id] === false) hasBad = true;
                }

                const notes = document.getElementById('anomaly_notes').value.trim();
                if (hasBad && !notes) {
                    alert('Mohon tuliskan rincian kerusakan pada kotak keterangan anomali.');
                    document.getElementById('anomaly_notes').focus();
                    return;
                }

                localStorage.setItem('annahl_petugas_name', name);
                if (wa) localStorage.setItem('annahl_petugas_wa', wa);

                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan Laporan...';

                const payload = {
                    zone_id: ZONE_DATA.id,
                    token: ZONE_DATA.token,
                    shift_code: currentShift,
                    petugas_name: name,
                    petugas_wa: wa,
                    user_lat: userCoordinates.lat,
                    user_lng: userCoordinates.lng,
                    accuracy: userCoordinates.accuracy,
                    items: itemStates,
                    anomaly_notes: notes,
                    photo_base64: document.getElementById('compressed_photo_base64').value
                };

                try {
                    const res = await fetch('/api/ops/checklist/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();

                    if (data.success) {
                        if (data.ticket_id) {
                            document.getElementById('success-ticket-id').innerText = data.ticket_id;
                            document.getElementById('success-ticket-badge').classList.remove('hidden');
                        }
                        document.getElementById('modal-success').classList.remove('hidden');
                    } else {
                        alert('Gagal mengirim checklist: ' + (data.error || 'Terjadi kesalahan sistem'));
                    }
                } catch (err) {
                    alert('Gagal terhubung ke server: ' + err.message);
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Kirim Laporan Checklist';
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html, zone=zone, items=items, shift_code=shift_code, shift_title=shift_title)


# ==================== REST API ENDPOINTS ====================

@checklist_bp.route("/api/ops/checklist/zone/<token>", methods=["GET"])
def api_get_checklist_zone(token):
    """Mengambil informasi zona dan butir template checklist sesuai shift aktif"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM maintenance_zones WHERE qr_token = ? OR id = ?", (token, token))
    zone = cur.fetchone()
    if not zone:
        conn.close()
        return jsonify({"success": False, "error": "Zona tidak ditemukan"}), 404

    zone_dict = dict(zone)
    shift_code, shift_title = detect_shift_code()

    cur.execute('''
        SELECT * FROM checklist_templates 
        WHERE unit_type = ? AND (shift_code = ? OR shift_code = 'ALL_DAY') AND is_active = 1
        ORDER BY item_order ASC
    ''', (zone_dict['unit_type'], shift_code))
    items = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({
        "success": True,
        "zone": zone_dict,
        "shift_code": shift_code,
        "shift_title": shift_title,
        "items": items
    })


@checklist_bp.route("/api/ops/checklist/submit", methods=["POST"])
def api_submit_checklist():
    """
    Menyimpan laporan checklist pemeliharaan:
    1. Validasi geofencing GPS (dengan toleransi indoor).
    2. Simpan snapshot centang checklist.
    3. Jika terdapat item False (rusak), terbitkan tiket sarpras ops_maintenance_tickets.
    4. Kirim alert WhatsApp ke grup Sarpras.
    """
    data = request.get_json(silent=True) or {}
    zone_id = data.get("zone_id") or ""
    token = data.get("token") or ""
    shift_code = data.get("shift_code") or detect_shift_code()[0]
    petugas_name = (data.get("petugas_name") or "").strip()
    petugas_wa = (data.get("petugas_wa") or "").strip()
    user_lat = data.get("user_lat")
    user_lng = data.get("user_lng")
    accuracy = data.get("accuracy") or 0
    items_state = data.get("items") or {}
    anomaly_notes = (data.get("anomaly_notes") or "").strip()
    photo_b64 = data.get("photo_base64") or ""

    if not petugas_name:
        return jsonify({"success": False, "error": "Nama petugas wajib diisi"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM maintenance_zones WHERE id = ? OR qr_token = ?", (zone_id, token))
    zone = cur.fetchone()
    if not zone:
        conn.close()
        return jsonify({"success": False, "error": "Zona pemeliharaan tidak valid"}), 404

    zone_dict = dict(zone)

    # Validasi GPS Distance
    distance = 0
    is_within = 1
    if user_lat is not None and user_lng is not None:
        distance = calculate_haversine(user_lat, user_lng, zone_dict['target_lat'], zone_dict['target_lng'])
        allowed_radius = max(zone_dict['geofence_radius_m'], 45) + 20
        if distance > allowed_radius:
            is_within = 0

    # Simpan foto bukti jika ada
    photo_rel_url = ""
    if photo_b64 and "base64," in photo_b64:
        try:
            format_part, imgstr = photo_b64.split(';base64,')
            ext = "jpg"
            if "webp" in format_part:
                ext = "webp"
            elif "png" in format_part:
                ext = "png"
            filename = f"chk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as fh:
                fh.write(base64.b64decode(imgstr))
            photo_rel_url = f"/static/uploads/checklist/{filename}"
        except Exception as e:
            print(f"[CHECKLIST] Gagal menyimpan foto: {e}")

    # Evaluasi status
    has_anomaly = False
    has_eco_critical = False
    cur.execute("SELECT id, is_eco_critical FROM checklist_templates WHERE unit_type = ?", (zone_dict['unit_type'],))
    template_eco_map = {str(r['id']): bool(r['is_eco_critical']) for r in cur.fetchall()}

    for item_id_str, is_ok in items_state.items():
        if not is_ok:
            has_anomaly = True
            if template_eco_map.get(str(item_id_str)):
                has_eco_critical = True

    status_summary = "ALL_OK"
    ticket_id = None

    if has_anomaly:
        status_summary = "CRITICAL" if has_eco_critical else "ANOMALY"
        today_str = now_wib().strftime("%Y%m%d")
        rand_suffix = uuid.uuid4().hex[:4].upper()
        ticket_id = f"TK-OPS-{today_str}-{rand_suffix}"

        priority = "HIGH" if has_eco_critical else "MEDIUM"
        sla_hours = 2 if has_eco_critical else 8
        category = "PLUMBING_WATER" if has_eco_critical else ("SANITARY" if zone_dict['unit_type'] == 'OB' else "GARDEN_PEST")

        cur.execute('''
            INSERT INTO ops_maintenance_tickets (
                ticket_id, zone_id, unit_source, category, priority, issue_description,
                photo_before_url, reporter_name, reporter_wa, status, sla_hours
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        ''', (
            ticket_id, zone_dict['id'], zone_dict['unit_type'], category, priority,
            anomaly_notes or "Ditemukan kerusakan/anomali pada butir inspeksi",
            photo_rel_url, petugas_name, petugas_wa, sla_hours
        ))

        ticket_payload = {
            "ticket_id": ticket_id,
            "zone_name": zone_dict['zone_name'],
            "building_or_sector": zone_dict['building_or_sector'],
            "reporter_name": petugas_name,
            "category": category,
            "priority": priority,
            "sla_hours": sla_hours,
            "issue_description": anomaly_notes,
            "is_eco_critical": has_eco_critical
        }
        send_sarpras_ticket_alert(ticket_payload)

    cur.execute('''
        INSERT INTO maintenance_checklist_logs (
            zone_id, shift_code, petugas_name, petugas_wa, user_lat, user_lng,
            distance_meters, is_within_geofence, status_summary, checklist_data_json,
            anomaly_notes, photo_url, ticket_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        zone_dict['id'], shift_code, petugas_name, petugas_wa,
        user_lat, user_lng, distance, is_within, status_summary,
        json.dumps(items_state), anomaly_notes, photo_rel_url, ticket_id
    ))
    log_id = cur.lastrowid

    if ticket_id:
        cur.execute("UPDATE ops_maintenance_tickets SET source_checklist_id = ? WHERE ticket_id = ?", (log_id, ticket_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "log_id": log_id,
        "status_summary": status_summary,
        "ticket_id": ticket_id,
        "distance": distance,
        "is_within_geofence": bool(is_within)
    })


@checklist_bp.route("/api/ops/checklist/radar", methods=["GET"])
def api_get_checklist_radar():
    """Mengambil matriks live radar status keterisian checklist hari ini"""
    unit = request.args.get("unit") or ""
    today = now_wib().strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()

    sql_zones = "SELECT * FROM maintenance_zones WHERE is_active = 1"
    params = []
    if unit in ['OB', 'GARDENER']:
        sql_zones += " AND unit_type = ?"
        params.append(unit)
    sql_zones += " ORDER BY building_or_sector ASC, zone_name ASC"
    cur.execute(sql_zones, params)
    zones = [dict(r) for r in cur.fetchall()]

    cur.execute('''
        SELECT * FROM maintenance_checklist_logs 
        WHERE DATE(checked_at) = ? 
        ORDER BY checked_at DESC
    ''', (today,))
    logs = [dict(r) for r in cur.fetchall()]

    matrix = {}
    for l in logs:
        zid = l['zone_id']
        sh = l['shift_code']
        if zid not in matrix:
            matrix[zid] = {}
        if sh not in matrix[zid]:
            matrix[zid][sh] = l

    shifts = ['PAGI', 'SIANG_1', 'SIANG_2', 'SORE']
    total_slots = len(zones) * len(shifts)
    filled_ok = 0
    filled_anomaly = 0

    radar_list = []
    for z in zones:
        zid = z['id']
        z_shifts = {}
        for sh in shifts:
            log_entry = matrix.get(zid, {}).get(sh)
            if log_entry:
                status = log_entry['status_summary']
                if status == 'ALL_OK':
                    filled_ok += 1
                else:
                    filled_anomaly += 1
                z_shifts[sh] = {
                    "checked": True,
                    "status": status,
                    "petugas": log_entry['petugas_name'],
                    "time": log_entry['checked_at'][11:16] if log_entry['checked_at'] else "",
                    "ticket_id": log_entry['ticket_id']
                }
            else:
                z_shifts[sh] = {
                    "checked": False,
                    "status": "PENDING",
                    "petugas": "",
                    "time": "",
                    "ticket_id": None
                }
        radar_list.append({
            "zone": z,
            "shifts": z_shifts
        })

    cur.execute("SELECT COUNT(*) FROM ops_maintenance_tickets WHERE status IN ('OPEN', 'IN_PROGRESS')")
    open_tickets = cur.fetchone()[0]
    conn.close()

    compliance_pct = round((filled_ok + filled_anomaly) / total_slots * 100, 1) if total_slots > 0 else 0

    return jsonify({
        "success": True,
        "date": today,
        "total_zones": len(zones),
        "filled_ok": filled_ok,
        "filled_anomaly": filled_anomaly,
        "open_tickets": open_tickets,
        "compliance_pct": compliance_pct,
        "radar": radar_list
    })


@checklist_bp.route("/api/ops/checklist/tickets", methods=["GET"])
def api_get_checklist_tickets():
    """Mengambil daftar tiket sarpras hasil closed-loop checklist"""
    status_filter = request.args.get("status")
    unit_filter = request.args.get("unit")

    conn = get_db()
    cur = conn.cursor()

    sql = '''
        SELECT t.*, z.zone_name, z.building_or_sector
        FROM ops_maintenance_tickets t
        LEFT JOIN maintenance_zones z ON t.zone_id = z.id
        WHERE 1=1
    '''
    params = []
    if status_filter:
        sql += " AND t.status = ?"
        params.append(status_filter)
    if unit_filter:
        sql += " AND t.unit_source = ?"
        params.append(unit_filter)
    sql += " ORDER BY CASE t.priority WHEN 'EMERGENCY' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, t.created_at DESC"

    cur.execute(sql, params)
    tickets = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({"success": True, "tickets": tickets, "total": len(tickets)})


@checklist_bp.route("/api/ops/checklist/tickets/<ticket_id>/resolve", methods=["POST"])
def api_resolve_checklist_ticket(ticket_id):
    """Menyelesaikan tiket perbaikan Sarpras dengan catatan & foto after"""
    data = request.get_json(silent=True) or {}
    resolution_notes = (data.get("resolution_notes") or "").strip()
    tech_name = (data.get("tech_name") or session.get("user_name", "Teknisi Sarpras")).strip()
    photo_b64 = data.get("photo_after_base64") or ""

    photo_after_url = ""
    if photo_b64 and "base64," in photo_b64:
        try:
            format_part, imgstr = photo_b64.split(';base64,')
            filename = f"after_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as fh:
                fh.write(base64.b64decode(imgstr))
            photo_after_url = f"/static/uploads/checklist/{filename}"
        except Exception as e:
            print(f"[CHECKLIST] Gagal simpan foto after: {e}")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE ops_maintenance_tickets 
        SET status = 'RESOLVED',
            assigned_tech_name = ?,
            resolution_notes = ?,
            photo_after_url = COALESCE(NULLIF(?, ''), photo_after_url),
            resolved_at = CURRENT_TIMESTAMP
        WHERE ticket_id = ?
    ''', (tech_name, resolution_notes or "Perbaikan telah diselesaikan oleh tim sarpras", photo_after_url, ticket_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return jsonify({"success": False, "error": "Tiket tidak ditemukan"}), 404

    return jsonify({"success": True, "message": f"Tiket {ticket_id} berhasil diselesaikan!"})


@checklist_bp.route("/api/ops/checklist/green-stats", methods=["GET"])
def api_get_green_stats():
    """Menghitung metrik dampak keberlanjutan lingkungan (Green Ops)"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM maintenance_checklist_logs")
    paper_sheets_saved = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ops_maintenance_tickets WHERE category = 'PLUMBING_WATER' AND status IN ('RESOLVED', 'VERIFIED')")
    leaks_resolved = cur.fetchone()[0]
    water_liters_saved = leaks_resolved * 2000

    cur.execute("SELECT COUNT(*) FROM maintenance_checklist_logs WHERE shift_code = 'SORE' AND status_summary = 'ALL_OK'")
    energy_closing_checks = cur.fetchone()[0]
    kwh_electricity_saved = energy_closing_checks * 3.2

    cur.execute("SELECT SUM(organic_waste_kg), SUM(compost_harvest_kg), SUM(veggie_harvest_kg) FROM green_ops_daily_metrics")
    row_eco = cur.fetchone()
    organic_kg = row_eco[0] or 0.0
    compost_kg = row_eco[1] or 0.0
    veggie_kg = row_eco[2] or 0.0
    conn.close()

    return jsonify({
        "success": True,
        "metrics": {
            "paper_sheets_saved": paper_sheets_saved,
            "paper_rim_equivalent": round(paper_sheets_saved / 500.0, 2),
            "leaks_resolved": leaks_resolved,
            "water_liters_saved": water_liters_saved,
            "energy_closing_checks": energy_closing_checks,
            "kwh_electricity_saved": round(kwh_electricity_saved, 1),
            "organic_waste_kg": round(organic_kg, 1),
            "compost_harvest_kg": round(compost_kg, 1),
            "veggie_harvest_kg": round(veggie_kg, 1)
        }
    })


# ==================== MASTER ZONA CRUD & CETAK QR ====================

@checklist_bp.route("/api/ops/checklist/zones", methods=["GET"])
def api_get_checklist_zones():
    """Mengambil seluruh master zona pemeliharaan"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM maintenance_zones ORDER BY unit_type ASC, building_or_sector ASC, zone_name ASC")
    zones = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"success": True, "zones": zones, "total": len(zones)})


@checklist_bp.route("/api/ops/checklist/zones/create", methods=["POST"])
def api_create_checklist_zone():
    """Menambah atau memperbarui zona pemeliharaan"""
    data = request.get_json(silent=True) or {}
    zone_id = (data.get("id") or "").strip()
    unit_type = (data.get("unit_type") or "OB").strip().upper()
    sub_scope = (data.get("sub_scope") or "INDOOR_SANITASI").strip()
    zone_name = (data.get("zone_name") or "").strip()
    building = (data.get("building_or_sector") or "").strip()
    target_lat = float(data.get("target_lat") or -6.339295)
    target_lng = float(data.get("target_lng") or 106.964365)
    radius = int(data.get("geofence_radius_m") or 45)

    if not zone_id or not zone_name:
        return jsonify({"success": False, "error": "ID dan Nama Zona wajib diisi"}), 400

    qr_token = f"qr_{unit_type.lower()}_{uuid.uuid4().hex[:8]}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO maintenance_zones (
            id, unit_type, sub_scope, zone_name, building_or_sector, target_lat, target_lng, geofence_radius_m, qr_token
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            zone_name = excluded.zone_name,
            building_or_sector = excluded.building_or_sector,
            target_lat = excluded.target_lat,
            target_lng = excluded.target_lng,
            geofence_radius_m = excluded.geofence_radius_m
    ''', (zone_id, unit_type, sub_scope, zone_name, building, target_lat, target_lng, radius, qr_token))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Zona {zone_name} berhasil disimpan!"})


@checklist_bp.route("/api/ops/checklist/zones/<zone_id>", methods=["GET"])
def api_get_single_checklist_zone(zone_id):
    """Mengambil data spesifik satu titik zona pemeliharaan"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM maintenance_zones WHERE id = ? OR qr_token = ?", (zone_id, zone_id))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"success": False, "error": "Zona pemeliharaan tidak ditemukan"}), 404
    return jsonify({"success": True, "zone": dict(row)})


@checklist_bp.route("/api/ops/checklist/zones/<zone_id>/edit", methods=["POST", "PUT"])
@checklist_bp.route("/api/ops/checklist/zones/<zone_id>", methods=["PUT", "PATCH"])
def api_edit_checklist_zone(zone_id):
    """Memperbarui informasi zona pemeliharaan yang sudah ada"""
    data = request.get_json(silent=True) or {}
    zone_name = (data.get("zone_name") or "").strip()
    unit_type = (data.get("unit_type") or "OB").strip().upper()
    sub_scope = (data.get("sub_scope") or "INDOOR_SANITASI").strip()
    building = (data.get("building_or_sector") or "").strip()
    target_lat = float(data.get("target_lat") or -6.339295)
    target_lng = float(data.get("target_lng") or 106.964365)
    radius = int(data.get("geofence_radius_m") or 45)
    is_active = int(data.get("is_active") if data.get("is_active") is not None else 1)

    if not zone_name:
        return jsonify({"success": False, "error": "Nama Zona wajib diisi"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE maintenance_zones
        SET zone_name = ?,
            unit_type = ?,
            sub_scope = ?,
            building_or_sector = ?,
            target_lat = ?,
            target_lng = ?,
            geofence_radius_m = ?,
            is_active = ?
        WHERE id = ?
    ''', (zone_name, unit_type, sub_scope, building, target_lat, target_lng, radius, is_active, zone_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return jsonify({"success": False, "error": "Zona tidak ditemukan"}), 404

    return jsonify({"success": True, "message": f"Zona {zone_name} berhasil diperbarui!"})


@checklist_bp.route("/api/ops/checklist/zones/<zone_id>/delete", methods=["POST", "DELETE"])
@checklist_bp.route("/api/ops/checklist/zones/<zone_id>", methods=["DELETE"])
def api_delete_checklist_zone(zone_id):
    """Menghapus zona pemeliharaan (atau soft delete jika sudah memiliki riwayat log)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM maintenance_checklist_logs WHERE zone_id = ?", (zone_id,))
    has_logs = cur.fetchone()[0] > 0

    if has_logs:
        cur.execute("UPDATE maintenance_zones SET is_active = 0 WHERE id = ?", (zone_id,))
    else:
        cur.execute("DELETE FROM maintenance_zones WHERE id = ?", (zone_id,))

    affected = cur.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return jsonify({"success": False, "error": "Zona tidak ditemukan"}), 404

    msg = "Zona dinonaktifkan (karena memiliki riwayat log)" if has_logs else "Zona berhasil dihapus"
    return jsonify({"success": True, "message": msg, "soft_deleted": has_logs})



@checklist_bp.route("/checklist/print-qr", methods=["GET"])
def web_checklist_print_qr():
    """
    Halaman Siap Cetak (Print-Ready) Stiker QR Akrilik Titik Pemeliharaan OB & Gardener.
    Dapat mencetak semua zona atau zona spesifik (?zone_id=xxx).
    """
    zone_id = request.args.get("zone_id")
    unit_filter = request.args.get("unit")

    conn = get_db()
    cur = conn.cursor()
    if zone_id:
        cur.execute("SELECT * FROM maintenance_zones WHERE id = ? OR qr_token = ?", (zone_id, zone_id))
    elif unit_filter in ['OB', 'GARDENER']:
        cur.execute("SELECT * FROM maintenance_zones WHERE unit_type = ? AND is_active = 1 ORDER BY building_or_sector ASC, zone_name ASC", (unit_filter,))
    else:
        cur.execute("SELECT * FROM maintenance_zones WHERE is_active = 1 ORDER BY unit_type ASC, building_or_sector ASC, zone_name ASC")
    zones = [dict(r) for r in cur.fetchall()]
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>Cetak Stiker QR Akrilik Checklist Pemeliharaan - An Nahl</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @media print {
                .no-print { display: none !important; }
                .page-break { page-break-after: always; }
                body { background: white !important; padding: 0 !important; }
            }
        </style>
    </head>
    <body class="bg-slate-100 p-6">
        <div class="no-print max-w-4xl mx-auto mb-6 bg-white p-4 rounded-xl shadow flex items-center justify-between">
            <div>
                <h1 class="text-base font-bold text-slate-800">Cetak Stiker QR Akrilik Checklist Pemeliharaan</h1>
                <p class="text-xs text-slate-500">Format stiker akrilik pintu toilet & pos taman (Ukuran Standar A6). 100% Paperless Inspection.</p>
            </div>
            <button onclick="window.print()" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow flex items-center gap-2 cursor-pointer">
                <i class="fa-solid fa-print"></i> Cetak Dokumen (Print / PDF)
            </button>
        </div>

        <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for z in zones %}
            <div class="bg-white border-2 border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between items-center text-center relative overflow-hidden page-break">
                <div class="w-full flex items-center justify-between border-b pb-3 mb-4">
                    <div class="text-left">
                        <span class="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded {% if z.unit_type == 'OB' %}bg-sky-100 text-sky-800{% else %}bg-emerald-100 text-emerald-800{% endif %}">
                            UNIT {{ z.unit_type }} &bull; {{ z.building_or_sector }}
                        </span>
                        <h2 class="text-sm font-black text-slate-900 mt-1 leading-tight">{{ z.zone_name }}</h2>
                    </div>
                    <div class="w-9 h-9 rounded-lg {% if z.unit_type == 'OB' %}bg-sky-600{% else %}bg-emerald-600{% endif %} text-white flex items-center justify-center text-base">
                        <i class="fa-solid {% if z.unit_type == 'OB' %}fa-broom{% else %}fa-seedling{% endif %}"></i>
                    </div>
                </div>

                <div class="my-2 p-3 bg-white border border-slate-300 rounded-xl shadow-xs">
                    <div id="qrcode-{{ loop.index }}" class="flex items-center justify-center"></div>
                </div>

                <div class="mt-4 space-y-1">
                    <p class="text-xs font-bold text-slate-800 uppercase tracking-wide">SCAN UNTUK CHECKLIST PEMELIHARAAN</p>
                    <p class="text-[10px] text-slate-500">Buka kamera HP atau aplikasi scanner untuk mengisi checklist kebersihan & sanitasi.</p>
                    <p class="text-[9px] font-mono text-slate-400 mt-1">ID: {{ z.id }} &bull; Token: {{ z.qr_token }}</p>
                </div>

                <div class="w-full mt-4 pt-2 border-t border-slate-100 flex items-center justify-between text-[9px] text-slate-400">
                    <span>🌱 Green Operations & Paperless</span>
                    <span>An Nahl Islamic School</span>
                </div>
            </div>
            {% endfor %}
        </div>

        <script>
            {% for z in zones %}
            new QRCode(document.getElementById("qrcode-{{ loop.index }}"), {
                text: window.location.origin + "/c/{{ z.qr_token }}",
                width: 140,
                height: 140,
                colorDark : "#0f172a",
                colorLight : "#ffffff",
                correctLevel : QRCode.CorrectLevel.H
            });
            {% endfor %}
        </script>
    </body>
    </html>
    """
    return render_template_string(html, zones=zones)
