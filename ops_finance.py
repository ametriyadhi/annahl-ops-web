# -*- coding: utf-8 -*-
"""
ops_finance.py - Modul Manajemen Keuangan & Pengeluaran Bagian Umum (GA)
An Nahl Islamic School - Terintegrasi dengan Standar FKP GA 2026-2027,
Google Drive Upload, Vision AI (Gemini Flash), & WhatsApp Bot Baileys.
"""

import os
import re
import json
import uuid
import sqlite3
import requests
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify, session, current_app

WIB = ZoneInfo("Asia/Jakarta")

def now_wib():
    return datetime.now(WIB)

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"

ops_finance_bp = Blueprint('ops_finance', __name__)

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.row_factory = sqlite3.Row
    return conn

def get_gemini_api_key():
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM system_settings WHERE key = 'GEMINI_API_KEY'").fetchone()
        if row and row['value']:
            return row['value']
    except Exception:
        pass
    finally:
        conn.close()
    return os.environ.get("GEMINI_API_KEY", "")

# ==================== COA MASTER LOOKUP & FALLBACK ====================
COA_MASTER = {
    '51411-001': {'name': 'Pemeliharaan Gedung', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '1. APBS Unit'},
    '51411-002': {'name': 'Pemeliharaan Kolam Renang - Obat Kolam', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '1. APBS Unit'},
    '51411-003': {'name': 'Pemeliharaan Kolam Renang - Treatment Vacum', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '2. SPP'},
    '51411-004': {'name': 'Pemeliharaan Prasarana (Jalan, Pagar, Saluran)', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '1. APBS Unit'},
    '51411-005': {'name': 'Pemeliharaan Kendaraan - Service Motor', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '2. SPP'},
    '51411-006': {'name': 'Pemeliharaan Kendaraan - Service Mobil', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '2. SPP'},
    '51411-007': {'name': 'Pemeliharaan Kendaraan - Pajak Motor', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '1. APBS Unit'},
    '51411-008': {'name': 'Pemeliharaan Kendaraan - Pajak Mobil', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '1. APBS Unit'},
    '51411-009': {'name': 'Pemeliharaan Barang Inventaris', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '1. APBS Unit'},
    '51411-010': {'name': 'Pemeliharaan Lainnya - Fogging', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '2. SPP'},
    '51411-011': {'name': 'Pemeliharaan AC - Cuci', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '2. SPP'},
    '51411-012': {'name': 'Pemeliharaan AC - Service & Perbaikan', 'cat': 'PEMELIHARAAN & PERBAIKAN', 'source': '2. SPP'},
    '51412-001': {'name': 'Biaya Perizinan', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51412-002': {'name': 'Iuran Lingkungan (Keamanan & Kebersihan Kawasan)', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51412-004': {'name': 'Admin Bank', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51412-005': {'name': 'Sewa Lahan / Ruang Ecopark & ISBI', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51412-006': {'name': 'Patty Cash GA (Kas Kecil Operasional)', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51412-007': {'name': 'Konsumsi Rapat, Tamu, Olahraga & Lembur', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51412-008': {'name': 'Pelatihan SDM Umum & Sertifikasi K3', 'cat': 'ADMINISTRASI DAN UMUM', 'source': '2. SPP'},
    '51413-001': {'name': 'Listrik PLN (YPPI & An Nahl)', 'cat': 'ENERGI & KOMUNIKASI', 'source': '2. SPP'},
    '51413-002': {'name': 'Telepon & Internet Sekolah', 'cat': 'ENERGI & KOMUNIKASI', 'source': '1. APBS Unit'},
    '51413-003': {'name': 'Air PDAM & Air Minum Galon', 'cat': 'ENERGI & KOMUNIKASI', 'source': '2. SPP'},
    '51414-001': {'name': 'Perlengkapan Kebersihan & Sanitasi OB', 'cat': 'PERLENGKAPAN', 'source': '2. SPP'},
    '51414-002': {'name': 'Perlengkapan Taman & Pertamanan', 'cat': 'PERLENGKAPAN', 'source': '2. SPP'},
    '51414-003': {'name': 'Barang Habis Pakai Chemical & Sabun', 'cat': 'PERLENGKAPAN', 'source': '2. SPP'},
    '51414-004': {'name': 'Barang Habis Pakai Sarpras & Alat Kerja', 'cat': 'PERLENGKAPAN', 'source': '2. SPP'},
    '51414-005': {'name': 'Perlengkapan Umum Sekolah & Logistik', 'cat': 'PERLENGKAPAN', 'source': '2. SPP'},
    '51415-001': {'name': 'Investasi PGTK', 'cat': 'INVESTASI', 'source': '2. SPP'},
    '51415-002': {'name': 'Investasi SD', 'cat': 'INVESTASI', 'source': '2. SPP'},
    '51415-003': {'name': 'Investasi SMP', 'cat': 'INVESTASI', 'source': '2. SPP'},
    '51415-004': {'name': 'Investasi SMA', 'cat': 'INVESTASI', 'source': '2. SPP'},
    '51415-005': {'name': 'Investasi Supporting & Sarpras Umum', 'cat': 'INVESTASI', 'source': '2. SPP'},
}

# ==================== VISION AI PARSER ENGINE ====================
def parse_receipt_with_vision(image_base64=None, mime_type="image/jpeg", caption_text="", reporter_name=""):
    """
    Menggunakan Gemini 3.5 Flash Lite untuk mengurai bukti bayar / struk / invoice
    menjadi entitas keuangan berstandar FKP GA 2026-2027.
    """
    api_key = get_gemini_api_key()
    today_str = now_wib().strftime('%Y-%m-%d')

    coa_reference_text = "\n".join([f"- {k}: {v['name']} ({v['cat']})" for k, v in COA_MASTER.items()])

    prompt = f"""Anda adalah AI Auditor & Akuntan Keuangan Resmi An Nahl Islamic School Bagian Umum (GA).
Tugas Anda: Analisis bukti transaksi (transfer m-banking / struk ATM / nota belanja / kwitansi / invoice) berikut secara teliti.

Tanggal hari ini: {today_str}
Pengirim Laporan: {reporter_name or 'Bu Rinni / Tim GA'}
Keterangan Tambahan / Caption: "{caption_text}"

Referensi Pos Mata Anggaran FKP GA 2026-2027:
{coa_reference_text}

Aturan Penilaian:
1. Nominal: Ambil jumlah uang yang dibayarkan (angka bulat tanpa titik/koma/Rp).
2. Tanggal: Format YYYY-MM-DD. Jika di gambar tidak ada tahun, gunakan tahun 2026. Jika tidak terbaca, gunakan tanggal hari ini: {today_str}.
3. Penerima / Toko: Nama merchant / toko / pemilik rekening tujuan transfer.
4. No. Referensi: Nomor referensi transfer, nomor invoice, atau nomor nota.
5. Uraian: Rincian barang / jasa yang dibeli (contoh: 'Cat dulux 2 galon & kuas untuk toilet SD').
6. Pos Mata Anggaran: Pilih kode COA FKP yang paling tepat dari daftar referensi di atas.
7. Kategori Utama: Salah satu dari [PEMELIHARAAN & PERBAIKAN, ADMINISTRASI DAN UMUM, ENERGI & KOMUNIKASI, PERLENGKAPAN, INVESTASI].
8. Sumber Dana: '1. APBS Unit' atau '2. SPP'.
9. Unit Target: TK, SD, SMP, SMA, Supporting, atau Umum.

Output HANYA berupa JSON murni tanpa markdown fence atau teks tambahan:
{{
  "tanggal": "YYYY-MM-DD",
  "nominal": 0,
  "penerima_toko": "",
  "bank_info": "",
  "nomor_referensi": "",
  "uraian": "",
  "items": [],
  "coa_code": "51411-001",
  "coa_nama": "Pemeliharaan Gedung",
  "kategori_utama": "PEMELIHARAAN & PERBAIKAN",
  "sumber_dana": "2. SPP",
  "unit_target": "Umum",
  "catatan_audit": ""
}}"""

    parts = [{"text": prompt}]
    if image_base64:
        parts.append({
            "inline_data": {
                "mime_type": mime_type or "image/jpeg",
                "data": image_base64
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1000
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean markdown codeblocks
            clean_json = re.sub(r'^```json\s*', '', raw_text)
            clean_json = re.sub(r'\s*```$', '', clean_json).strip()
            data = json.loads(clean_json)
            
            # Validasi COA code
            coa_code = data.get('coa_code', '51412-006')
            if coa_code in COA_MASTER:
                data['coa_nama'] = COA_MASTER[coa_code]['name']
                data['kategori_utama'] = COA_MASTER[coa_code]['cat']
            return data
        else:
            print(f"[Vision AI Error {res.status_code}] {res.text[:200]}")
    except Exception as e:
        print("[Vision AI Exception]", e)

    # Fallback jika gagal AI
    return {
        "tanggal": today_str,
        "nominal": 0,
        "penerima_toko": "Toko / Rekening",
        "bank_info": "",
        "nomor_referensi": "-",
        "uraian": caption_text or "Pengeluaran Operasional GA",
        "items": [],
        "coa_code": "51412-006",
        "coa_nama": "Patty Cash GA (Kas Kecil Operasional)",
        "kategori_utama": "ADMINISTRASI DAN UMUM",
        "sumber_dana": "2. SPP",
        "unit_target": "Umum",
        "catatan_audit": "Dianalisis secara manual oleh sistem (Fallback)"
    }


# ==================== TRANSACTION RECORDING ENGINE ====================
def record_ga_expense(parsed_data, drive_file_url="", drive_file_id="", reporter_name="", reporter_wa="", source="WHATSAPP_BOT", file_hash=""):
    """
    Menyimpan data transaksi pengeluaran GA ke tabel ops_ga_expenses
    dan men-generate nomor KB berstandar FKP GA.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        now = now_wib()
        date_str = parsed_data.get('tanggal') or now.strftime('%Y-%m-%d')
        
        # Format Periode Bulan (contoh: Oktober 2026)
        try:
            t_dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
            bulan_names = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            month_period = f"{bulan_names[t_dt.month]} {t_dt.year}"
            month_code = str(t_dt.month)
        except Exception:
            month_period = now.strftime('%B %Y')
            month_code = str(now.month)

        # Generate Unique Expense ID: EXP-YYYYMMDD-XXXX
        date_num = now.strftime('%Y%m%d')
        hex_rand = uuid.uuid4().hex[:4].upper()
        expense_id = f"EXP-{date_num}-{hex_rand}"

        coa_code = parsed_data.get('coa_code', '51412-006')
        sumber_dana = parsed_data.get('sumber_dana', '2. SPP')
        
        # Hitung urutan transaksi dalam bulan ini untuk KB code FKP
        count_row = cur.execute("SELECT COUNT(*) as c FROM ops_ga_expenses WHERE month_period = ?", (month_period,)).fetchone()
        seq_num = (count_row['c'] if count_row else 0) + 1
        
        # Format KB Code FKP: [Bulan][COA][Sumber Dana] [Seq] (contoh: 1051411-0012. SPP 45)
        kb_code = f"{month_code}{coa_code}{sumber_dana} {seq_num}"

        amount = int(parsed_data.get('nominal') or 0)
        vendor_name = parsed_data.get('penerima_toko') or '-'
        bank_info = parsed_data.get('bank_info') or ''
        ref_no = parsed_data.get('nomor_referensi') or '-'
        description = parsed_data.get('uraian') or 'Pengeluaran GA'
        coa_name = parsed_data.get('coa_nama') or COA_MASTER.get(coa_code, {}).get('name', 'Umum')
        main_cat = parsed_data.get('kategori_utama') or COA_MASTER.get(coa_code, {}).get('cat', 'ADMINISTRASI DAN UMUM')
        unit_target = parsed_data.get('unit_target') or 'Umum'
        items_json = json.dumps(parsed_data.get('items', []))
        ai_raw_json = json.dumps(parsed_data)

        cur.execute("""
            INSERT INTO ops_ga_expenses 
            (id, kb_code, transaction_date, academic_year, month_period, coa_code, coa_name, main_category,
             fund_source, unit_target, amount, vendor_name, bank_info, reference_no, description, items_json,
             drive_file_url, drive_file_id, reporter_name, reporter_wa, source, status, approval_status,
             file_hash, ai_raw_json, created_at, updated_at)
            VALUES (?, ?, ?, '2026-2027', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Recorded', 'Pending', ?, ?, ?, ?)
        """, (
            expense_id, kb_code, date_str, month_period, coa_code, coa_name, main_cat,
            sumber_dana, unit_target, amount, vendor_name, bank_info, ref_no, description, items_json,
            drive_file_url, drive_file_id, reporter_name, reporter_wa, source,
            file_hash, ai_raw_json, now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()

        return {
            'success': True,
            'id': expense_id,
            'kb_code': kb_code,
            'tanggal': date_str,
            'nominal': amount,
            'nominal_formatted': f"Rp {amount:,.0f}".replace(',', '.'),
            'penerima_toko': vendor_name,
            'bank_info': bank_info,
            'nomor_referensi': ref_no,
            'uraian': description,
            'coa_code': coa_code,
            'coa_nama': coa_name,
            'kategori_utama': main_cat,
            'sumber_dana': sumber_dana,
            'unit_target': unit_target,
            'drive_file_url': drive_file_url,
            'reporter_name': reporter_name,
            'month_period': month_period
        }
    except Exception as e:
        conn.rollback()
        print("[Record Expense Error]", e)
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


# ==================== REST API ENDPOINTS ====================

@ops_finance_bp.route('/api/ga/expenses/process-upload', methods=['POST'])
def api_process_expense_upload():
    """
    Endpoint menerima upload bukti transaksi dari WhatsApp Bot atau Web form.
    Dilengkapi deteksi anti-duplikat otomatis (file hash, nomor referensi, dan transaksi kembar).
    """
    data = request.get_json(silent=True) or {}
    
    # 1. Parameter Identitas & Caption
    reporter_wa = data.get('reporter_wa') or request.form.get('reporter_wa', '')
    reporter_name = data.get('reporter_name') or request.form.get('reporter_name', 'Bu Rinni')
    caption_text = data.get('caption') or request.form.get('caption', '')
    drive_file_url = data.get('drive_file_url') or request.form.get('drive_file_url', '')
    drive_file_id = data.get('drive_file_id') or request.form.get('drive_file_id', '')
    image_base64 = data.get('image_base64', '')
    mime_type = data.get('mime_type', 'image/jpeg')
    file_hash = data.get('file_hash', '').strip()

    # Jika dikirim via multipart file upload
    if 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename:
            file_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(file_bytes).decode('utf-8')
            mime_type = uploaded_file.content_type or 'image/jpeg'

    # Hitung hash SHA-256 jika belum ada
    if not file_hash and image_base64:
        try:
            import hashlib
            file_hash = hashlib.sha256(base64.b64decode(image_base64)).hexdigest()
        except Exception:
            pass

    # ==================== DETEKSI DUPLIKAT LAYER 1: FILE HASH IDENTIK ====================
    if file_hash:
        conn = get_db()
        try:
            dup = conn.execute("SELECT * FROM ops_ga_expenses WHERE file_hash = ? LIMIT 1", (file_hash,)).fetchone()
            if dup:
                return jsonify({
                    'success': False,
                    'is_duplicate': True,
                    'duplicate_by': 'FILE_HASH',
                    'existing_id': dup['id'],
                    'existing_kb_code': dup['kb_code'],
                    'existing_date': dup['transaction_date'],
                    'existing_nominal': dup['amount'],
                    'existing_nominal_formatted': f"Rp {dup['amount']:,.0f}".replace(',', '.'),
                    'existing_vendor': dup['vendor_name'],
                    'existing_ref': dup['reference_no'],
                    'existing_coa': f"{dup['coa_code']} ({dup['coa_name']})",
                    'existing_drive_url': dup['drive_file_url'],
                    'existing_created_at': dup['created_at'],
                    'message': 'Foto / file bukti transaksi ini persis sama dengan dokumen yang sudah ada di sistem.'
                }), 200
        finally:
            conn.close()

    # 2. Analisis Vision AI Gemini
    parsed = parse_receipt_with_vision(
        image_base64=image_base64,
        mime_type=mime_type,
        caption_text=caption_text,
        reporter_name=reporter_name
    )

    # ==================== DETEKSI DUPLIKAT LAYER 2: NOMOR REFERENSI / INVOICE ====================
    ref_no = (parsed.get('nomor_referensi') or '').strip()
    invalid_refs = ['-', 'NONE', 'TIDAK ADA', 'NULL', 'BERHASIL', '', 'SUCCESS', 'OK', 'TRANSFER', 'M-BCA', 'TRF']
    if ref_no and ref_no.upper() not in invalid_refs and len(ref_no) >= 5:
        conn = get_db()
        try:
            dup = conn.execute("SELECT * FROM ops_ga_expenses WHERE UPPER(reference_no) = UPPER(?) LIMIT 1", (ref_no,)).fetchone()
            if dup:
                return jsonify({
                    'success': False,
                    'is_duplicate': True,
                    'duplicate_by': 'REFERENCE_NO',
                    'existing_id': dup['id'],
                    'existing_kb_code': dup['kb_code'],
                    'existing_date': dup['transaction_date'],
                    'existing_nominal': dup['amount'],
                    'existing_nominal_formatted': f"Rp {dup['amount']:,.0f}".replace(',', '.'),
                    'existing_vendor': dup['vendor_name'],
                    'existing_ref': dup['reference_no'],
                    'existing_coa': f"{dup['coa_code']} ({dup['coa_name']})",
                    'existing_drive_url': dup['drive_file_url'],
                    'existing_created_at': dup['created_at'],
                    'message': f"Nomor referensi / nota invoice '{ref_no}' sudah terdaftar sebelumnya di sistem."
                }), 200
        finally:
            conn.close()

    # ==================== DETEKSI DUPLIKAT LAYER 3: TRANSAKSI KEMBAR (TANGGAL, TOKO & NOMINAL) ====================
    nominal = int(parsed.get('nominal') or 0)
    tgl = parsed.get('tanggal') or ''
    vendor = (parsed.get('penerima_toko') or '').strip()
    if nominal > 0 and tgl and vendor and vendor != '-':
        conn = get_db()
        try:
            dup = conn.execute("""
                SELECT * FROM ops_ga_expenses 
                WHERE transaction_date = ? AND amount = ? AND UPPER(vendor_name) = UPPER(?)
                LIMIT 1
            """, (tgl, nominal, vendor)).fetchone()
            if dup:
                return jsonify({
                    'success': False,
                    'is_duplicate': True,
                    'duplicate_by': 'EXACT_TRANSACTION',
                    'existing_id': dup['id'],
                    'existing_kb_code': dup['kb_code'],
                    'existing_date': dup['transaction_date'],
                    'existing_nominal': dup['amount'],
                    'existing_nominal_formatted': f"Rp {dup['amount']:,.0f}".replace(',', '.'),
                    'existing_vendor': dup['vendor_name'],
                    'existing_ref': dup['reference_no'],
                    'existing_coa': f"{dup['coa_code']} ({dup['coa_name']})",
                    'existing_drive_url': dup['drive_file_url'],
                    'existing_created_at': dup['created_at'],
                    'message': f"Pengeluaran ke '{vendor}' sebesar Rp {nominal:,.0f}".replace(',', '.') + f" pada tanggal {tgl} sudah pernah dicatat sebelumnya."
                }), 200
        finally:
            conn.close()

    # 3. Simpan ke Database jika bukan duplikat
    result = record_ga_expense(
        parsed_data=parsed,
        drive_file_url=drive_file_url,
        drive_file_id=drive_file_id,
        reporter_name=reporter_name,
        reporter_wa=reporter_wa,
        source="WHATSAPP_BOT" if reporter_wa else "WEB_UPLOAD",
        file_hash=file_hash
    )

    return jsonify(result), (200 if result.get('success') else 500)


@ops_finance_bp.route('/api/ga/expenses', methods=['GET'])
def api_get_ga_expenses():
    """Mengambil riwayat transaksi pengeluaran GA dengan filter."""
    conn = get_db()
    month_filter = request.args.get('month', '').strip()
    category_filter = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()

    query = "SELECT * FROM ops_ga_expenses WHERE 1=1"
    params = []

    if month_filter:
        query += " AND month_period = ?"
        params.append(month_filter)
    if category_filter:
        query += " AND main_category = ?"
        params.append(category_filter)
    if search:
        query += " AND (description LIKE ? OR vendor_name LIKE ? OR coa_name LIKE ? OR kb_code LIKE ?)"
        wild = f"%{search}%"
        params.extend([wild, wild, wild, wild])

    query += " ORDER BY transaction_date DESC, created_at DESC LIMIT 200"

    rows = conn.execute(query, params).fetchall()
    expenses = [dict(r) for r in rows]
    conn.close()

    return jsonify({'success': True, 'count': len(expenses), 'data': expenses})


@ops_finance_bp.route('/api/ga/expenses/stats', methods=['GET'])
def api_get_ga_expense_stats():
    """Mengambil statistik realisasi pengeluaran vs anggaran FKP."""
    conn = get_db()
    try:
        # Total per kategori utama
        cat_stats = conn.execute("""
            SELECT main_category, SUM(amount) as total_realisasi, COUNT(*) as total_transaksi
            FROM ops_ga_expenses
            GROUP BY main_category
        """).fetchall()

        # Total seluruh realisasi
        tot_row = conn.execute("SELECT SUM(amount) as grand_total, COUNT(*) as count FROM ops_ga_expenses").fetchone()
        grand_total = tot_row['grand_total'] or 0
        total_trx = tot_row['count'] or 0

        # Master Plafon Anggaran dari Induk COA (-000)
        budget_rows = conn.execute("SELECT parent_category, budget_annual as total_budget FROM ops_ga_coa WHERE coa_code LIKE '%-000'").fetchall()
        budgets = {b['parent_category']: b['total_budget'] for b in budget_rows}

        category_summary = []
        for cs in cat_stats:
            cat_name = cs['main_category']
            real = cs['total_realisasi'] or 0
            bgt = budgets.get(cat_name, 0)
            pct = round((real / bgt * 100), 1) if bgt > 0 else 0
            category_summary.append({
                'category': cat_name,
                'realisasi': real,
                'anggaran': bgt,
                'sisa': bgt - real,
                'persentase': pct,
                'transaksi': cs['total_transaksi']
            })

        return jsonify({
            'success': True,
            'grand_total_realisasi': grand_total,
            'total_transaksi': total_trx,
            'categories': category_summary
        })
    finally:
        conn.close()


@ops_finance_bp.route('/api/ga/expenses/<expense_id>/update', methods=['POST'])
def api_update_ga_expense(expense_id):
    """Memperbarui data transaksi pengeluaran GA secara manual."""
    data = request.get_json(silent=True) or request.form.to_dict()
    conn = get_db()
    cur = conn.cursor()
    try:
        now = now_wib()
        date_str = data.get('transaction_date') or now.strftime('%Y-%m-%d')
        amount = int(data.get('amount') or 0)
        vendor_name = data.get('vendor_name', '').strip() or '-'
        bank_info = data.get('bank_info', '').strip()
        ref_no = data.get('reference_no', '').strip() or '-'
        description = data.get('description', '').strip() or '-'
        coa_code = data.get('coa_code', '51412-006')
        fund_source = data.get('fund_source', '2. SPP')
        unit_target = data.get('unit_target', 'Umum')

        # Lookup COA info
        coa_info = COA_MASTER.get(coa_code, {'name': 'Kas Kecil GA', 'cat': 'ADMINISTRASI DAN UMUM'})
        coa_name = coa_info['name']
        main_cat = coa_info['cat']

        # Update bulan period jika tanggal berubah
        try:
            t_dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
            bulan_names = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            month_period = f"{bulan_names[t_dt.month]} {t_dt.year}"
        except Exception:
            month_period = now.strftime('%B %Y')

        cur.execute("""
            UPDATE ops_ga_expenses
            SET transaction_date = ?,
                month_period = ?,
                amount = ?,
                vendor_name = ?,
                bank_info = ?,
                reference_no = ?,
                description = ?,
                coa_code = ?,
                coa_name = ?,
                main_category = ?,
                fund_source = ?,
                unit_target = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            date_str, month_period, amount, vendor_name, bank_info, ref_no,
            description, coa_code, coa_name, main_cat, fund_source, unit_target,
            now.strftime('%Y-%m-%d %H:%M:%S'), expense_id
        ))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({'success': False, 'error': 'Transaksi tidak ditemukan'}), 404

        return jsonify({'success': True, 'message': 'Data transaksi berhasil diperbarui'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@ops_finance_bp.route('/api/ga/expenses/<expense_id>/delete', methods=['POST', 'DELETE'])
def api_delete_ga_expense(expense_id):
    """Menghapus transaksi pengeluaran GA."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM ops_ga_expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Transaksi berhasil dihapus'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
