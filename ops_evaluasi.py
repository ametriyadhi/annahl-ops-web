"""
Modul Analisa & Evaluasi Kinerja Personil (OB & Gardener)
An Nahl Ops Web Dashboard - note-umum.ametriyadhi.com
Mengintegrasikan Kesiagaan Pos Geotagging, Kebersihan, Mutabaah, dan Pemeliharaan Sarpras
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

def get_evaluasi_analytics(period_year: Optional[int] = None, period_month: Optional[int] = None, unit_filter: str = "ALL") -> Dict[str, Any]:
    """Menghitung analitik mendalam kinerja dan kedisiplinan staf OB & Gardener"""
    init_evaluasi_tables()
    conn = get_db()
    cur = conn.cursor()

    # Default ke periode saat ini
    now = datetime.date.today()
    if period_year is None:
        period_year = now.year
    if period_month is None:
        period_month = now.month

    # Ambil seluruh data standby logs
    cur.execute("""
        SELECT * FROM ops_standby_logs
        ORDER BY date ASC, checkin_time ASC
    """)
    standby_rows = cur.fetchall()

    # Ambil catatan supervisi yang sudah disimpan
    cur.execute("""
        SELECT * FROM ops_staff_evaluations
        WHERE period_year = ? AND period_month = ?
    """, (period_year, period_month))
    eval_records = {r["petugas_name"]: dict(r) for r in cur.fetchall()}

    conn.close()

    # Load kebersihan logs
    kebersihan_counts = Counter()
    try:
        with open(KEBERSIHAN_LOG_PATH, "r", encoding="utf-8") as f:
            k_logs = json.load(f)
            for k in k_logs:
                nama = (k.get("nama") or "").strip()
                if nama:
                    kebersihan_counts[nama] += 1
    except Exception:
        pass

    # Kelompokkan data per personil
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

    # Master pemetaan nama ke unit yang konsisten
    gardener_names = {"Samad", "Pak Samad", "Amat", "Pak Amat", "Jimin", "Pak Jimin", "Nandi", "Pak Nandi", "Somad", "Pak Somad"}

    for r in standby_rows:
        nama = (r["petugas_name"] or "").strip()
        if not nama or nama in ["Mr Slam", "H3RM4W4N"]: # skip admin/testing
            continue

        p = personnel_data[nama]
        p["nama"] = nama
        
        # Unit normalization
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

    # Susun Rapor Personil & Hitung Skor
    leaderboard = []
    total_checkins_all = 0
    total_late_all = 0
    total_out_radius_all = 0
    total_on_time_all = 0

    for nama, p in personnel_data.items():
        # Filter unit jika ada
        if unit_filter != "ALL" and p["unit"] != unit_filter:
            continue

        tot = p["total_checkin"]
        if tot == 0:
            continue

        total_checkins_all += tot
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

        # Rumus Skor Disiplin (0 - 100):
        # Base: 100
        # Penalti Terlambat: - (late_pct * 0.7)
        # Penalti Di Luar Radius: - (out_radius_pct * 0.5)
        # Bonus Laporan Kebersihan aktif: + min(kebersihan_count * 0.5, 10)
        score = 100.0 - (late_pct * 0.7) - (out_radius_pct * 0.5)
        k_count = kebersihan_counts.get(nama, 0)
        score += min(k_count * 0.2, 5.0)
        score = max(0.0, min(100.0, round(score, 1)))

        # Kategori Status Evaluasi
        if score >= 85 and late_pct <= 15:
            eval_category = "TELADAN"
            eval_badge = "🌟 Sangat Disiplin"
            badge_color = "emerald"
        elif score >= 70:
            eval_category = "BAIK"
            eval_badge = "🟢 Baik & Produktif"
            badge_color = "teal"
        elif score >= 50:
            eval_category = "CUKUP"
            eval_badge = "🟡 Cukup / Perlu Arahan"
            badge_color = "amber"
        else:
            eval_category = "PEMBINAAN"
            eval_badge = "🔴 Butuh Pembinaan Khusus"
            badge_color = "rose"

        # Rekomendasi Tindak Lanjut Otomatis
        recommendation = ""
        if late_pct >= 40:
            recommendation = f"Sering terlambat ({late_pct}% sesi, rata-rata telat {avg_late_min} mnt). Perlu pembinaan jam hadir sesi pagi."
        elif out_radius_pct >= 30:
            recommendation = f"Check-in sering di luar titik pos fisik ({out_radius_pct}% sesi, jarak terjauh {max_dist}m). Wajibkan scan QR akrilik di meja pos."
        elif score >= 85:
            recommendation = f"Kinerja & kedisiplinan sangat baik ({on_time_pct}% tepat waktu). Layak dipertimbangkan untuk apresiasi/petugas teladan."
        else:
            recommendation = "Kedisiplinan standar. Pertahankan dan tingkatkan konsistensi waktu tiba di pos."

        # Catatan yang sudah disimpan pimpinan
        saved_eval = eval_records.get(nama, {})
        supervisor_notes = saved_eval.get("supervisor_notes", "")

        leaderboard.append({
            "nama": nama,
            "unit": p["unit"],
            "total_checkin": tot,
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
            "discipline_score": score,
            "eval_category": eval_category,
            "eval_badge": eval_badge,
            "badge_color": badge_color,
            "recommendation": recommendation,
            "supervisor_notes": supervisor_notes,
            "late_details": p["late_details"][-5:], # 5 riwayat telat terakhir
            "out_radius_details": p["out_radius_details"][-5:], # 5 riwayat radius terakhir
            "top_pos": [pos for pos, _ in p["pos_visited"].most_common(2)]
        })

    # Urutkan leaderboard berdasarkan skor tertinggi ke terendah
    leaderboard.sort(key=lambda x: x["discipline_score"], reverse=True)

    # Top terlambat (diurutkan berdasarkan total terlambat terbanyak)
    top_late = sorted([p for p in leaderboard if p["terlambat"] > 0], key=lambda x: (x["terlambat"], x["late_pct"]), reverse=True)

    # Top di luar radius
    top_out_radius = sorted([p for p in leaderboard if p["diluar_radius"] > 0], key=lambda x: (x["diluar_radius"], x["out_radius_pct"]), reverse=True)

    # Ringkasan KPI Global
    compliance_rate = round((total_on_time_all / total_checkins_all * 100), 1) if total_checkins_all else 0.0
    late_rate = round((total_late_all / total_checkins_all * 100), 1) if total_checkins_all else 0.0
    out_radius_rate = round((total_out_radius_all / total_checkins_all * 100), 1) if total_checkins_all else 0.0

    return {
        "period": f"{period_year}-{period_month:02d}",
        "total_personnel": len(leaderboard),
        "total_checkins": total_checkins_all,
        "compliance_rate": compliance_rate,
        "late_rate": late_rate,
        "out_radius_rate": out_radius_rate,
        "leaderboard": leaderboard,
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
