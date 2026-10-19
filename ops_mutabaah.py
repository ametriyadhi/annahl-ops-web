"""
Modul Laporan, Evaluasi & Radar Kepatuhan Mutaba'ah Petugas (OB, Gardener, Security)
An Nahl Ops Web Dashboard - note-umum.ametriyadhi.com
"""

import os
import io
import re
import json
import sqlite3
import datetime
from typing import Dict, Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"
MUTABAAH_LOGS_PATH = "/home/ametriyadhi/mutabaah-wa-bot/mutabaah_logs.json"

# Master personil operasional terintegrasi
DEFAULT_PERSONNEL = [
    # --- OB (Office Boy) ---
    {"name": "Masdik", "phone": "6289516458570", "unit": "OB", "job_title": "Koordinator OB / Umum"},
    {"name": "Amir", "phone": "6281284936149", "unit": "OB", "job_title": "OB Supporting & Logistik"},
    {"name": "Aji Kurniawan", "phone": "6283173047973", "unit": "OB", "job_title": "OB Operasional"},
    {"name": "Risman", "phone": "6281294875143", "unit": "OB", "job_title": "OB Gedung SD"},
    {"name": "Mahmudin", "phone": "6281290731669", "unit": "OB", "job_title": "OB Gedung SD"},
    {"name": "Hasanudin", "phone": "6287881480282", "unit": "OB", "job_title": "OB Gedung SMA"},
    {"name": "Didin", "phone": "6281324382218", "unit": "OB", "job_title": "OB Gedung TK / Playgroup"},
    {"name": "Kusmawan", "phone": "6281220795285", "unit": "OB", "job_title": "OB Bawah Masjid & Koridor"},
    {"name": "Rafli", "phone": "628999198672", "unit": "OB", "job_title": "OB Operasional"},
    {"name": "Samih Susilawati", "phone": "6283857186192", "unit": "OB", "job_title": "OB Umum & Kantor"},
    {"name": "Azril Falis Setiawan", "phone": "6289676625832", "unit": "OB", "job_title": "OB Area Kolam & Olahraga"},
    {"name": "Cecep", "phone": "6281383355207", "unit": "OB", "job_title": "OB Lapangan & Sarpras"},
    # --- GARDENER (Taman & Ecopark) ---
    {"name": "Amat", "phone": "628569837510", "unit": "GARDENER", "job_title": "Gardener Taman Utama"},
    {"name": "Jimin", "phone": "6285213629255", "unit": "GARDENER", "job_title": "Gardener Area Utara & Gerbang"},
    {"name": "Nandi", "phone": "6288213011571", "unit": "GARDENER", "job_title": "Gardener Jalur Koridor"},
    {"name": "Samad", "phone": "6285280542806", "unit": "GARDENER", "job_title": "Gardener Ciangsana Ecopark"},
    {"name": "Somad", "phone": "6285772140361", "unit": "GARDENER", "job_title": "Gardener Pembibitan & Kebun"},
    # --- SECURITY (Keamanan & Ketertiban) ---
    {"name": "Amin", "phone": "6282111384428", "unit": "SECURITY", "job_title": "Security Pos Utama"},
    {"name": "Taufik", "phone": "6285890764955", "unit": "SECURITY", "job_title": "Security Patroli Lapangan"},
    {"name": "Hendri Susilo", "phone": "6285385072949", "unit": "SECURITY", "job_title": "Security Pos Belakang & Dropzone"},
    {"name": "Pendi", "phone": "62895622752131", "unit": "SECURITY", "job_title": "Security Pos Gerbang"},
    {"name": "Syarif", "phone": "6285691138459", "unit": "SECURITY", "job_title": "Security Pos Barat"},
    {"name": "Warnadi", "phone": "6289649558367", "unit": "SECURITY", "job_title": "Security Pos Selatan"},
    {"name": "Rochman", "phone": "6285776914508", "unit": "SECURITY", "job_title": "Security Siaga 24 Jam"},
]

def clean_str(s: Any) -> str:
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())

def clean_phone(p: Any) -> str:
    digits = re.sub(r'[^0-9]', '', str(p or ''))
    if digits.startswith('0'):
        digits = '62' + digits[1:]
    return digits

def load_mutabaah_logs() -> List[Dict[str, Any]]:
    """Membaca log mutabaah murni (tanpa personal log Mr Slam)"""
    if not os.path.exists(MUTABAAH_LOGS_PATH):
        return []
    try:
        with open(MUTABAAH_LOGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [l for l in data if l.get("type") not in ("mutubaah_personal", "mutabaah_personal")]
    except Exception as e:
        print(f"[ERROR load_mutabaah_logs] {e}")
        return []

def get_master_personnel(unit_filter: str = "ALL") -> List[Dict[str, Any]]:
    """
    Mengambil master personil operasional terintegrasi dari SQLite dan daftar standar.
    """
    personnel_dict = {clean_str(p["name"]): dict(p) for p in DEFAULT_PERSONNEL}

    # Sinkronisasi dari SQLite tabel ops_standby_assignments
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT unit_code, petugas_name, no_wa FROM ops_standby_assignments WHERE is_active = 1")
            for r in cur.fetchall():
                pname = (r["petugas_name"] or "").strip()
                k = clean_str(pname)
                unit = (r["unit_code"] or "OB").upper()
                wa = clean_phone(r["no_wa"] or "")
                if k in personnel_dict:
                    if wa:
                        personnel_dict[k]["phone"] = wa
                    personnel_dict[k]["unit"] = unit
                else:
                    personnel_dict[k] = {
                        "name": pname,
                        "phone": wa,
                        "unit": unit,
                        "job_title": f"Petugas {unit}"
                    }
            conn.close()
        except Exception as e:
            print(f"[WARN get_master_personnel DB] {e}")

    result = list(personnel_dict.values())

    # Filter unit
    u_filter = (unit_filter or "ALL").upper()
    if u_filter != "ALL":
        result = [p for p in result if p["unit"].upper() == u_filter or (u_filter == "OB" and "OB" in p["unit"].upper())]

    # Urutkan berdasarkan nama
    result.sort(key=lambda x: (x["unit"], x["name"]))
    return result

def match_log_to_personnel(log: Dict[str, Any], personnel_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pencocokan cerdas antara rekaman log mutabaah dengan personil master"""
    l_sender = clean_phone(log.get("sender", ""))
    l_name = clean_str(log.get("nama", ""))

    # 1. Cek kecocokan nomor telepon (9 digit terakhir)
    if l_sender and len(l_sender) >= 9:
        s_tail = l_sender[-9:]
        for p in personnel_list:
            p_phone = clean_phone(p.get("phone", ""))
            if p_phone and p_phone[-9:] == s_tail:
                return p

    # 2. Cek kecocokan nama langsung atau substring
    for p in personnel_list:
        p_name = clean_str(p.get("name", ""))
        if p_name and (p_name == l_name or p_name in l_name or l_name in p_name):
            return p

    # 3. Penanganan alias khusus umum An Nahl
    special_alias = {
        "aji": "Aji Kurniawan",
        "ajikurnia": "Aji Kurniawan",
        "hasan": "Hasanudin",
        "hasanudin": "Hasanudin",
        "masdik": "Masdik",
        "masdikafdhal": "Masdik",
        "kusmawan": "Kusmawan",
        "mahmudin": "Mahmudin",
        "risman": "Risman",
        "didin": "Didin",
        "samih": "Samih Susilawati",
        "samihsusilawati": "Samih Susilawati",
        "azril": "Azril Falis Setiawan",
        "azrilfalis": "Azril Falis Setiawan",
        "syarip": "Syarif",
        "syarif": "Syarif",
        "warnadi": "Warnadi",
        "rohman": "Rochman",
        "rochman": "Rochman",
        "somad": "Somad",
        "samad": "Samad",
        "paksamad": "Samad",
        "paksomad": "Somad",
    }
    alias_target = special_alias.get(l_name)
    if alias_target:
        for p in personnel_list:
            if clean_str(p.get("name", "")) == clean_str(alias_target):
                return p

    return None

def get_mutabaah_radar(date_str: Optional[str] = None, unit_filter: str = "OB") -> Dict[str, Any]:
    """
    Radar Kepatuhan Mutaba'ah Harian:
    Menampilkan status seluruh personil untuk tanggal terpilih:
    - Siapa yang sudah lapor & detail mutabaahnya
    - Siapa yang belum lapor & tombol ingatkan via WhatsApp
    """
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    personnel = get_master_personnel(unit_filter)
    all_logs = load_mutabaah_logs()

    # Filter logs untuk tanggal yang diminta
    day_logs = []
    for l in all_logs:
        log_date = l.get("wibDate") or (l.get("timestamp") or "")[:10]
        if log_date == date_str:
            day_logs.append(l)

    # Petakan laporan per personil
    radar_items = []
    reported_count = 0
    sholat_5_count = 0
    tilawah_count = 0
    dzikir_count = 0

    # Lacak siapa saja yang sudah matched agar tidak double
    matched_log_indices = set()

    for p in personnel:
        p_log = None
        for idx, l in enumerate(day_logs):
            if idx in matched_log_indices:
                continue
            matched_person = match_log_to_personnel(l, [p])
            if matched_person:
                p_log = l
                matched_log_indices.add(idx)
                break

        if p_log is not None:
            reported_count += 1
            sholat_text = str(p_log.get("sholat", "")).strip()
            tilawah_text = str(p_log.get("tilawah", "")).strip()
            dzikir_text = str(p_log.get("dzikir", "")).strip()

            is_sholat_5 = bool(re.search(r'5|lima|penuh|lengkap|waktu', sholat_text, re.I))
            is_tilawah = bool(tilawah_text and tilawah_text not in ('-', '0', 'belum'))
            is_dzikir = bool(dzikir_text and dzikir_text not in ('-', '0', 'belum'))

            if is_sholat_5:
                sholat_5_count += 1
            if is_tilawah:
                tilawah_count += 1
            if is_dzikir:
                dzikir_count += 1

            # Format jam lapor
            raw_ts = str(p_log.get("timestamp", ""))
            time_wib = ""
            if "T" in raw_ts:
                try:
                    # Parse UTC to WIB (+7)
                    dt_utc = datetime.datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                    dt_wib = dt_utc + datetime.timedelta(hours=7)
                    time_wib = dt_wib.strftime("%H:%M") + " WIB"
                except Exception:
                    time_wib = raw_ts[11:16] + " WIB"

            radar_items.append({
                "personnel": p,
                "has_reported": True,
                "badge_status": "SUDAH_LAPOR",
                "report_time": time_wib,
                "sholat": sholat_text,
                "is_sholat_5": is_sholat_5,
                "tilawah": tilawah_text,
                "is_tilawah": is_tilawah,
                "dzikir": dzikir_text,
                "is_dzikir": is_dzikir,
                "raw_text": p_log.get("rawText", ""),
                "sender": p_log.get("sender", ""),
                "unit_reported": p_log.get("unit", p["unit"])
            })
        else:
            # Belum lapor -> Buat link reminder WA
            p_phone = clean_phone(p.get("phone", ""))
            clean_wa = p_phone
            if clean_wa.startswith("0"):
                clean_wa = "62" + clean_wa[1:]

            msg_template = (
                f"Assalamu'alaikum Akhi {p['name']},\n\n"
                f"Mengingatkan untuk laporan Mutaba'ah Yaumiyah hari ini ({date_str}) belum tercatat di bot operasional An Nahl.\n\n"
                f"Mohon dapat mengirimkan format mutaba'ah seperti biasa:\n"
                f"Mutabaah\n"
                f"Nama: {p['name']}\n"
                f"Unit: {p['unit']}\n"
                f"Sholat: 5 waktu\n"
                f"Tilawah: [Juz/Ayat]\n"
                f"Dzikir: [Pagi/Petang]\n\n"
                f"Jazakallahu khairan. 🙏"
            )
            encoded_msg = re.sub(r'\s+', '%20', msg_template).replace('\n', '%0A')
            wa_link = f"https://wa.me/{clean_wa}?text={encoded_msg}" if clean_wa else ""

            radar_items.append({
                "personnel": p,
                "has_reported": False,
                "badge_status": "BELUM_LAPOR",
                "report_time": "-",
                "sholat": "-",
                "is_sholat_5": False,
                "tilawah": "-",
                "is_tilawah": False,
                "dzikir": "-",
                "is_dzikir": False,
                "raw_text": "",
                "sender": p.get("phone", ""),
                "unit_reported": p["unit"],
                "wa_reminder_link": wa_link
            })

    total_personnel = len(personnel)
    unreported_count = total_personnel - reported_count
    compliance_pct = round((reported_count / total_personnel * 100), 1) if total_personnel > 0 else 0.0

    # Urutkan: Yang belum lapor taruh di atas agar mudah di-follow up oleh Mr Slam / Koordinator
    radar_items.sort(key=lambda x: (x["has_reported"], x["personnel"]["name"]))

    return {
        "success": True,
        "date": date_str,
        "unit_filter": unit_filter,
        "summary": {
            "total_personnel": total_personnel,
            "reported_count": reported_count,
            "unreported_count": unreported_count,
            "compliance_pct": compliance_pct,
            "sholat_5_count": sholat_5_count,
            "tilawah_count": tilawah_count,
            "dzikir_count": dzikir_count
        },
        "radar": radar_items
    }

def get_mutabaah_logs_filtered(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    unit_filter: str = "ALL",
    search: str = ""
) -> Dict[str, Any]:
    """Mengambil riwayat log mutabaah dengan filter tanggal, unit, dan pencarian"""
    logs = load_mutabaah_logs()
    filtered = []
    q_search = clean_str(search)
    u_filter = (unit_filter or "ALL").upper()

    for l in logs:
        l_date = l.get("wibDate") or (l.get("timestamp") or "")[:10]
        l_nama = l.get("nama", "")
        l_unit = l.get("unit", "")
        l_sholat = l.get("sholat", "")
        l_tilawah = l.get("tilawah", "")
        l_dzikir = l.get("dzikir", "")

        # Filter tanggal
        if start_date and l_date < start_date:
            continue
        if end_date and l_date > end_date:
            continue

        # Filter unit
        if u_filter != "ALL":
            if u_filter == "OB" and "ob" not in l_unit.lower() and not any(k in clean_str(l_nama) for k in ("masdik", "amir", "hasan", "mahmudin", "didin", "kusmawan", "risman", "samih")):
                continue
            elif u_filter == "SECURITY" and "security" not in l_unit.lower() and "scurity" not in l_unit.lower():
                continue
            elif u_filter == "GARDENER" and "garden" not in l_unit.lower():
                continue

        # Filter pencarian
        if q_search:
            combined = clean_str(f"{l_nama} {l_unit} {l_sholat} {l_tilawah} {l_dzikir}")
            if q_search not in combined:
                continue

        # Format jam lapor WIB
        raw_ts = l.get("timestamp", "")
        time_wib = ""
        if "T" in raw_ts:
            try:
                dt_utc = datetime.datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                dt_wib = dt_utc + datetime.timedelta(hours=7)
                time_wib = dt_wib.strftime("%H:%M")
            except Exception:
                time_wib = raw_ts[11:16]

        filtered.append({
            "date": l_date,
            "time_wib": time_wib,
            "nama": l_nama,
            "unit": l_unit,
            "sholat": l_sholat,
            "tilawah": l_tilawah,
            "dzikir": l_dzikir,
            "sender": l.get("sender", ""),
            "raw_text": l.get("rawText", "")
        })

    # Urutkan dari tanggal terbaru ke terlama
    filtered.sort(key=lambda x: (x["date"], x["time_wib"]), reverse=True)

    return {
        "success": True,
        "total_records": len(filtered),
        "logs": filtered
    }

def get_mutabaah_evaluasi(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    unit_filter: str = "OB"
) -> Dict[str, Any]:
    """
    Rapor & Evaluasi Disiplin Mutaba'ah Petugas:
    Menghitung persentase kepatuhan lapor per personil dalam rentang tanggal.
    """
    ref_end = datetime.date.today()
    ref_start = ref_end - datetime.timedelta(days=29)

    s_date = start_date or ref_start.strftime("%Y-%m-%d")
    e_date = end_date or ref_end.strftime("%Y-%m-%d")

    try:
        d1 = datetime.datetime.strptime(s_date, "%Y-%m-%d").date()
        d2 = datetime.datetime.strptime(e_date, "%Y-%m-%d").date()
        total_days = max(1, (d2 - d1).days + 1)
    except Exception:
        total_days = 30

    personnel = get_master_personnel(unit_filter)
    all_logs = load_mutabaah_logs()

    # Filter logs rentang tanggal
    period_logs = []
    for l in all_logs:
        log_date = l.get("wibDate") or (l.get("timestamp") or "")[:10]
        if s_date <= log_date <= e_date:
            period_logs.append(l)

    evaluasi_list = []

    for p in personnel:
        # Cari seluruh log milik personil ini dalam periode
        p_logs = []
        reported_dates = set()
        sholat_5_cnt = 0
        tilawah_cnt = 0
        dzikir_cnt = 0

        for l in period_logs:
            matched_person = match_log_to_personnel(l, [p])
            if matched_person:
                p_logs.append(l)
                l_date = l.get("wibDate") or (l.get("timestamp") or "")[:10]
                reported_dates.add(l_date)

                sholat_text = str(l.get("sholat", ""))
                tilawah_text = str(l.get("tilawah", ""))
                dzikir_text = str(l.get("dzikir", ""))

                if re.search(r'5|lima|penuh|lengkap|waktu', sholat_text, re.I):
                    sholat_5_cnt += 1
                if tilawah_text and tilawah_text not in ('-', '0', 'belum'):
                    tilawah_cnt += 1
                if dzikir_text and dzikir_text not in ('-', '0', 'belum'):
                    dzikir_cnt += 1

        days_reported = len(reported_dates)
        compliance_pct = round((days_reported / total_days * 100), 1)

        # Kategori Disiplin
        if compliance_pct >= 85.0:
            predikat = "Sangat Disiplin"
            predikat_badge = "emerald"
        elif compliance_pct >= 70.0:
            predikat = "Disiplin"
            predikat_badge = "sky"
        elif compliance_pct >= 50.0:
            predikat = "Cukup"
            predikat_badge = "amber"
        else:
            predikat = "Perlu Pembinaan"
            predikat_badge = "rose"

        last_date = max(reported_dates) if reported_dates else "-"

        evaluasi_list.append({
            "personnel": p,
            "total_days": total_days,
            "days_reported": days_reported,
            "compliance_pct": compliance_pct,
            "sholat_5_count": sholat_5_cnt,
            "tilawah_count": tilawah_cnt,
            "dzikir_count": dzikir_cnt,
            "predikat": predikat,
            "predikat_badge": predikat_badge,
            "last_reported_date": last_date
        })

    # Urutkan berdasarkan persentase kepatuhan tertinggi
    evaluasi_list.sort(key=lambda x: (-x["compliance_pct"], -x["days_reported"], x["personnel"]["name"]))

    return {
        "success": True,
        "start_date": s_date,
        "end_date": e_date,
        "total_days": total_days,
        "unit_filter": unit_filter,
        "evaluasi": evaluasi_list
    }

def create_mutabaah_excel_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    unit_filter: str = "ALL"
) -> io.BytesIO:
    """
    Membuat file Excel (.xlsx) 2-Sheet berstandar An Nahl:
    Sheet 1: Rekap Evaluasi Kepatuhan & Kedisiplinan Petugas
    Sheet 2: Riwayat Log Transaksi Mutaba'ah Lengkap
    """
    eval_data = get_mutabaah_evaluasi(start_date, end_date, unit_filter)
    logs_data = get_mutabaah_logs_filtered(start_date, end_date, unit_filter)

    wb = openpyxl.Workbook()

    # Style standar
    header_fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
    header_font = Font(name="Plus Jakarta Sans", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Plus Jakarta Sans", size=14, bold=True, color="064E3B")
    subtitle_font = Font(name="Plus Jakarta Sans", size=10, italic=True, color="475569")
    regular_font = Font(name="Plus Jakarta Sans", size=10)
    bold_font = Font(name="Plus Jakarta Sans", size=10, bold=True)
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # ========================================================
    # SHEET 1: REKAP EVALUASI KEPATUHAN
    # ========================================================
    ws1 = wb.active
    if ws1 is None:
        ws1 = wb.create_sheet(title="Rekap Evaluasi Kepatuhan")
    else:
        ws1.title = "Rekap Evaluasi Kepatuhan"

    ws1["A1"] = f"LAPORAN EVALUASI & KEDISIPLINAN MUTABA'AH PETUGAS ({unit_filter})"
    ws1["A1"].font = title_font
    ws1["A2"] = f"Periode Analisis: {eval_data.get('start_date')} s/d {eval_data.get('end_date')} ({eval_data.get('total_days')} Hari Kalender) | Dicetak pada: {datetime.datetime.now().strftime('%d %B %Y %H:%M')} WIB"
    ws1["A2"].font = subtitle_font

    headers1 = [
        "No", "Nama Petugas", "Unit Kerja", "Tugas / Jabatan", "No WhatsApp",
        "Target Hari", "Hari Lapor", "Kepatuhan (%)", "Sholat 5 Waktu", "Tilawah", "Dzikir", "Predikat Disiplin", "Lapor Terakhir"
    ]
    ws1.append([])  # Row 3 blank
    ws1.append(headers1)  # Row 4 headers

    for col_idx in range(1, len(headers1) + 1):
        cell = ws1.cell(row=4, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for idx, e in enumerate(eval_data.get("evaluasi", []), start=1):
        p = e["personnel"]
        row_vals = [
            idx,
            p["name"],
            p["unit"],
            p["job_title"],
            p["phone"] or "-",
            e["total_days"],
            e["days_reported"],
            f"{e['compliance_pct']}%",
            e["sholat_5_count"],
            e["tilawah_count"],
            e["dzikir_count"],
            e["predikat"],
            e["last_reported_date"]
        ]
        ws1.append(row_vals)
        cur_row = ws1.max_row
        for c in range(1, len(headers1) + 1):
            cell = ws1.cell(row=cur_row, column=c)
            cell.font = regular_font
            cell.border = border_thin
            if c in (1, 6, 7, 8, 9, 10, 11, 13):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c == 12:
                cell.font = bold_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

    ws1.auto_filter.ref = f"A4:M{ws1.max_row}"
    for col in ws1.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws1.column_dimensions[col_letter].width = min(40, max(max_len + 3, 11))

    # ========================================================
    # SHEET 2: RIWAYAT LOG MUTABAAH
    # ========================================================
    ws2 = wb.create_sheet(title="Log Mutabaah")
    ws2["A1"] = f"RIWAYAT TRANSAKSI LOG MUTABA'AH YAUMIYAH (WHATSAPP)"
    ws2["A1"].font = title_font
    ws2["A2"] = f"Total Entri: {logs_data.get('total_records')} Catatan Masuk | Sumber: mutabaah_logs.json"
    ws2["A2"].font = subtitle_font

    headers2 = ["No", "Tanggal", "Jam WIB", "Nama Petugas", "Unit", "Sholat", "Tilawah", "Dzikir", "Nomor Pengirim WA"]
    ws2.append([])
    ws2.append(headers2)

    for col_idx in range(1, len(headers2) + 1):
        cell = ws2.cell(row=4, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for idx, l in enumerate(logs_data.get("logs", []), start=1):
        row_vals = [
            idx,
            l["date"],
            l["time_wib"] or "-",
            l["nama"],
            l["unit"],
            l["sholat"] or "-",
            l["tilawah"] or "-",
            l["dzikir"] or "-",
            l["sender"] or "-"
        ]
        ws2.append(row_vals)
        cur_row = ws2.max_row
        for c in range(1, len(headers2) + 1):
            cell = ws2.cell(row=cur_row, column=c)
            cell.font = regular_font
            cell.border = border_thin
            if c in (1, 2, 3):
                cell.alignment = Alignment(horizontal="center", vertical="center")

    ws2.auto_filter.ref = f"A4:I{ws2.max_row}"
    for col in ws2.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws2.column_dimensions[col_letter].width = min(45, max(max_len + 3, 12))

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
