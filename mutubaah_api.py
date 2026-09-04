import sqlite3
import datetime
from flask import Blueprint, request, jsonify

mutubaah_bp = Blueprint('mutubaah', __name__)

DB_PATH = '/home/ametriyadhi/sas-annahl/database.sqlite'

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    # 1. Pastikan tabel mutubaah_laporan ada
    con.execute('''
        CREATE TABLE IF NOT EXISTS mutubaah_laporan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT DEFAULT CURRENT_DATE,
            nama TEXT,
            usia INTEGER,
            tilawah TEXT,
            khatam_ke INTEGER DEFAULT 0,
            faham_sholat TEXT,
            doa_orang_tua INTEGER DEFAULT 0,
            doa_nabi_yunus INTEGER DEFAULT 0,
            hauqolah INTEGER DEFAULT 0,
            hasballah INTEGER DEFAULT 0,
            sholawat INTEGER DEFAULT 0,
            total_dzikir INTEGER GENERATED ALWAYS AS (
                doa_orang_tua + doa_nabi_yunus + hauqolah + hasballah + sholawat
            ) STORED,
            unit TEXT DEFAULT 'UMUM',
            user_id INTEGER,
            jabatan TEXT DEFAULT 'Pimpinan',
            no_wa TEXT,
            created_at DATETIME
        )
    ''')
    
    # 2. Periksa migrasi kolom bila tabel dibuat dari versi lama
    cur = con.cursor()
    cur.execute('PRAGMA table_info(mutubaah_laporan)')
    cols = [c[1] for c in cur.fetchall()]
    new_cols = [
        ('unit', 'TEXT DEFAULT "UMUM"'),
        ('user_id', 'INTEGER'),
        ('jabatan', 'TEXT DEFAULT "Pimpinan"'),
        ('no_wa', 'TEXT'),
        ('created_at', 'DATETIME')
    ]
    for col_name, col_type in new_cols:
        if col_name not in cols:
            con.execute(f'ALTER TABLE mutubaah_laporan ADD COLUMN {col_name} {col_type}')

    # 3. Pastikan tabel peserta & preferensi pengingat ada
    con.execute('''
        CREATE TABLE IF NOT EXISTS mutabaah_peserta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            unit TEXT NOT NULL,
            jabatan TEXT,
            no_wa TEXT UNIQUE,
            user_id INTEGER,
            is_active INTEGER DEFAULT 1,
            remind_1730 INTEGER DEFAULT 1,
            remind_tilawah_all INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    con.commit()
    con.close()

init_db()

def lookup_user_profile(no_wa=None, nama=None):
    """Cari profil unit dan jabatan dari mutabaah_peserta, ops_users, atau users."""
    con = get_db()
    cur = con.cursor()
    profile = {"unit": "UMUM", "jabatan": "Pimpinan", "user_id": None, "nama": nama}
    
    # Cek di mutabaah_peserta
    if no_wa:
        clean_wa = no_wa.replace('@s.whatsapp.net', '').replace('+', '').strip()
        row = cur.execute('SELECT * FROM mutabaah_peserta WHERE no_wa LIKE ?', (f'%{clean_wa}%',)).fetchone()
        if row:
            con.close()
            return {"unit": row["unit"], "jabatan": row["jabatan"], "user_id": row["user_id"], "nama": row["nama"]}

    if nama:
        row = cur.execute('SELECT * FROM mutabaah_peserta WHERE nama LIKE ?', (f'%{nama.strip()}%',)).fetchone()
        if row:
            con.close()
            return {"unit": row["unit"], "jabatan": row["jabatan"], "user_id": row["user_id"], "nama": row["nama"]}

    # Fallback ke ops_users
    if nama:
        row = cur.execute('SELECT * FROM ops_users WHERE nama_lengkap LIKE ?', (f'%{nama.strip()}%',)).fetchone()
        if row:
            con.close()
            return {"unit": row["unit_code"], "jabatan": row["role_code"], "user_id": row["id"], "nama": row["nama_lengkap"]}

    con.close()
    return profile

@mutubaah_bp.route("/api/mutubaah/laporan", methods=["GET"])
def get_laporan():
    try:
        limit = int(request.args.get("limit", 100))
        nama = request.args.get("nama")
        unit = request.args.get("unit")
        from_date = request.args.get("from")
        to_date = request.args.get("to")
        user_id = request.args.get("user_id")

        query = "SELECT * FROM mutubaah_laporan WHERE 1=1"
        params = []

        if nama and nama.strip() and nama != "all":
            query += " AND nama LIKE ?"
            params.append(f"%{nama.strip()}%")

        if unit and unit.strip() and unit != "all":
            query += " AND (unit = ? OR unit LIKE ?)"
            params.append(unit.strip())
            params.append(f"%{unit.strip()}%")

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if from_date:
            query += " AND tanggal >= ?"
            params.append(from_date)

        if to_date:
            query += " AND tanggal <= ?"
            params.append(to_date)

        query += " ORDER BY tanggal DESC, id DESC LIMIT ?"
        params.append(limit)

        con = get_db()
        rows = con.execute(query, params).fetchall()
        con.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mutubaah_bp.route("/api/mutubaah/laporan", methods=["POST"])
def add_laporan():
    try:
        data = request.get_json() or {}
        nama = data.get("nama", "").strip()
        unit = data.get("unit")
        jabatan = data.get("jabatan")
        no_wa = data.get("no_wa")
        user_id = data.get("user_id")
        tanggal = data.get("tanggal") or datetime.date.today().isoformat()

        # Lookup jika unit atau jabatan belum terisi
        if not unit or not jabatan:
            prof = lookup_user_profile(no_wa=no_wa, nama=nama)
            unit = unit or prof.get("unit") or "UMUM"
            jabatan = jabatan or prof.get("jabatan") or "Pimpinan"
            user_id = user_id or prof.get("user_id")
            if not nama and prof.get("nama"):
                nama = prof.get("nama")

        if not nama:
            nama = "Pimpinan"

        con = get_db()
        con.execute('''
            INSERT INTO mutubaah_laporan (
                tanggal, nama, unit, jabatan, no_wa, user_id,
                usia, tilawah, khatam_ke, faham_sholat,
                doa_orang_tua, doa_nabi_yunus, hauqolah, hasballah, sholawat, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        ''', (
            tanggal,
            nama,
            unit,
            jabatan,
            no_wa,
            user_id,
            data.get("usia", 40),
            data.get("tilawah", data.get("juz", "-")),
            data.get("khatam_ke", 0),
            data.get("faham_sholat", "-"),
            data.get("dzikir", {}).get("doa_orang_tua", data.get("doa_orang_tua", 0)),
            data.get("dzikir", {}).get("doa_nabi_yunus", data.get("doa_nabi_yunus", 0)),
            data.get("dzikir", {}).get("hauqolah", data.get("hauqolah", 0)),
            data.get("dzikir", {}).get("hasballah", data.get("hasballah", 0)),
            data.get("dzikir", {}).get("sholawat", data.get("sholawat", 0))
        ))
        con.commit()
        con.close()
        return jsonify({"success": True, "message": "Laporan mutabaah berhasil disimpan", "nama": nama, "unit": unit}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mutubaah_bp.route("/api/mutubaah/peserta", methods=["GET"])
def get_peserta():
    try:
        con = get_db()
        rows = con.execute('''
            SELECT id, nama, unit, jabatan, no_wa, is_active, remind_1730, remind_tilawah_all
            FROM mutabaah_peserta
            ORDER BY unit ASC, nama ASC
        ''').fetchall()
        
        # Juga ambil nama & unit yang pernah kirim laporan namun belum di mutabaah_peserta
        other_users = con.execute('''
            SELECT DISTINCT nama, unit, jabatan FROM mutubaah_laporan 
            WHERE nama NOT IN (SELECT nama FROM mutabaah_peserta)
        ''').fetchall()
        
        con.close()
        
        peserta_list = [dict(r) for r in rows]
        for u in other_users:
            peserta_list.append({
                "id": None,
                "nama": u["nama"],
                "unit": u["unit"] or "UMUM",
                "jabatan": u["jabatan"] or "Civitas",
                "no_wa": "-",
                "is_active": 1,
                "remind_1730": 0
            })

        return jsonify(peserta_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mutubaah_bp.route("/api/mutubaah/stats", methods=["GET"])
def get_stats():
    try:
        today = datetime.date.today().isoformat()
        con = get_db()
        
        # Laporan hari ini
        today_count = con.execute("SELECT COUNT(*) FROM mutubaah_laporan WHERE tanggal = ?", (today,)).fetchone()[0]
        
        # Total akumulasi dzikir
        total_dzikir_all = con.execute("SELECT COALESCE(SUM(total_dzikir), 0) FROM mutubaah_laporan").fetchone()[0]
        
        # Peserta aktif
        total_peserta = con.execute("SELECT COUNT(DISTINCT nama) FROM mutubaah_laporan").fetchone()[0]
        
        # Unit breakdown hari ini
        unit_breakdown = con.execute('''
            SELECT unit, COUNT(*) as count 
            FROM mutubaah_laporan 
            WHERE tanggal = ? 
            GROUP BY unit
        ''', (today,)).fetchall()

        # 5 Peserta paling istiqomah (total laporan)
        top_istiqomah = con.execute('''
            SELECT nama, unit, COUNT(*) as total_laporan, MAX(tanggal) as last_date, MAX(khatam_ke) as khatam
            FROM mutubaah_laporan
            GROUP BY nama, unit
            ORDER BY total_laporan DESC
            LIMIT 5
        ''').fetchall()
        
        con.close()
        return jsonify({
            "today": today,
            "today_reports": today_count,
            "total_dzikir": total_dzikir_all,
            "total_peserta": total_peserta,
            "units_today": [dict(r) for r in unit_breakdown],
            "top_istiqomah": [dict(r) for r in top_istiqomah]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== PETUGAS LOGS ENDPOINT ==========
MUTABAAH_LOGS_PATH = "/home/ametriyadhi/mutabaah-wa-bot/mutabaah_logs.json"

@mutubaah_bp.route("/api/mutubaah/petugas", methods=["GET"])
def get_petugas_logs():
    try:
        limit = int(request.args.get("limit", 100))
        import json, os
        
        if not os.path.exists(MUTABAAH_LOGS_PATH):
            return jsonify([])
        
        with open(MUTABAAH_LOGS_PATH, 'r') as f:
            logs = json.load(f)
        
        # Filter only petugas logs (exclude personal mutabaah)
        logs = [l for l in logs if l.get('type') not in ['mutubaah_personal', 'mutabaah_personal']]
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        logs = logs[:limit]
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

