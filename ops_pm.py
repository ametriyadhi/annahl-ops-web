"""
Modul Pemeliharaan Sarana dan Prasarana (Preventive & Corrective Maintenance)
Berdasarkan Dokumen Standar Mutu FM-UMUM-AIS-03-02 Rev.00
Sekolah Islam An Nahl Tahun 2025-2026
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, Any, List, Optional

DB_PATH = "/home/ametriyadhi/sas-annahl/database.sqlite"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_pm_tables():
    """Membuat tabel master, jadwal, dan log eksekusi pemeliharaan sarpras"""
    conn = get_db()
    cur = conn.cursor()

    # 1. Master Parameter Pemeliharaan
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops_pm_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope VARCHAR(20) NOT NULL,            -- 'INDOOR' / 'OUTDOOR'
            category VARCHAR(50) NOT NULL,         -- 'GEDUNG', 'LISTRIK', 'KOLAM', 'TOILET', 'AC', 'TAMAN', dll
            sub_category VARCHAR(100),             -- 'Outdoor AC', 'Indoor AC', 'Saung', 'Kandang', dll
            item_name VARCHAR(150) NOT NULL,       -- 'Pembersihan filter dan kipas', 'Potong Rumput', dll
            indicator_standard TEXT NOT NULL,      -- 'Terlihat bersih dan tidak berdebu', 'Hawa dingin', dll
            frequency VARCHAR(50) NOT NULL,        -- '2x Sehari', 'Setiap Hari', '3x Sepekan', '2 Pekan Sekali', 'Bulanan', '2 Bulan Sekali', '3 Bulan Sekali', '4 Bulan Sekali', '6 Bulan Sekali', '1 Kali Setahun', '2 Tahun Sekali', 'Kondisional'
            frequency_days INTEGER DEFAULT 30,     -- interval hari rata-rata untuk kalkulasi jatuh tempo
            executor_type VARCHAR(20) NOT NULL,    -- 'GARDENER', 'OB', 'VENDOR', 'SARPRAS'
            executor_name_default VARCHAR(100),    -- 'Tim Gardener', 'Tim Office Boy', 'Vendor Rekanan'
            pj_role VARCHAR(50) NOT NULL,          -- 'Koordinator OB', 'Koordinator Gardener', 'Kabag Umum', 'Kabag Ecopark'
            pj_name_default VARCHAR(100),          -- 'Mr. Slam', 'Koordinator Lapangan', dll
            schedule_months_json TEXT NOT NULL,    -- '[1,2,3,4,5,6,7,8,9,10,11,12]'
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Jadwal Periodik Pemeliharaan (Schedules)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops_pm_schedules (
            id VARCHAR(50) PRIMARY KEY,            -- 'PMS-202610-001'
            master_id INTEGER NOT NULL,
            period_year INTEGER NOT NULL,          -- 2026
            period_month INTEGER NOT NULL,         -- 10
            cycle_code VARCHAR(50),                -- 'PEKAN_1', 'PEKAN_2', 'SEMESTER_1', dll
            due_date DATE NOT NULL,
            executor_type VARCHAR(20) NOT NULL,
            assigned_to VARCHAR(100),
            status VARCHAR(30) DEFAULT 'PENDING',  -- 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE'
            completed_at DATETIME,
            completed_by VARCHAR(100),
            verified_by VARCHAR(100),
            verified_at DATETIME,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (master_id) REFERENCES ops_pm_master(id)
        )
    """)

    # 3. Log Riwayat Eksekusi Pemeliharaan & Bukti Fisik
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops_pm_execution_logs (
            id VARCHAR(50) PRIMARY KEY,            -- 'PML-20261001-001'
            schedule_id VARCHAR(50),
            master_id INTEGER NOT NULL,
            execution_date DATE NOT NULL,
            execution_time TIME,
            executor_type VARCHAR(20) NOT NULL,
            executor_name VARCHAR(100) NOT NULL,
            condition_rating VARCHAR(30) NOT NULL, -- 'BAIK', 'CUKUP', 'RUSAK_BUTUH_PERBAIKAN'
            finding_notes TEXT,
            action_taken TEXT,
            photo_before_url TEXT,
            photo_after_url TEXT,
            vendor_name VARCHAR(100),
            vendor_invoice_no VARCHAR(100),
            ticket_id VARCHAR(50),                 -- Tautan otomatis ke ops_tasks / ops_maintenance_tickets jika ada kerusakan
            verified_by VARCHAR(100),
            verified_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (master_id) REFERENCES ops_pm_master(id)
        )
    """)

    conn.commit()
    conn.close()

def seed_pm_master_data():
    """Mengisi 54 parameter master pemeliharaan resmi dari Dokumen ISO FM-UMUM-AIS-03-02 Rev.00"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM ops_pm_master")
    count = cur.fetchone()[0]
    if count >= 50:
        conn.close()
        return

    # List seluruh 54 parameter dari Dokumen 1 (Indoor) & Dokumen 2 (Outdoor)
    master_items = [
        # --- DOKUMEN 1: INDOOR & GEDUNG UTAMA ---
        # 1. Gedung
        ("INDOOR", "Gedung", "Struktur & Dinding", "Pengecatan Gedung", "Terlihat cerah dan tidak berjamur", "1 Kali Setahun", 365, "VENDOR", "Vendor Rekanan Pengecatan", "Kabag Umum", "Mr Slam", "[6]"),
        ("INDOOR", "Gedung", "Struktur & Dinding", "Perbaikan Struktur Gedung", "Tidak ada kerusakan fisik/retak", "Kondisional", 0, "VENDOR", "Vendor Sipil", "Kabag Umum", "Mr Slam", "[]"),
        ("INDOOR", "Gedung", "Atap & Plafon", "Perbaikan Atap Luar", "Tidak bocor dan posisi genteng/spandek rapat", "Kondisional", 0, "VENDOR", "Vendor Atap/Sarpras", "Kabag Umum", "Mr Slam", "[]"),

        # 2. Instalasi Listrik
        ("INDOOR", "Instalasi Listrik", "Kabel & Jalur", "Perapihan & Pengecekan Kabel", "Tersambung dengan baik dan rapi aman", "Kondisional", 0, "VENDOR", "Teknisi Listrik Sarpras", "Kabag Umum", "Mr Slam", "[]"),
        ("INDOOR", "Instalasi Listrik", "Saklar", "Pengecekan & Perbaikan Saklar", "Hidup dan berfungsi normal menyala", "Kondisional", 0, "VENDOR", "Teknisi Listrik Sarpras", "Kabag Umum", "Mr Slam", "[]"),
        ("INDOOR", "Instalasi Listrik", "Lampu Penerangan", "Pengecekan & Penggantian Lampu", "Hidup dan menyala terang", "Kondisional", 0, "VENDOR", "Teknisi Listrik Sarpras", "Kabag Umum", "Mr Slam", "[]"),
        ("INDOOR", "Instalasi Listrik", "Genset Cadangan", "Pemanasan & Uji Fungsi Genset", "Berfungsi dengan baik saat listrik padam", "Kondisional", 0, "VENDOR", "Teknisi Genset Sarpras", "Kabag Umum", "Mr Slam", "[]"),

        # 4. Kolam Renang
        ("INDOOR", "Kolam Renang", "Mesin & Filter", "Pembersihan Pompa Filter Kolam", "Terlihat bersih dan sirkulasi lancar", "3x Sepekan", 2, "OB", "Tim OB Kolam", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Kolam Renang", "Mesin & Filter", "Pembersihan Tabung Filter Kolam", "Terlihat bersih bebas kotoran", "Setiap Hari", 1, "OB", "Tim OB Kolam", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Kolam Renang", "Air & Dasar Kolam", "Vakum Dasar Air Kolam Renang", "Tidak ada endapan lumpur/pasir", "2 Pekan Sekali", 14, "OB", "Tim OB Kolam", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Kolam Renang", "Sanitasi Fasilitas", "Pembersihan Kamar Bilas Kolam", "Tidak berkerak dan lantai tidak licin", "Setiap Hari", 1, "OB", "Tim OB Kolam", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Kolam Renang", "Permukaan Air", "Pembersihan Vakum Atas / Serokan", "Terlihat bersih bebas daun terapung", "Setiap Hari", 1, "OB", "Tim OB Kolam", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Kolam Renang", "Fasilitas Pengguna", "Pembersihan & Kerapihan Lemari Baju Ganti", "Terlihat rapi dan bersih", "Setiap Hari", 1, "OB", "Tim OB Kolam", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),

        # 5. Toilet Indoor
        ("INDOOR", "Toilet", "Sanitasi Wastafel", "Pembersihan Wastafel & Kran", "Terlihat bersih, kesat dan kran tidak bocor", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Sanitasi Cermin", "Pembersihan Kaca / Cermin Toilet", "Terlihat bening, bersih dan kesat", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Perlengkapan Higienis", "Pengecekan & Pengisian Handsoap", "Tersedia dan botol dispenser bersih", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Dinding", "Pembersihan Dinding & Partisi Toilet", "Terlihat bersih dan kesat bebas noda", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Urinal", "Pembersihan Urinal Bowl Pria", "Terlihat bersih, kesat dan bebas kerak/bau", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Closet", "Pembersihan Kloset Duduk/Jongkok", "Terlihat bersih, kesat dan flush lancar", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Utilitas Air", "Pembersihan Ember & Gayung", "Terlihat bersih dan kesat bebas lumut", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Lantai", "Penyikatan & Pengepelan Lantai Toilet", "Terlihat bersih, kesat dan tidak licin", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Aksesoris", "Pencucian & Pengeringan Keset Toilet", "Terlihat bersih, kering dan kesat", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Toilet", "Tempat Sampah", "Pengosongan & Pembersihan Tempat Sampah", "Terlihat bersih dan kantong baru terpasang", "2x Sehari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),

        # 6. AC (Air Conditioner)
        ("INDOOR", "AC", "Outdoor AC", "Cuci Kipas & Kondensor Outdoor AC", "Hawa dingin maksimal dan tidak bocor", "6 Bulan Sekali", 180, "VENDOR", "Vendor AC Rekanan", "Kabag Umum", "Mr Slam", "[6,12]"),
        ("INDOOR", "AC", "Outdoor AC", "Pengecekan Ampere Listrik Kompresor", "Ampere stabil sesuai standar nameplate", "6 Bulan Sekali", 180, "VENDOR", "Vendor AC Rekanan", "Kabag Umum", "Mr Slam", "[6,12]"),
        ("INDOOR", "AC", "Outdoor AC", "Pengecekan Tekanan Freon & Perpipaan", "Tekanan freon normal dan pipa tidak beku", "6 Bulan Sekali", 180, "VENDOR", "Vendor AC Rekanan", "Kabag Umum", "Mr Slam", "[6,12]"),
        ("INDOOR", "AC", "Indoor AC", "Pembersihan Body Luar Indoor AC", "Terlihat bersih dan tidak berdebu", "2 Bulan Sekali", 60, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[2,4,6,8,10,12]"),
        ("INDOOR", "AC", "Indoor AC", "Pencucian Filter & Kipas Indoor AC", "Terlihat bersih, bebas debu dan angin kencang", "2 Pekan Sekali", 14, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "AC", "Drainase AC", "Pembersihan & Flushing Saluran Pembuangan Air AC", "Tidak ada sumbatan dan air mengalir lancar", "4 Bulan Sekali", 120, "VENDOR", "Vendor AC Rekanan", "Kabag Umum", "Mr Slam", "[3,6,9,12]"),
        ("INDOOR", "AC", "Aksesoris", "Pemeriksaan & Penggantian Baterai Remote AC", "Remote responsif dan dapat digunakan", "Kondisional", 0, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[]"),

        # 7. Ruangan & Kelas
        ("INDOOR", "Ruangan", "Lantai Ruang", "Penyapuan & Pengepelan Lantai Kelas/Kantor", "Terlihat bersih, wangi dan tidak berdebu", "Setiap Hari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Ruangan", "Plafon & Sudut", "Pembersihan Sarang Laba-laba / Sawang", "Tidak ada sawang di sudut plafon", "Kondisional", 14, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Ruangan", "Kaca & Jendela", "Pembersihan Kaca Jendela Ruangan", "Terlihat bening dan tidak berdebu", "Setiap Hari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Ruangan", "Meja & Mebeler", "Pengelapan Perlengkapan Meja & Kursi", "Terlihat bersih, rapi dan tidak berdebu", "Setiap Hari", 1, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Ruangan", "Kipas Angin", "Pembersihan Baling-baling Kipas Angin", "Terlihat bersih bebas gumpalan debu", "2 Pekan Sekali", 14, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),

        # 8. Dispenser
        ("INDOOR", "Dispenser", "Tabung Air", "Pengurasan & Sterilisasi Tabung Galon Dispenser", "Air galon higienis, bersih dan tidak berlumut", "2 Bulan Sekali", 60, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[2,4,6,8,10,12]"),

        # 9. Jam Dinding
        ("INDOOR", "Jam Dinding", "Baterai", "Pengecekan & Penggantian Baterai Jam Dinding", "Berfungsi tepat waktu dan jarum bergerak", "Kondisional", 0, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[]"),

        # 10. Karpet Kelas & Masjid
        ("INDOOR", "Karpet Kelas", "Penyedotan Debu", "Vakum Debu Karpet Kelas", "Tidak kotor dan bebas debu halus", "2 Pekan Sekali", 14, "OB", "Petugas OB Gedung", "Koordinator OB", "Koordinator OB", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("INDOOR", "Karpet Kelas", "Pencucian Karpet", "Laundry Karpet Kelas Menyeluruh", "Tidak kotor, wangi dan bersih steril", "3 Bulan Sekali", 90, "OB", "Vendor Laundry / Tim OB", "Koordinator OB", "Koordinator OB", "[3,6,9,12]"),

        # 11. Fogging
        ("INDOOR", "Fogging", "Disinfektan Ruang", "Fogging Disinfektan Ruangan Indoor", "Steril dari bakteri, virus dan tidak bau", "2 Bulan Sekali", 60, "OB", "Tim Khusus Fogging", "Koordinator OB", "Koordinator OB", "[2,4,6,8,10,12]"),
        ("INDOOR", "Fogging", "Nyamuk & Hama", "Fogging Nyamuk & Pest Control Indoor/Outdoor", "Bebas jentik nyamuk dan serangga hama", "6 Bulan Sekali", 180, "OB", "Tim Khusus Fogging", "Koordinator OB", "Koordinator OB", "[6,12]"),

        # --- DOKUMEN 2: OUTDOOR, TAMAN & KAWASAN ECOPARK ---
        # 1. Saung Ecopark
        ("OUTDOOR", "Saung", "Struktur & Cat", "Pengecatan Saung & Gazebo", "Terlihat cerah, mengkilap dan tidak berjamur", "2 Tahun Sekali", 730, "VENDOR", "Vendor Pengecatan Kayu", "Koordinator Lapangan", "Koordinator Lapangan", "[6]"),
        ("OUTDOOR", "Saung", "Kebersihan Luar", "Pembersihan Sampah & Serasah Daun Saung", "Tidak ada sampah dan kotoran daun", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Saung", "Atap Saung", "Perbaikan Atap Saung & Ijuk/Sirap", "Tidak bocor saat hujan deras", "Kondisional", 0, "VENDOR", "Sarpras / Vendor", "Koordinator Lapangan", "Koordinator Lapangan", "[]"),

        # 2. Playground Anak
        ("OUTDOOR", "Playground", "Fisik Wahana", "Perbaikan Wahana Bermain Rusak/Patah", "Tidak ada bagian patah atau membahayakan anak", "Kondisional", 0, "VENDOR", "Sarpras / Vendor Las", "Koordinator Lapangan", "Koordinator Lapangan", "[]"),
        ("OUTDOOR", "Playground", "Kebersihan Area", "Pembersihan Area Bermain Playground", "Tidak ada sampah, ranting dan kotoran", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Playground", "Pengecatan Wahana", "Pengecatan Wahana Ayunan, Seluncuran, Jungkat-jungkit", "Warna cerah ceria dan tidak berkarat", "2 Tahun Sekali", 730, "VENDOR", "Vendor Pengecatan", "Koordinator Lapangan", "Koordinator Lapangan", "[6]"),

        # 3. Lapangan Upacara
        ("OUTDOOR", "Lapangan Upacara", "Paving Lapangan", "Perbaikan Lantai / Paving Lapangan Pecah", "Permukaan rata, tidak berlubang dan aman", "Kondisional", 0, "VENDOR", "Vendor Sipil", "Kabag Ecopark", "Syarief Hidayatulloh", "[]"),
        ("OUTDOOR", "Lapangan Upacara", "Kebersihan Lapangan", "Penyapuan Lapangan Upacara", "Tidak ada sampah plastik dan serasah daun", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Lapangan Upacara", "Pengecatan Garis", "Pengecatan Marka Lapangan Upacara", "Garis pembatas tegas dan warna cerah", "2 Tahun Sekali", 730, "VENDOR", "Vendor Pengecatan", "Kabag Ecopark", "Syarief Hidayatulloh", "[6]"),

        # 4. Lapangan Futsal
        ("OUTDOOR", "Lapangan Futsal", "Lantai Futsal", "Perbaikan Lantai Futsal Retak/Pecah", "Lantai aman untuk bermain", "Kondisional", 0, "VENDOR", "Vendor Sipil / Sarpras", "Kabag Ecopark", "Syarief Hidayatulloh", "[]"),
        ("OUTDOOR", "Lapangan Futsal", "Kebersihan", "Penyapuan & Pembersihan Lapangan Futsal", "Bebas sampah dan debu kerikil", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Lapangan Futsal", "Pengecatan Garis", "Pengecatan Garis Lapangan Futsal", "Garis terlihat tegas dan rapi", "2 Tahun Sekali", 730, "VENDOR", "Vendor Pengecatan", "Kabag Ecopark", "Syarief Hidayatulloh", "[6]"),
        ("OUTDOOR", "Lapangan Futsal", "Pagar Pengaman", "Perbaikan Pagar Kawat & Jaring Futsal", "Kawat rapat, tidak keropos dan tidak jebol", "Kondisional", 0, "VENDOR", "Teknisi Sarpras", "Kabag Ecopark", "Syarief Hidayatulloh", "[]"),

        # 5. Toilet Outdoor Ecopark
        ("OUTDOOR", "Toilet Outdoor", "Sanitasi Kloset", "Pembersihan Kloset Toilet Outdoor", "Terlihat bersih, kesat dan tidak berbau", "2x Sehari", 1, "OB", "Petugas OB Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Toilet Outdoor", "Utilitas Air", "Pembersihan Ember & Gayung Toilet Outdoor", "Bersih, kesat dan air jernih", "2x Sehari", 1, "OB", "Petugas OB Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Toilet Outdoor", "Lantai", "Penyikatan Lantai Toilet Outdoor", "Bersih, kesat dan tidak licin", "2x Sehari", 1, "OB", "Petugas OB Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Toilet Outdoor", "Tempat Sampah", "Pengosongan Tong Sampah Toilet Outdoor", "Bersih dan tidak menumpuk", "2x Sehari", 1, "OB", "Petugas OB Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),

        # 6. Area Parkir
        ("OUTDOOR", "Parkir", "Kebersihan Paving", "Penyapuan Area Parkir Mobil & Motor", "Bebas sampah plastik dan tumpukan daun", "Setiap Hari", 1, "GARDENER", "Tim Gardener Lapangan", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Parkir", "Aspal & Paving", "Penambalan Paving / Aspal Parkir Berlubang", "Permukaan rata dan aman dilewati kendaraan", "Kondisional", 0, "VENDOR", "Vendor Aspal / Sarpras", "Kabag Ecopark", "Syarief Hidayatulloh", "[]"),
        ("OUTDOOR", "Parkir", "Marka Parkir", "Pengecatan Marka Garis Batas Parkir", "Terlihat jelas batas jarak parkir", "1 Kali Setahun", 365, "VENDOR", "Vendor Marka Jalan", "Koordinator Lapangan", "Koordinator Lapangan", "[6]"),

        # 7. Kandang Ternak & Unggas Ecopark
        ("OUTDOOR", "Kandang", "Sanitasi Ternak", "Pembersihan Kandang Ternak & Unggas", "Terlihat bersih, kotoran terangkat dan tidak bau", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Kandang", "Struktur Kandang", "Perbaikan Pagar, Engsel & Atap Kandang", "Terlihat rapi, kokoh dan ternak aman", "Kondisional", 0, "GARDENER", "Tim Gardener / Sarpras", "Koordinator OB", "Koordinator OB", "[]"),

        # 8. Kolam Ikan
        ("OUTDOOR", "Kolam Ikan", "Kebersihan Kolam", "Pembersihan Permukaan Kolam Ikan & Lumut", "Terlihat bersih dan sirkulasi air lancar", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Kolam Ikan", "Debit Air", "Kontrol Ketinggian & Batas Air Kolam Ikan", "Berada di batas aman yang ditentukan", "Kondisional", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),

        # 9. Taman & Area Hijau
        ("OUTDOOR", "Taman", "Kebersihan Area Hijau", "Pembersihan Taman, Pengumpulan Serasah Daun & Gulma", "Tidak ada sampah liar dan tumpukan daun kering", "Setiap Hari", 1, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]"),
        ("OUTDOOR", "Taman", "Pemotongan Rumput", "Pemotongan Rumput Lapangan & Jalur Hijau", "Rata, rapi dan tidak ada rumput liar tinggi", "2 Pekan Sekali", 14, "GARDENER", "Tim Gardener Ecopark", "Koordinator Lapangan", "Koordinator Lapangan", "[1,2,3,4,5,6,7,8,9,10,11,12]")
    ]

    for item in master_items:
        cur.execute("""
            INSERT INTO ops_pm_master (
                scope, category, sub_category, item_name, indicator_standard,
                frequency, frequency_days, executor_type, executor_name_default,
                pj_role, pj_name_default, schedule_months_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    conn.commit()
    conn.close()

def generate_monthly_schedules(year: Optional[int] = None, month: Optional[int] = None):
    """Menghasilkan instance jadwal bulan berjalan berdasarkan master jadwal ISO"""
    now = datetime.date.today()
    y: int = year if year is not None else now.year
    m_val: int = month if month is not None else now.month

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM ops_pm_master WHERE is_active = 1")
    masters = cur.fetchall()

    for m in masters:
        months_allowed = json.loads(m["schedule_months_json"]) if m["schedule_months_json"] else []
        freq = m["frequency"]

        # Jika jadwal berkala bulan ini masuk daftar bulan atau frekuensi rutin/2pekanan
        should_schedule = False
        if m_val in months_allowed or freq in ["2x Sehari", "Setiap Hari", "3x Sepekan", "2 Pekan Sekali"]:
            should_schedule = True

        if should_schedule:
            sched_id = f"PMS-{y}{m_val:02d}-{m['id']:03d}"
            # Cek apakah sudah ada
            cur.execute("SELECT id FROM ops_pm_schedules WHERE id = ?", (sched_id,))
            if not cur.fetchone():
                due_date = f"{y}-{m_val:02d}-28"
                if freq == "2 Pekan Sekali":
                    due_date = f"{y}-{m_val:02d}-15"
                cur.execute("""
                    INSERT INTO ops_pm_schedules (
                        id, master_id, period_year, period_month, cycle_code,
                        due_date, executor_type, assigned_to, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
                """, (sched_id, m["id"], y, m_val, freq, due_date, m["executor_type"], m["executor_name_default"]))

    conn.commit()
    conn.close()

def get_pm_dashboard_summary(year: Optional[int] = None, month: Optional[int] = None) -> Dict[str, Any]:
    """Menghitung metrik ringkasan pemeliharaan untuk dashboard"""
    now = datetime.date.today()
    y: int = year if year is not None else now.year
    m_val: int = month if month is not None else now.month

    conn = get_db()
    cur = conn.cursor()

    # Pastikan jadwal bulan ini sudah ter-generate
    generate_monthly_schedules(y, m_val)

    # 1. Total Jadwal Bulan Ini
    cur.execute("""
        SELECT 
            count(*) as total,
            SUM(CASE WHEN s.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN s.status = 'PENDING' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN s.status = 'OVERDUE' THEN 1 ELSE 0 END) as overdue,
            SUM(CASE WHEN m.executor_type = 'GARDENER' THEN 1 ELSE 0 END) as gardener_total,
            SUM(CASE WHEN m.executor_type = 'OB' THEN 1 ELSE 0 END) as ob_total,
            SUM(CASE WHEN m.executor_type = 'VENDOR' THEN 1 ELSE 0 END) as vendor_total
        FROM ops_pm_schedules s
        JOIN ops_pm_master m ON s.master_id = m.id
        WHERE s.period_year = ? AND s.period_month = ?
    """, (y, m_val))
    stats_row = cur.fetchone()

    total = stats_row["total"] or 0
    completed = stats_row["completed"] or 0
    pending = stats_row["pending"] or 0
    overdue = stats_row["overdue"] or 0
    compliance_pct = round((completed / max(1, total)) * 100, 1)

    # 2. Daftar Jadwal Aktif Bulan Ini
    cur.execute("""
        SELECT s.id, s.master_id, s.due_date, s.executor_type, s.assigned_to, s.status, s.completed_at,
               m.scope, m.category, m.sub_category, m.item_name, m.indicator_standard, m.frequency,
               m.pj_role, m.pj_name_default, m.schedule_months_json
        FROM ops_pm_schedules s
        JOIN ops_pm_master m ON s.master_id = m.id
        WHERE s.period_year = ? AND s.period_month = ?
        ORDER BY CASE s.status WHEN 'OVERDUE' THEN 1 WHEN 'PENDING' THEN 2 ELSE 3 END, m.scope DESC, m.category ASC
    """, (y, m_val))
    schedules = [dict(r) for r in cur.fetchall()]

    # 3. Log Eksekusi Terkini (10 Terakhir)
    cur.execute("""
        SELECT l.*, m.item_name, m.category, m.scope, m.indicator_standard
        FROM ops_pm_execution_logs l
        JOIN ops_pm_master m ON l.master_id = m.id
        ORDER BY l.created_at DESC LIMIT 10
    """)
    recent_logs = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "year": y,
        "month": m_val,
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "compliance_pct": compliance_pct,
        "by_executor": {
            "gardener": stats_row["gardener_total"] or 0,
            "ob": stats_row["ob_total"] or 0,
            "vendor": stats_row["vendor_total"] or 0
        },
        "schedules": schedules,
        "recent_logs": recent_logs
    }

def record_pm_execution(
    schedule_id: str,
    master_id: int,
    execution_date: str,
    executor_name: str,
    executor_type: str,
    condition_rating: str,
    finding_notes: str = "",
    action_taken: str = "",
    photo_before_url: str = "",
    photo_after_url: str = "",
    vendor_name: str = "",
    vendor_invoice_no: str = "",
    create_ticket: bool = False,
    verified_by: str = "Mr Slam"
) -> Dict[str, Any]:
    """Merekam bukti pelaksanaan pemeliharaan preventif/korektif dan meng-update jadwal"""
    conn = get_db()
    cur = conn.cursor()

    log_id = f"PML-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    exec_time = datetime.datetime.now().strftime("%H:%M:%S")

    ticket_id = None
    if create_ticket or condition_rating == "RUSAK_BUTUH_PERBAIKAN":
        # Terbitkan tiket sarpras otomatis di tabel ops_tasks
        ticket_id = f"task_pm_{datetime.datetime.now().strftime('%m%d_%H%M%S')}"
        cur.execute("""
            INSERT INTO ops_tasks (
                id, unit_code, sub_scope, category, title, description, priority, status,
                source, source_ref, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', 'PM_MAINTENANCE', ?, ?, CURRENT_TIMESTAMP)
        """, (
            ticket_id,
            executor_type,
            "Temuan Kerusakan Pemeliharaan",
            "SARPRAS_REPAIR",
            f"Perbaikan Lanjutan: {finding_notes[:50]}",
            f"Temuan anomali dari ceklis PM: {finding_notes}. Tindakan sementara: {action_taken}",
            "Tinggi" if condition_rating == "RUSAK_BUTUH_PERBAIKAN" else "Sedang",
            schedule_id or log_id,
            executor_name
        ))

    # Masukkan log eksekusi
    cur.execute("""
        INSERT INTO ops_pm_execution_logs (
            id, schedule_id, master_id, execution_date, execution_time,
            executor_type, executor_name, condition_rating, finding_notes, action_taken,
            photo_before_url, photo_after_url, vendor_name, vendor_invoice_no,
            ticket_id, verified_by, verified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        log_id, schedule_id, master_id, execution_date, exec_time,
        executor_type, executor_name, condition_rating, finding_notes, action_taken,
        photo_before_url, photo_after_url, vendor_name, vendor_invoice_no,
        ticket_id, verified_by
    ))

    # Update status jadwal menjadi COMPLETED jika ada schedule_id
    if schedule_id:
        cur.execute("""
            UPDATE ops_pm_schedules
            SET status = 'COMPLETED',
                completed_at = CURRENT_TIMESTAMP,
                completed_by = ?,
                verified_by = ?,
                verified_at = CURRENT_TIMESTAMP,
                notes = ?
            WHERE id = ?
        """, (executor_name, verified_by, finding_notes, schedule_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "log_id": log_id,
        "ticket_id": ticket_id,
        "status": "COMPLETED"
    }

def check_and_send_pm_reminders(target_wa: str = "6287809199096@s.whatsapp.net", bot_url: str = "http://127.0.0.1:3005/send_alert") -> Dict[str, Any]:
    """Mengecek jadwal pemeliharaan yang jatuh tempo atau overdue dan mengirim pengingat WhatsApp"""
    import urllib.request
    now = datetime.date.today()
    today_str = now.strftime("%Y-%m-%d")
    h3_str = (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()

    # 1. Update status OVERDUE untuk jadwal yang telah melewati due_date tapi masih PENDING
    cur.execute("""
        UPDATE ops_pm_schedules
        SET status = 'OVERDUE'
        WHERE due_date < ? AND status = 'PENDING'
    """, (today_str,))
    conn.commit()

    # 2. Ambil jadwal yang jatuh tempo dalam 3 hari ke depan atau sudah overdue
    cur.execute("""
        SELECT s.id, s.due_date, s.status, s.executor_type, s.assigned_to,
               m.scope, m.category, m.item_name, m.indicator_standard, m.frequency, m.pj_role
        FROM ops_pm_schedules s
        JOIN ops_pm_master m ON s.master_id = m.id
        WHERE (s.due_date <= ? AND s.status IN ('PENDING', 'OVERDUE'))
        ORDER BY s.due_date ASC, m.executor_type ASC
        LIMIT 10
    """, (h3_str,))
    items = cur.fetchall()
    conn.close()

    if not items:
        return {"status": "no_reminders", "count": 0}

    # Kelompokkan teks pengingat
    gardener_lines = []
    ob_lines = []
    vendor_lines = []

    for it in items:
        status_icon = "⚠️ [OVERDUE]" if it["status"] == "OVERDUE" else "⏳"
        line = f"• {status_icon} *{it['item_name']}* ({it['category']})\n  Standar: _{it['indicator_standard']}_\n  Tenggat: {it['due_date']} | Frekuensi: {it['frequency']}"
        if it["executor_type"] == "GARDENER":
            gardener_lines.append(line)
        elif it["executor_type"] == "OB":
            ob_lines.append(line)
        else:
            vendor_lines.append(line)

    msg_parts = [
        "🔔 *PENGINGAT JADWAL PEMELIHARAAN SARPRAS AN NAHL*",
        "_(Standar ISO FM-UMUM-AIS-03-02 Rev.00)_\n"
    ]

    if gardener_lines:
        msg_parts.append("🌿 *Unit Gardener (Taman & Ecopark):*")
        msg_parts.extend(gardener_lines)
        msg_parts.append("")

    if ob_lines:
        msg_parts.append("🧹 *Unit Office Boy (Gedung & Sanitasi):*")
        msg_parts.extend(ob_lines)
        msg_parts.append("")

    if vendor_lines:
        msg_parts.append("🛠️ *Vendor & Sarpras Spesialis:*")
        msg_parts.extend(vendor_lines)
        msg_parts.append("")

    msg_parts.append("📲 _Silakan laksanakan pemeliharaan dan unggah bukti foto pelaksanaan di portal An Nahl Ops:_")
    msg_parts.append("https://note-umum.ametriyadhi.com/#tab-pemeliharaan")

    full_message = "\n".join(msg_parts)

    try:
        req = urllib.request.Request(
            bot_url,
            data=json.dumps({"target": target_wa, "text": full_message}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"status": "sent", "count": len(items), "response": resp.read().decode("utf-8")}
    except Exception as e:
        return {"status": "error", "error": str(e), "count": len(items)}

# Inisialisasi awal saat modul dimuat
init_pm_tables()
seed_pm_master_data()
generate_monthly_schedules()
