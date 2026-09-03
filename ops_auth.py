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
            return redirect(url_for('ops_auth.login', next=request.url))
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

# ==================== TEMPLATES ====================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="id" class="bg-slate-950">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - An Nahl Ops Command Center</title>
    <link rel="stylesheet" href="/static/tailwind.min.css?v=20260902_login_fix2">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-center items-center py-10 sm:py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 text-slate-100 overflow-y-auto">
    
    <div class="w-full max-w-md my-auto space-y-6">
        <!-- Logo & Header -->
        <div class="text-center pt-2">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 shadow-xl shadow-emerald-950/50 mb-3.5">
                <i class="fa-solid fa-school text-3xl"></i>
            </div>
            <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">An Nahl Ops</h2>
            <p class="mt-1.5 text-xs sm:text-sm text-emerald-300 font-medium">Command Center IT & General Affairs</p>
            <p class="mt-0.5 text-xs text-slate-400">Portal Kolaborasi & Pendelegasian Tim Koordinator</p>
        </div>

        <div class="bg-slate-900/80 backdrop-blur-md py-8 px-6 sm:px-10 shadow-2xl rounded-2xl border border-slate-800">
            
            {% if error %}
            <div class="mb-5 p-3.5 rounded-xl bg-rose-950/80 border border-rose-800/80 text-rose-200 text-xs flex items-center space-x-3">
                <i class="fa-solid fa-circle-exclamation text-base text-rose-400 shrink-0"></i>
                <span>{{ error }}</span>
            </div>
            {% endif %}

            <form class="space-y-5" action="/login" method="POST">
                <input type="hidden" name="next" value="{{ next_url }}">
                
                <div>
                    <label for="username" class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Username</label>
                    <div class="relative rounded-xl shadow-sm">
                        <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <i class="fa-solid fa-user"></i>
                        </div>
                        <input type="text" id="username" name="username" required autofocus autocomplete="username"
                               placeholder="Contoh: admin atau koord_ob"
                               class="w-full pl-10 pr-4 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition">
                    </div>
                </div>

                <div>
                    <div class="flex items-center justify-between mb-2">
                        <label for="password" class="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Password</label>
                    </div>
                    <div class="relative rounded-xl shadow-sm">
                        <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <i class="fa-solid fa-lock"></i>
                        </div>
                        <input type="password" id="password" name="password" required autocomplete="current-password"
                               placeholder="••••••••"
                               class="w-full pl-10 pr-10 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition">
                        <button type="button" onclick="togglePasswordVisibility()" class="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200">
                            <i class="fa-solid fa-eye" id="toggle-pwd-icon"></i>
                        </button>
                    </div>
                </div>

                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <input id="remember_me" name="remember_me" type="checkbox" checked
                               class="h-4 w-4 rounded bg-slate-800 border-slate-700 text-emerald-600 focus:ring-emerald-500">
                        <label for="remember_me" class="ml-2 block text-xs text-slate-400">Ingat sesi saya</label>
                    </div>
                    <span class="text-xs text-emerald-400 font-medium">An Nahl Islamic School</span>
                </div>

                <div>
                    <button type="submit"
                            class="w-full flex justify-center items-center space-x-2 py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-emerald-500 transition active:scale-95">
                        <i class="fa-solid fa-right-to-bracket"></i>
                        <span>Masuk ke Dashboard</span>
                    </button>
                </div>
            </form>

            <div class="mt-6 pt-5 border-t border-slate-800/80">
                <div class="text-[11px] text-slate-400 text-center space-y-1.5">
                    <p class="font-semibold text-slate-300">Struktur Unit Koordinator Terdaftar:</p>
                    <div class="flex flex-wrap justify-center gap-1.5 pt-1 text-[10px]">
                        <span class="px-2 py-0.5 rounded-full bg-slate-800 text-emerald-300 border border-slate-700">IT</span>
                        <span class="px-2 py-0.5 rounded-full bg-slate-800 text-teal-300 border border-slate-700">Office Boy</span>
                        <span class="px-2 py-0.5 rounded-full bg-slate-800 text-amber-300 border border-slate-700">Gardener</span>
                        <span class="px-2 py-0.5 rounded-full bg-slate-800 text-blue-300 border border-slate-700">Security</span>
                    </div>
                </div>
            </div>

        </div>

        <p class="mt-6 text-center text-xs text-slate-500">
            &copy; 2026 An Nahl Islamic School &bull; IT & General Affairs Department
        </p>
    </div>

    <script>
        function togglePasswordVisibility() {
            const pwd = document.getElementById('password');
            const icon = document.getElementById('toggle-pwd-icon');
            if (pwd.type === 'password') {
                pwd.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                pwd.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }
    </script>
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

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        next_url = request.form.get('next', '/') or '/'

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
