import os
import sqlite3
import json
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template_string, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

ops_auth_bp = Blueprint('ops_auth', __name__)

DB_PATH = '/home/ametriyadhi/sas-annahl/database.sqlite'

def get_ops_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_ops_auth_db():
    con = get_ops_db()
    cur = con.cursor()
    
    # 1. Tabel Roles
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_code TEXT UNIQUE NOT NULL,
            role_name TEXT NOT NULL,
            description TEXT,
            permissions TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Tabel Users
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ops_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role_code TEXT NOT NULL,
            unit_code TEXT NOT NULL,
            sub_scope TEXT,
            no_wa TEXT,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            FOREIGN KEY (role_code) REFERENCES ops_roles(role_code)
        )
    ''')
    con.commit()
    
    # Pre-seed Roles jika belum ada
    default_roles = [
        (
            'manager',
            'Manager Operasional & IT',
            'Pimpinan IT & Kabag Umum dengan kendali penuh atas seluruh sistem dan 4 unit kerja.',
            json.dumps([
                "all", "view_all_units", "delegate_tasks", "verify_tasks",
                "manage_users", "manage_roles",
                "tab-dashboard", "tab-journal", "tab-todo", "tab-tasks",
                "tab-mutabaah", "tab-kebersihan", "tab-sapaais", "tab-mutubaah",
                "tab-server", "tab-kuma", "tab-analytics", "tab-report",
                "tab-users", "tab-roles", "tab-pengadaan", "tab-evaluasi"
            ])
        ),
        (
            'koordinator_it',
            'Koordinator IT',
            'Penanggung jawab infrastruktur jaringan, server, lab, CBT, AV, dan sistem digital.',
            json.dumps([
                "unit_it", "tab-dashboard", "tab-tasks", "tab-todo",
                "tab-journal", "tab-sapaais", "tab-server", "tab-kuma", "tab-evaluasi"
            ])
        ),
        (
            'koordinator_ob',
            'Koordinator Office Boy',
            'Penanggung jawab kebersihan indoor, sanitasi toilet, kelas, kantor, dan logistik.',
            json.dumps([
                "unit_ob", "tab-dashboard", "tab-tasks", "tab-todo",
                "tab-journal", "tab-kebersihan", "tab-sapaais", "tab-mutabaah", "tab-evaluasi"
            ])
        ),
        (
            'koordinator_gardener',
            'Koordinator Gardener',
            'Penanggung jawab kebersihan taman/Ecopark, kebun buah, budidaya sayuran, dan ternak.',
            json.dumps([
                "unit_gardener", "tab-dashboard", "tab-tasks", "tab-todo",
                "tab-journal", "tab-kebersihan", "tab-evaluasi"
            ])
        ),
        (
            'koordinator_security',
            'Koordinator Security',
            'Penanggung jawab keamanan gerbang, perimeter kampus, ketertiban lalu lintas, dan pos jaga.',
            json.dumps([
                "unit_security", "tab-dashboard", "tab-tasks", "tab-todo",
                "tab-journal", "tab-mutabaah", "tab-evaluasi"
            ])
        ),
        (
            'pic_sarpras',
            'PIC Perbaikan Sarpras',
            'Teknisi sarana & prasarana (sipil, listrik, plumbing, AC, mebeler, dan perbaikan fisik fasilitas).',
            json.dumps([
                "unit_sarpras", "tab-dashboard", "tab-tasks", "tab-todo",
                "tab-journal", "tab-kebersihan", "tab-sapaais", "tab-pengadaan", "tab-evaluasi"
            ])
        ),
        (
            'pic_pengadaan',
            'PIC Pengadaan & Logistik',
            'Pengadaan barang, sparepart/material teknis perbaikan, pencatatan nota, dan logistik sarpras.',
            json.dumps([
                "unit_pengadaan", "tab-dashboard", "tab-pengadaan", "tab-tasks",
                "tab-todo", "tab-journal", "tab-evaluasi"
            ])
        )
    ]
    
    for r_code, r_name, r_desc, r_perms in default_roles:
        cur.execute('''
            INSERT OR IGNORE INTO ops_roles (role_code, role_name, description, permissions)
            VALUES (?, ?, ?, ?)
        ''', (r_code, r_name, r_desc, r_perms))
        # Update permissions if role already exists
        cur.execute('''
            UPDATE ops_roles SET role_name = ?, description = ?, permissions = ?
            WHERE role_code = ?
        ''', (r_name, r_desc, r_perms, r_code))
    con.commit()
    
    # Pre-seed User Awal jika belum ada
    default_users = [
        (
            'admin',
            generate_password_hash('password123'),
            'Mr Slam',
            'manager',
            'ALL',
            None,
            '6287809199096'
        ),
        (
            'koord_it',
            generate_password_hash('password123'),
            'Koordinator IT',
            'koordinator_it',
            'IT',
            None,
            ''
        ),
        (
            'koord_ob',
            generate_password_hash('password123'),
            'Koordinator OB',
            'koordinator_ob',
            'OB',
            None,
            ''
        ),
        (
            'koord_gardener',
            generate_password_hash('password123'),
            'Koordinator Gardener',
            'koordinator_gardener',
            'GARDENER',
            'TAMAN_ECOPARK_TERNAK',
            ''
        ),
        (
            'koord_security',
            generate_password_hash('password123'),
            'Koordinator Security',
            'koordinator_security',
            'SECURITY',
            None,
            ''
        ),
        (
            'pic_sarpras',
            generate_password_hash('password123'),
            'PIC Perbaikan Sarpras',
            'pic_sarpras',
            'SARPRAS',
            'SIPIL_LISTRIK_MEBELER',
            ''
        ),
        (
            'pic_pengadaan',
            generate_password_hash('password123'),
            'PIC Pengadaan',
            'pic_pengadaan',
            'PENGADAAN',
            'PENGADAAN_LOGISTIK',
            ''
        ),
    ]
    
    for u_name, u_pass, u_full, u_role, u_unit, u_sub, u_wa in default_users:
        cur.execute('''
            INSERT OR IGNORE INTO ops_users (username, password_hash, nama_lengkap, role_code, unit_code, sub_scope, no_wa)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (u_name, u_pass, u_full, u_role, u_unit, u_sub, u_wa))
    con.commit()
    con.close()

# Jalankan inisialisasi tabel saat modul di-import
init_ops_auth_db()

# ==================== DECORATORS ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'ops_user_id' not in session:
            # Cegah redirect ke localhost 127.0.0.1: gunakan path relatif
            next_path = request.full_path if request.query_string else request.path
            if not next_path or next_path.startswith('//') or '127.0.0.1' in next_path or 'localhost' in next_path:
                next_path = '/'
            return redirect(url_for('ops_auth.login', next=next_path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'ops_user_id' not in session:
                return redirect(url_for('ops_auth.login'))
            user_role = session.get('ops_role_code', '')
            if user_role not in allowed_roles and user_role != 'manager':
                return jsonify({"error": "Akses ditolak. Anda tidak memiliki izin."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== TEMPLATES (SPLIT SCREEN SAS-ANNAHL STYLE) ====================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Masuk - An Nahl Ops Command Center</title>
    <link rel="icon" type="image/png" href="/static/favicon.png?v=20260930">
    <link rel="apple-touch-icon" href="/static/logo-icon.png?v=20260930">
    <link rel="stylesheet" href="/static/tailwind.min.css?v=20260930_taste">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif; }
        .brand-logo-login {
            height: 76px !important;
            max-height: 80px !important;
            width: auto !important;
            max-width: 140px !important;
            object-fit: contain !important;
            display: block !important;
        }
        .brand-logo-mobile {
            height: 52px !important;
            max-height: 56px !important;
            width: auto !important;
            max-width: 100px !important;
            object-fit: contain !important;
            display: block !important;
        }
    </style>
</head>
<body class="bg-slate-50 antialiased selection:bg-emerald-600/10 selection:text-emerald-900">
<div class="min-h-screen flex">
  
  <!-- SISI KIRI (DESKTOP BRANDING HERO IDENTIK SAS-ANNAHL) -->
  <div class="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-emerald-950 items-center justify-center">
    <div class="absolute inset-0 opacity-[0.07]" style="background-image:url('data:image/svg+xml,%3Csvg width=%2260%22 height=%2260%22 viewBox=%220 0 60 60%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cg fill='none' stroke='%23ffffff' stroke-width='1'%3E%3Cpath d='M30 2 L58 30 L30 58 L2 30 Z'/%3E%3Ccircle cx='30' cy='30' r='12'/%3E%3C/g%3E%3C/svg%3E');"></div>
    <div class="absolute -top-24 -left-24 w-96 h-96 bg-emerald-800/40 rounded-full blur-3xl"></div>
    <div class="absolute bottom-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl"></div>
    
    <div class="relative z-10 px-12 text-center max-w-lg">
      <div class="inline-flex items-center justify-center p-3 rounded-2xl bg-white shadow-xl mb-6 border border-white/20">
        <img src="/static/logo.png?v=20260930_opt" alt="An Nahl" class="brand-logo-login" style="height:76px;width:auto;max-width:140px;max-height:80px;object-fit:contain;display:block;">
      </div>
      <h1 class="text-white font-bold text-3xl leading-snug">An Nahl Ops<br><span class="text-emerald-300 font-semibold text-2xl">Command Center</span></h1>
      <p class="text-emerald-200/90 mt-4 text-sm leading-relaxed max-w-md mx-auto">Portal komando terpadu IT, Sarpras, dan General Affairs — koordinasi 4 unit lapangan (OB, Gardener, Security, IT), pemantauan server, dan mutabaah ibadah.</p>
      
      <div class="mt-9 flex items-center justify-center gap-6 text-emerald-200/70 text-xs font-medium">
        <span><i class="fa-solid fa-tower-broadcast text-emerald-400 mr-1.5"></i> Uptime Monitor</span>
        <span><i class="fa-solid fa-users-gear text-emerald-400 mr-1.5"></i> Multi-Unit Koordinator</span>
        <span><i class="fa-solid fa-shield-halved text-emerald-400 mr-1.5"></i> Akses Terkendali</span>
      </div>
    </div>
    <div class="absolute bottom-5 inset-x-0 text-center text-emerald-300/40 text-[11px] z-10">&copy; 2026 An Nahl Islamic School &bull; IT & General Affairs Department</div>
  </div>

  <!-- SISI KANAN (FORM LOGIN) -->
  <div class="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10 bg-slate-50">
    <div class="w-full max-w-md">
      
      <!-- Mobile Logo Header -->
      <div class="lg:hidden flex flex-col items-center mb-6">
        <div class="inline-flex items-center justify-center p-2 rounded-2xl bg-white shadow-md mb-2.5 border border-slate-200/60">
          <img src="/static/logo.png?v=20260930_opt" alt="An Nahl" class="brand-logo-mobile" style="height:52px;width:auto;max-width:100px;max-height:56px;object-fit:contain;display:block;">
        </div>
        <h1 class="font-bold text-xl text-slate-800">An Nahl Ops</h1>
        <p class="text-xs text-emerald-700 font-semibold">Command Center IT & General Affairs</p>
      </div>

      <!-- Card Container -->
      <div class="bg-white rounded-3xl shadow-xl shadow-slate-200/60 border border-slate-100 p-8 sm:p-10">
        <div class="mb-7">
          <p class="text-xs font-semibold tracking-widest text-emerald-700 uppercase mb-1">Selamat Datang Kembali</p>
          <h2 class="text-2xl font-bold text-slate-800">Masuk ke Command Center</h2>
          <p class="text-sm text-slate-500 mt-1.5">Silakan login untuk mengakses dashboard operasional An Nahl Ops.</p>
        </div>

        {% if error %}
        <div class="mb-6 flex items-center gap-2.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium px-4 py-3 rounded-2xl animate-in fade-in duration-200">
          <i class="fa-solid fa-circle-exclamation text-rose-500 text-sm shrink-0"></i>
          <span>{{ error }}</span>
        </div>
        {% endif %}

        <form method="POST" action="/login" class="space-y-5">
          <input type="hidden" name="next" value="{{ next_url }}">
          
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Username</label>
            <div class="relative">
              <i class="fa-solid fa-user absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
              <input name="username" id="username" placeholder="Masukkan username (contoh: admin atau koord_ob)" required autofocus autocomplete="username"
                     class="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-2xl focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 outline-none transition bg-slate-50 focus:bg-white text-slate-800 placeholder-slate-400">
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wide">Password</label>
            </div>
            <div class="relative">
              <i class="fa-solid fa-lock absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
              <input type="password" id="pwfield" name="password" placeholder="Masukkan password" required autocomplete="current-password"
                     class="w-full pl-11 pr-12 py-3.5 text-sm border border-slate-200 rounded-2xl focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 outline-none transition bg-slate-50 focus:bg-white text-slate-800 placeholder-slate-400">
              <button type="button" onclick="const f=document.getElementById('pwfield');f.type=f.type==='password'?'text':'password'" 
                      class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-emerald-700 transition" title="Lihat password">
                <i class="fa-regular fa-eye"></i>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between text-xs pt-1">
            <label class="flex items-center cursor-pointer select-none text-slate-600 hover:text-slate-800">
              <input id="remember_me" name="remember_me" type="checkbox" checked
                     class="h-4 w-4 rounded border-slate-300 text-emerald-700 focus:ring-emerald-500 accent-emerald-700">
              <span class="ml-2 font-medium">Ingat sesi saya</span>
            </label>
            <span class="font-semibold text-emerald-700/80">Sekolah Islam An Nahl</span>
          </div>

          <button type="submit" 
                  class="w-full py-4 bg-emerald-800 hover:bg-emerald-900 text-white font-bold text-sm rounded-2xl shadow-lg shadow-emerald-800/25 hover:shadow-emerald-800/35 transition-all active:scale-[0.98] flex items-center justify-center gap-2">
            <span>Masuk ke Dashboard</span>
            <i class="fa-solid fa-arrow-right-to-bracket text-xs"></i>
          </button>
        </form>

        <div class="mt-7 pt-5 border-t border-slate-100 space-y-2">
          <p class="text-[11px] font-semibold text-slate-500 text-center uppercase tracking-wider">Unit Koordinator Terdaftar:</p>
          <div class="flex flex-wrap justify-center gap-1.5 text-[10px]">
            <span class="px-2.5 py-1 rounded-xl bg-slate-100 text-slate-700 font-semibold border border-slate-200">IT</span>
            <span class="px-2.5 py-1 rounded-xl bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">Office Boy</span>
            <span class="px-2.5 py-1 rounded-xl bg-amber-50 text-amber-800 font-semibold border border-amber-200">Gardener</span>
            <span class="px-2.5 py-1 rounded-xl bg-sky-50 text-sky-800 font-semibold border border-sky-200">Security</span>
            <span class="px-2.5 py-1 rounded-xl bg-indigo-50 text-indigo-800 font-semibold border border-indigo-200">Sarpras</span>
            <span class="px-2.5 py-1 rounded-xl bg-rose-50 text-rose-800 font-semibold border border-rose-200">Pengadaan</span>
          </div>
        </div>

      </div>

      <div class="mt-6 text-center text-xs text-slate-400">
        <i class="fa-solid fa-circle-question mr-1"></i> Bantuan kendala akses? Hubungi Admin IT An Nahl
      </div>

    </div>
  </div>
</div>
</body>
</html>
"""

# ==================== AUTH ROUTES ====================
@ops_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'ops_user_id' in session:
        return redirect('/')

    error = None
    next_url = request.args.get('next', '/')
    # Sanitize next_url agar tidak redirect ke localhost / domain asing
    if not next_url or not next_url.startswith('/') or next_url.startswith('//') or '127.0.0.1' in next_url or 'localhost' in next_url:
        next_url = '/'

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        raw_next = request.form.get('next', '/') or '/'
        if not raw_next or not raw_next.startswith('/') or raw_next.startswith('//') or '127.0.0.1' in raw_next or 'localhost' in raw_next:
            next_url = '/'
        else:
            next_url = raw_next

        if not username or not password:
            error = "Username dan password wajib diisi."
        else:
            con = get_ops_db()
            user = con.execute('''
                SELECT u.*, r.role_name, r.permissions
                FROM ops_users u
                JOIN ops_roles r ON u.role_code = r.role_code
                WHERE u.username = ? AND u.is_active = 1
            ''', (username,)).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Update last login
                con.execute('UPDATE ops_users SET last_login = ? WHERE id = ?', 
                            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user['id']))
                con.commit()
                con.close()

                # Set session
                session.permanent = True
                session['ops_user_id'] = user['id']
                session['ops_username'] = user['username']
                session['ops_nama'] = user['nama_lengkap']
                session['ops_role_code'] = user['role_code']
                session['ops_role_name'] = user['role_name']
                session['ops_unit_code'] = user['unit_code']
                session['ops_sub_scope'] = user['sub_scope']
                session['ops_permissions'] = json.loads(user['permissions'])

                return redirect(next_url)
            else:
                con.close()
                error = "Username atau password salah, atau akun tidak aktif."

    return render_template_string(LOGIN_HTML, error=error, next_url=next_url)

@ops_auth_bp.route('/logout')
def logout():
    session.pop('ops_user_id', None)
    session.pop('ops_username', None)
    session.pop('ops_nama', None)
    session.pop('ops_role_code', None)
    session.pop('ops_role_name', None)
    session.pop('ops_unit_code', None)
    session.pop('ops_sub_scope', None)
    session.pop('ops_permissions', None)
    return redirect(url_for('ops_auth.login'))

# ==================== USER MANAGEMENT API ====================
@ops_auth_bp.route('/api/ops/users', methods=['GET'])
@login_required
@role_required(['manager'])
def api_get_users():
    con = get_ops_db()
    rows = con.execute('''
        SELECT u.id, u.username, u.nama_lengkap, u.role_code, u.unit_code,
               u.sub_scope, u.no_wa, u.is_active, u.created_at, u.last_login,
               r.role_name
        FROM ops_users u
        LEFT JOIN ops_roles r ON u.role_code = r.role_code
        ORDER BY u.id ASC
    ''').fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@ops_auth_bp.route('/api/ops/users', methods=['POST'])
@login_required
@role_required(['manager'])
def api_add_user():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    nama_lengkap = data.get('nama_lengkap', '').strip()
    role_code = data.get('role_code', '').strip()
    unit_code = data.get('unit_code', '').strip()
    sub_scope = data.get('sub_scope', '').strip() or None
    no_wa = data.get('no_wa', '').strip()

    if not username or not password or not nama_lengkap or not role_code or not unit_code:
        return jsonify({"error": "Semua field bertanda * wajib diisi"}), 400

    con = get_ops_db()
    existing = con.execute('SELECT id FROM ops_users WHERE username = ?', (username,)).fetchone()
    if existing:
        con.close()
        return jsonify({"error": f"Username '{username}' sudah digunakan."}), 400

    pwd_hash = generate_password_hash(password)
    cur = con.cursor()
    cur.execute('''
        INSERT INTO ops_users (username, password_hash, nama_lengkap, role_code, unit_code, sub_scope, no_wa)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, pwd_hash, nama_lengkap, role_code, unit_code, sub_scope, no_wa))
    con.commit()
    new_id = cur.lastrowid
    con.close()

    return jsonify({"success": True, "message": "User berhasil ditambahkan", "id": new_id}), 201

@ops_auth_bp.route('/api/ops/users/<int:user_id>/edit', methods=['POST'])
@login_required
@role_required(['manager'])
def api_edit_user(user_id):
    data = request.get_json() or {}
    nama_lengkap = data.get('nama_lengkap', '').strip()
    role_code = data.get('role_code', '').strip()
    unit_code = data.get('unit_code', '').strip()
    sub_scope = data.get('sub_scope', '').strip() or None
    no_wa = data.get('no_wa', '').strip()

    if not nama_lengkap or not role_code or not unit_code:
        return jsonify({"error": "Nama lengkap, role, dan unit wajib diisi"}), 400

    con = get_ops_db()
    con.execute('''
        UPDATE ops_users
        SET nama_lengkap = ?, role_code = ?, unit_code = ?, sub_scope = ?, no_wa = ?
        WHERE id = ?
    ''', (nama_lengkap, role_code, unit_code, sub_scope, no_wa, user_id))
    con.commit()
    con.close()

    return jsonify({"success": True, "message": "Data user berhasil diperbarui"})

@ops_auth_bp.route('/api/ops/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required(['manager'])
def api_toggle_user_status(user_id):
    con = get_ops_db()
    u = con.execute('SELECT is_active, username FROM ops_users WHERE id = ?', (user_id,)).fetchone()
    if not u:
        con.close()
        return jsonify({"error": "User tidak ditemukan"}), 404

    if u['username'] == 'admin':
        con.close()
        return jsonify({"error": "Akun admin utama tidak boleh dinonaktifkan."}), 400

    new_status = 0 if u['is_active'] == 1 else 1
    con.execute('UPDATE ops_users SET is_active = ? WHERE id = ?', (new_status, user_id))
    con.commit()
    con.close()

    status_str = "diaktifkan" if new_status == 1 else "dinonaktifkan"
    return jsonify({"success": True, "is_active": new_status, "message": f"User berhasil {status_str}."})

@ops_auth_bp.route('/api/ops/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required(['manager'])
def api_reset_user_password(user_id):
    data = request.get_json() or {}
    new_password = data.get('new_password', '').strip()

    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password baru minimal 6 karakter."}), 400

    pwd_hash = generate_password_hash(new_password)
    con = get_ops_db()
    con.execute('UPDATE ops_users SET password_hash = ? WHERE id = ?', (pwd_hash, user_id))
    con.commit()
    con.close()

    return jsonify({"success": True, "message": "Password user berhasil direset."})

# ==================== ROLE MANAGEMENT API ====================
@ops_auth_bp.route('/api/ops/roles', methods=['GET'])
@login_required
@role_required(['manager'])
def api_get_roles():
    con = get_ops_db()
    rows = con.execute('SELECT * FROM ops_roles ORDER BY id ASC').fetchall()
    con.close()
    
    result = []
    for r in rows:
        item = dict(r)
        try:
            item['permissions'] = json.loads(item['permissions'])
        except Exception:
            item['permissions'] = []
        result.append(item)
    return jsonify(result)

@ops_auth_bp.route('/api/ops/roles/<role_code>/permissions', methods=['POST'])
@login_required
@role_required(['manager'])
def api_update_role_permissions(role_code):
    data = request.get_json() or {}
    permissions = data.get('permissions', [])

    if not isinstance(permissions, list):
        return jsonify({"error": "Permissions harus berupa array"}), 400

    con = get_ops_db()
    con.execute('UPDATE ops_roles SET permissions = ? WHERE role_code = ?', (json.dumps(permissions), role_code))
    con.commit()
    con.close()

    return jsonify({"success": True, "message": f"Izin akses role '{role_code}' berhasil diperbarui."})
