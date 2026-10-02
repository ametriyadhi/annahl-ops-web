"""
Modul Analisa & Evaluasi Kinerja Personil (OB & Gardener)
An Nahl Ops Web Dashboard - note-umum.ametriyadhi.com
Dilengkapi dengan Filter Rentang Tanggal Dinamis & Target Sesi Pos Sesuai Masa Berlaku Unit
"""

import sqlite3
import json
import datetime
from collections import Counter, defaultdict
from typing import Dict, Any, List, Optional

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"
KEBERSIHAN_LOG_PATH = "/home/ametriyadhi/mutabaah-wa-bot/kebersihan_logs.json"
MUTABAAH_LOG_PATH = "/home/ametriyadhi/mutabaah-wa-bot/mutabaah_logs.json"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_evaluasi_tables():
    """Membuat tabel catatan evaluasi & pembinaan staf jika belum ada"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops_staff_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            petugas_name TEXT NOT NULL,
            unit_code TEXT NOT NULL,
            period_year INTEGER NOT NULL,
            period_month INTEGER NOT NULL,
            discipline_score REAL DEFAULT 0,
            late_count INTEGER DEFAULT 0,
            out_radius_count INTEGER DEFAULT 0,
            evaluation_status TEXT DEFAULT 'BAIK',
            supervisor_notes TEXT DEFAULT '',
            evaluated_by TEXT DEFAULT 'Mr Slam',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(petugas_name, period_year, period_month)
        )
    """)
    conn.commit()
    conn.close()

def get_evaluasi_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
    unit_filter: str = "ALL"
) -> Dict[str, Any]:
    """
    Menghitung analitik mendalam kinerja staf OB & Gardener dengan Target Sesi Adil per Unit
    mendukung filter rentang tanggal (start_date s.d. end_date).
    """
    init_evaluasi_tables()
    conn = get_db()
    cur = conn.cursor()

    # Tentukan rentang tanggal
    cur.execute("SELECT MIN(date), MAX(date) FROM ops_standby_logs")
    min_d, max_d = cur.fetchone()
    
    s_date: str = start_date or min_d or "2026-09-01"
    e_date: str = end_date or max_d or datetime.date.today().strftime("%Y-%m-%d")

    # Ambil catatan supervisi
    ref_date = datetime.date.today()
    try:
        dt_end = datetime.datetime.strptime(e_date, "%Y-%m-%d").date()
        cur_year = dt_end.year
        cur_month = dt_end.month
    except Exception:
        cur_year = ref_date.year
        cur_month = ref_date.month

    cur.execute("""
        SELECT * FROM ops_staff_evaluations
        WHERE period_year = ? AND period_month = ?
    """, (cur_year, cur_month))
    eval_records = {r["petugas_name"]: dict(r) for r in cur.fetchall()}

    # Hitung jumlah sesi operasional unik (date, session_type) per unit pada rentang tanggal ini
    gardener_names = {"Samad", "Pak Samad", "Amat", "Pak Amat", "Jimin", "Pak Jimin", "Nandi", "Pak Nandi", "Somad", "Pak Somad"}

    cur.execute("""
        SELECT DISTINCT date || '_' || session_type
        FROM ops_standby_logs
        WHERE date >= ? AND date <= ? AND unit_code = 'OB'
    """, (s_date, e_date))
    ob_sessions_count = len(cur.fetchall())

    cur.execute("""
        SELECT DISTINCT date || '_' || session_type
        FROM ops_standby_logs
        WHERE date >= ? AND date <= ?
          AND (unit_code LIKE '%garden%' OR petugas_name IN ('Samad', 'Amat', 'Jimin', 'Nandi', 'Somad'))
    """, (s_date, e_date))
    gardener_sessions_count = len(cur.fetchall())

    # Fallback minimal jika data rentang sempit
    if ob_sessions_count == 0:
        ob_sessions_count = 1
    if gardener_sessions_count == 0:
        gardener_sessions_count = 1

    # Query logs pada rentang tanggal yang dipilih
    cur.execute("""
        SELECT * FROM ops_standby_logs
        WHERE date >= ? AND date <= ?
        ORDER BY date ASC, checkin_time ASC
    """, (s_date, e_date))
    standby_rows = cur.fetchall()
    conn.close()

    # Load kebersihan logs
    kebersihan_counts = Counter()
    try:
        with open(KEBERSIHAN_LOG_PATH, "r", encoding="utf-8") as f:
            k_logs = json.load(f)
            for k in k_logs:
                nama = (k.get("nama") or "").strip()
                tgl = (k.get("tanggal") or k.get("date") or "")[:10]
                if nama and (not tgl or (tgl >= s_date and tgl <= e_date)):
                    kebersihan_counts[nama] += 1
    except Exception:
        pass

    personnel_data = defaultdict(lambda: {
        "nama": "",
        "unit": "OB",
        "total_checkin": 0,
        "tepat_waktu": 0,
        "terlambat": 0,
        "diluar_radius": 0,
        "minutes_diffs": [],
        "distances": [],
        "dates_active": set(),
        "pos_visited": Counter(),
        "late_details": [],
        "out_radius_details": []
    })

    for r in standby_rows:
        nama = (r["petugas_name"] or "").strip()
        if not nama or nama in ["Mr Slam", "H3RM4W4N"]:
            continue

        p = personnel_data[nama]
        p["nama"] = nama
        
        unit = r["unit_code"] or "OB"
        if nama in gardener_names or "garden" in unit.lower():
            p["unit"] = "GARDENER"
        else:
            p["unit"] = "OB"

        p["total_checkin"] += 1
        p["dates_active"].add(r["date"])
        p["pos_visited"][f"{r['point_code']} - {r['point_name']}"] += 1

        status = r["status"]
        min_diff = r["minutes_diff"] or 0
        dist = r["distance_meters"] or 0

        if status == "TEPAT_WAKTU":
            p["tepat_waktu"] += 1
        elif status == "TERLAMBAT":
            p["terlambat"] += 1
            p["minutes_diffs"].append(abs(min_diff))
            p["late_details"].append({
                "date": r["date"],
                "session": r["session_type"],
                "time": r["checkin_time"],
                "pos": r["point_name"],
                "minutes_late": abs(min_diff)
            })
        elif status == "DILUAR_RADIUS":
            p["diluar_radius"] += 1
            p["distances"].append(dist)
            p["out_radius_details"].append({
                "date": r["date"],
                "session": r["session_type"],
                "time": r["checkin_time"],
                "pos": r["point_name"],
                "distance_meters": dist
            })

    leaderboard = []
    total_checkins_all = 0
    total_missed_all = 0
    total_late_all = 0
    total_out_radius_all = 0
    total_on_time_all = 0
    total_target_sessions_all = 0

    for nama, p in personnel_data.items():
        if unit_filter != "ALL" and p["unit"] != unit_filter:
            continue

        tot = p["total_checkin"]
        if tot == 0:
            continue

        # Target Sesi Adil Berdasarkan Unit Masing-masing:
        # OB mengikuti jadwal operasional OB, Gardener mengikuti jadwal operasional Gardener
        target_sessions = gardener_sessions_count if p["unit"] == "GARDENER" else ob_sessions_count

        missed = max(0, target_sessions - tot)
        attendance_rate = min(100.0, round((tot / target_sessions) * 100, 1))

        total_checkins_all += tot
        total_missed_all += missed
        total_target_sessions_all += target_sessions
        total_on_time_all += p["tepat_waktu"]
        total_late_all += p["terlambat"]
        total_out_radius_all += p["diluar_radius"]

        on_time_pct = round((p["tepat_waktu"] / tot) * 100, 1)
        late_pct = round((p["terlambat"] / tot) * 100, 1)
        out_radius_pct = round((p["diluar_radius"] / tot) * 100, 1)

        avg_late_min = round(sum(p["minutes_diffs"]) / len(p["minutes_diffs"]), 1) if p["minutes_diffs"] else 0.0
        max_late_min = max(p["minutes_diffs"]) if p["minutes_diffs"] else 0

        avg_dist = round(sum(p["distances"]) / len(p["distances"]), 1) if p["distances"] else 0.0
        max_dist = round(max(p["distances"]), 1) if p["distances"] else 0.0

        # Formulasi Skor Disiplin:
        # 1. Kehadiran di Pos (50 Poin)
        score_att = (min(tot, target_sessions) / target_sessions) * 50.0

        # 2. Ketepatan Waktu Jam Hadir (30 Poin)
        score_punctuality = (p["tepat_waktu"] / tot) * 30.0 if tot else 0.0

        # 3. Kepatuhan Radius Pos Geofence (20 Poin)
        score_geofence = ((tot - p["diluar_radius"]) / tot) * 20.0 if tot else 0.0

        # Bonus Laporan Kebersihan Aktif: max 5 poin
        k_count = kebersihan_counts.get(nama, 0)
        bonus_k = min(k_count * 0.2, 5.0)

        total_score = round(score_att + score_punctuality + score_geofence + bonus_k, 1)
        total_score = max(0.0, min(100.0, total_score))

        # Kategori Status Evaluasi
        missed_ratio = missed / target_sessions
        if total_score >= 80 and missed_ratio <= 0.15 and late_pct <= 25:
            eval_category = "TELADAN"
            eval_badge = "🌟 Sangat Disiplin"
            badge_color = "emerald"
        elif total_score >= 65 and missed_ratio <= 0.30:
            eval_category = "BAIK"
            eval_badge = "🟢 Baik & Produktif"
            badge_color = "teal"
        elif total_score >= 50:
            eval_category = "CUKUP"
            eval_badge = "🟡 Cukup / Perlu Arahan"
            badge_color = "amber"
        else:
            eval_category = "PEMBINAAN"
            eval_badge = "🔴 Butuh Pembinaan Khusus"
            badge_color = "rose"

        # Rekomendasi Tindak Lanjut Otomatis
        recommendation = ""
        if missed_ratio >= 0.40:
            recommendation = f"Mangkir/tidak check-in sebanyak {missed} sesi dari {target_sessions} sesi ({attendance_rate}% kehadiran). Pos sering kosong! Perlu teguran tertulis."
        elif late_pct >= 40:
            recommendation = f"Sering terlambat ({late_pct}% sesi, rata-rata telat {avg_late_min} mnt). Perlu pembinaan jam tiba sesi pagi."
        elif out_radius_pct >= 30:
            recommendation = f"Check-in sering di luar titik pos ({out_radius_pct}% sesi, terjauh {max_dist}m). Wajibkan scan QR akrilik di meja pos."
        elif total_score >= 80:
            recommendation = f"Kehadiran dan kedisiplinan sangat baik ({tot}/{target_sessions} sesi, {attendance_rate}% hadir). Sangat layak diapresiasi."
        else:
            recommendation = f"Kehadiran {attendance_rate}%, keterlambatan {late_pct}%. Tingkatkan konsistensi check-in tepat waktu."

        saved_eval = eval_records.get(nama, {})
        supervisor_notes = saved_eval.get("supervisor_notes", "")

        leaderboard.append({
            "nama": nama,
            "unit": p["unit"],
            "target_sessions": target_sessions,
            "total_checkin": tot,
            "missed_checkin": missed,
            "attendance_rate": attendance_rate,
            "days_active": len(p["dates_active"]),
            "tepat_waktu": p["tepat_waktu"],
            "on_time_pct": on_time_pct,
            "terlambat": p["terlambat"],
            "late_pct": late_pct,
            "avg_late_min": avg_late_min,
            "max_late_min": max_late_min,
            "diluar_radius": p["diluar_radius"],
            "out_radius_pct": out_radius_pct,
            "avg_dist": avg_dist,
            "max_dist": max_dist,
            "kebersihan_count": k_count,
            "discipline_score": total_score,
            "eval_category": eval_category,
            "eval_badge": eval_badge,
            "badge_color": badge_color,
            "recommendation": recommendation,
            "supervisor_notes": supervisor_notes,
            "late_details": p["late_details"][-5:],
            "out_radius_details": p["out_radius_details"][-5:],
            "top_pos": [pos for pos, _ in p["pos_visited"].most_common(2)]
        })

    leaderboard.sort(key=lambda x: x["discipline_score"], reverse=True)

    top_missed = sorted([p for p in leaderboard if p["missed_checkin"] > 0], key=lambda x: (x["missed_checkin"], -x["attendance_rate"]), reverse=True)
    top_late = sorted([p for p in leaderboard if p["terlambat"] > 0], key=lambda x: (x["terlambat"], x["late_pct"]), reverse=True)
    top_out_radius = sorted([p for p in leaderboard if p["diluar_radius"] > 0], key=lambda x: (x["diluar_radius"], x["out_radius_pct"]), reverse=True)

    overall_attendance = round((total_checkins_all / total_target_sessions_all * 100), 1) if total_target_sessions_all else 0.0
    compliance_rate = round((total_on_time_all / total_checkins_all * 100), 1) if total_checkins_all else 0.0
    late_rate = round((total_late_all / total_checkins_all * 100), 1) if total_checkins_all else 0.0
    out_radius_rate = round((total_out_radius_all / total_checkins_all * 100), 1) if total_checkins_all else 0.0

    return {
        "start_date": s_date,
        "end_date": e_date,
        "target_sessions_ob": ob_sessions_count,
        "target_sessions_gardener": gardener_sessions_count,
        "total_personnel": len(leaderboard),
        "total_target_sessions_all": total_target_sessions_all,
        "total_checkins": total_checkins_all,
        "total_missed": total_missed_all,
        "overall_attendance": overall_attendance,
        "compliance_rate": compliance_rate,
        "late_rate": late_rate,
        "out_radius_rate": out_radius_rate,
        "leaderboard": leaderboard,
        "top_missed": top_missed[:6],
        "top_late": top_late[:6],
        "top_out_radius": top_out_radius[:6],
        "summary_counts": {
            "teladan": len([p for p in leaderboard if p["eval_category"] == "TELADAN"]),
            "baik": len([p for p in leaderboard if p["eval_category"] == "BAIK"]),
            "cukup": len([p for p in leaderboard if p["eval_category"] == "CUKUP"]),
            "pembinaan": len([p for p in leaderboard if p["eval_category"] == "PEMBINAAN"])
        }
    }

def save_supervisor_notes(petugas_name: str, unit_code: str, period_year: int, period_month: int, notes: str, supervisor_name: str = "Mr Slam") -> Dict[str, Any]:
    """Menyimpan catatan evaluasi supervisi personal untuk seorang petugas"""
    init_evaluasi_tables()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ops_staff_evaluations (
            petugas_name, unit_code, period_year, period_month, supervisor_notes, evaluated_by, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(petugas_name, period_year, period_month) DO UPDATE SET
            supervisor_notes = excluded.supervisor_notes,
            evaluated_by = excluded.evaluated_by,
            updated_at = CURRENT_TIMESTAMP
    """, (petugas_name, unit_code, period_year, period_month, notes, supervisor_name))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Catatan evaluasi untuk {petugas_name} berhasil disimpan."}
