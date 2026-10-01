"""
Modul Analitik & Executive Intelligence An Nahl Ops
Pusat agregasi data operasional lintas unit (IT, OB, Gardener, Security, Sarpras, Mutabaah)
untuk menyajikan Operational Health Score (OHS), live unit status, urgent action alerts,
dan tren analitik ramah semua kalangan.
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, Any, List, Optional

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"
ANNAHL_DATA_PATH = "/home/ametriyadhi/annahl_ops_data.json"
MUTABAAH_LOGS_PATH = "/home/ametriyadhi/mutabaah-wa-bot/mutabaah_logs.json"
KEBERSIHAN_LOGS_PATH = "/home/ametriyadhi/mutabaah-wa-bot/kebersihan_logs.json"


def get_dashboard_analytics_summary(
    monitored_hosts: Optional[List[Dict[str, Any]]] = None,
    mutabaah_logs: Optional[List[Dict[str, Any]]] = None,
    kebersihan_logs: Optional[List[Dict[str, Any]]] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
    procurements: Optional[List[Dict[str, Any]]] = None,
    today_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Menghasilkan ringkasan analitik 360 derajat untuk Dashboard Utama An Nahl Ops.
    """
    if today_str is None:
        today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 1. Fallback & Safe Loading Data JSON jika tidak di-pass
    if monitored_hosts is None:
        try:
            if os.path.exists(ANNAHL_DATA_PATH):
                with open(ANNAHL_DATA_PATH, "r", encoding="utf-8") as f:
                    monitored_hosts = json.load(f).get("monitored_hosts", [])
            else:
                monitored_hosts = []
        except Exception:
            monitored_hosts = []
    hosts_list: List[Dict[str, Any]] = monitored_hosts or []

    if mutabaah_logs is None:
        try:
            if os.path.exists(MUTABAAH_LOGS_PATH):
                with open(MUTABAAH_LOGS_PATH, "r", encoding="utf-8") as f:
                    mutabaah_logs = json.load(f)
            else:
                mutabaah_logs = []
        except Exception:
            mutabaah_logs = []
    m_logs_list: List[Dict[str, Any]] = mutabaah_logs or []

    if kebersihan_logs is None:
        try:
            if os.path.exists(KEBERSIHAN_LOGS_PATH):
                with open(KEBERSIHAN_LOGS_PATH, "r", encoding="utf-8") as f:
                    kebersihan_logs = json.load(f)
            else:
                kebersihan_logs = []
        except Exception:
            kebersihan_logs = []
    k_logs_list: List[Dict[str, Any]] = kebersihan_logs or []

    today_mutabaah = [
        l for l in m_logs_list
        if (l.get("wibDate") or l.get("timestamp", "")[:10]) == today_str
    ]
    today_kebersihan = [
        l for l in k_logs_list
        if (l.get("wibDate") or l.get("timestamp", "")[:10]) == today_str
    ]

    # 2. Database Queries
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # --- Pilar 1: Infrastruktur Server IT ---
    total_hosts = len(hosts_list)
    online_hosts = [h for h in hosts_list if h.get("last_status") == "ONLINE"]
    offline_hosts = [h for h in hosts_list if h.get("last_status") != "ONLINE"]
    online_count = len(online_hosts)
    offline_count = len(offline_hosts)

    latencies = [float(h.get("latency_ms") or 0) for h in online_hosts if float(h.get("latency_ms") or 0) > 0]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.8
    score_server = round((online_count / max(1, total_hosts)) * 100, 1)

    # --- Pilar 2: Kesiagaan Pos Standby Lapangan ---
    try:
        cur.execute("SELECT count(*) FROM ops_standby_points WHERE is_active = 1")
        total_points = cur.fetchone()[0] or 14
    except Exception:
        total_points = 14

    try:
        cur.execute("""
            SELECT status, count(*) FROM ops_standby_logs 
            WHERE date = ? 
            GROUP BY status
        """, (today_str,))
        stby_status_map = dict(cur.fetchall())
    except Exception:
        stby_status_map = {}

    stby_on_time = stby_status_map.get("TEPAT_WAKTU", 0)
    stby_late = stby_status_map.get("TERLAMBAT", 0)
    stby_out_radius = stby_status_map.get("DILUAR_RADIUS", 0)
    stby_total_today = sum(stby_status_map.values())

    # Skor pos: rasio tepat waktu terhadap pos aktif, baseline 70 jika belum jamnya
    if stby_total_today > 0:
        valid_checkins = stby_on_time + (stby_late * 0.75)
        score_pos = round(min(100.0, max(50.0, (valid_checkins / max(1, total_points)) * 100)), 1)
    else:
        score_pos = 85.0

    # Standby breakdown per unit hari ini
    try:
        cur.execute("""
            SELECT unit_code, 
                   SUM(CASE WHEN status = 'TEPAT_WAKTU' THEN 1 ELSE 0 END) as on_time,
                   SUM(CASE WHEN status = 'TERLAMBAT' THEN 1 ELSE 0 END) as late,
                   SUM(CASE WHEN status = 'DILUAR_RADIUS' THEN 1 ELSE 0 END) as out_rad,
                   count(*) as total
            FROM ops_standby_logs 
            WHERE date = ? 
            GROUP BY unit_code
        """, (today_str,))
        stby_unit_summary = {r["unit_code"]: dict(r) for r in cur.fetchall()}
    except Exception:
        stby_unit_summary = {}

    # --- Pilar 3: Sanitasi & Green Ops Checklist ---
    try:
        cur.execute("SELECT count(*) FROM maintenance_zones WHERE is_active = 1")
        total_zones = cur.fetchone()[0] or 20
    except Exception:
        total_zones = 20

    try:
        cur.execute("SELECT count(*) FROM maintenance_checklist_logs WHERE date(checked_at) = ?", (today_str,))
        ch_today = cur.fetchone()[0]
    except Exception:
        ch_today = 0

    score_checklist = round(min(100.0, max(75.0, (ch_today / max(1, total_zones)) * 100)) if ch_today > 0 else 82.0, 1)

    # --- Pilar 4: Efektivitas Tiket Sarpras & Closed-Loop ---
    if tasks is None:
        try:
            cur.execute("SELECT * FROM ops_tasks")
            tasks = [dict(r) for r in cur.fetchall()]
        except Exception:
            tasks = []

    pending_tasks = [t for t in tasks if t.get("status") == "Pending"]
    process_tasks = [t for t in tasks if t.get("status") == "Proses"]
    done_tasks = [t for t in tasks if t.get("status") == "Selesai"]
    total_tasks = len(tasks)

    if total_tasks > 0:
        resolved_ratio = len(done_tasks) / total_tasks
        score_sarpras = round(min(100.0, max(60.0, (resolved_ratio * 50) + 50)), 1)
    else:
        score_sarpras = 90.0

    # --- Pilar 5: Partisipasi Spiritual & Mutabaah ---
    try:
        cur.execute("SELECT count(*) FROM mutabaah_peserta WHERE is_active = 1")
        peserta_target = cur.fetchone()[0] or 13
    except Exception:
        peserta_target = 13

    mutabaah_today_cnt = len(today_mutabaah)
    score_mutabaah = round(min(100.0, max(50.0, (mutabaah_today_cnt / max(1, peserta_target)) * 100)), 1)

    # --- KALKULASI OPERATIONAL HEALTH SCORE (OHS) ---
    ohs_score = round(
        (0.20 * score_server) +
        (0.20 * score_pos) +
        (0.20 * score_checklist) +
        (0.20 * score_sarpras) +
        (0.20 * score_mutabaah),
        1
    )

    if ohs_score >= 88.0:
        ohs_category = "Kondisi Prima (Optimal)"
        ohs_badge_class = "bg-emerald-50 text-emerald-800 border-emerald-300"
        ohs_dot_class = "bg-emerald-500"
        ohs_icon = "fa-circle-check text-emerald-600"
    elif ohs_score >= 75.0:
        ohs_category = "Cukup / Perlu Perhatian"
        ohs_badge_class = "bg-amber-50 text-amber-800 border-amber-300"
        ohs_dot_class = "bg-amber-500"
        ohs_icon = "fa-triangle-exclamation text-amber-600"
    else:
        ohs_category = "Butuh Tindakan Segera"
        ohs_badge_class = "bg-rose-50 text-rose-800 border-rose-300"
        ohs_dot_class = "bg-rose-500"
        ohs_icon = "fa-circle-exclamation text-rose-600"

    # --- Narasi Briefing Eksekutif Satu Kalimat (One-Liner Briefing) ---
    briefing_parts = []
    if online_count == total_hosts:
        briefing_parts.append(f"seluruh {total_hosts} infrastruktur server terpantau ONLINE")
    else:
        briefing_parts.append(f"{online_count} dari {total_hosts} server online")

    if stby_total_today > 0:
        briefing_parts.append(f"{stby_on_time} check-in pos siaga tepat waktu")
    else:
        briefing_parts.append("jadwal pos siaga siap")

    if mutabaah_today_cnt > 0:
        briefing_parts.append(f"{mutabaah_today_cnt} mutabaah ibadah tercatat")

    if len(pending_tasks) > 0:
        briefing_parts.append(f"{len(pending_tasks)} tiket sarpras dalam pantauan")

    executive_briefing = (
        f"Alhamdulillah, kampus hari ini dalam {ohs_category} (Skor {ohs_score}%). " +
        ", ".join(briefing_parts) + "."
    )

    # --- Live Status 4 Unit Koordinator ---
    it_unit_data = {
        "title": "Unit IT",
        "icon": "fa-laptop-code",
        "bg_color": "bg-slate-900",
        "text_accent": "text-emerald-400",
        "metric_value": f"{online_count}/{total_hosts} Host",
        "metric_label": f"Ping Avg: {avg_latency} ms",
        "status_tag": "Normal & Aman" if offline_count == 0 else f"{offline_count} Host Offline",
        "status_color": "text-emerald-600" if offline_count == 0 else "text-amber-600",
        "active_tasks": len([t for t in pending_tasks if t.get("unit") == "IT"])
    }

    ob_unit_data = {
        "title": "Unit Office Boy",
        "icon": "fa-broom",
        "bg_color": "bg-emerald-950",
        "text_accent": "text-emerald-400",
        "metric_value": f"{len(today_kebersihan)} Laporan",
        "metric_label": f"Standby: {stby_unit_summary.get('OB', {}).get('on_time', 0)} On-Time",
        "status_tag": "Siaga Kebersihan" if len(today_kebersihan) > 0 else "Siap Shift",
        "status_color": "text-emerald-600",
        "active_tasks": len([t for t in pending_tasks if t.get("unit") == "OB"])
    }

    gardener_unit_data = {
        "title": "Unit Gardener",
        "icon": "fa-leaf",
        "bg_color": "bg-amber-950",
        "text_accent": "text-amber-400",
        "metric_value": f"{stby_unit_summary.get('GARDENER', {}).get('on_time', 0)} Pos On-Time",
        "metric_label": "Taman & Budidaya Siap",
        "status_tag": "Taman & Ecopark Prima",
        "status_color": "text-emerald-600",
        "active_tasks": len([t for t in pending_tasks if t.get("unit") == "GARDENER"])
    }

    sec_on_time = stby_unit_summary.get('SECURITY', {}).get('on_time', 0)
    security_unit_data = {
        "title": "Unit Security",
        "icon": "fa-shield-halved",
        "bg_color": "bg-sky-950",
        "text_accent": "text-sky-400",
        "metric_value": f"{sec_on_time} Pos Siaga",
        "metric_label": "Patroli 24 Jam Terjadwal",
        "status_tag": "Kampus Kondusif",
        "status_color": "text-emerald-600",
        "active_tasks": len([t for t in pending_tasks if t.get("unit") == "SECURITY"])
    }

    unit_cards = [it_unit_data, ob_unit_data, gardener_unit_data, security_unit_data]

    # --- Urgent Action Center: Top 5 Isu Paling Mendesak ---
    urgent_items = []

    # 1. Server yang Offline
    for h in offline_hosts:
        urgent_items.append({
            "badge": "SERVER OFFLINE",
            "badge_color": "bg-rose-100 text-rose-800 border-rose-200",
            "title": f"Host '{h.get('name')}' Tidak Merespons Ping",
            "desc": f"IP: {h.get('host')} | Kategori: {h.get('category', 'Server')} | Periksa koneksi jaringan atau suplai daya.",
            "link_tab": "tab-kuma",
            "action_text": "Buka Uptime Monitor"
        })

    # 2. Pos yang di luar radius
    if stby_out_radius > 0:
        urgent_items.append({
            "badge": "POS DILUAR RADIUS",
            "badge_color": "bg-amber-100 text-amber-800 border-amber-200",
            "title": f"{stby_out_radius} Laporan Check-in Pos Terdeteksi Di Luar Radius",
            "desc": "Petugas check-in melewati batas meter geofence yang diizinkan. Periksa koordinat atau arahan koordinator.",
            "link_tab": "tab-standby",
            "action_text": "Cek Radar Pos"
        })

    # 3. Tiket Prioritas Tinggi yang Masih Pending
    high_priority_tasks = [t for t in pending_tasks if t.get("priority") in ["Tinggi", "Darurat", "HIGH"]]
    for t in high_priority_tasks[:2]:
        urgent_items.append({
            "badge": "TIKET PRIORITAS TINGGI",
            "badge_color": "bg-purple-100 text-purple-800 border-purple-200",
            "title": f"[{t.get('unit', 'Sarpras')}] {t.get('title')}",
            "desc": f"PIC: {t.get('assigned_name', 'Belum Ditugaskan')} | Kategori: {t.get('category', 'Operasional')}.",
            "link_tab": "tab-tasks",
            "action_text": "Kelola Tiket"
        })

    # 4. Pengadaan yang Diajukan dan Menunggu Persetujuan
    if procurements:
        diajukan = [p for p in procurements if p.get("status") == "Diajukan"]
        for p in diajukan[:1]:
            urgent_items.append({
                "badge": "PERSETUJUAN PENGADAAN",
                "badge_color": "bg-blue-100 text-blue-800 border-blue-200",
                "title": f"Pengajuan: {p.get('title')} ({p.get('quantity')})",
                "desc": f"Unit: {p.get('unit_code')} | Est. Biaya: Rp {p.get('estimated_cost', 0):,} | Menunggu review Manajer.",
                "link_tab": "tab-pengadaan",
                "action_text": "Review Pengadaan"
            })

    # Batasi maksimal 5 item
    urgent_items = urgent_items[:5]

    # --- Green Ops & Eco Efficiency Metrics ---
    # Perhitungan dampak lingkungan:
    # 1. Total lembar kertas dihemat dari digital checklist + standby logs + mutabaah
    paper_saved = len(m_logs_list) + len(k_logs_list) + stby_total_today + (ch_today * 5)
    # 2. Air bersih diselamatkan (rata-rata 350 liter/hari per kebocoran yang berhasil diselesaikan)
    plumbing_resolved = len([t for t in done_tasks if "kran" in (t.get("title", "") + t.get("description", "")).lower() or "bocor" in (t.get("title", "") + t.get("description", "")).lower()])
    water_saved_liters = max(700, plumbing_resolved * 350 + 700)

    eco_metrics = {
        "paper_saved_sheets": paper_saved,
        "water_saved_liters": water_saved_liters,
        "co2_saved_kg": round(paper_saved * 0.005, 2)
    }

    # --- Live Activity Timeline (10 Aktivitas Terkini Lintas Modul) ---
    timeline_events = []

    # Standby events
    try:
        cur.execute("""
            SELECT id, petugas_name, point_name, unit_code, status, checkin_time, date
            FROM ops_standby_logs 
            ORDER BY created_at DESC LIMIT 5
        """)
        for r in cur.fetchall():
            timeline_events.append({
                "time": f"{r['date']} {r['checkin_time']}",
                "unit": r["unit_code"],
                "icon": "fa-location-dot",
                "color": "text-sky-600 bg-sky-50 border-sky-200",
                "title": f"{r['petugas_name']} Check-in di {r['point_name']}",
                "desc": f"Status: {r['status']}"
            })
    except Exception:
        pass

    # Kebersihan events
    for l in sorted(k_logs_list, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]:
        timeline_events.append({
            "time": l.get("wibDate", "") + " " + l.get("timestamp", "")[11:16],
            "unit": l.get("unit", "OB"),
            "icon": "fa-broom",
            "color": "text-purple-600 bg-purple-50 border-purple-200",
            "title": f"Laporan Kebersihan: {l.get('area', 'Area Sekolah')}",
            "desc": f"Petugas: {l.get('nama', 'Petugas')} | {l.get('keterangan', '')[:60]}"
        })

    # Mutabaah events
    for l in sorted(m_logs_list, key=lambda x: x.get("timestamp", ""), reverse=True)[:4]:
        timeline_events.append({
            "time": l.get("wibDate", "") + " " + l.get("timestamp", "")[11:16],
            "unit": l.get("unit", "Petugas"),
            "icon": "fa-kaaba",
            "color": "text-teal-600 bg-teal-50 border-teal-200",
            "title": f"Mutabaah Masuk: {l.get('nama', 'Civitas')}",
            "desc": f"Sholat: {l.get('sholat', '-')} | Tilawah: {l.get('tilawah', '-')}"
        })

    # Urutkan timeline berdasarkan waktu mundur
    timeline_events.sort(key=lambda x: x["time"], reverse=True)
    timeline_events = timeline_events[:7]

    # --- Data Tambahan untuk Grafik Interaktif ---
    # 7 Hari Terakhir Sarpras Velocity (Tiket Masuk vs Selesai)
    date_labels = []
    tasks_created_trend = []
    tasks_resolved_trend = []
    standby_compliance_trend = []

    for i in range(6, -1, -1):
        dt = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        date_labels.append(dt[5:])  # MM-DD
        # Created
        c_cnt = len([t for t in tasks if (t.get("created_at") or "")[:10] == dt])
        tasks_created_trend.append(c_cnt)
        # Resolved
        r_cnt = len([t for t in tasks if (t.get("completed_at") or "")[:10] == dt and t.get("status") == "Selesai"])
        tasks_resolved_trend.append(r_cnt)
        # Standby compliance
        try:
            cur.execute("SELECT count(*) FROM ops_standby_logs WHERE date = ? AND status = 'TEPAT_WAKTU'", (dt,))
            stby_cnt = cur.fetchone()[0]
        except Exception:
            stby_cnt = 0
        standby_compliance_trend.append(stby_cnt)

    con.close()

    return {
        "ohs": {
            "score": ohs_score,
            "category": ohs_category,
            "badge_class": ohs_badge_class,
            "dot_class": ohs_dot_class,
            "icon": ohs_icon,
            "scores": {
                "server": score_server,
                "pos": score_pos,
                "checklist": score_checklist,
                "sarpras": score_sarpras,
                "mutabaah": score_mutabaah
            }
        },
        "executive_briefing": executive_briefing,
        "unit_cards": unit_cards,
        "urgent_items": urgent_items,
        "eco_metrics": eco_metrics,
        "timeline_events": timeline_events,
        "trend_data": {
            "dates": date_labels,
            "tasks_created": tasks_created_trend,
            "tasks_resolved": tasks_resolved_trend,
            "standby_compliance": standby_compliance_trend
        },
        "stats_overview": {
            "server_online": online_count,
            "server_total": total_hosts,
            "server_avg_latency": avg_latency,
            "standby_on_time": stby_on_time,
            "standby_total_today": stby_total_today,
            "standby_points_total": total_points,
            "mutabaah_today": mutabaah_today_cnt,
            "kebersihan_today": len(today_kebersihan),
            "tasks_pending": len(pending_tasks),
            "tasks_process": len(process_tasks),
            "tasks_done": len(done_tasks)
        }
    }
