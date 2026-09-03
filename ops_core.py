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
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Blueprint, request, jsonify, session

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
    """Mengirim WhatsApp alert melalui loopback mutabaah-bot (Port 3005)"""
    if not target_wa:
        return False, "Nomor WA tujuan kosong"
    clean_wa = re.sub(r'\D', '', str(target_wa))
    if clean_wa.startswith('0'):
        clean_wa = '62' + clean_wa[1:]
    target = f"{clean_wa}@s.whatsapp.net"
    try:
        r = requests.post("http://127.0.0.1:3005/send_alert", json={"target": target, "text": message}, timeout=4)
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

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
