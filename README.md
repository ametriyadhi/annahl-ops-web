# An Nahl Operations Hub (annahl-ops-web)

Sistem Dashboard Operasional Terpadu & Pemantauan Infrastruktur IT & Sarpras Sekolah Islam Al-Azhar An Nahl.

## 🚀 Fitur Utama

- **Operational Tasks & Delegation**: Manajemen to-do list, delegasi tugas antarstaf, dan pelacakan status penugasan secara real-time.
- **Jurnal Kegiatan Operasional**: Pencatatan jurnal harian kerja dengan dukungan supervisi dan feedback terstruktur.
- **Infrastruktur & Host Monitor (Uptime Kuma Integration)**: Pemantauan ketersediaan server/host lokal via ICMP ping (`monitor_daemon.py`) dengan notifikasi otomatis ke WhatsApp Koordinator.
- **Mutabaah Tracker & Analytics**: Dashboard monitoring mutabaah harian (mutabaah personal dan mutabaah yaumiyah staf), terintegrasi dengan Google Sheets dan WhatsApp Bot.
- **Role-Based Access Control (RBAC)**: Pembagian hak akses berjenjang (Super Admin, Koordinator, Supervisor, Staf Operasional).
- **Export Laporan**: Ekspor rekap data ke format Excel (`.xlsx`) dan CSV.

## 🛠️ Tech Stack

- **Backend**: Python 3.11, Flask, Gunicorn
- **Database**: SQLite3 (`database.sqlite`)
- **Frontend**: Tailwind CSS, Vanilla JS, Jinja2 Template Engine
- **Integrasi**: WhatsApp Bot (`@whiskeysockets/baileys`), Google Apps Script Webhooks

## 📦 Instalasi & Menjalankan Aplikasi

1. Clone repositori:
   ```bash
   git clone git@github.com:ametriyadhi/annahl-ops-web.git
   cd annahl-ops-web
   ```

2. Buat dan aktifkan virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```

4. Jalankan aplikasi (Development):
   ```bash
   python app.py
   ```

5. Jalankan aplikasi (Production via Gunicorn):
   ```bash
   gunicorn --workers 2 --threads 4 --bind 127.0.0.1:8080 app:app
   ```

6. Jalankan Monitoring Daemon (Background service):
   ```bash
   python monitor_daemon.py
   ```

## ⚙️ Layanan Systemd (Production)

Service dikelola via systemd user unit:
- Web Dashboard: `systemctl --user status annahl-ops-web`
- Host Monitor Daemon: `systemctl --user status annahl-monitor`

## 📄 Lisensi
Hak Cipta © Yayasan An Nahl Islamic School. Seluruh hak cipta dilindungi.
