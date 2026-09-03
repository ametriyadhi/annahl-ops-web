import sqlite3
from flask import Blueprint, request, jsonify

mutubaah_bp = Blueprint('mutubaah', __name__)

DB_PATH = '/home/ametriyadhi/sas-annahl/database.sqlite'

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
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
            ) STORED
        )
    ''')
    con.commit()
    con.close()

init_db()

@mutubaah_bp.route("/api/mutubaah/laporan", methods=["GET"])
def get_laporan():
    try:
        limit = int(request.args.get("limit", 50))
        con = get_db()
        rows = con.execute("SELECT * FROM mutubaah_laporan ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        con.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mutubaah_bp.route("/api/mutubaah/laporan", methods=["POST"])
def add_laporan():
    try:
        data = request.get_json()
        con = get_db()
        con.execute('''
            INSERT INTO mutubaah_laporan (nama, usia, tilawah, khatam_ke, faham_sholat,
                doa_orang_tua, doa_nabi_yunus, hauqolah, hasballah, sholawat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get("nama"), data.get("usia"), data.get("tilawah", data.get("juz", "-")), data.get("khatam_ke", 0),
            data.get("faham_sholat"),
            data.get("dzikir", {}).get("doa_orang_tua", 0),
            data.get("dzikir", {}).get("doa_nabi_yunus", 0),
            data.get("dzikir", {}).get("hauqolah", 0),
            data.get("dzikir", {}).get("hasballah", 0),
            data.get("dzikir", {}).get("sholawat", 0),
        ))
        con.commit()
        con.close()
        return jsonify({"success": True, "message": "Laporan berhasil disimpan"}), 201
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

        # Sort by timestamp desc
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        logs = logs[:limit]
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

