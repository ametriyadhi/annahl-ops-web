# -*- coding: utf-8 -*-
"""
ops_finance_ecopark.py - Modul Manajemen Keuangan Terpadu Ciangsana Ecopark
An Nahl Islamic School - Terintegrasi dengan Standar RKAS/RAPBS FKP ECO 2026-2027,
Google Drive Upload, Vision AI (Gemini Flash), & WhatsApp Bot Baileys.
Mendukung Pencatatan Kas Masuk (Pendapatan/Omset) & Kas Keluar (Pengeluaran Operasional).
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
from flask import Blueprint, request, jsonify, session, Response

WIB = ZoneInfo("Asia/Jakarta")

def now_wib():
    return datetime.now(WIB)

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"

ops_finance_ecopark_bp = Blueprint('ops_finance_ecopark', __name__)

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

# ==================== COA MASTER LOOKUP ====================
def get_eco_coa_master():
    conn = get_db()
    try:
        rows = conn.execute("SELECT coa_code, coa_name, parent_category, budget_annual, is_parent FROM ops_eco_coa WHERE is_active = 1").fetchall()
        master = {}
        for r in rows:
            master[r['coa_code']] = {
                'name': r['coa_name'],
                'parent': r['parent_category'],
                'budget': r['budget_annual'],
                'is_parent': bool(r['is_parent'])
            }
        return master
    finally:
        conn.close()

# Month translation helper
def format_month_period(date_str):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        bulan_indo = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                      'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        return f"{bulan_indo[dt.month - 1]} {dt.year}"
    except Exception:
        return now_wib().strftime('%B %Y')

# Smart classification rule for expense
def classify_eco_expense_rule(text):
    txt = str(text or "").lower()
    if any(w in txt for w in ['benih', 'bibit', 'pupuk', 'm21', 'obat tanaman', 'polybag', 'pot', 'tanaman', 'kemasan', 'packing']):
        if 'bibit' in txt or 'benih' in txt:
            return '52111-003', 'Bibit Sayuran', 'OPERASIONAL BUDIDAYA'
        if any(w in txt for w in ['pupuk', 'm21', 'obat']):
            return '52111-001', 'Pupuk & Obat untuk tanaman', 'OPERASIONAL BUDIDAYA'
        if any(w in txt for w in ['polybag', 'pot']):
            return '52111-002', 'Polybag & Pot', 'OPERASIONAL BUDIDAYA'
        if any(w in txt for w in ['kemasan', 'packing', 'plastik', 'hd merah']):
            return '52111-004', 'Kemasan', 'OPERASIONAL BUDIDAYA'
        return '52111-000', 'OPERASIONAL BUDIDAYA', 'OPERASIONAL BUDIDAYA'

    if any(w in txt for w in ['pur', 'gt', 'gd21', 'garda', 'dedak', 'pakan', 'top mix', 'neubro', 'tetrachlor', 'lele', 'kelinci', 'telur', 'ngarit', 'ayam', 'bebek', 'unggas', 'vitamin']):
        if 'kelinci' in txt:
            return '52121-006', 'Budidaya Kelinci (Pakan)', 'OPERASIONAL PETERNAKAN'
        if 'lele' in txt:
            return '52121-007', 'Operasional Lele', 'OPERASIONAL PETERNAKAN'
        if any(w in txt for w in ['vitamin', 'obat', 'tetrachlor', 'neubro']):
            return '52121-003', 'Vitamin & obat-obatan hewan ternak', 'OPERASIONAL PETERNAKAN'
        if 'ngarit' in txt:
            return '52121-004', 'Bensin untuk operasional kendaraan ngarit', 'OPERASIONAL PETERNAKAN'
        return '52121-008', 'Hewan Edukasi (Pakan Unggas/Ternak)', 'OPERASIONAL PETERNAKAN'

    if any(w in txt for w in ['pompa', 'chainsaw', 'mesin potong rumput', 'kambing pejantan', 'indukan', 'sign system', 'kontener']):
        if 'pompa' in txt:
            return '52134-001', 'Mesin & Pompa Air Ecopark', 'INVESTASI'
        if 'potong rumput' in txt:
            return '52134-004', 'Pengadaan Mesin Potong Rumput', 'INVESTASI'
        return '52134-000', 'INVESTASI', 'INVESTASI'

    if any(w in txt for w in ['kunjungan', 'outbound', 'workshop', 'edukasi', 'jersey', 'panahan']):
        return '52132-000', 'OPERASIONAL KUNJUNGAN & EDUKASI', 'OPERASIONAL KUNJUNGAN & EDUKASI'

    if any(w in txt for w in ['banner', 'spanduk', 'brosur', 'marketing', 'reels', 'kuota', 'pulsa']):
        return '52133-000', 'MARKETING', 'MARKETING'

    if any(w in txt for w in ['pertalite', 'bensin', 'oli', 'solar', 'mesin rumput']):
        return '52131-005', 'Bensin dan Olie untuk mesin potong rumput', 'PEMELIHARAAN'
    if any(w in txt for w in ['keramik', 'cat', 'semen', 'pipa', 'lampu', 'kawat', 'sarpras', 'tukang', 'toilet', 'auditorium', 'kunci', 'baut', 'gergaji', 'pisau']):
        return '52131-001', 'Perbaikan Sarpras & Fasilitas', 'PEMELIHARAAN'
    if any(w in txt for w in ['sabun', 'sapu', 'pembersih']):
        return '52131-006', 'Sabun & alat Pembersihan toilet', 'PEMELIHARAAN'
    if any(w in txt for w in ['gorengan', 'makan', 'kopi', 'konsumsi', 'snack']):
        return '52131-008', 'Konsumsi team', 'PEMELIHARAAN'
    if 'fogging' in txt:
        return '52131-012', 'Fogging (Solar, Bensin, Obat)', 'PEMELIHARAAN'

    return '52131-000', 'PEMELIHARAAN', 'PEMELIHARAAN'

# ==================== STRUCTURED TEXT PARSER ====================
def parse_eco_text_report(text):
    """
    Mengurai format teks cepat WhatsApp:
    Format Belanja:
      #belanja_ecopark
      Tanggal: DD-MM-YYYY
      Pos: Pakan
      Barang: Pur GT 1 karung
      Nominal: 395.000
      Toko: Toko Berkah
      Metode: Cash / Transfer
      Keterangan: ...
    Format Pemasukan:
      #pemasukan_ecopark
      Tanggal: DD-MM-YYYY
      Kategori: Sewa Fasilitas
      Uraian: Sewa Kolam Renang
      Pembeli: Bu Ani
      Nominal: 500.000
      Metode: Transfer
      Keterangan: ...
    """
    txt = text.strip()
    today_str = now_wib().strftime('%Y-%m-%d')
    lines = [l.strip() for l in txt.split('\n') if l.strip()]

    # Tentukan tipe transaksi
    first_line_lower = lines[0].lower() if lines else ""
    is_income = any(tag in first_line_lower for tag in ['#pemasukan', '#masuk_ecopark', '#omset_ecopark', '#pendapatan_ecopark', '#terima_ecopark'])
    is_expense = any(tag in first_line_lower for tag in ['#belanja', '#keluar_ecopark', '#pengeluaran_ecopark', '#nota_ecopark', '#kas_ecopark'])

    if not is_income and not is_expense:
        # Default deteksi berdasarkan kata kunci
        if any(w in txt.lower() for w in ['pembeli:', 'omset', 'sewa kolam', 'tiket', 'sayuran terjual', 'penerimaan']):
            is_income = True
        else:
            is_expense = True

    trx_type = "INCOME" if is_income else "EXPENSE"

    extracted = {
        'trx_type': trx_type,
        'tanggal': today_str,
        'nominal': 0,
        'pihak': '', # Toko atau Pembeli
        'kategori': '',
        'uraian': '',
        'metode': 'Cash',
        'keterangan': ''
    }

    for line in lines:
        if ':' in line:
            k, v = line.split(':', 1)
            k = k.strip().lower()
            v = v.strip()
            if any(x in k for x in ['tanggal', 'tgl', 'waktu']):
                # Parsing tanggal DD-MM-YYYY atau YYYY-MM-DD
                m_iso = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', v)
                m_indo = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', v)
                if m_iso:
                    extracted['tanggal'] = f"{m_iso.group(1)}-{int(m_iso.group(2)):02d}-{int(m_iso.group(3)):02d}"
                elif m_indo:
                    extracted['tanggal'] = f"{m_indo.group(3)}-{int(m_indo.group(2)):02d}-{int(m_indo.group(1)):02d}"
            elif any(x in k for x in ['nominal', 'jumlah', 'harga', 'total', 'biaya']):
                # Bersihkan Rp, titik, koma
                num_str = re.sub(r'[^\d]', '', v)
                if num_str:
                    extracted['nominal'] = float(num_str)
            elif any(x in k for x in ['toko', 'vendor', 'pembeli', 'nama', 'konsumen', 'pelanggan']):
                extracted['pihak'] = v
            elif any(x in k for x in ['pos', 'kategori', 'jenis', 'bidang']):
                extracted['kategori'] = v
            elif any(x in k for x in ['barang', 'uraian', 'deskripsi', 'layanan', 'produk', 'item']):
                extracted['uraian'] = v
            elif any(x in k for x in ['metode', 'transaksi', 'bayar', 'via']):
                if 'transfer' in v.lower() or 'tf' in v.lower():
                    extracted['metode'] = 'Transfer'
                elif 'qris' in v.lower():
                    extracted['metode'] = 'QRIS'
                else:
                    extracted['metode'] = 'Cash'
            elif any(x in k for x in ['keterangan', 'catatan', 'notes', 'ket']):
                extracted['keterangan'] = v

    if not extracted['uraian']:
        # Ambil baris yang belum terurai sebagai uraian
        for l in lines[1:]:
            if not any(l.lower().startswith(p) for p in ['tanggal', 'nominal', 'toko', 'pos', 'metode', 'kategori', 'pembeli']):
                extracted['uraian'] = l.strip()
                break

    if not extracted['pihak']:
        extracted['pihak'] = "Pembeli / Pengunjung Ecopark" if is_income else "Toko / Mitra Ecopark"

    # Mapping COA
    if is_expense:
        coa_code, coa_name, parent_cat = classify_eco_expense_rule(f"{extracted['kategori']} {extracted['uraian']}")
        extracted['coa_code'] = coa_code
        extracted['coa_nama'] = coa_name
        extracted['main_category'] = parent_cat
    else:
        cat_name = extracted['kategori'] or 'Sewa Fasilitas'
        extracted['coa_code'] = '41000-000'
        extracted['coa_nama'] = f"Penerimaan {cat_name}"
        extracted['main_category'] = cat_name

    return extracted


# ==================== VISION AI PARSER (GEMINI FLASH) ====================
def parse_eco_receipt_with_vision(image_base64=None, mime_type="image/jpeg", caption_text="", reporter_name=""):
    """
    Menggunakan Gemini Flash untuk membaca bukti transfer m-banking atau struk/nota belanja Ecopark.
    Mendeteksi otomatis apakah ini Kas Masuk (Pendapatan) atau Kas Keluar (Pengeluaran).
    """
    api_key = get_gemini_api_key()
    today_str = now_wib().strftime('%Y-%m-%d')

    coa_master = get_eco_coa_master()
    coa_summary_lines = []
    for code, info in coa_master.items():
        if not info['is_parent']:
            coa_summary_lines.append(f"- {code}: {info['name']} (Induk: {info['parent']})")
    coa_text = "\n".join(coa_summary_lines[:35])

    prompt = f"""Anda adalah AI Auditor & Akuntan Resmi Ciangsana Ecopark (An Nahl Islamic School).
Tugas Anda: Analisis bukti transaksi (transfer m-banking / struk nota / bukti pembayaran / invoice) berikut secara akurat.

Tanggal hari ini: {today_str}
Pengirim Laporan: {reporter_name or 'Pengelola / Koordinator Ecopark'}
Caption / Keterangan Teks: "{caption_text}"

Referensi Pos Anggaran Pengeluaran FKP ECO:
{coa_text}

Aturan Penilaian:
1. Tentukan tipe transaksi: "EXPENSE" (Pengeluaran/Belanja pakan, pupuk, benih, BBM, sarpras) ATAU "INCOME" (Pendapatan/Sewa kolam renang, tiket outbound/camping, penjualan telur, sayur, buah).
   - Jika bukti transfer ditujukan KE rekening sekolah/Ecopark atau atas sewa fasilitas/pembelian hasil panen -> "INCOME".
   - Jika struk belanja toko/nota pembelian pakan/struk bensin/bukti transfer ke toko/vendor -> "EXPENSE".
2. Nominal: Ambil jumlah total uang yang dibayar/diterima (angka bulat tanpa titik/koma/Rp).
3. Tanggal: Format YYYY-MM-DD. Jika tidak tertera tahun, gunakan tahun 2026. Jika tidak terbaca, gunakan {today_str}.
4. Pihak Terkait:
   - Jika EXPENSE: Nama Toko / Penjual / Bengkel / Merchant.
   - Jika INCOME: Nama Pembeli / Pengirim Transfer / Penyewa Fasilitas.
5. Metode Pembayaran: 'Transfer', 'Cash', atau 'QRIS'.
6. Uraian & Rincian Barang: Nama produk / layanan / barang yang dibeli atau dijual (misal: 'Pur GT 1 Karung & Dedak' atau 'Sewa Kolam Renang Fee Aquatic').
7. Jika EXPENSE, tentukan COA Code yang paling relevan (misal 52121-008 untuk pakan ternak, 52131-005 untuk bensin).
8. Jika INCOME, tentukan Kategori Utama (Sewa Fasilitas, Sayuran, Telur, Buah, Ternak, Kunjungan & Edukasi, Lain-lain).

Output HANYA berupa JSON valid tanpa markdown fence:
{{
  "trx_type": "EXPENSE" atau "INCOME",
  "tanggal": "YYYY-MM-DD",
  "nominal": 0,
  "pihak": "Nama Toko atau Pembeli",
  "uraian": "Deskripsi barang / layanan",
  "metode": "Transfer" atau "Cash",
  "coa_code": "52121-008",
  "coa_nama": "Hewan Edukasi (Pakan Unggas/Ternak)",
  "main_category": "OPERASIONAL PETERNAKAN",
  "items": [],
  "catatan_audit": ""
}}"""

    parts: list = [{"text": prompt}]
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
        res = requests.post(url, json=payload, timeout=25)
        if res.status_code == 200:
            raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            clean_json = re.sub(r'^```json\s*', '', raw_text)
            clean_json = re.sub(r'\s*```$', '', clean_json).strip()
            data = json.loads(clean_json)

            # Validasi COA
            if data.get('trx_type') == 'EXPENSE':
                code = data.get('coa_code', '')
                if code in coa_master:
                    data['coa_nama'] = coa_master[code]['name']
                    data['main_category'] = coa_master[code]['parent']
                else:
                    c, n, p = classify_eco_expense_rule(data.get('uraian', ''))
                    data['coa_code'] = c
                    data['coa_nama'] = n
                    data['main_category'] = p
            return data
    except Exception as e:
        print("[Vision AI Ecopark Exception]", e)

    # Fallback ke text parser
    return parse_eco_text_report(caption_text)


# ==================== RECORDING & STORAGE ENGINE ====================
def record_eco_transaction(parsed_data, drive_file_url="", drive_file_id="", reporter_name="", reporter_wa="", source="WHATSAPP_BOT", file_hash=""):
    """Menyimpan data transaksi terurai ke database ops_eco_transactions."""
    conn = get_db()
    try:
        trx_type = parsed_data.get('trx_type', 'EXPENSE').upper()
        if trx_type not in ['INCOME', 'EXPENSE']:
            trx_type = 'EXPENSE'

        tgl = parsed_data.get('tanggal') or now_wib().strftime('%Y-%m-%d')
        month_period = format_month_period(tgl)
        yyyy_mm = tgl[:7].replace('-', '')

        prefix = "IN" if trx_type == 'INCOME' else "EX"

        # Hitung nomor urut bulan berjalan
        seq_row = conn.execute("""
            SELECT COUNT(*) as cnt FROM ops_eco_transactions
            WHERE id LIKE ?
        """, (f"ECO-{prefix}-{yyyy_mm}-%",)).fetchone()
        next_seq = (seq_row['cnt'] or 0) + 1
        trx_id = f"ECO-{prefix}-{yyyy_mm}-{next_seq:04d}"

        amount = float(parsed_data.get('nominal', 0))
        coa_code = parsed_data.get('coa_code')
        coa_name = parsed_data.get('coa_nama')
        main_cat = parsed_data.get('main_category')
        pihak = parsed_data.get('pihak') or ("Pembeli" if trx_type == 'INCOME' else "Toko/Mitra Ecopark")
        uraian = parsed_data.get('uraian') or ("Pendapatan Ecopark" if trx_type == 'INCOME' else "Belanja Ecopark")
        metode = parsed_data.get('metode') or 'Cash'
        notes = parsed_data.get('catatan_audit') or parsed_data.get('keterangan') or ''

        conn.execute("""
            INSERT INTO ops_eco_transactions (
                id, trx_type, transaction_date, academic_year, month_period,
                coa_code, coa_name, main_category, category_type, amount,
                payment_method, buyer_or_vendor, description,
                drive_file_url, drive_file_id, reporter_name, reporter_wa,
                source, status, file_hash, notes, ai_raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trx_id, trx_type, tgl, '2026-2027', month_period,
            coa_code, coa_name, main_cat, main_cat, amount,
            metode, pihak, uraian,
            drive_file_url, drive_file_id, reporter_name, reporter_wa,
            source, 'RECORDED', file_hash, notes, json.dumps(parsed_data)
        ))
        conn.commit()

        return {
            'success': True,
            'id': trx_id,
            'trx_type': trx_type,
            'transaction_date': tgl,
            'month_period': month_period,
            'amount': amount,
            'coa_code': coa_code,
            'coa_name': coa_name,
            'main_category': main_cat,
            'buyer_or_vendor': pihak,
            'description': uraian,
            'payment_method': metode,
            'drive_file_url': drive_file_url,
            'reporter_name': reporter_name
        }
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


# ==================== REST API ENDPOINTS ====================

@ops_finance_ecopark_bp.route('/api/eco/process-upload', methods=['POST'])
def api_process_eco_upload():
    """
    Endpoint utama penerimaan bukti transaksi dari WhatsApp Bot atau Web Upload.
    Menerima base64 gambar atau teks laporan berformat.
    """
    data = request.get_json(silent=True) or {}
    image_b64 = data.get('image_base64')
    mime_type = data.get('mime_type', 'image/jpeg')
    caption = data.get('caption', '')
    reporter_name = data.get('reporter_name', 'Tim Ecopark')
    reporter_wa = data.get('reporter_wa', '')
    file_hash = data.get('file_hash', '')
    drive_file_url = data.get('drive_file_url', '')
    drive_file_id = data.get('drive_file_id', '')

    # 1. Cek Duplikat Layer 1 (File Hash) jika ada
    if file_hash:
        conn = get_db()
        try:
            dup = conn.execute("SELECT * FROM ops_eco_transactions WHERE file_hash = ?", (file_hash,)).fetchone()
            if dup:
                return jsonify({
                    'success': False,
                    'is_duplicate': True,
                    'duplicate_layer': 'FILE_HASH',
                    'existing_id': dup['id'],
                    'message': f"Bukti gambar ini sudah pernah dicatat sebelumnya pada transaksi {dup['id']} ({dup['description']} - Rp {dup['amount']:,.0f})."
                }), 200
        finally:
            conn.close()

    # 2. Parsing via Vision AI atau Text Parser
    if image_b64:
        parsed = parse_eco_receipt_with_vision(image_b64, mime_type, caption, reporter_name)
    else:
        parsed = parse_eco_text_report(caption)

    # 3. Cek Duplikat Layer 2 (Nominal + Tanggal + Pihak Kembar)
    nominal = parsed.get('nominal', 0)
    tgl = parsed.get('tanggal')
    pihak = parsed.get('pihak', '')
    trx_type = parsed.get('trx_type', 'EXPENSE')

    if nominal > 0 and tgl and pihak:
        conn = get_db()
        try:
            dup = conn.execute("""
                SELECT * FROM ops_eco_transactions
                WHERE trx_type = ? AND amount = ? AND transaction_date = ? AND buyer_or_vendor LIKE ?
            """, (trx_type, nominal, tgl, f"%{pihak[:10]}%")).fetchone()
            if dup:
                return jsonify({
                    'success': False,
                    'is_duplicate': True,
                    'duplicate_layer': 'TRANSACTION_MATCH',
                    'existing_id': dup['id'],
                    'message': f"Transaksi {trx_type} sebesar Rp {nominal:,.0f} dengan '{pihak}' pada tanggal {tgl} sudah pernah dicatat ({dup['id']})."
                }), 200
        finally:
            conn.close()

    # 4. Simpan Transaksi Baru
    result = record_eco_transaction(
        parsed_data=parsed,
        drive_file_url=drive_file_url,
        drive_file_id=drive_file_id,
        reporter_name=reporter_name,
        reporter_wa=reporter_wa,
        source="WHATSAPP_BOT" if reporter_wa else "WEB_UPLOAD",
        file_hash=file_hash
    )

    return jsonify(result), (200 if result.get('success') else 500)


@ops_finance_ecopark_bp.route('/api/eco/transactions', methods=['GET'])
def api_get_eco_transactions():
    """Mengambil riwayat transaksi Ecopark dengan multi-filter."""
    conn = get_db()
    try:
        trx_type = request.args.get('type', '').strip().upper()
        month = request.args.get('month', '').strip()
        category = request.args.get('category', '').strip()
        search = request.args.get('search', '').strip()
        limit = int(request.args.get('limit', 150))
        offset = int(request.args.get('offset', 0))

        query = "SELECT * FROM ops_eco_transactions WHERE 1=1"
        params = []

        if trx_type in ['INCOME', 'EXPENSE']:
            query += " AND trx_type = ?"
            params.append(trx_type)
        if month:
            query += " AND month_period = ?"
            params.append(month)
        if category:
            query += " AND (main_category = ? OR coa_name = ?)"
            params.extend([category, category])
        if search:
            wild = f"%{search}%"
            query += " AND (description LIKE ? OR buyer_or_vendor LIKE ? OR coa_name LIKE ? OR id LIKE ?)"
            params.extend([wild, wild, wild, wild])

        query += " ORDER BY transaction_date DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        trx_list = [dict(r) for r in rows]

        return jsonify({'success': True, 'count': len(trx_list), 'data': trx_list})
    finally:
        conn.close()


@ops_finance_ecopark_bp.route('/api/eco/stats', methods=['GET'])
def api_get_eco_stats():
    """Mengambil statistik realisasi kas Ecopark vs RKAS FKP ECO."""
    conn = get_db()
    try:
        month = request.args.get('month', '').strip()

        # Filter query
        time_clause = ""
        params = []
        if month:
            time_clause = " WHERE month_period = ?"
            params = [month]

        # Total Income & Expense
        inc_row = conn.execute(f"SELECT SUM(amount) as total, COUNT(*) as cnt FROM ops_eco_transactions {time_clause} {'AND' if time_clause else 'WHERE'} trx_type = 'INCOME'", params).fetchone()
        exp_row = conn.execute(f"SELECT SUM(amount) as total, COUNT(*) as cnt FROM ops_eco_transactions {time_clause} {'AND' if time_clause else 'WHERE'} trx_type = 'EXPENSE'", params).fetchone()

        tot_income = inc_row['total'] or 0.0
        cnt_income = inc_row['cnt'] or 0
        tot_expense = exp_row['total'] or 0.0
        cnt_expense = exp_row['cnt'] or 0
        saldo_kas = tot_income - tot_expense

        # Kontrol 6 Pos Plafon Anggaran FKP ECO
        parent_coas = conn.execute("""
            SELECT coa_code, coa_name, budget_annual
            FROM ops_eco_coa
            WHERE is_parent = 1
            ORDER BY coa_code ASC
        """).fetchall()

        # Realisasi per parent category
        exp_by_parent = conn.execute("""
            SELECT main_category, SUM(amount) as realisasi, COUNT(*) as cnt
            FROM ops_eco_transactions
            WHERE trx_type = 'EXPENSE'
            GROUP BY main_category
        """).fetchall()
        real_map = {r['main_category']: (r['realisasi'] or 0.0) for r in exp_by_parent}
        cnt_map = {r['main_category']: (r['cnt'] or 0) for r in exp_by_parent}

        category_summary = []
        grand_budget = 0.0
        grand_realisasi = 0.0

        for pc in parent_coas:
            c_name = pc['coa_name']
            bgt = pc['budget_annual'] or 0.0
            grand_budget += bgt
            real = real_map.get(c_name, 0.0)
            grand_realisasi += real
            pct = round((real / bgt * 100), 1) if bgt > 0 else 0.0
            category_summary.append({
                'code': pc['coa_code'],
                'name': c_name,
                'anggaran': bgt,
                'realisasi': real,
                'sisa': bgt - real,
                'persentase': pct,
                'transaksi': cnt_map.get(c_name, 0)
            })

        overall_pct = round((grand_realisasi / grand_budget * 100), 1) if grand_budget > 0 else 0.0

        return jsonify({
            'success': True,
            'summary': {
                'total_income': tot_income,
                'count_income': cnt_income,
                'total_expense': tot_expense,
                'count_expense': cnt_expense,
                'saldo_kas': saldo_kas,
                'grand_budget_annual': grand_budget,
                'grand_realisasi_annual': grand_realisasi,
                'overall_pct': overall_pct
            },
            'categories': category_summary
        })
    finally:
        conn.close()


@ops_finance_ecopark_bp.route('/api/eco/transactions/<trx_id>/update', methods=['POST'])
def api_update_eco_transaction(trx_id):
    """Koreksi manual transaksi oleh Admin / Koordinator."""
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        tgl = data.get('transaction_date')
        nominal = float(data.get('amount', 0))
        pihak = data.get('buyer_or_vendor', '').strip()
        desc = data.get('description', '').strip()
        coa_code = data.get('coa_code', '').strip()
        metode = data.get('payment_method', 'Cash')

        month_period = format_month_period(tgl) if tgl else None

        # Resolve COA name if code provided
        coa_row = conn.execute("SELECT coa_name, parent_category FROM ops_eco_coa WHERE coa_code = ?", (coa_code,)).fetchone()
        coa_name = coa_row['coa_name'] if coa_row else None
        main_cat = coa_row['parent_category'] if coa_row else None

        fields = [
            ("transaction_date = ?", tgl),
            ("amount = ?", nominal),
            ("buyer_or_vendor = ?", pihak),
            ("description = ?", desc),
            ("payment_method = ?", metode),
            ("updated_at = CURRENT_TIMESTAMP", None)
        ]
        if month_period:
            fields.append(("month_period = ?", month_period))
        if coa_code:
            fields.append(("coa_code = ?", coa_code))
        if coa_name:
            fields.append(("coa_name = ?", coa_name))
        if main_cat:
            fields.append(("main_category = ?", main_cat))

        set_clause = ", ".join([f[0] for f in fields])
        params = [f[1] for f in fields if f[1] is not None]
        params.append(trx_id)

        conn.execute(f"UPDATE ops_eco_transactions SET {set_clause} WHERE id = ?", params)
        conn.commit()

        return jsonify({'success': True, 'message': 'Transaksi berhasil diperbarui'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@ops_finance_ecopark_bp.route('/api/eco/transactions/<trx_id>', methods=['DELETE'])
def api_delete_eco_transaction(trx_id):
    """Menghapus transaksi dari database."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM ops_eco_transactions WHERE id = ?", (trx_id,))
        conn.commit()
        return jsonify({'success': True, 'message': f'Transaksi {trx_id} berhasil dihapus'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


@ops_finance_ecopark_bp.route('/api/eco/transactions/manual', methods=['POST'])
def api_create_manual_eco_transaction():
    """Input transaksi manual dari modal web dashboard."""
    data = request.get_json(silent=True) or {}
    trx_type = data.get('trx_type', 'EXPENSE').upper()
    tgl = data.get('transaction_date') or now_wib().strftime('%Y-%m-%d')
    amount = float(data.get('amount', 0))
    pihak = data.get('buyer_or_vendor', '').strip()
    desc = data.get('description', '').strip()
    metode = data.get('payment_method', 'Cash')
    coa_code = data.get('coa_code', '')

    coa_master = get_eco_coa_master()
    if trx_type == 'EXPENSE':
        if coa_code in coa_master:
            coa_name = coa_master[coa_code]['name']
            main_cat = coa_master[coa_code]['parent']
        else:
            coa_code, coa_name, main_cat = classify_eco_expense_rule(desc)
    else:
        coa_code = '41000-000'
        main_cat = data.get('main_category') or 'Sewa Fasilitas'
        coa_name = f"Penerimaan {main_cat}"

    parsed = {
        'trx_type': trx_type,
        'tanggal': tgl,
        'nominal': amount,
        'pihak': pihak or ("Pembeli" if trx_type == 'INCOME' else "Toko/Mitra"),
        'uraian': desc or ("Penerimaan Ecopark" if trx_type == 'INCOME' else "Belanja Ecopark"),
        'metode': metode,
        'coa_code': coa_code,
        'coa_nama': coa_name,
        'main_category': main_cat,
        'catatan_audit': 'Input manual via Dashboard Web'
    }

    result = record_eco_transaction(
        parsed_data=parsed,
        reporter_name=session.get('user_name', 'Admin Web'),
        source="WEB_MANUAL"
    )

    return jsonify(result), (200 if result.get('success') else 500)


@ops_finance_ecopark_bp.route('/api/eco/export', methods=['GET'])
def api_export_eco_csv():
    """Ekspor seluruh data transaksi Ecopark ke format CSV Excel."""
    conn = get_db()
    try:
        month = request.args.get('month', '').strip()
        trx_type = request.args.get('type', '').strip().upper()

        query = "SELECT * FROM ops_eco_transactions WHERE 1=1"
        params = []
        if month:
            query += " AND month_period = ?"
            params.append(month)
        if trx_type in ['INCOME', 'EXPENSE']:
            query += " AND trx_type = ?"
            params.append(trx_type)

        query += " ORDER BY transaction_date DESC, created_at DESC"
        rows = conn.execute(query, params).fetchall()

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID Transaksi', 'Tipe', 'Tanggal', 'Bulan', 'Kategori',
            'Kode Akun', 'Nama Pos Anggaran', 'Pihak (Toko / Pembeli)',
            'Uraian Transaksi', 'Qty', 'Satuan', 'Nominal (Rp)',
            'Metode Pembayaran', 'Pelapor', 'Sumber Data', 'Link Bukti Drive'
        ])

        for r in rows:
            writer.writerow([
                r['id'],
                'KAS MASUK (OMSET)' if r['trx_type'] == 'INCOME' else 'KAS KELUAR (BELANJA)',
                r['transaction_date'],
                r['month_period'],
                r['main_category'] or '',
                r['coa_code'] or '',
                r['coa_name'] or '',
                r['buyer_or_vendor'] or '',
                r['description'] or '',
                r['qty'] or 1,
                r['unit'] or '',
                f"{r['amount']:,.0f}".replace(',', '.'),
                r['payment_method'] or '',
                r['reporter_name'] or '',
                r['source'] or '',
                r['drive_file_url'] or ''
            ])

        csv_data = output.getvalue()
        filename = f"Keuangan_Ecopark_{month.replace(' ', '_') if month else 'Semua'}_{now_wib().strftime('%Y%m%d')}.csv"

        return Response(
            "\ufeff" + csv_data,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    finally:
        conn.close()


@ops_finance_ecopark_bp.route('/api/eco/coa', methods=['GET'])
def api_get_eco_coa():
    """Mengambil master COA FKP ECO untuk dropdown form web."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT coa_code, coa_name, parent_category, budget_annual, is_parent FROM ops_eco_coa WHERE is_active = 1 ORDER BY coa_code ASC").fetchall()
        return jsonify({'success': True, 'data': [dict(r) for r in rows]})
    finally:
        conn.close()
