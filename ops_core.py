# -*- coding: utf-8 -*-
"""
ops_core.py - Core Operational Engine for An Nahl Ops
Handles Tasks delegation, Todos, Journals with Supervisor Feedback,
Closed-Loop Kebersihan conversion, and WhatsApp Coordinator Alerts.
"""

import os
import re
import json
import uuid
import sqlite3
import requests
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Blueprint, request, jsonify, session, render_template_string

WIB = ZoneInfo("Asia/Jakarta")

def now_wib():
    return datetime.now(WIB)

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"
JSON_DATA_PATH = os.path.expanduser("~/annahl_ops_data.json")

ops_core_bp = Blueprint('ops_core', __name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== DATABASE INITIALIZATION & MIGRATION ====================
def init_ops_core_db():
    conn = get_db()
    cur = conn.cursor()

    # 1. Tabel ops_tasks
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_tasks (
            id TEXT PRIMARY KEY,
            unit_code TEXT NOT NULL,
            sub_scope TEXT,
            category TEXT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Sedang',
            status TEXT DEFAULT 'Pending',
            assigned_to TEXT,
            assigned_name TEXT,
            due_date TEXT,
            progress_notes TEXT,
            source TEXT DEFAULT 'manual',
            source_ref TEXT,
            created_by TEXT,
            created_at TEXT,
            completed_at TEXT
        )
    ''')

    # 2. Tabel ops_todos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_todos (
            id TEXT PRIMARY KEY,
            unit_code TEXT DEFAULT 'ALL',
            title TEXT NOT NULL,
            category TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'Sedang',
            completed INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TEXT,
            completed_at TEXT
        )
    ''')

    # 3. Tabel ops_journals
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_journals (
            id TEXT PRIMARY KEY,
            unit_code TEXT DEFAULT 'ALL',
            author_username TEXT,
            author_nama TEXT,
            category TEXT,
            date TEXT,
            time TEXT,
            title TEXT NOT NULL,
            description TEXT,
            output TEXT,
            supervisor_feedback TEXT,
            supervisor_feedback_by TEXT,
            supervisor_feedback_at TEXT,
            created_at TEXT
        )
    ''')

    # 4. Tabel ops_procurements (Pengadaan & Logistik Suku Cadang/Barang)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_procurements (
            id TEXT PRIMARY KEY,
            ticket_ref TEXT,
            title TEXT NOT NULL,
            unit_code TEXT NOT NULL,
            category TEXT DEFAULT 'Material Sarpras',
            quantity TEXT,
            estimated_cost INTEGER DEFAULT 0,
            actual_cost INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Diajukan',
            urgency TEXT DEFAULT 'Sedang',
            vendor_info TEXT,
            receipt_no TEXT,
            notes TEXT,
            requested_by TEXT,
            requested_at TEXT,
            approver_note TEXT,
            approved_by TEXT,
            approved_at TEXT,
            purchased_at TEXT,
            received_at TEXT,
            completed_at TEXT
        )
    ''')

    # 5. Tabel ops_standby_points (Master Titik Lokasi Standby Geofencing Dinamis)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_standby_points (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            unit_code TEXT NOT NULL,
            sub_scope TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_meters INTEGER DEFAULT 35,
            morning_start TEXT DEFAULT '09:45',
            morning_cutoff TEXT DEFAULT '10:00',
            noon_start TEXT DEFAULT '12:45',
            noon_cutoff TEXT DEFAULT '13:00',
            nudge_minutes INTEGER DEFAULT 5,
            target_group_jid TEXT,
            target_personal_wa TEXT,
            qr_token TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 6. Tabel ops_standby_assignments (Penugasan Personel ke Titik Pos)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_standby_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            point_id TEXT NOT NULL,
            petugas_name TEXT NOT NULL,
            no_wa TEXT NOT NULL,
            unit_code TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (point_id) REFERENCES ops_standby_points(id) ON DELETE CASCADE
        )
    ''')

    # 7. Tabel ops_standby_logs (Riwayat Transaksi Check-in Geotagging)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_standby_logs (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            session_type TEXT NOT NULL,
            point_id TEXT,
            point_code TEXT,
            point_name TEXT,
            petugas_name TEXT NOT NULL,
            no_wa TEXT,
            unit_code TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            checkin_lat REAL NOT NULL,
            checkin_long REAL NOT NULL,
            distance_meters REAL NOT NULL,
            accuracy_meters REAL DEFAULT 0,
            radius_allowed INTEGER DEFAULT 35,
            status TEXT NOT NULL,
            minutes_diff INTEGER DEFAULT 0,
            channel TEXT NOT NULL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 8. Tabel ops_standby_cron_tracking (Pencegahan Notifikasi Ganda / Double Dispatch)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_standby_cron_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            session_type TEXT NOT NULL,
            action_type TEXT NOT NULL,
            point_id TEXT NOT NULL,
            target TEXT NOT NULL,
            dispatched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, session_type, action_type, point_id, target)
        )
    ''')
    conn.commit()

    # Seed master titik standby jika tabel masih kosong
    cur.execute("SELECT COUNT(*) FROM ops_standby_points")
    if cur.fetchone()[0] == 0:
        initial_points = [
            (
                'pos_sec_01', 'POS-SEC-01', 'Pos Jaga Gerbang Utama & Drop-off', 'SECURITY',
                'Gerbang Utama & Perimeter Kampus', -6.348100, 106.964500, 30,
                '09:45', '10:00', '12:45', '13:00', 5,
                '120363428379955493@g.us', '6285282212856', str(uuid.uuid4())[:12]
            ),
            (
                'pos_sec_02', 'POS-SEC-02', 'Pos Jaga Barat & Parkir Siswa', 'SECURITY',
                'Perimeter Barat & Parkir Kendaraan', -6.348400, 106.964200, 35,
                '09:45', '10:00', '12:45', '13:00', 5,
                '120363428379955493@g.us', '6285282212856', str(uuid.uuid4())[:12]
            ),
            (
                'pos_ob_sd01', 'POS-OB-SD01', 'Gedung SD Lantai 1 & Lobby Utama', 'OB',
                'Lobby & Kelas SD Lt 1', -6.347800, 106.964600, 35,
                '09:50', '10:00', '12:45', '13:00', 5,
                '120363133177081285@g.us', '6289516458570', str(uuid.uuid4())[:12]
            ),
            (
                'pos_ob_sd02', 'POS-OB-SD02', 'Gedung SD Lantai 2 & Koridor', 'OB',
                'Kelas & Toilet SD Lt 2', -6.347750, 106.964650, 35,
                '09:50', '10:00', '12:45', '13:00', 5,
                '120363133177081285@g.us', '6289516458570', str(uuid.uuid4())[:12]
            ),
            (
                'pos_ob_smp01', 'POS-OB-SMP01', 'Gedung SMP - SMA & Kantor Guru', 'OB',
                'Ruang Guru & Kelas SMP/SMA', -6.347600, 106.964800, 40,
                '09:50', '10:00', '12:45', '13:00', 5,
                '120363133177081285@g.us', '6289516458570', str(uuid.uuid4())[:12]
            ),
            (
                'pos_gar_01', 'POS-GAR-01', 'Ecopark, Ternak Edukasi & Rumah Bibit', 'GARDENER',
                'Kandang Ternak & Sayuran Ecopark', -6.347300, 106.965200, 50,
                '09:35', '09:45', '12:30', '13:00', 5,
                '120363429164534679@g.us', '6285282212855', str(uuid.uuid4())[:12]
            ),
            (
                'pos_gar_02', 'POS-GAR-02', 'Lanskap Taman Depan & Kebun Buah', 'GARDENER',
                'Taman Depan, Rumput & Kebun Buah', -6.347900, 106.964300, 55,
                '09:35', '09:45', '12:30', '13:00', 5,
                '120363429164534679@g.us', '6285282212855', str(uuid.uuid4())[:12]
            )
        ]
        for p in initial_points:
            cur.execute('''
                INSERT INTO ops_standby_points (
                    id, code, name, unit_code, sub_scope, latitude, longitude, radius_meters,
                    morning_start, morning_cutoff, noon_start, noon_cutoff, nudge_minutes,
                    target_group_jid, target_personal_wa, qr_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)

        initial_assignments = [
            ('pos_sec_01', 'Jaka (Security)', '6285282212856', 'SECURITY'),
            ('pos_sec_02', 'Petugas Pos Barat', '6285282212856', 'SECURITY'),
            ('pos_ob_sd01', 'Samih (OB)', '6289516458570', 'OB'),
            ('pos_ob_sd02', 'Kusmawan (OB)', '6281220795285', 'OB'),
            ('pos_ob_smp01', 'Risman (OB)', '6289676625832', 'OB'),
            ('pos_gar_01', 'Ekky Satria (Gardener)', '6285282212855', 'GARDENER'),
            ('pos_gar_01', 'Said Husaen (Ecopark)', '6289669447980', 'GARDENER'),
            ('pos_gar_02', 'Didin (Gardener)', '6285282212855', 'GARDENER')
        ]
        for a in initial_assignments:
            cur.execute('''
                INSERT INTO ops_standby_assignments (point_id, petugas_name, no_wa, unit_code)
                VALUES (?, ?, ?, ?)
            ''', a)
        conn.commit()

    # Seed data from annahl_ops_data.json if tables are empty
    if os.path.exists(JSON_DATA_PATH):
        try:
            with open(JSON_DATA_PATH, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Seed tasks
            cur.execute("SELECT COUNT(*) FROM ops_tasks")
            if cur.fetchone()[0] == 0 and "tasks" in json_data:
                for t in json_data["tasks"]:
                    cur.execute('''
                        INSERT INTO ops_tasks (id, unit_code, category, title, priority, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        t.get("id") or ("TK-" + str(uuid.uuid4())[:8]),
                        t.get("unit", "Umum"),
                        t.get("category", "Umum"),
                        t.get("title", "Tugas"),
                        t.get("priority", "Sedang"),
                        t.get("status", "Pending"),
                        t.get("created_at") or now_wib().strftime("%Y-%m-%d %H:%M")
                    ))

            # Seed todos
            cur.execute("SELECT COUNT(*) FROM ops_todos")
            if cur.fetchone()[0] == 0 and "todos" in json_data:
                for td in json_data["todos"]:
                    cur.execute('''
                        INSERT INTO ops_todos (id, unit_code, title, category, due_date, priority, completed, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        td.get("id") or ("td_" + str(uuid.uuid4())[:8]),
                        td.get("unit_code", "ALL"),
                        td.get("title", ""),
                        td.get("category", "Umum"),
                        td.get("due_date", ""),
                        td.get("priority", "Sedang"),
                        1 if td.get("completed") else 0,
                        td.get("created_at") or now_wib().strftime("%Y-%m-%d %H:%M")
                    ))

            # Seed journals
            cur.execute("SELECT COUNT(*) FROM ops_journals")
            if cur.fetchone()[0] == 0 and "journals" in json_data:
                for j in json_data["journals"]:
                    cur.execute('''
                        INSERT INTO ops_journals (id, unit_code, author_nama, category, date, time, title, description, output, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        j.get("id") or ("j_" + str(uuid.uuid4())[:8]),
                        j.get("unit_code", "ALL"),
                        j.get("author_nama", "Mr Slam"),
                        j.get("category", "IT & GA"),
                        j.get("date", ""),
                        j.get("time", ""),
                        j.get("title", ""),
                        j.get("description", ""),
                        j.get("output", ""),
                        j.get("created_at") or now_wib().strftime("%Y-%m-%d %H:%M")
                    ))
            conn.commit()
        except Exception as e:
            print(f"[ops_core] Error seeding from json: {e}")

    conn.close()

# Initialize DB on module import
init_ops_core_db()

# ==================== HELPER FUNCTIONS ====================
def send_ops_wa_alert(target_wa, message):
    """Mengirim WhatsApp alert melalui loopback mutabaah-bot (Port 3005) - mendukung nomor pribadi maupun JID Group"""
    if not target_wa:
        return False, "Nomor WA tujuan kosong"
    target_str = str(target_wa).strip()
    if "@g.us" in target_str or "@s.whatsapp.net" in target_str:
        target = target_str
    else:
        clean_wa = re.sub(r'\D', '', target_str)
        if clean_wa.startswith('0'):
            clean_wa = '62' + clean_wa[1:]
        target = f"{clean_wa}@s.whatsapp.net"
    try:
        r = requests.post("http://127.0.0.1:3005/send_alert", json={"target": target, "text": message}, timeout=4)
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

def broadcast_ops_alert(targets, message):
    """Mengirim pesan alert ke beberapa nomor WA atau Group sekaligus"""
    if not targets:
        return []
    if isinstance(targets, str):
        target_list = [t.strip() for t in targets.split(',') if t.strip()]
    else:
        target_list = [str(t).strip() for t in targets if t and str(t).strip()]
    
    results = []
    for t in target_list:
        ok, res = send_ops_wa_alert(t, message)
        results.append({"target": t, "success": ok, "response": res})
    return results

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Menghitung jarak dalam meter antara dua koordinat GPS menggunakan formula Haversine"""
    try:
        R = 6371000.0  # Radius bumi (meter)
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)
    except Exception as e:
        return 999999.0

def get_coordinator_info(unit_code):
    """Mencari kontak koordinator aktif untuk unit kerja tertentu dari tabel ops_users"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT username, nama_lengkap, no_wa, sub_scope 
        FROM ops_users 
        WHERE unit_code = ? AND is_active = 1 
        ORDER BY id ASC LIMIT 1
    ''', (unit_code,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def resolve_ops_user(author_username=None, phone_wa=None, author_nama=None):
    """Mencari data user dari tabel ops_users berdasarkan username, no WA, atau nama"""
    conn = get_db()
    cur = conn.cursor()
    user = None

    if author_username:
        cur.execute('''
            SELECT id, username, nama_lengkap, role_code, unit_code, sub_scope, no_wa 
            FROM ops_users 
            WHERE username = ? AND is_active = 1
        ''', (str(author_username).strip(),))
        row = cur.fetchone()
        if row:
            user = dict(row)

    if not user and phone_wa:
        clean_wa = re.sub(r'\D', '', str(phone_wa))
        if clean_wa.startswith('0'):
            clean_wa = '62' + clean_wa[1:]
        cur.execute('''
            SELECT id, username, nama_lengkap, role_code, unit_code, sub_scope, no_wa 
            FROM ops_users 
            WHERE is_active = 1
        ''')
        for r in cur.fetchall():
            db_wa = re.sub(r'\D', '', str(r['no_wa'] or ''))
            if db_wa.startswith('0'):
                db_wa = '62' + db_wa[1:]
            if db_wa and (db_wa == clean_wa or clean_wa.endswith(db_wa) or db_wa.endswith(clean_wa)):
                user = dict(r)
                break

    if not user and author_nama:
        cur.execute('''
            SELECT id, username, nama_lengkap, role_code, unit_code, sub_scope, no_wa 
            FROM ops_users 
            WHERE (nama_lengkap LIKE ? OR username LIKE ?) AND is_active = 1
            LIMIT 1
        ''', (f"%{str(author_nama).strip()}%", f"%{str(author_nama).strip()}%"))
        row = cur.fetchone()
        if row:
            user = dict(row)

    conn.close()
    return user

def sync_db_to_json():
    """Menjaga kompatibilitas ke annahl_ops_data.json untuk service eksternal (monitor_daemon)"""
    try:
        data = {}
        if os.path.exists(JSON_DATA_PATH):
            with open(JSON_DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        conn = get_db()
        cur = conn.cursor()
        
        # Sync tasks
        cur.execute("SELECT * FROM ops_tasks ORDER BY created_at DESC")
        data["tasks"] = [dict(r) for r in cur.fetchall()]
        
        # Sync todos
        cur.execute("SELECT * FROM ops_todos ORDER BY created_at DESC")
        todos = []
        for r in cur.fetchall():
            d = dict(r)
            d["completed"] = bool(d["completed"])
            todos.append(d)
        data["todos"] = todos

        # Sync journals
        cur.execute("SELECT * FROM ops_journals ORDER BY date DESC, time DESC")
        data["journals"] = [dict(r) for r in cur.fetchall()]

        # Sync procurements
        cur.execute("SELECT * FROM ops_procurements ORDER BY requested_at DESC")
        data["procurements"] = [dict(r) for r in cur.fetchall()]

        conn.close()

        with open(JSON_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ops_core] Sync DB to JSON error: {e}")

# ==================== REST API: TASKS / TIKET OPERASIONAL ====================

@ops_core_bp.route("/api/ops/tasks", methods=["GET"])
def api_get_tasks():
    user_role = session.get('ops_role_code', '')
    user_unit = session.get('ops_unit_code', '')

    filter_unit = request.args.get('unit')
    filter_status = request.args.get('status')
    search = request.args.get('q', '').strip().lower()

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM ops_tasks WHERE 1=1"
    params = []

    # Scoping: Koordinator hanya melihat tiket unitnya sendiri
    if user_role and user_role != 'manager':
        query += " AND unit_code = ?"
        params.append(user_unit)
    elif filter_unit and filter_unit != 'ALL':
        query += " AND unit_code = ?"
        params.append(filter_unit)

    if filter_status and filter_status != 'ALL':
        query += " AND status = ?"
        params.append(filter_status)

    query += " ORDER BY CASE status WHEN 'Pending' THEN 1 WHEN 'Proses' THEN 2 ELSE 3 END, created_at DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    if search:
        rows = [r for r in rows if search in (r.get('title', '') + ' ' + r.get('description', '') + ' ' + r.get('category', '')).lower()]

    return jsonify(rows)

@ops_core_bp.route("/api/ops/tasks/create", methods=["POST"])
def api_create_task():
    data = request.get_json(silent=True) or request.form
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Judul tugas wajib diisi"}), 400

    unit_code = data.get("unit_code") or data.get("unit") or "IT"
    sub_scope = data.get("sub_scope", "").strip()
    category = data.get("category", "Operasional").strip()
    description = data.get("description", "").strip()
    priority = data.get("priority", "Sedang")
    due_date = data.get("due_date", "").strip()
    send_wa = data.get("send_wa", True)

    created_by = session.get('ops_nama', 'Mr Slam')
    
    # Auto-generate ID: TK-YYYYMMDD-XXXX
    date_part = now_wib().strftime("%Y%m%d")
    task_id = f"TK-{date_part}-{str(uuid.uuid4())[:4].upper()}"

    # Cari koordinator dari unit tujuan
    coord = get_coordinator_info(unit_code)
    assigned_to = coord["username"] if coord else ""
    assigned_name = coord["nama_lengkap"] if coord else ""

    now_str = now_wib().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO ops_tasks (
            id, unit_code, sub_scope, category, title, description, priority, 
            status, assigned_to, assigned_name, due_date, source, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, 'manual', ?, ?)
    ''', (
        task_id, unit_code, sub_scope, category, title, description, 
        priority, assigned_to, assigned_name, due_date, created_by, now_str
    ))
    conn.commit()
    conn.close()

    sync_db_to_json()

    # Kirim WhatsApp alert ke koordinator jika ada kontak
    wa_status = "Tidak dikirim"
    if send_wa and coord and coord.get("no_wa"):
        sub_text = f" ({sub_scope})" if sub_scope else ""
        msg = (
            f"🔔 *PENDELEGASIAN TUGAS BARU - AN NAHL OPS*\n\n"
            f"📌 *No. Tiket* : `{task_id}`\n"
            f"🏢 *Unit Kerja* : {unit_code}{sub_text}\n"
            f"🎯 *Tugas* : {title}\n"
            f"⚡ *Prioritas* : {priority}\n"
            f"📅 *Target Selesai* : {due_date or 'Hari Ini'}\n"
            f"👤 *Disposisi Oleh* : {created_by}\n"
        )
        if description:
            msg += f"📝 *Instruksi* : {description}\n"
        msg += f"\n🌐 Silakan perbarui progres di Dashboard: https://note-umum.ametriyadhi.com"
        
        ok, res = send_ops_wa_alert(coord["no_wa"], msg)
        wa_status = "Terkirim" if ok else f"Gagal: {res}"

    return jsonify({
        "success": True, 
        "id": task_id, 
        "message": "Tugas berhasil didelegasikan", 
        "wa_status": wa_status
    }), 201

@ops_core_bp.route("/api/ops/tasks/<task_id>/update", methods=["POST"])
def api_update_task(task_id):
    data = request.get_json(silent=True) or request.form
    new_status = data.get("status", "Selesai").strip()
    progress_notes = data.get("progress_notes", "").strip()

    completed_at = now_wib().strftime("%Y-%m-%d %H:%M") if new_status == "Selesai" else None

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE ops_tasks 
        SET status = ?, progress_notes = COALESCE(NULLIF(?, ''), progress_notes), completed_at = COALESCE(?, completed_at)
        WHERE id = ?
    ''', (new_status, progress_notes, completed_at, task_id))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "message": f"Status tiket {task_id} berhasil diubah menjadi {new_status}"})

@ops_core_bp.route("/api/ops/tasks/<task_id>/delete", methods=["POST"])
def api_delete_task(task_id):
    if session.get('ops_role_code') != 'manager':
        return jsonify({"error": "Hanya manager yang dapat menghapus tiket"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ops_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "message": f"Tiket {task_id} berhasil dihapus"})

# ==================== REST API: KONVERSI KEBERSIHAN -> TIKET ====================

@ops_core_bp.route("/api/ops/tasks/convert_kebersihan", methods=["POST"])
def api_convert_kebersihan():
    """
    Mengonversi laporan kebersihan sarpras menjadi tiket pekerjaan terstruktur
    dan mengirim notifikasi penugasan ke WhatsApp koordinator unit terkait.
    """
    data = request.get_json(silent=True) or request.form
    pelapor_nama = data.get("pelapor_nama", "").strip()
    area = data.get("area", "").strip()
    keterangan = data.get("keterangan", "").strip()

    unit_code = data.get("unit_code", "OB").strip()
    sub_scope = data.get("sub_scope", "").strip()
    priority = data.get("priority", "Sedang")
    due_date = data.get("due_date", "").strip()
    instructions = data.get("instructions", "").strip()
    send_wa = data.get("send_wa", True)

    date_part = now_wib().strftime("%Y%m%d")
    task_id = f"TK-OPS-{date_part}-{str(uuid.uuid4())[:4].upper()}"

    title = f"Perbaikan di {area}: {keterangan[:60]}"
    description = f"Temuan Kebersihan oleh {pelapor_nama}.\nLokasi: {area}\nKeterangan: {keterangan}"
    if instructions:
        description += f"\nInstruksi Tambahan: {instructions}"

    coord = get_coordinator_info(unit_code)
    assigned_to = coord["username"] if coord else ""
    assigned_name = coord["nama_lengkap"] if coord else ""
    created_by = session.get('ops_nama', 'Mr Slam')
    now_str = now_wib().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO ops_tasks (
            id, unit_code, sub_scope, category, title, description, priority,
            status, assigned_to, assigned_name, due_date, source, source_ref, created_by, created_at
        ) VALUES (?, ?, ?, 'Temuan Kebersihan', ?, ?, ?, 'Pending', ?, ?, ?, 'kebersihan_log', ?, ?, ?)
    ''', (
        task_id, unit_code, sub_scope, title, description, priority,
        assigned_to, assigned_name, due_date, f"{pelapor_nama} - {area}", created_by, now_str
    ))
    conn.commit()
    conn.close()

    sync_db_to_json()

    # Kirim WA ke Koordinator Unit terkait
    wa_status = "Tidak dikirim"
    if send_wa and coord and coord.get("no_wa"):
        sub_text = f" ({sub_scope})" if sub_scope else ""
        msg = (
            f"🚨 *TIKET SARPRAS BARU - HASIL LAPORAN KEBERSIHAN*\n\n"
            f"📌 *No. Tiket* : `{task_id}`\n"
            f"🏢 *Unit Tujuan* : {unit_code}{sub_text}\n"
            f"📍 *Area / Lokasi* : {area}\n"
            f"🔍 *Temuan* : {keterangan}\n"
            f"⚡ *Prioritas* : {priority}\n"
            f"📅 *Target Selesai* : {due_date or 'Hari Ini'}\n"
            f"👤 *Pelapor Lapangan* : {pelapor_nama}\n"
            f"👮 *Disposisi* : {created_by}\n"
        )
        if instructions:
            msg += f"📝 *Instruksi Khusus* : {instructions}\n"
        msg += f"\n🌐 Cek & selesaikan di Dashboard: https://note-umum.ametriyadhi.com"

        ok, res = send_ops_wa_alert(coord["no_wa"], msg)
        wa_status = "Terkirim" if ok else f"Gagal: {res}"

    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": f"Laporan kebersihan berhasil dikonversi menjadi tiket {task_id}",
        "wa_status": wa_status
    }), 201

# ==================== REST API: JURNAL HARIAN & SUPERVISI ====================

@ops_core_bp.route("/api/ops/journals", methods=["GET"])
def api_get_journals():
    user_role = session.get('ops_role_code', '')
    user_unit = session.get('ops_unit_code', '')
    user_username = session.get('ops_username', '')

    filter_unit = request.args.get('unit')
    limit = int(request.args.get('limit', 100))

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM ops_journals WHERE 1=1"
    params = []

    if user_role and user_role != 'manager':
        query += """ AND (unit_code = ? OR author_username = ?) 
                     AND unit_code != 'ALL' 
                     AND (author_username IS NULL OR author_username != 'admin')"""
        params.extend([user_unit, user_username])
    elif filter_unit and filter_unit != 'ALL':
        query += " AND unit_code = ?"
        params.append(filter_unit)

    query += " ORDER BY date DESC, time DESC, created_at DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@ops_core_bp.route("/api/ops/journals/create", methods=["POST"])
def api_create_journal():
    data = request.get_json(silent=True) or request.form
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()

    if not title or not description:
        return jsonify({"error": "Judul dan deskripsi jurnal wajib diisi"}), 400

    # Cek session login web atau panggilan API eksternal (WA Bot)
    if 'ops_username' in session:
        user_role = session.get('ops_role_code', 'manager')
        user_unit = session.get('ops_unit_code', 'ALL')
        user_nama = session.get('ops_nama', 'Mr Slam')
        user_username = session.get('ops_username', 'admin')
        unit_code = data.get("unit_code", user_unit) if user_role == 'manager' else user_unit
    else:
        author_username = data.get("author_username")
        sender_wa = data.get("sender_wa") or data.get("phone")
        author_nama = data.get("author_nama")

        user_info = resolve_ops_user(author_username=author_username, phone_wa=sender_wa, author_nama=author_nama)
        if user_info:
            user_role = user_info.get('role_code', 'koordinator')
            user_unit = user_info.get('unit_code', 'ALL')
            user_nama = user_info.get('nama_lengkap', 'Petugas')
            user_username = user_info.get('username', 'petugas')
            unit_code = data.get("unit_code") or user_unit
        else:
            user_role = 'user'
            clean_digits = re.sub(r'\D', '', str(sender_wa or ''))
            user_username = author_username or (f"wa_{clean_digits[-4:]}" if clean_digits else "wa_guest")
            user_nama = author_nama or data.get("nama") or "Petugas Lapangan"

            inferred_unit = data.get("unit_code")
            if not inferred_unit:
                text_to_check = f"{title} {description} {data.get('category', '')}".lower()
                if any(w in text_to_check for w in ['it', 'server', 'wifi', 'jaringan', 'cbt', 'lab', 'komputer', 'absensi', 'web', 'aplikasi']):
                    inferred_unit = 'IT'
                elif any(w in text_to_check for w in ['ob', 'kebersihan', 'toilet', 'sampah', 'sapu', 'pel']):
                    inferred_unit = 'OB'
                elif any(w in text_to_check for w in ['taman', 'gardener', 'kebun', 'ternak', 'pohon', 'ecopark']):
                    inferred_unit = 'GARDENER'
                elif any(w in text_to_check for w in ['security', 'satpam', 'pos', 'gerbang', 'patroli', 'parkir']):
                    inferred_unit = 'SECURITY'
                else:
                    inferred_unit = 'ALL'
            unit_code = inferred_unit

    category = data.get("category", "").strip() or (f"Unit {unit_code}" if unit_code != 'ALL' else "Manajemen")
    date_val = data.get("date", "").strip() or now_wib().strftime("%Y-%m-%d")
    time_val = data.get("time", "").strip() or now_wib().strftime("%H:%M")
    output_val = data.get("output", "").strip() or "Tercatat via WhatsApp Bot"

    journal_id = "j_" + str(uuid.uuid4())[:8]
    now_str = now_wib().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO ops_journals (
            id, unit_code, author_username, author_nama, category, date, time, title, description, output, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        journal_id, unit_code, user_username, user_nama, category, date_val, time_val, title, description, output_val, now_str
    ))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({
        "success": True,
        "id": journal_id,
        "unit_code": unit_code,
        "author_nama": user_nama,
        "author_username": user_username,
        "category": category,
        "message": "Jurnal kegiatan berhasil dicatat"
    }), 201

@ops_core_bp.route("/api/ops/journals/<journal_id>/feedback", methods=["POST"])
def api_journal_feedback(journal_id):
    """Memberikan catatan supervisi / apresiasi dari Mr. Slam ke jurnal koordinator"""
    if session.get('ops_role_code') != 'manager':
        return jsonify({"error": "Hanya pimpinan / manager yang dapat memberikan catatan supervisi"}), 403

    data = request.get_json(silent=True) or request.form
    feedback_text = data.get("feedback", "").strip()
    if not feedback_text:
        return jsonify({"error": "Catatan feedback tidak boleh kosong"}), 400

    supervisor_name = session.get('ops_nama', 'Mr Slam (Manager)')
    now_str = now_wib().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE ops_journals
        SET supervisor_feedback = ?, supervisor_feedback_by = ?, supervisor_feedback_at = ?
        WHERE id = ?
    ''', (feedback_text, supervisor_name, now_str, journal_id))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "message": "Catatan supervisi berhasil disimpan"})

@ops_core_bp.route("/api/ops/journals/<journal_id>/delete", methods=["POST"])
def api_delete_journal(journal_id):
    user_role = session.get('ops_role_code')
    user_username = session.get('ops_username')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT author_username FROM ops_journals WHERE id = ?", (journal_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Jurnal tidak ditemukan"}), 404

    if user_role != 'manager' and row["author_username"] != user_username:
        conn.close()
        return jsonify({"error": "Anda hanya dapat menghapus jurnal yang Anda buat sendiri"}), 403

    cur.execute("DELETE FROM ops_journals WHERE id = ?", (journal_id,))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "message": "Jurnal berhasil dihapus"})

# ==================== REST API: TO-DO KOORDINATOR ====================

@ops_core_bp.route("/api/ops/todos", methods=["GET"])
def api_get_todos():
    user_role = session.get('ops_role_code', '')
    user_unit = session.get('ops_unit_code', '')
    filter_unit = request.args.get('unit')

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM ops_todos WHERE 1=1"
    params = []

    if user_role and user_role != 'manager':
        query += " AND unit_code = ?"
        params.append(user_unit)
    elif filter_unit and filter_unit != 'ALL':
        query += " AND unit_code = ?"
        params.append(filter_unit)

    query += " ORDER BY completed ASC, CASE priority WHEN 'Tinggi' THEN 1 WHEN 'Sedang' THEN 2 ELSE 3 END, created_at DESC"
    cur.execute(query, params)
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["completed"] = bool(d["completed"])
        rows.append(d)
    conn.close()
    return jsonify(rows)

@ops_core_bp.route("/api/ops/todos/create", methods=["POST"])
def api_create_todo():
    data = request.get_json(silent=True) or request.form
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Judul to-do wajib diisi"}), 400

    if 'ops_username' in session:
        user_unit = session.get('ops_unit_code', 'ALL')
        user_role = session.get('ops_role_code', 'manager')
        created_by = session.get('ops_nama', 'Mr Slam')
        unit_code = user_unit if user_role != 'manager' else (data.get("unit_code") or data.get("category") or "Umum")
    else:
        author_username = data.get("author_username")
        sender_wa = data.get("sender_wa") or data.get("phone")
        author_nama = data.get("author_nama")
        user_info = resolve_ops_user(author_username=author_username, phone_wa=sender_wa, author_nama=author_nama)
        if user_info:
            user_unit = user_info.get('unit_code', 'ALL')
            unit_code = data.get("unit_code") or user_unit
            created_by = user_info.get('nama_lengkap', 'Petugas')
        else:
            unit_code = data.get("unit_code", "ALL")
            created_by = author_nama or data.get("nama") or "WA Bot"

    category = data.get("category") or (f"Unit {unit_code}" if unit_code != 'ALL' else "Umum")
    due_date = data.get("due_date", "").strip() or now_wib().strftime("%Y-%m-%d")
    priority = data.get("priority", "Sedang")

    todo_id = "td_" + str(uuid.uuid4())[:8]
    now_str = now_wib().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO ops_todos (id, unit_code, title, category, due_date, priority, completed, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
    ''', (todo_id, unit_code, title, category, due_date, priority, created_by, now_str))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({
        "success": True,
        "id": todo_id,
        "unit_code": unit_code,
        "created_by": created_by,
        "message": "To-Do berhasil disimpan"
    }), 201

@ops_core_bp.route("/api/ops/todos/<todo_id>/toggle", methods=["POST"])
def api_toggle_todo(todo_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT completed FROM ops_todos WHERE id = ?", (todo_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "To-do tidak ditemukan"}), 404

    new_val = 0 if row["completed"] else 1
    completed_at = now_wib().strftime("%Y-%m-%d %H:%M") if new_val == 1 else None

    cur.execute("UPDATE ops_todos SET completed = ?, completed_at = ? WHERE id = ?", (new_val, completed_at, todo_id))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "completed": bool(new_val)})

@ops_core_bp.route("/api/ops/todos/<todo_id>/delete", methods=["POST"])
def api_delete_todo(todo_id):
    user_role = session.get('ops_role_code', '')
    user_nama = session.get('ops_nama', '')
    user_username = session.get('ops_username', '')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT created_by, unit_code FROM ops_todos WHERE id = ?", (todo_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "To-do tidak ditemukan"}), 404

    # Koordinator dilarang menghapus to-do yang dibuat oleh pimpinan / orang lain
    if user_role != 'manager' and row["created_by"] not in [user_username, user_nama]:
        conn.close()
        return jsonify({"error": "Anda tidak memiliki hak akses untuk menghapus to-do yang dibuat oleh pimpinan."}), 403

    cur.execute("DELETE FROM ops_todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "message": "To-do berhasil dihapus"})

# ==================== REST API: PENGADAAN & LOGISTIK SARPRAS ====================

@ops_core_bp.route("/api/ops/procurements", methods=["GET"])
def api_get_procurements():
    user_role = session.get('ops_role_code', '')
    user_unit = session.get('ops_unit_code', '')

    filter_status = request.args.get('status')
    filter_unit = request.args.get('unit')
    search = request.args.get('q', '').strip().lower()

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM ops_procurements WHERE 1=1"
    params = []

    # Scoping: Manager dan PIC Pengadaan melihat semua; Koordinator/PIC Sarpras melihat unitnya sendiri
    if user_role not in ['manager', 'pic_pengadaan']:
        query += " AND unit_code = ?"
        params.append(user_unit)
    elif filter_unit and filter_unit != 'ALL':
        query += " AND unit_code = ?"
        params.append(filter_unit)

    if filter_status and filter_status != 'ALL':
        query += " AND status = ?"
        params.append(filter_status)

    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(id) LIKE ? OR LOWER(vendor_info) LIKE ? OR LOWER(ticket_ref) LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY CASE status WHEN 'Diajukan' THEN 1 WHEN 'Disetujui' THEN 2 WHEN 'Proses Beli' THEN 3 WHEN 'Barang Tiba' THEN 4 ELSE 5 END, requested_at DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@ops_core_bp.route("/api/ops/procurements/create", methods=["POST"])
def api_create_procurement():
    data = request.get_json(silent=True) or request.form
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Nama barang / material wajib diisi"}), 400

    user_unit = session.get('ops_unit_code', 'SARPRAS')
    user_role = session.get('ops_role_code', 'manager')
    unit_code = data.get("unit_code") or (user_unit if user_role != 'manager' else "SARPRAS")
    category = data.get("category", "Material Sarpras")
    quantity = data.get("quantity", "").strip()
    estimated_cost = int(data.get("estimated_cost") or 0)
    urgency = data.get("urgency", "Sedang")
    notes = data.get("notes", "").strip()
    ticket_ref = data.get("ticket_ref", "").strip() or None

    date_part = now_wib().strftime("%Y%m%d")
    proc_id = f"PR-{date_part}-{str(uuid.uuid4())[:4].upper()}"
    now_str = now_wib().strftime("%Y-%m-%d %H:%M")
    requested_by = session.get('ops_nama', 'Mr Slam')

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO ops_procurements (
            id, ticket_ref, title, unit_code, category, quantity,
            estimated_cost, status, urgency, notes, requested_by, requested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Diajukan', ?, ?, ?, ?)
    ''', (proc_id, ticket_ref, title, unit_code, category, quantity, estimated_cost, urgency, notes, requested_by, now_str))

    # Jika pengadaan terhubung ke tiket pekerjaan perbaikan
    if ticket_ref:
        cur.execute("SELECT progress_notes FROM ops_tasks WHERE id = ?", (ticket_ref,))
        task_row = cur.fetchone()
        if task_row:
            cur_notes = task_row["progress_notes"] or ""
            append_note = f"[{now_str}] Pengadaan diajukan: {proc_id} - {title} ({quantity}) est. Rp {estimated_cost:,}"
            new_task_notes = (cur_notes + "\n" + append_note).strip()
            cur.execute("UPDATE ops_tasks SET progress_notes = ? WHERE id = ?", (new_task_notes, ticket_ref))

    conn.commit()
    conn.close()

    # Notifikasi WA ke Manager jika yang mengajukan adalah staf/PIC
    wa_status = None
    if user_role != 'manager':
        mgr = get_coordinator_info('ALL')
        if mgr and mgr.get('no_wa'):
            wa_text = (
                f"🛒 *PENGAJUAN PENGADAAN BARU*\n"
                f"----------------------------------------\n"
                f"No PR      : {proc_id}\n"
                f"Unit       : {unit_code}\n"
                f"Pemohon    : {requested_by}\n"
                f"Barang     : {title}\n"
                f"Jumlah     : {quantity or '-'}\n"
                f"Est. Biaya : Rp {estimated_cost:,}\n"
                f"Urgensi    : {urgency}\n"
                + (f"Ref Tiket  : {ticket_ref}\n" if ticket_ref else "")
                + f"Catatan    : {notes or '-'}\n\n"
                f"Mohon verifikasi & persetujuan di Dashboard An Nahl Ops."
            )
            success, resp = send_ops_wa_alert(mgr['no_wa'], wa_text)
            wa_status = "Terkirim ke Pimpinan" if success else f"Gagal WA ({resp})"

    sync_db_to_json()
    return jsonify({
        "success": True,
        "id": proc_id,
        "message": f"Pengajuan pengadaan {proc_id} berhasil dibuat",
        "wa_status": wa_status
    }), 201

@ops_core_bp.route("/api/ops/procurements/<proc_id>/approve", methods=["POST"])
def api_approve_procurement(proc_id):
    if session.get('ops_role_code') != 'manager':
        return jsonify({"error": "Hanya Manager yang berwenang menyetujui pengadaan"}), 403

    data = request.get_json(silent=True) or request.form
    action = data.get("action", "approve").lower()
    approver_note = data.get("approver_note", "").strip()

    now_str = now_wib().strftime("%Y-%m-%d %H:%M")
    approved_by = session.get('ops_nama', 'Mr Slam')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ops_procurements WHERE id = ?", (proc_id,))
    proc = cur.fetchone()
    if not proc:
        conn.close()
        return jsonify({"error": "Data pengadaan tidak ditemukan"}), 404

    new_status = 'Disetujui' if action == 'approve' else 'Ditolak'

    cur.execute('''
        UPDATE ops_procurements 
        SET status = ?, approver_note = ?, approved_by = ?, approved_at = ?
        WHERE id = ?
    ''', (new_status, approver_note, approved_by, now_str, proc_id))

    # Update progress notes di tiket perbaikan jika ada
    if proc["ticket_ref"]:
        cur.execute("SELECT progress_notes FROM ops_tasks WHERE id = ?", (proc["ticket_ref"],))
        task_row = cur.fetchone()
        if task_row:
            cur_notes = task_row["progress_notes"] or ""
            append_note = f"[{now_str}] Pengadaan {proc_id} {new_status} oleh {approved_by}. Catatan: {approver_note or '-'}"
            new_task_notes = (cur_notes + "\n" + append_note).strip()
            cur.execute("UPDATE ops_tasks SET progress_notes = ? WHERE id = ?", (new_task_notes, proc["ticket_ref"]))

    conn.commit()
    conn.close()

    # Notifikasi WA ke PIC Pengadaan jika disetujui
    wa_status = None
    if action == 'approve':
        pic_p = get_coordinator_info('PENGADAAN')
        if pic_p and pic_p.get('no_wa'):
            wa_text = (
                f"✅ *PENGADAAN DISETUJUI PIMPINAN*\n"
                f"----------------------------------------\n"
                f"No PR      : {proc_id}\n"
                f"Barang     : {proc['title']}\n"
                f"Jumlah     : {proc['quantity'] or '-'}\n"
                f"Est. Biaya : Rp {proc['estimated_cost']:,}\n"
                f"Disetujui  : {approved_by}\n"
                f"Arahan     : {approver_note or 'Segera proses pembelian.'}\n\n"
                f"Silakan proses pembelian dan update status di Dashboard An Nahl Ops."
            )
            success, resp = send_ops_wa_alert(pic_p['no_wa'], wa_text)
            wa_status = "Alert terkirim ke PIC Pengadaan" if success else f"Gagal WA ({resp})"

    sync_db_to_json()
    return jsonify({
        "success": True,
        "message": f"Pengadaan {proc_id} berhasil di-{new_status.lower()}",
        "wa_status": wa_status
    })

@ops_core_bp.route("/api/ops/procurements/<proc_id>/update", methods=["POST"])
def api_update_procurement(proc_id):
    user_role = session.get('ops_role_code', '')
    if user_role not in ['manager', 'pic_pengadaan']:
        return jsonify({"error": "Hanya Manager atau PIC Pengadaan yang dapat memperbarui status pengadaan"}), 403

    data = request.get_json(silent=True) or request.form
    new_status = data.get("status", "Proses Beli")
    actual_cost = int(data.get("actual_cost") or 0)
    vendor_info = data.get("vendor_info", "").strip()
    receipt_no = data.get("receipt_no", "").strip()
    notes = data.get("notes", "").strip()

    now_str = now_wib().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ops_procurements WHERE id = ?", (proc_id,))
    proc = cur.fetchone()
    if not proc:
        conn.close()
        return jsonify({"error": "Data pengadaan tidak ditemukan"}), 404

    purchased_at = proc["purchased_at"]
    received_at = proc["received_at"]
    completed_at = proc["completed_at"]

    if new_status == 'Proses Beli' and not purchased_at:
        purchased_at = now_str
    elif new_status == 'Barang Tiba' and not received_at:
        received_at = now_str
    elif new_status in ['Diserahkan', 'Selesai'] and not completed_at:
        completed_at = now_str

    cur.execute('''
        UPDATE ops_procurements 
        SET status = ?,
            actual_cost = CASE WHEN ? > 0 THEN ? ELSE actual_cost END,
            vendor_info = COALESCE(NULLIF(?, ''), vendor_info),
            receipt_no = COALESCE(NULLIF(?, ''), receipt_no),
            notes = COALESCE(NULLIF(?, ''), notes),
            purchased_at = ?,
            received_at = ?,
            completed_at = ?
        WHERE id = ?
    ''', (new_status, actual_cost, actual_cost, vendor_info, receipt_no, notes, purchased_at, received_at, completed_at, proc_id))

    # Jika terhubung ke tiket perbaikan, laporkan perkembangan material
    if proc["ticket_ref"]:
        cur.execute("SELECT progress_notes FROM ops_tasks WHERE id = ?", (proc["ticket_ref"],))
        task_row = cur.fetchone()
        if task_row:
            cur_notes = task_row["progress_notes"] or ""
            append_note = f"[{now_str}] Update Pengadaan {proc_id}: Status {new_status}. Vendor: {vendor_info or '-'}. Nota: {receipt_no or '-'}"
            if new_status in ['Diserahkan', 'Selesai']:
                append_note += " (Material sudah siap digunakan untuk perbaikan)"
            new_task_notes = (cur_notes + "\n" + append_note).strip()
            cur.execute("UPDATE ops_tasks SET progress_notes = ? WHERE id = ?", (new_task_notes, proc["ticket_ref"]))

    conn.commit()
    conn.close()

    # Notifikasi WA ke pemohon (misal PIC Sarpras) saat barang diserahkan
    wa_status = None
    if new_status in ['Diserahkan', 'Barang Tiba']:
        requester_unit = proc["unit_code"]
        target_info = get_coordinator_info(requester_unit)
        if target_info and target_info.get('no_wa'):
            wa_text = (
                f"📦 *BARANG PENGADAAN TELAH TIBA / DISERAHKAN*\n"
                f"----------------------------------------\n"
                f"No PR      : {proc_id}\n"
                f"Barang     : {proc['title']}\n"
                f"Jumlah     : {proc['quantity'] or '-'}\n"
                f"Status     : {new_status}\n"
                + (f"Ref Tiket  : {proc['ticket_ref']}\n" if proc['ticket_ref'] else "")
                + f"Nota/Bon   : {receipt_no or '-'}\n\n"
                f"Material siap digunakan untuk pengerjaan perbaikan di lapangan."
            )
            success, resp = send_ops_wa_alert(target_info['no_wa'], wa_text)
            wa_status = f"Alert terkirim ke {requester_unit}" if success else f"Gagal WA ({resp})"

    sync_db_to_json()
    return jsonify({
        "success": True,
        "message": f"Status pengadaan {proc_id} berhasil diubah menjadi {new_status}",
        "wa_status": wa_status
    })

@ops_core_bp.route("/api/ops/procurements/<proc_id>/delete", methods=["POST"])
def api_delete_procurement(proc_id):
    if session.get('ops_role_code') != 'manager':
        return jsonify({"error": "Hanya Manager yang berwenang menghapus pengajuan pengadaan"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ops_procurements WHERE id = ?", (proc_id,))
    conn.commit()
    conn.close()

    sync_db_to_json()
    return jsonify({"success": True, "message": f"Pengadaan {proc_id} berhasil dihapus"})


# ==============================================================================
# ==================== SISTEM STANDBY GEOTAGGING (ZERO-LOGIN) ====================
# ==============================================================================

def process_standby_checkin(sender_wa, push_name, lat, long, accuracy=0, channel='WA_LOCATION', point_id=None, notes=''):
    """
    Core engine pemrosesan check-in standby:
    1. Validasi koordinat GPS
    2. Pencocokan titik pos standby dinamis
    3. Kalkulasi jarak presisi menggunakan Haversine
    4. Evaluasi sesi (PAGI vs SIANG) dan ketepatan waktu terhadap cut-off
    5. Pencatatan transaksi ke ops_standby_logs
    6. Dispatching alert ke group & nomor pribadi koordinator jika Terlambat / Di Luar Radius
    7. Pembuatan pesan balasan interaktif
    """
    try:
        lat_f = float(lat)
        long_f = float(long)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": "Koordinat GPS tidak valid",
            "reply_message": "⚠️ Koordinat GPS tidak valid. Pastikan fitur lokasi HP Anda aktif."
        }

    clean_wa = re.sub(r'\D', '', str(sender_wa or ''))
    if clean_wa.startswith('0'):
        clean_wa = '62' + clean_wa[1:]

    conn = get_db()
    cur = conn.cursor()
    target_point = None

    # 1. Cari berdasarkan point_id eksplisit jika disediakan (misal dari QR Code)
    if point_id:
        cur.execute("SELECT * FROM ops_standby_points WHERE (id = ? OR code = ?) AND is_active = 1", (point_id, point_id))
        row = cur.fetchone()
        if row:
            target_point = dict(row)

    # 2. Jika tanpa point_id (misal kirim lokasi langsung via WhatsApp), cari dari penugasan petugas
    if not target_point and clean_wa:
        cur.execute("""
            SELECT p.* FROM ops_standby_points p
            JOIN ops_standby_assignments a ON a.point_id = p.id
            WHERE (a.no_wa = ? OR a.no_wa LIKE ?) AND a.is_active = 1 AND p.is_active = 1
        """, (clean_wa, f"%{clean_wa[-9:]}%"))
        assigned_rows = [dict(r) for r in cur.fetchall()]
        if assigned_rows:
            if len(assigned_rows) == 1:
                target_point = assigned_rows[0]
            else:
                # Jika petugas memiliki beberapa pos penugasan, pilih yang jaraknya paling dekat saat ini
                assigned_rows.sort(key=lambda p: calculate_haversine_distance(lat_f, long_f, p['latitude'], p['longitude']))
                target_point = assigned_rows[0]

    # 3. Jika belum terdaftar penugasan, cari titik pos terdekat dari semua pos aktif
    if not target_point:
        cur.execute("SELECT * FROM ops_standby_points WHERE is_active = 1")
        all_points = [dict(r) for r in cur.fetchall()]
        if all_points:
            all_points.sort(key=lambda p: calculate_haversine_distance(lat_f, long_f, p['latitude'], p['longitude']))
            target_point = all_points[0]
        else:
            conn.close()
            return {
                "success": False,
                "error": "Belum ada titik standby aktif di sistem.",
                "reply_message": "⚠️ Belum ada titik standby yang terdaftar di sistem. Silakan hubungi Koordinator Unit."
            }

    # Hitung jarak Haversine ke titik pusat pos
    distance = calculate_haversine_distance(lat_f, long_f, target_point['latitude'], target_point['longitude'])
    radius_allowed = int(target_point['radius_meters'] or 35)

    # Evaluasi Sesi & Cutoff Time
    now = now_wib()
    current_time_str = now.strftime("%H:%M")
    cur_minutes = now.hour * 60 + now.minute

    if "07:00" <= current_time_str <= "11:30":
        session_type = "PAGI"
        target_cutoff = target_point['morning_cutoff'] or "10:00"
        start_window = target_point['morning_start'] or "09:45"
    elif "11:31" <= current_time_str <= "16:00":
        session_type = "SIANG"
        target_cutoff = target_point['noon_cutoff'] or "13:00"
        start_window = target_point['noon_start'] or "12:45"
    else:
        session_type = "LAINNYA"
        target_cutoff = target_point['noon_cutoff'] or "13:00"
        start_window = "07:00"

    c_h, c_m = [int(x) for x in target_cutoff.split(':')]
    cutoff_minutes = c_h * 60 + c_m
    minutes_diff = cutoff_minutes - cur_minutes

    # Tentukan Status Kehadiran
    if distance > radius_allowed:
        status = "DILUAR_RADIUS"
    elif minutes_diff >= 0:
        status = "TEPAT_WAKTU"
    else:
        status = "TERLAMBAT"

    # Resolusi Nama Petugas
    resolved_name = push_name or ""
    if clean_wa:
        cur.execute("SELECT petugas_name FROM ops_standby_assignments WHERE (no_wa = ? OR no_wa LIKE ?) AND is_active = 1 LIMIT 1", (clean_wa, f"%{clean_wa[-9:]}%"))
        p_row = cur.fetchone()
        if p_row and p_row[0]:
            resolved_name = p_row[0]
        else:
            cur.execute("SELECT nama_lengkap FROM ops_users WHERE no_wa LIKE ? LIMIT 1", (f"%{clean_wa[-9:]}%",))
            u_row = cur.fetchone()
            if u_row and u_row[0]:
                resolved_name = u_row[0]
    if not resolved_name:
        resolved_name = f"Petugas ({clean_wa[-4:] if clean_wa else 'Anonim'})"

    # Catat ke tabel riwayat ops_standby_logs
    log_id = f"stby_{now.strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
    today_date = now.strftime("%Y-%m-%d")
    checkin_time = now.strftime("%H:%M:%S")

    cur.execute("""
        INSERT INTO ops_standby_logs (
            id, date, session_type, point_id, point_code, point_name,
            petugas_name, no_wa, unit_code, checkin_time, checkin_lat, checkin_long,
            distance_meters, accuracy_meters, radius_allowed, status, minutes_diff, channel, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_id, today_date, session_type, target_point['id'], target_point['code'], target_point['name'],
        resolved_name, clean_wa, target_point['unit_code'], checkin_time, lat_f, long_f,
        distance, float(accuracy or 0), radius_allowed, status, minutes_diff, channel, notes or ""
    ))
    conn.commit()
    conn.close()

    # Susun balasan interaktif
    if status == "TEPAT_WAKTU":
        time_note = "Tepat Waktu" if minutes_diff == 0 else f"{minutes_diff} menit lebih awal"
        reply_text = (
            f"✅ *ALHAMDULILLAH, STANDBY TERVERIFIKASI!*\n\n"
            f"👤 *Petugas* : {resolved_name}\n"
            f"🏢 *Pos Tugas* : {target_point['name']} ({target_point['code']})\n"
            f"🏷️ *Unit Kerja* : {target_point['unit_code']}\n"
            f"⏰ *Waktu Lapor* : {checkin_time} WIB ({time_note})\n"
            f"📍 *Jarak GPS* : {distance} meter (Radius Maks: {radius_allowed} m)\n\n"
            f"Jazakallahu khairan atas kedisiplinan antum. Selamat bertugas kembali menjaga amanah! 🌿"
        )
    elif status == "TERLAMBAT":
        late_min = abs(minutes_diff)
        reply_text = (
            f"🟡 *STANDBY TERCATAT (TERLAMBAT)*\n\n"
            f"👤 *Petugas* : {resolved_name}\n"
            f"🏢 *Pos Tugas* : {target_point['name']} ({target_point['code']})\n"
            f"🏷️ *Unit Kerja* : {target_point['unit_code']}\n"
            f"⏰ *Waktu Lapor* : {checkin_time} WIB (*Terlambat {late_min} menit* dari batas {target_cutoff} WIB)\n"
            f"📍 *Jarak GPS* : {distance} meter (Dalam Radius Pos)\n\n"
            f"⚠️ Catatan kedisiplinan telah direkam di sistem An Nahl Ops. Mohon tingkatkan ketepatan waktu untuk sesi berikutnya."
        )
    else: # DILUAR_RADIUS
        diff_meters = round(distance - radius_allowed, 1)
        reply_text = (
            f"⚠️ *LOKASI DILUAR TITIK STANDBY!*\n\n"
            f"👤 *Petugas* : {resolved_name}\n"
            f"🏢 *Pos Terdekat* : {target_point['name']} ({target_point['code']})\n"
            f"📍 *Jarak Anda* : *{distance} meter* dari titik pos\n"
            f"📏 *Toleransi Maks* : {radius_allowed} meter\n"
            f"❌ *Selisih* : {diff_meters} meter di luar radius pos!\n\n"
            f"Mohon segera merapat tepat di titik pos standby antum, lalu kirim ulang Lokasi Terkini WhatsApp antum. Terima kasih!"
        )

    # Kirim notifikasi instan ke group dan nomor pribadi koordinator jika TERLAMBAT atau DILUAR_RADIUS
    if status in ["TERLAMBAT", "DILUAR_RADIUS"]:
        status_label = "TERLAMBAT KEMBALI KE POS" if status == "TERLAMBAT" else "TERDETEKSI DI LUAR RADIUS POS"
        alert_msg = (
            f"⚠️ *PERINGATAN STANDBY PETUGAS ({status_label})*\n\n"
            f"👤 *Petugas* : {resolved_name}\n"
            f"🏢 *Pos* : {target_point['name']} ({target_point['code']})\n"
            f"🏷️ *Unit* : {target_point['unit_code']}\n"
            f"⏰ *Waktu* : {checkin_time} WIB (Batas: {target_cutoff} WIB)\n"
            f"📍 *Jarak GPS* : {distance} m (Toleransi: {radius_allowed} m)\n"
            f"📱 *Kanal* : {'WhatsApp Location' if channel == 'WA_LOCATION' else 'Scan QR Web'}\n\n"
            f"Mohon atensi dan pembinaan Koordinator Unit terkait."
        )
        targets = []
        if target_point.get('target_group_jid'):
            targets.append(target_point['target_group_jid'])
        if target_point.get('target_personal_wa'):
            targets.append(target_point['target_personal_wa'])
        broadcast_ops_alert(targets, alert_msg)

    return {
        "success": True,
        "log_id": log_id,
        "status": status,
        "distance": distance,
        "radius_allowed": radius_allowed,
        "point": {
            "id": target_point['id'],
            "code": target_point['code'],
            "name": target_point['name'],
            "unit_code": target_point['unit_code']
        },
        "petugas_name": resolved_name,
        "session_type": session_type,
        "checkin_time": checkin_time,
        "minutes_diff": minutes_diff,
        "reply_message": reply_text
    }


# ==================== REST API ENDPOINTS STANDBY ====================

@ops_core_bp.route("/api/ops/standby/checkin", methods=["POST"])
def api_standby_checkin():
    """Endpoint untuk submit check-in standby dari WhatsApp Bot maupun Web Micro-Checkin"""
    data = request.get_json(silent=True) or {}
    sender_wa = data.get("sender_wa") or ""
    push_name = data.get("push_name") or data.get("sender_name") or ""
    lat = data.get("lat") if data.get("lat") is not None else data.get("latitude")
    long_val = data.get("long") if data.get("long") is not None else (data.get("lng") if data.get("lng") is not None else data.get("longitude"))
    accuracy = data.get("accuracy") or 0
    channel = data.get("channel") or data.get("source") or "WA_LOCATION"
    point_id = data.get("point_id") or ""
    notes = data.get("notes") or ""

    if lat is None or long_val is None:
        return jsonify({"success": False, "error": "Parameter koordinat lat & long wajib disertakan"}), 400

    result = process_standby_checkin(
        sender_wa=sender_wa,
        push_name=push_name,
        lat=lat,
        long=long_val,
        accuracy=accuracy,
        channel=channel,
        point_id=point_id,
        notes=notes
    )
    return jsonify(result), (200 if result.get("success") else 400)


@ops_core_bp.route("/api/ops/standby/points", methods=["GET"])
def api_get_standby_points():
    """Mengambil daftar seluruh titik pos standby beserta personel yang ditugaskan"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ops_standby_points ORDER BY unit_code ASC, code ASC")
    points = [dict(r) for r in cur.fetchall()]

    for p in points:
        cur.execute("SELECT * FROM ops_standby_assignments WHERE point_id = ? AND is_active = 1", (p['id'],))
        p['assignments'] = [dict(a) for a in cur.fetchall()]
    conn.close()

    return jsonify({"success": True, "points": points, "total": len(points)})


@ops_core_bp.route("/api/ops/standby/points/create", methods=["POST"])
def api_create_standby_point():
    """Membuat titik pos standby baru dengan parameter geofencing dan jadwal dinamis"""
    if session.get('ops_role_code') not in ['manager', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security']:
        return jsonify({"error": "Akses ditolak"}), 403

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    code = data.get("code", "").strip().upper()
    unit_code = data.get("unit_code", "OB").strip().upper()
    sub_scope = data.get("sub_scope", "").strip()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    radius_meters = int(data.get("radius_meters") or 35)
    morning_start = data.get("morning_start", "09:45").strip()
    morning_cutoff = data.get("morning_cutoff", "10:00").strip()
    noon_start = data.get("noon_start", "12:45").strip()
    noon_cutoff = data.get("noon_cutoff", "13:00").strip()
    nudge_minutes = int(data.get("nudge_minutes") or 5)
    target_group_jid = data.get("target_group_jid", "").strip()
    target_personal_wa = data.get("target_personal_wa", "").strip()

    if not name or not code or latitude is None or longitude is None:
        return jsonify({"error": "Nama pos, kode unik, latitude, dan longitude wajib diisi"}), 400

    point_id = f"pos_{code.lower().replace('-', '_')}_{str(uuid.uuid4())[:4]}"
    qr_token = str(uuid.uuid4())[:12]

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ops_standby_points (
                id, code, name, unit_code, sub_scope, latitude, longitude, radius_meters,
                morning_start, morning_cutoff, noon_start, noon_cutoff, nudge_minutes,
                target_group_jid, target_personal_wa, qr_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            point_id, code, name, unit_code, sub_scope, float(latitude), float(longitude), radius_meters,
            morning_start, morning_cutoff, noon_start, noon_cutoff, nudge_minutes,
            target_group_jid, target_personal_wa, qr_token
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Titik pos {name} berhasil dibuat", "point_id": point_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"Kode pos '{code}' sudah digunakan, silakan pilih kode lain"}), 400


@ops_core_bp.route("/api/ops/standby/points/<point_id>/edit", methods=["POST"])
def api_edit_standby_point(point_id):
    """Mengubah parameter titik pos standby (radius dinamis, jam cut-off, pengingat, kontak)"""
    if session.get('ops_role_code') not in ['manager', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security']:
        return jsonify({"error": "Akses ditolak"}), 403

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    code = data.get("code", "").strip().upper()
    unit_code = data.get("unit_code", "OB").strip().upper()
    sub_scope = data.get("sub_scope", "").strip()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    radius_meters = int(data.get("radius_meters") or 35)
    morning_start = data.get("morning_start", "09:45").strip()
    morning_cutoff = data.get("morning_cutoff", "10:00").strip()
    noon_start = data.get("noon_start", "12:45").strip()
    noon_cutoff = data.get("noon_cutoff", "13:00").strip()
    nudge_minutes = int(data.get("nudge_minutes") or 5)
    target_group_jid = data.get("target_group_jid", "").strip()
    target_personal_wa = data.get("target_personal_wa", "").strip()
    is_active = 1 if data.get("is_active", True) else 0

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE ops_standby_points SET
            code = ?, name = ?, unit_code = ?, sub_scope = ?, latitude = ?, longitude = ?,
            radius_meters = ?, morning_start = ?, morning_cutoff = ?, noon_start = ?, noon_cutoff = ?,
            nudge_minutes = ?, target_group_jid = ?, target_personal_wa = ?, is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        code, name, unit_code, sub_scope, float(latitude), float(longitude),
        radius_meters, morning_start, morning_cutoff, noon_start, noon_cutoff,
        nudge_minutes, target_group_jid, target_personal_wa, is_active, point_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Konfigurasi titik pos {name} berhasil diperbarui"})


@ops_core_bp.route("/api/ops/standby/points/<point_id>/delete", methods=["POST"])
def api_delete_standby_point(point_id):
    """Menghapus atau menonaktifkan titik pos standby"""
    if session.get('ops_role_code') != 'manager':
        return jsonify({"error": "Hanya Manager yang dapat menghapus titik pos standby"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ops_standby_points WHERE id = ?", (point_id,))
    cur.execute("DELETE FROM ops_standby_assignments WHERE point_id = ?", (point_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Titik pos berhasil dihapus"})


@ops_core_bp.route("/api/ops/standby/assignments", methods=["GET"])
def api_get_standby_assignments():
    """Mengambil seluruh daftar penugasan personel pos standby"""
    point_id = request.args.get("point_id")
    conn = get_db()
    cur = conn.cursor()
    if point_id:
        cur.execute("SELECT a.*, p.name as point_name, p.code as point_code FROM ops_standby_assignments a JOIN ops_standby_points p ON p.id = a.point_id WHERE a.point_id = ? AND a.is_active = 1 ORDER BY a.petugas_name ASC", (point_id,))
    else:
        cur.execute("SELECT a.*, p.name as point_name, p.code as point_code FROM ops_standby_assignments a JOIN ops_standby_points p ON p.id = a.point_id WHERE a.is_active = 1 ORDER BY a.unit_code ASC, a.petugas_name ASC")
    assignments = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"success": True, "assignments": assignments})


@ops_core_bp.route("/api/ops/standby/assignments/save", methods=["POST"])
def api_save_standby_assignment():
    """Menambahkan penugasan personel baru ke suatu titik pos"""
    if session.get('ops_role_code') not in ['manager', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security']:
        return jsonify({"error": "Akses ditolak"}), 403

    data = request.get_json(silent=True) or {}
    point_id = data.get("point_id")
    petugas_name = data.get("petugas_name", "").strip()
    no_wa = data.get("no_wa", "").strip()
    unit_code = data.get("unit_code", "OB").strip()

    if not point_id or not petugas_name or not no_wa:
        return jsonify({"error": "Titik pos, nama petugas, dan nomor WA wajib diisi"}), 400

    clean_wa = re.sub(r'\D', '', no_wa)
    if clean_wa.startswith('0'):
        clean_wa = '62' + clean_wa[1:]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ops_standby_assignments (point_id, petugas_name, no_wa, unit_code)
        VALUES (?, ?, ?, ?)
    """, (point_id, petugas_name, clean_wa, unit_code))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Penugasan {petugas_name} berhasil disimpan"})


@ops_core_bp.route("/api/ops/standby/assignments/<int:assign_id>/delete", methods=["POST"])
def api_delete_standby_assignment(assign_id):
    """Menghapus penugasan personel dari titik pos"""
    if session.get('ops_role_code') not in ['manager', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security']:
        return jsonify({"error": "Akses ditolak"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ops_standby_assignments WHERE id = ?", (assign_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Penugasan berhasil dihapus"})


@ops_core_bp.route("/api/ops/standby/logs", methods=["GET"])
def api_get_standby_logs():
    """Mengambil riwayat transaksi check-in standby dengan filter tanggal, unit, dan status"""
    date_filter = request.args.get("date", now_wib().strftime("%Y-%m-%d"))
    unit_filter = request.args.get("unit", "ALL")
    status_filter = request.args.get("status", "ALL")
    session_filter = request.args.get("session", "ALL")

    query = "SELECT * FROM ops_standby_logs WHERE date = ?"
    params = [date_filter]

    if unit_filter != "ALL":
        query += " AND unit_code = ?"
        params.append(unit_filter)
    if status_filter != "ALL":
        query += " AND status = ?"
        params.append(status_filter)
    if session_filter != "ALL":
        query += " AND session_type = ?"
        params.append(session_filter)

    query += " ORDER BY checkin_time DESC"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    logs = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({"success": True, "date": date_filter, "logs": logs, "total": len(logs)})


@ops_core_bp.route("/api/ops/standby/radar", methods=["GET"])
def api_get_standby_radar():
    """
    Mengambil status konsolidasi real-time seluruh titik pos standby untuk sesi aktif (Pagi / Siang).
    Menghasilkan data Papan Siaga & Radar Monitoring untuk Dashboard Pimpinan & Koordinator.
    """
    now = now_wib()
    today_date = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")

    # Sesi default
    req_session = request.args.get("session")
    if req_session:
        active_session = req_session.upper()
    else:
        active_session = "PAGI" if current_time_str <= "11:30" else "SIANG"

    unit_filter = request.args.get("unit", "ALL")

    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM ops_standby_points WHERE is_active = 1"
    params = []
    if unit_filter != "ALL":
        query += " AND unit_code = ?"
        params.append(unit_filter)
    query += " ORDER BY unit_code ASC, code ASC"

    cur.execute(query, params)
    points = [dict(r) for r in cur.fetchall()]

    summary = {
        "total_points": len(points),
        "standby_on_time": 0,
        "standby_late": 0,
        "out_of_range": 0,
        "empty_points": 0
    }

    radar_list = []
    for p in points:
        # Ambil penugasan
        cur.execute("SELECT petugas_name, no_wa FROM ops_standby_assignments WHERE point_id = ? AND is_active = 1", (p['id'],))
        assigned = [dict(a) for a in cur.fetchall()]
        assigned_names = ", ".join([a['petugas_name'] for a in assigned]) if assigned else "Belum Ditugaskan"

        # Cek log check-in hari ini untuk sesi terkait
        cur.execute("""
            SELECT * FROM ops_standby_logs 
            WHERE point_id = ? AND date = ? AND session_type = ?
            ORDER BY checkin_time DESC LIMIT 1
        """, (p['id'], today_date, active_session))
        latest_log = cur.fetchone()

        cutoff_time = p['morning_cutoff'] if active_session == "PAGI" else p['noon_cutoff']

        if latest_log:
            log_dict = dict(latest_log)
            st = log_dict['status']
            if st == "TEPAT_WAKTU":
                summary["standby_on_time"] += 1
                badge_status = "ON_TIME"
            elif st == "TERLAMBAT":
                summary["standby_late"] += 1
                badge_status = "LATE"
            else:
                summary["out_of_range"] += 1
                badge_status = "OUT_OF_RANGE"
        else:
            summary["empty_points"] += 1
            badge_status = "EMPTY"
            log_dict = None

        radar_list.append({
            "point": p,
            "assigned_names": assigned_names,
            "assigned_list": assigned,
            "cutoff_time": cutoff_time,
            "badge_status": badge_status,
            "latest_log": log_dict
        })

    conn.close()

    return jsonify({
        "success": True,
        "date": today_date,
        "session": active_session,
        "summary": summary,
        "radar": radar_list
    })


@ops_core_bp.route("/api/ops/cron/standby-check", methods=["GET"])
def api_cron_standby_check():
    """
    Poller Background AI Agent (dipanggil setiap 1 menit oleh cron bot/daemon):
    1. Mengirim Pengingat Proaktif (Nudge) sebelum cut-off (waktu dinamis per pos)
    2. Mendeteksi Pos Kosong & Mengirim Eskalasi Otomatis (Cut-off + 5 menit)
       ke Group WA dan Nomor Pribadi Koordinator Unit terkait.
    """
    now = now_wib()
    today_date = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")
    cur_minutes = now.hour * 60 + now.minute

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ops_standby_points WHERE is_active = 1")
    points = [dict(r) for r in cur.fetchall()]

    dispatched_actions = []

    for p in points:
        point_id = p['id']
        nudge_min = int(p['nudge_minutes'] or 5)

        # Evaluasi untuk 2 Sesi: PAGI dan SIANG
        sessions = [
            ("PAGI", p['morning_cutoff']),
            ("SIANG", p['noon_cutoff'])
        ]

        for sess_type, cutoff_str in sessions:
            if not cutoff_str or ":" not in cutoff_str:
                continue

            c_h, c_m = [int(x) for x in cutoff_str.split(':')]
            cutoff_total_mins = c_h * 60 + c_m
            nudge_trigger_min = cutoff_total_mins - nudge_min
            escalate_trigger_min = cutoff_total_mins + 5  # Cutoff + 5 menit

            # 1. PENGINGAT PROAKTIF (NUDGE)
            if cur_minutes == nudge_trigger_min:
                cur.execute("""
                    SELECT COUNT(*) FROM ops_standby_cron_tracking
                    WHERE date = ? AND session_type = ? AND action_type = 'NUDGE' AND point_id = ?
                """, (today_date, sess_type, point_id))
                already_nudged = cur.fetchone()[0] > 0

                if not already_nudged:
                    nudge_text = (
                        f"⏰ *PENGINGAT KEMBALI KE POS STANDBY ({nudge_min} MENIT LAGI)*\n\n"
                        f"Ikhwan & Rekan Petugas *{p['unit_code']}*,\n"
                        f"Waktu istirahat {sess_type.lower()} akan berakhir pada pukul *{cutoff_str} WIB*.\n\n"
                        f"Pos Siaga : *{p['name']}* ({p['code']})\n"
                        f"Silakan segera merapat ke pos masing-masing dan kirimkan *Lokasi Terkini (Share Location)* via WhatsApp ini atau scan stiker QR di pos tugas antum. 🙏"
                    )
                    targets = []
                    if p.get('target_group_jid'):
                        targets.append(p['target_group_jid'])
                    if p.get('target_personal_wa'):
                        targets.append(p['target_personal_wa'])

                    for t in targets:
                        send_ops_wa_alert(t, nudge_text)
                        try:
                            cur.execute("""
                                INSERT INTO ops_standby_cron_tracking (date, session_type, action_type, point_id, target)
                                VALUES (?, ?, 'NUDGE', ?, ?)
                            """, (today_date, sess_type, point_id, t))
                            conn.commit()
                        except Exception:
                            pass

                    dispatched_actions.append({"action": "NUDGE", "point": p['code'], "session": sess_type})

            # 2. ESKALASI POS KOSONG / BELUM STANDBY (T+5 MENIT)
            if cur_minutes == escalate_trigger_min:
                cur.execute("""
                    SELECT COUNT(*) FROM ops_standby_cron_tracking
                    WHERE date = ? AND session_type = ? AND action_type = 'ESCALATION' AND point_id = ?
                """, (today_date, sess_type, point_id))
                already_escalated = cur.fetchone()[0] > 0

                if not already_escalated:
                    # Cek apakah ada check-in valid hari ini
                    cur.execute("""
                        SELECT COUNT(*) FROM ops_standby_logs
                        WHERE point_id = ? AND date = ? AND session_type = ? AND status IN ('TEPAT_WAKTU', 'TERLAMBAT')
                    """, (point_id, today_date, sess_type))
                    has_checkin = cur.fetchone()[0] > 0

                    if not has_checkin:
                        # Ambil nama personel yang ditugaskan
                        cur.execute("SELECT petugas_name FROM ops_standby_assignments WHERE point_id = ? AND is_active = 1", (point_id,))
                        assignees = [r[0] for r in cur.fetchall()]
                        pic_names = ", ".join(assignees) if assignees else "Belum Ditugaskan"

                        escalate_text = (
                            f"🚨 *PERINGATAN POS KOSONG / BELUM STANDBY!* 🚨\n\n"
                            f"Sesi : *Istirahat {sess_type} (Batas: {cutoff_str} WIB)*\n"
                            f"Waktu Pantau : *{current_time_str} WIB (+5 menit)*\n"
                            f"🏢 *Pos Tugas* : {p['name']} ({p['code']})\n"
                            f"🏷️ *Unit Kerja* : {p['unit_code']}\n"
                            f"👤 *Personel Ditugaskan* : {pic_names}\n\n"
                            f"⚠️ Pos belum menerima laporan siaga dari petugas terkait. Mohon Koordinator Unit segera melakukan pengecekan langsung ke lokasi."
                        )
                        targets = []
                        if p.get('target_group_jid'):
                            targets.append(p['target_group_jid'])
                        if p.get('target_personal_wa'):
                            targets.append(p['target_personal_wa'])
                        # Selalu tembuskan ke nomor pimpinan (Mr. Slam)
                        targets.append("6287809199096")

                        for t in set(targets):
                            send_ops_wa_alert(t, escalate_text)
                            try:
                                cur.execute("""
                                    INSERT INTO ops_standby_cron_tracking (date, session_type, action_type, point_id, target)
                                    VALUES (?, ?, 'ESCALATION', ?, ?)
                                """, (today_date, sess_type, point_id, t))
                                conn.commit()
                            except Exception:
                                pass

                        dispatched_actions.append({"action": "ESCALATION", "point": p['code'], "session": sess_type})

    conn.close()
    return jsonify({
        "success": True,
        "time": current_time_str,
        "dispatched_count": len(dispatched_actions),
        "actions": dispatched_actions
    })


# ==================== ZERO-LOGIN WEB MICRO-CHECKIN PAGE ====================

@ops_core_bp.route("/standby/c/<point_id>", methods=["GET"])
def web_standby_micro_checkin(point_id):
    """
    Halaman Micro-Checkin Cepat Ultra-Ringan (<30KB) - ZERO LOGIN:
    Petugas cukup scan QR Code stiker di pos, perangkat mengingat identitas petugas,
    GPS HTML5 otomatis aktif dan menekan 1 tombol besar konfirmasi.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ops_standby_points WHERE (id = ? OR code = ?) AND is_active = 1", (point_id, point_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return "<h3>Titik pos standby tidak ditemukan atau tidak aktif.</h3>", 404

    point = dict(row)
    cur.execute("SELECT petugas_name, no_wa FROM ops_standby_assignments WHERE point_id = ? AND is_active = 1", (point['id'],))
    assignments = [dict(a) for a in cur.fetchall()]
    conn.close()

    now = now_wib()
    cur_time = now.strftime("%H:%M")
    active_sess = "PAGI" if cur_time <= "11:30" else "SIANG"
    target_cutoff = point['morning_cutoff'] if active_sess == "PAGI" else point['noon_cutoff']

    html_template = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Konfirmasi Standby Pos - {{ point.name }}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @keyframes pulse-ring {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 14px rgba(16, 185, 129, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }
            .pulse-green { animation: pulse-ring 2s infinite; }
        </style>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">
        <div class="w-full max-w-md bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 space-y-5">
            <!-- Header Identitas Pos -->
            <div class="text-center space-y-1">
                <div class="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-950 border border-emerald-700 text-emerald-300 text-xs font-bold rounded-full uppercase tracking-wider">
                    <i class="fa-solid fa-satellite-dish"></i> Pos {{ point.unit_code }}
                </div>
                <h1 class="text-xl font-bold text-white mt-2">{{ point.name }}</h1>
                <p class="text-xs text-slate-400">{{ point.code }} • {{ point.sub_scope or 'Sekolah Islam An Nahl' }}</p>
            </div>

            <!-- Target Jam Standby Info -->
            <div class="bg-slate-900/80 border border-slate-700/80 rounded-xl p-3 flex items-center justify-between text-xs">
                <div>
                    <span class="text-slate-400 block text-[10px] uppercase font-semibold">Sesi Wajib Siaga</span>
                    <span class="text-white font-bold">{{ active_sess }} (Batas: {{ target_cutoff }} WIB)</span>
                </div>
                <div class="text-right">
                    <span class="text-slate-400 block text-[10px] uppercase font-semibold">Batas Radius GPS</span>
                    <span class="text-emerald-400 font-bold">{{ point.radius_meters }} Meter</span>
                </div>
            </div>

            <!-- Form Identitas Petugas (Auto-Remember via LocalStorage) -->
            <div class="space-y-3">
                <div id="saved-user-badge" class="hidden bg-emerald-900/40 border border-emerald-600/60 p-3 rounded-xl flex items-center justify-between">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xs">
                            <i class="fa-solid fa-user-check"></i>
                        </div>
                        <div>
                            <p id="label-petugas-name" class="text-xs font-bold text-white"></p>
                            <p id="label-petugas-wa" class="text-[10px] text-emerald-300"></p>
                        </div>
                    </div>
                    <button type="button" onclick="changePetugas()" class="text-[10px] font-semibold text-slate-300 hover:text-white underline">Ganti</button>
                </div>

                <div id="input-user-section" class="space-y-2">
                    <label class="block text-xs font-semibold text-slate-300">Pilih / Masukkan Nama Anda:</label>
                    <select id="select-petugas" onchange="onSelectPetugasChange()" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                        <option value="">-- Pilih Nama Terdaftar --</option>
                        {% for a in assignments %}
                        <option value="{{ a.petugas_name }}" data-wa="{{ a.no_wa }}">{{ a.petugas_name }}</option>
                        {% endfor %}
                        <option value="__custom__">+ Ketik Nama Lainnya</option>
                    </select>

                    <input type="text" id="custom-petugas-name" placeholder="Nama Lengkap Petugas" class="hidden w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                    <input type="tel" id="custom-petugas-wa" placeholder="Nomor WhatsApp (Contoh: 08123456789)" class="hidden w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                </div>
            </div>

            <!-- Status Radar Geofence GPS -->
            <div id="gps-status-card" class="bg-slate-900/90 border border-slate-700 rounded-xl p-3.5 text-center space-y-1.5">
                <div class="flex items-center justify-center gap-2 text-xs text-slate-300">
                    <i id="gps-icon" class="fa-solid fa-spinner fa-spin text-amber-400"></i>
                    <span id="gps-status-text">Mendeteksi lokasi GPS HP Anda...</span>
                </div>
                <p id="gps-distance-text" class="text-xs font-bold text-slate-400">Pastikan izin lokasi GPS di browser disetujui</p>
            </div>

            <!-- Tombol Konfirmasi Standby -->
            <button id="btn-submit-standby" onclick="submitStandby()" disabled class="w-full py-3.5 px-4 rounded-xl font-bold text-sm text-white bg-slate-700 cursor-not-allowed transition flex items-center justify-center gap-2">
                <i class="fa-solid fa-location-crosshairs"></i>
                <span>Menunggu Akurasi GPS...</span>
            </button>

            <!-- Result Box -->
            <div id="result-box" class="hidden p-4 rounded-xl text-xs space-y-2"></div>
        </div>

        <p class="text-[11px] text-slate-500 mt-4 text-center">Sekolah Islam An Nahl • Sistem Manajemen Kedisiplinan Pos</p>

        <script>
            const TARGET_LAT = {{ point.latitude }};
            const TARGET_LON = {{ point.longitude }};
            const RADIUS_LIMIT = {{ point.radius_meters }};
            const POINT_ID = "{{ point.id }}";

            let currentLat = null;
            let currentLon = null;
            let currentAcc = null;
            let currentDist = null;

            // Hitung jarak Haversine di sisi klien
            function calcDistance(lat1, lon1, lat2, lon2) {
                const R = 6371000;
                const dLat = (lat2 - lat1) * Math.PI / 180;
                const dLon = (lon2 - lon1) * Math.PI / 180;
                const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                          Math.sin(dLon/2) * Math.sin(dLon/2);
                const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                return Math.round(R * c);
            }

            // Inisialisasi User dari LocalStorage
            function initUser() {
                const savedName = localStorage.getItem('annahl_standby_name');
                const savedWa = localStorage.getItem('annahl_standby_wa');
                if (savedName) {
                    document.getElementById('label-petugas-name').innerText = savedName;
                    document.getElementById('label-petugas-wa').innerText = savedWa || 'Tersimpan';
                    document.getElementById('saved-user-badge').classList.remove('hidden');
                    document.getElementById('input-user-section').classList.add('hidden');
                }
            }

            function changePetugas() {
                document.getElementById('saved-user-badge').classList.add('hidden');
                document.getElementById('input-user-section').classList.remove('hidden');
            }

            function onSelectPetugasChange() {
                const sel = document.getElementById('select-petugas');
                const customName = document.getElementById('custom-petugas-name');
                const customWa = document.getElementById('custom-petugas-wa');
                if (sel.value === '__custom__') {
                    customName.classList.remove('hidden');
                    customWa.classList.remove('hidden');
                } else {
                    customName.classList.add('hidden');
                    customWa.classList.add('hidden');
                }
            }

            // Pelacakan GPS Realtime
            function startGpsTracking() {
                if (!navigator.geolocation) {
                    document.getElementById('gps-status-text').innerText = "Browser tidak mendukung Geolocation GPS";
                    return;
                }

                navigator.geolocation.watchPosition(
                    (pos) => {
                        currentLat = pos.coords.latitude;
                        currentLon = pos.coords.longitude;
                        currentAcc = Math.round(pos.coords.accuracy);
                        currentDist = calcDistance(currentLat, currentLon, TARGET_LAT, TARGET_LON);

                        const icon = document.getElementById('gps-icon');
                        const statusTxt = document.getElementById('gps-status-text');
                        const distTxt = document.getElementById('gps-distance-text');
                        const btn = document.getElementById('btn-submit-standby');

                        icon.className = "fa-solid fa-circle-check text-emerald-400";
                        statusTxt.innerHTML = `GPS Terkunci (Akurasi: <span class="font-bold">${currentAcc}m</span>)`;

                        if (currentDist <= RADIUS_LIMIT) {
                            distTxt.innerHTML = `Jarak ke Pos: <span class="text-emerald-400 font-bold">${currentDist} meter (VALID)</span>`;
                            btn.disabled = false;
                            btn.className = "w-full py-3.5 px-4 rounded-xl font-bold text-sm text-white bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-900/40 pulse-green transition flex items-center justify-center gap-2 cursor-pointer";
                            btn.innerHTML = `<i class="fa-solid fa-location-dot"></i><span>📍 KONFIRMASI STANDBY DI POS</span>`;
                        } else {
                            const selisih = currentDist - RADIUS_LIMIT;
                            distTxt.innerHTML = `Jarak ke Pos: <span class="text-rose-400 font-bold">${currentDist} meter</span> (${selisih}m di luar batas)`;
                            btn.disabled = false;
                            btn.className = "w-full py-3.5 px-4 rounded-xl font-bold text-sm text-white bg-amber-600 hover:bg-amber-500 transition flex items-center justify-center gap-2 cursor-pointer";
                            btn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i><span>KIRIM STANDBY (DILUAR RADIUS)</span>`;
                        }
                    },
                    (err) => {
                        document.getElementById('gps-icon').className = "fa-solid fa-circle-exclamation text-rose-400";
                        document.getElementById('gps-status-text').innerText = "Gagal mengambil GPS: " + err.message;
                        document.getElementById('gps-distance-text').innerText = "Silakan aktifkan GPS HP dan izinkan akses lokasi";
                    },
                    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                );
            }

            async function submitStandby() {
                const btn = document.getElementById('btn-submit-standby');
                btn.disabled = true;
                btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Memproses Verifikasi...</span>`;

                let name = "";
                let wa = "";

                const savedName = localStorage.getItem('annahl_standby_name');
                if (savedName && !document.getElementById('saved-user-badge').classList.contains('hidden')) {
                    name = savedName;
                    wa = localStorage.getItem('annahl_standby_wa') || '';
                } else {
                    const sel = document.getElementById('select-petugas');
                    if (sel.value === '__custom__') {
                        name = document.getElementById('custom-petugas-name').value.trim();
                        wa = document.getElementById('custom-petugas-wa').value.trim();
                    } else if (sel.value) {
                        name = sel.value;
                        const opt = sel.options[sel.selectedIndex];
                        wa = opt.getAttribute('data-wa') || '';
                    }
                }

                if (!name) {
                    alert("Silakan pilih atau masukkan nama Anda terlebih dahulu.");
                    btn.disabled = false;
                    btn.innerHTML = `<span>Coba Lagi</span>`;
                    return;
                }

                localStorage.setItem('annahl_standby_name', name);
                if (wa) localStorage.setItem('annahl_standby_wa', wa);

                try {
                    const res = await fetch('/api/ops/standby/checkin', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            sender_wa: wa,
                            push_name: name,
                            lat: currentLat,
                            long: currentLon,
                            accuracy: currentAcc,
                            channel: 'QR_WEB',
                            point_id: POINT_ID
                        })
                    });
                    const data = await res.json();
                    const box = document.getElementById('result-box');
                    box.classList.remove('hidden');

                    if (data.success) {
                        if (data.status === 'TEPAT_WAKTU') {
                            box.className = "p-4 rounded-xl text-xs space-y-1.5 bg-emerald-950/80 border border-emerald-600 text-emerald-200";
                            box.innerHTML = `<div class="font-bold text-sm flex items-center gap-2"><i class="fa-solid fa-circle-check text-emerald-400 text-base"></i> Standby Berhasil Terverifikasi!</div>
                                             <p>Terima kasih <b>${data.petugas_name}</b>, kehadiran antum di ${data.point.name} telah tercatat tepat waktu (${data.checkin_time} WIB) dengan jarak ${data.distance}m.</p>`;
                        } else if (data.status === 'TERLAMBAT') {
                            box.className = "p-4 rounded-xl text-xs space-y-1.5 bg-amber-950/80 border border-amber-600 text-amber-200";
                            box.innerHTML = `<div class="font-bold text-sm flex items-center gap-2"><i class="fa-solid fa-clock-rotate-left text-amber-400 text-base"></i> Standby Tercatat (Terlambat)</div>
                                             <p>Laporan diterima pukul ${data.checkin_time} WIB (terlambat). Jarak: ${data.distance}m. Data telah diteruskan ke Koordinator Unit.</p>`;
                        } else {
                            box.className = "p-4 rounded-xl text-xs space-y-1.5 bg-rose-950/80 border border-rose-600 text-rose-200";
                            box.innerHTML = `<div class="font-bold text-sm flex items-center gap-2"><i class="fa-solid fa-triangle-exclamation text-rose-400 text-base"></i> Peringatan: Di Luar Radius Pos!</div>
                                             <p>Antum terdeteksi berjarak <b>${data.distance} meter</b> (toleransi maksimal ${data.radius_allowed} meter). Harap segera berada tepat di pos tugas.</p>`;
                        }
                        btn.style.display = "none";
                    } else {
                        box.className = "p-4 rounded-xl text-xs bg-rose-950/80 border border-rose-600 text-rose-200";
                        box.innerHTML = `Gagal: ${data.error || 'Terjadi kesalahan sistem'}`;
                        btn.disabled = false;
                        btn.innerHTML = `<span>Kirim Ulang</span>`;
                    }
                } catch (e) {
                    alert("Koneksi gagal: " + e.message);
                    btn.disabled = false;
                    btn.innerHTML = `<span>Coba Lagi</span>`;
                }
            }

            window.onload = () => {
                initUser();
                startGpsTracking();
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, point=point, assignments=assignments, active_sess=active_sess, target_cutoff=target_cutoff)


# ==================== CETAK STIKER AKRILIK QR STANDBY ====================

@ops_core_bp.route("/standby/print-qr", methods=["GET"])
def web_standby_print_qr():
    """
    Halaman siap cetak (Print-Ready) Stiker QR Akrilik Titik Pos Standby Sekolah Islam An Nahl.
    Dapat mencetak semua pos sekaligus atau pos spesifik (?point_id=pos_xxx).
    """
    target_id = request.args.get("point_id")
    conn = get_db()
    cur = conn.cursor()
    if target_id:
        cur.execute("SELECT * FROM ops_standby_points WHERE id = ? OR code = ?", (target_id, target_id))
    else:
        cur.execute("SELECT * FROM ops_standby_points WHERE is_active = 1 ORDER BY unit_code ASC, code ASC")
    points = [dict(r) for r in cur.fetchall()]
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>Cetak Stiker QR Akrilik Pos Standby - Sekolah Islam An Nahl</title>
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
                <h1 class="text-base font-bold text-slate-800">Cetak Stiker Akrilik QR Pos Standby</h1>
                <p class="text-xs text-slate-500">Desain standar akrilik meja/dinding (A5/A6) untuk ditempel di masing-masing titik pos.</p>
            </div>
            <button onclick="window.print()" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow flex items-center gap-2 cursor-pointer">
                <i class="fa-solid fa-print"></i> Cetak Dokumen
            </button>
        </div>

        <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for p in points %}
            <div class="bg-white border-2 border-emerald-600 rounded-2xl p-6 shadow-md flex flex-col items-center text-center space-y-3 relative overflow-hidden page-break">
                <!-- Watermark / Header -->
                <div class="w-full border-b border-emerald-100 pb-3">
                    <p class="text-[10px] font-extrabold uppercase tracking-widest text-emerald-800">SEKOLAH ISLAM AN NAHL</p>
                    <p class="text-[9px] text-slate-500 font-semibold tracking-wider uppercase">Operational & General Affairs</p>
                </div>

                <!-- Unit Badge -->
                <div class="px-3 py-1 bg-emerald-100 text-emerald-800 text-[11px] font-black rounded-full uppercase tracking-wider border border-emerald-300">
                    POS SIAGA {{ p.unit_code }}
                </div>

                <div class="space-y-0.5">
                    <h2 class="text-lg font-black text-slate-800 uppercase leading-tight">{{ p.name }}</h2>
                    <p class="text-xs font-mono font-bold text-emerald-700">{{ p.code }}</p>
                </div>

                <!-- QR Container -->
                <div class="p-3 bg-white border border-slate-200 rounded-xl shadow-inner my-2">
                    <div id="qrcode-{{ p.id }}" class="flex items-center justify-center"></div>
                </div>

                <!-- Instructions -->
                <div class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-left space-y-1 text-[11px] text-slate-700">
                    <p class="font-bold text-emerald-800 flex items-center gap-1.5">
                        <i class="fa-solid fa-circle-info"></i> Petunjuk Lapor Standby:
                    </p>
                    <ol class="list-decimal pl-4 space-y-0.5 text-[10px]">
                        <li>Buka Kamera HP / Google Lens dan <b>Scan QR Code</b> di atas.</li>
                        <li>Tekan tombol <b>"Konfirmasi Standby di Pos"</b> di layar HP.</li>
                        <li>Atau kirim <b>Share Location</b> WhatsApp ke Bot Operasional.</li>
                    </ol>
                </div>

                <div class="w-full text-center text-[9px] text-slate-400 pt-1 border-t border-slate-100">
                    Batas Standby: Pagi {{ p.morning_cutoff }} WIB • Siang {{ p.noon_cutoff }} WIB • Radius {{ p.radius_meters }}m
                </div>
            </div>
            {% endfor %}
        </div>

        <script>
            {% for p in points %}
            new QRCode(document.getElementById("qrcode-{{ p.id }}"), {
                text: window.location.origin + "/standby/c/{{ p.id }}?t={{ p.qr_token }}",
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
    return render_template_string(html, points=points)

