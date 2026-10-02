from mutubaah_api import mutubaah_bp
from ops_auth import ops_auth_bp, login_required, get_ops_db
import os
import sys
import json
import time
import uuid
import socket
import urllib.request
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from flask import Flask, render_template_string, request, jsonify, Response, session, redirect, url_for, send_from_directory, make_response

WIB = ZoneInfo("Asia/Jakarta")

def now_wib():
    return datetime.now(WIB)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "annahl-ops-super-secret-key-2026-bismillah")

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

from ops_core import ops_core_bp
from checklist_core import checklist_bp
import templates_pm
import ops_pm
import templates_evaluasi
import ops_evaluasi
app.register_blueprint(ops_auth_bp)
app.register_blueprint(ops_core_bp)
app.register_blueprint(checklist_bp)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.png", mimetype="image/png")

@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return send_from_directory(os.path.join(app.root_path, "static"), "logo-icon.png", mimetype="image/png")

# Paths
DATA_FILE = os.path.expanduser("~/annahl_ops_data.json")
MUTABAAH_LOGS_PATH = os.path.expanduser("~/mutabaah-wa-bot/mutabaah_logs.json")
KEBERSIHAN_LOGS_PATH = os.path.expanduser("~/mutabaah-wa-bot/kebersihan_logs.json")

UNITS = [
    "PGTK", "SD", "SMP", "SMA",
    "SARPRAS", "PENGADAAN",
    "Mutu & Pengembangan", "Keuangan", "Marketing", "SDM", "Umum", "Ecopark"
]

def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "tasks": [],
            "todos": [],
            "journals": [],
            "monitored_hosts": [
                {"id": "h_1", "name": "Server Utama (Local)", "host": "127.0.0.1", "type": "ping", "category": "Server", "port": "", "last_status": "ONLINE", "latency_ms": 0.5},
                {"id": "h_2", "name": "Google DNS", "host": "8.8.8.8", "type": "ping", "category": "Network", "port": "", "last_status": "ONLINE", "latency_ms": 12.0}
            ]
        }
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "todos" not in data: data["todos"] = []
            if "journals" not in data: data["journals"] = []
            if "tasks" not in data: data["tasks"] = []
            if "monitored_hosts" not in data: data["monitored_hosts"] = []
            
            for j in data["journals"]:
                if "id" not in j: j["id"] = "j_" + str(uuid.uuid4())[:8]
            for t in data["todos"]:
                if "id" not in t: t["id"] = "td_" + str(uuid.uuid4())[:8]
            for tk in data["tasks"]:
                if "id" not in tk: tk["id"] = "tk_" + str(uuid.uuid4())[:8]
            for h in data["monitored_hosts"]:
                if "id" not in h: h["id"] = "h_" + str(uuid.uuid4())[:8]
                if "category" not in h: h["category"] = "Server"
                
            return data
    except Exception:
        return {"tasks": [], "todos": [], "journals": [], "monitored_hosts": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_logs(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def get_server_stats():
    mem_info = {}
    if os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = int(parts[1].split()[0])
        total_mem = mem_info.get("MemTotal", 1) / (1024 * 1024)
        avail_mem = mem_info.get("MemAvailable", 0) / (1024 * 1024)
        used_mem = total_mem - avail_mem
        mem_pct = round((used_mem / total_mem) * 100, 1)
        mem_str = f"{used_mem:.1f} GB / {total_mem:.1f} GB ({mem_pct}%)"
    else:
        mem_str = "N/A"
        mem_pct = 0
        total_mem = 0
        used_mem = 0

    try:
        st = os.statvfs('/')
        free_disk = (st.f_bavail * st.f_frsize) / (1024**3)
        total_disk = (st.f_blocks * st.f_frsize) / (1024**3)
        used_disk = total_disk - free_disk
        disk_pct = round((used_disk / total_disk) * 100, 1)
        disk_str = f"{used_disk:.1f} GB / {total_disk:.1f} GB ({disk_pct}%)"
    except Exception:
        disk_str = "N/A"
        disk_pct = 0
        total_disk = 0
        used_disk = 0

    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            mins = int((uptime_seconds % 3600) // 60)
            uptime_str = f"{hours}j {mins}m"
    except Exception:
        uptime_str = "N/A"

    return {
        "mem_str": mem_str,
        "mem_pct": mem_pct,
        "disk_str": disk_str,
        "disk_pct": disk_pct,
        "uptime": uptime_str,
        "mem_total_gb": round(total_mem, 1),
        "mem_used_gb": round(used_mem, 1),
        "disk_total_gb": round(total_disk, 1),
        "disk_used_gb": round(used_disk, 1)
    }


def get_detailed_server_stats():
    """Extended server stats: CPU cores, load avg, top processes (htop-like)"""
    import subprocess

    stats = get_server_stats()

    # CPU info
    cpu_cores = os.cpu_count() or 0
    load_avg = [0.0, 0.0, 0.0]
    if os.path.exists("/proc/loadavg"):
        try:
            with open("/proc/loadavg") as f:
                load_avg = list(map(float, f.read().split()[:3]))
        except Exception:
            pass

    # CPU usage from /proc/stat
    cpu_pct = 0.0
    try:
        with open("/proc/stat") as f:
            first_line = f.readline()
            if first_line.startswith("cpu "):
                parts = list(map(int, first_line.split()[1:]))
                idle = parts[3]
                total = sum(parts)
                # We need delta from previous read; simple approximation:
                # Read twice with small interval
                import time
                time.sleep(0.05)
                with open("/proc/stat") as f2:
                    parts2 = list(map(int, f2.readline().split()[1:]))
                    idle2 = parts2[3]
                    total2 = sum(parts2)
                    idle_delta = idle2 - idle
                    total_delta = total2 - total
                    if total_delta > 0:
                        cpu_pct = round((1.0 - idle_delta / total_delta) * 100, 1)
    except Exception:
        pass

    # Top processes (like htop) - using ps
    top_processes = []
    try:
        # ps aux --sort=-%cpu | head -11 (header + top 10)
        result = subprocess.run(
            ["ps", "aux", "--sort=-%cpu"],
            capture_output=True, text=True, timeout=3
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            header = lines[0].split()
            for line in lines[1:11]:  # top 10
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    top_processes.append({
                        "user": parts[0],
                        "pid": parts[1],
                        "cpu": float(parts[2]),
                        "mem": float(parts[3]),
                        "vsz": parts[4],
                        "rss": parts[5],
                        "tty": parts[6],
                        "stat": parts[7],
                        "start": parts[8],
                        "time": parts[9],
                        "command": parts[10][:80]  # truncate
                    })
    except Exception:
        pass

    # Network interfaces (brief)
    net_interfaces = []
    try:
        result = subprocess.run(
            ["ip", "-br", "addr", "show"],
            capture_output=True, text=True, timeout=2
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 3 and parts[1] in ("UP", "DOWN"):
                net_interfaces.append({
                    "name": parts[0],
                    "status": parts[1],
                    "ip": parts[2] if len(parts) > 2 else ""
                })
    except Exception:
        pass

    stats.update({
        "cpu_cores": cpu_cores,
        "load_avg": load_avg,
        "cpu_pct": cpu_pct,
        "top_processes": top_processes,
        "net_interfaces": net_interfaces
    })
    return stats

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>An Nahl Ops - Command Center IT & General Affairs</title>
    <!-- Favicon & App Icons -->
    <link rel="icon" type="image/png" href="/static/favicon.png?v=20260930">
    <link rel="apple-touch-icon" href="/static/logo-icon.png?v=20260930">
    <!-- Tailwind CSS (build lokal, anti CDN-failure) -->
    <link rel="stylesheet" href="/static/tailwind.min.css?v=20260930_taste">
    <!-- FontAwesome CDN -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        body { 
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #FAF8F5;
        }
        .ops-card {
            background-color: #FFFFFF;
            border: 1px solid #E8E4DD;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03), 0 1px 2px -1px rgba(0, 0, 0, 0.03);
        }
        .brand-logo-hero {
            height: 48px !important;
            max-height: 52px !important;
            width: auto !important;
            max-width: 60px !important;
            object-fit: contain !important;
            display: block !important;
        }
        .brand-icon-sidebar {
            height: 26px !important;
            width: 26px !important;
            max-width: 28px !important;
            max-height: 28px !important;
            object-fit: contain !important;
            display: block !important;
        }
        .brand-icon-nav {
            height: 22px !important;
            width: 22px !important;
            max-width: 24px !important;
            max-height: 24px !important;
            object-fit: contain !important;
            display: block !important;
        }
        .tab-btn {
            text-align: left !important;
            justify-content: flex-start !important;
        }
        .tab-btn span {
            text-align: left !important;
        }
        @media print {
            #sidebar, #sidebar-backdrop, header, .no-print {
                display: none !important;
            }
            main {
                margin-left: 0 !important;
                padding: 0 !important;
            }
            .tab-content {
                display: none !important;
            }
            #tab-report {
                display: block !important;
            }
            body {
                background: white !important;
            }
        }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex selection:bg-emerald-600/10 selection:text-emerald-950">

    <!-- BACKDROP MOBILE -->
    <div id="sidebar-backdrop" onclick="toggleSidebar()" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-30 hidden transition-opacity"></div>

    <!-- RESPONSIVE SIDEBAR -->
    <aside id="sidebar" class="w-64 bg-slate-900 text-slate-300 min-h-screen flex flex-col border-r border-slate-800 fixed inset-y-0 left-0 z-40 transition-transform duration-300 transform -translate-x-full md:translate-x-0">
        <!-- Brand / Header -->
        <div class="p-4 sm:p-4.5 border-b border-slate-800/80 flex items-center justify-between bg-gradient-to-r from-slate-900 via-[#132721] to-slate-900 text-white">
            <div class="flex items-center space-x-3 min-w-0">
                <div class="w-9 h-9 rounded-xl bg-white p-1 shrink-0 flex items-center justify-center shadow-xs border border-white/20">
                    <img src="/static/logo-icon.png?v=20260930_opt" alt="Logo An Nahl" class="brand-icon-sidebar" style="height:26px;width:26px;max-width:28px;max-height:28px;object-fit:contain;display:block;">
                </div>
                <div class="min-w-0">
                    <div class="flex items-center gap-1.5">
                        <h1 class="font-bold text-sm tracking-tight text-white truncate">An Nahl Ops</h1>
                        <span class="px-1.5 py-0.2 rounded-md bg-[#4F786C]/40 text-emerald-200 text-[9px] font-mono uppercase tracking-wider border border-[#4F786C]/50">HQ</span>
                    </div>
                    <p class="text-[10.5px] text-slate-400 truncate">IT & General Affairs</p>
                </div>
            </div>
            <button onclick="toggleSidebar()" class="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800/80 md:hidden" title="Tutup Menu">
                <i class="fa-solid fa-xmark text-base"></i>
            </button>
        </div>

        <!-- Navigation Links -->
        <div class="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
            <div class="px-3 text-[10px] font-bold tracking-wider text-slate-500 uppercase mb-2">Operasional & Koordinator</div>

            <button onclick="showTab('tab-dashboard')" id="btn-tab-dashboard" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-white bg-emerald-600 transition">
                <i class="fa-solid fa-gauge text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Dashboard Utama</span>
            </button>

            <button onclick="showTab('tab-tasks')" id="btn-tab-tasks" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-clipboard-list text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Tiket & Pendelegasian</span>
            </button>

            <button onclick="showTab('tab-todo')" id="btn-tab-todo" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-square-check text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">To-Do List Unit</span>
            </button>

            <button onclick="showTab('tab-journal')" id="btn-tab-journal" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-book text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Jurnal Kegiatan Harian</span>
            </button>

            <div class="px-3 text-[10px] font-bold tracking-wider text-slate-500 uppercase mt-4 mb-2">Log Lapangan & Sarpras</div>

            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security'] %}
            <button onclick="showTab('tab-standby')" id="btn-tab-standby" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-satellite-dish text-base w-5 shrink-0 text-center text-sky-400"></i>
                <span class="text-left flex-1">Kesiagaan Pos (Standby)</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'pic_sarpras'] %}
            <button onclick="showTab('tab-checklist')" id="btn-tab-checklist" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-clipboard-check text-base w-5 shrink-0 text-center text-emerald-400"></i>
                <span class="text-left flex-1">Checklist OB & Green Ops</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_security'] %}
            <button onclick="showTab('tab-mutabaah')" id="btn-tab-mutabaah" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-hands-praying text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Log Mutabaah WA</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'pic_sarpras'] %}
            <button onclick="showTab('tab-kebersihan')" id="btn-tab-kebersihan" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-broom text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Log Kebersihan & Foto</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'pic_pengadaan', 'pic_sarpras'] %}
            <button onclick="showTab('tab-pengadaan')" id="btn-tab-pengadaan" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-cart-shopping text-base w-5 shrink-0 text-center text-amber-400"></i>
                <span class="text-left flex-1">Pengadaan Barang & Sarpras</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'pic_sarpras'] %}
            <button onclick="showTab('tab-pemeliharaan')" id="btn-tab-pemeliharaan" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-screwdriver-wrench text-base w-5 shrink-0 text-center text-teal-400"></i>
                <span class="text-left flex-1">Pemeliharaan Sarpras (PM)</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'pic_sarpras'] %}
            <button onclick="showTab('tab-evaluasi')" id="btn-tab-evaluasi" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-clipboard-user text-base w-5 shrink-0 text-center text-indigo-400"></i>
                <span class="text-left flex-1">Rapor & Evaluasi Personil</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_it', 'pic_sarpras', 'koordinator_ob'] %}
            <button onclick="showTab('tab-sapaais')" id="btn-tab-sapaais" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-bullhorn text-base w-5 shrink-0 text-center text-emerald-400"></i>
                <span class="text-left flex-1">Sapa Ais / LaporPak</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_it', 'pic_sarpras', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security', 'pic_pengadaan'] %}
            <button onclick="showTab('tab-mutubaah')" id="btn-tab-mutubaah" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-book-open text-base w-5 shrink-0 text-center text-teal-400"></i>
                <span class="text-left flex-1">Mutabaah Diri Civitas</span>
            </button>
            {% endif %}

            {% if user_role in ['manager', 'koordinator_it'] %}
            <div class="px-3 text-[10px] font-bold tracking-wider text-slate-500 uppercase mt-4 mb-2">Monitor Server</div>

            <button onclick="showTab('tab-server')" id="btn-tab-server" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-server text-base w-5 shrink-0 text-center text-blue-400"></i>
                <span class="text-left flex-1">Server</span>
            </button>

            <button onclick="showTab('tab-kuma')" id="btn-tab-kuma" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-tower-broadcast text-base w-5 shrink-0 text-center text-rose-400"></i>
                <span class="text-left flex-1">Uptime Kuma Monitor</span>
            </button>
            {% endif %}

            {% if user_role == 'manager' %}
            <button onclick="showTab('tab-analytics')" id="btn-tab-analytics" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-chart-pie text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Grafik & Analitik Tren</span>
            </button>

            <button onclick="showTab('tab-report')" id="btn-tab-report" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-print text-base w-5 shrink-0 text-center"></i>
                <span class="text-left flex-1">Cetak Laporan</span>
            </button>

            <div class="px-3 text-[10px] font-bold tracking-wider text-emerald-400 uppercase mt-4 mb-2 flex items-center justify-between">
                <span>Pengaturan & Akses</span>
                <span class="text-[9px] px-1.5 py-0.2 bg-emerald-950 border border-emerald-700 text-emerald-300 rounded">Admin</span>
            </div>

            <button onclick="showTab('tab-users')" id="btn-tab-users" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-users-gear text-base w-5 shrink-0 text-center text-emerald-400"></i>
                <span class="text-left flex-1">Manajemen User</span>
            </button>

            <button onclick="showTab('tab-roles')" id="btn-tab-roles" class="tab-btn w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition">
                <i class="fa-solid fa-shield-halved text-base w-5 shrink-0 text-center text-teal-400"></i>
                <span class="text-left flex-1">Manajemen Role Akses</span>
            </button>

            <a href="/bot-qr" target="_blank" class="w-full px-3.5 py-2.5 rounded-xl flex items-center text-left space-x-3 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition group">
                <i class="fa-brands fa-whatsapp text-base w-5 shrink-0 text-center text-emerald-400 group-hover:scale-110 transition"></i>
                <span class="text-left flex-1">Koneksi WhatsApp Bot</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[10px] ml-auto opacity-60"></i>
            </a>
            {% endif %}
        </div>

        <!-- Sidebar Footer User Profile & Logout -->
        <div class="p-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
            <div class="flex items-center space-x-2.5 min-w-0 flex-1">
                <div class="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center font-bold text-white text-xs shrink-0 shadow-xs">
                    {{ user_nama[:2]|upper }}
                </div>
                <div class="min-w-0 flex-1">
                    <p class="text-xs font-semibold text-white truncate">{{ user_nama }}</p>
                    <p class="text-[10px] text-slate-400 truncate">{{ user_role_name }}</p>
                </div>
            </div>
            <a href="/logout" onclick="return confirm('Apakah Anda yakin ingin keluar dari sistem?')" title="Keluar dari Sistem An Nahl Ops" class="px-2.5 py-1.5 text-xs font-bold text-rose-400 hover:text-white bg-rose-950/40 hover:bg-rose-600 border border-rose-800/60 rounded-lg transition flex items-center gap-1.5 shrink-0 ml-1">
                <i class="fa-solid fa-right-from-bracket text-xs"></i>
                <span class="text-[11px]">Logout</span>
            </a>
        </div>
    </aside>

    <!-- RIGHT MAIN CONTENT -->
    <main id="main-content" class="flex-1 transition-all duration-300 md:ml-64 min-h-screen flex flex-col w-full">

        <!-- Top Header Bar -->
        <header class="h-14 sm:h-16 bg-white/95 backdrop-blur-md border-b border-[#E8E4DD] px-3 sm:px-6 flex items-center justify-between shadow-2xs sticky top-0 z-20">
            <div class="flex items-center space-x-2.5 sm:space-x-3">
                <button onclick="toggleSidebar()" class="p-2 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none transition active:scale-95" title="Buka/Tutup Menu">
                    <i class="fa-solid fa-bars text-base sm:text-lg"></i>
                </button>
                <div class="flex items-center gap-2.5">
                    <span class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center text-xs font-bold border border-emerald-200 shadow-2xs">
                        <i class="fa-solid fa-gauge-high"></i>
                    </span>
                    <div>
                        <h2 id="page-title" class="text-xs sm:text-sm font-bold text-slate-800 leading-tight">Dashboard Utama</h2>
                        <p class="text-[10px] text-slate-500 font-medium hidden sm:block leading-tight">Sekolah Islam An Nahl &bull; Command Center</p>
                    </div>
                </div>
            </div>
            <div class="flex items-center space-x-2 sm:space-x-3 text-xs">
                <div id="bot-status-badge" class="inline-flex items-center"></div>
                <span class="px-2.5 py-1 bg-[#EAF1EE] text-[#2E584C] font-semibold rounded-full border border-[#D5E3DD] hidden lg:flex items-center gap-1.5 text-[11px]">
                    <span class="w-2 h-2 rounded-full bg-[#4F786C] animate-pulse"></span> Tunnel Active
                </span>
                <span class="text-slate-500 text-[11px] sm:text-xs hidden md:inline-flex items-center font-medium">
                    <i class="fa-regular fa-clock mr-1 text-[#4F786C]"></i> {{ now_str }}
                </span>

                <!-- Top Header User Info & Logout Button -->
                <div class="flex items-center pl-2 sm:pl-3 border-l border-[#E8E4DD] space-x-2">
                    <div class="hidden sm:flex items-center space-x-2 bg-[#FAF9F6] border border-[#E2DDD5] rounded-xl px-2.5 py-1 shadow-2xs">
                        <div class="w-6 h-6 rounded-lg bg-[#4F786C] text-white flex items-center justify-center font-bold text-[10px] shrink-0">
                            {{ user_nama[:2]|upper }}
                        </div>
                        <div class="text-left">
                            <span class="block text-xs font-bold text-slate-800 leading-tight">{{ user_nama }}</span>
                            <span class="block text-[10px] text-slate-500 leading-tight">{{ user_role_name }}</span>
                        </div>
                    </div>

                    <!-- Tombol Logout Terlihat Jelas -->
                    <a href="/logout" onclick="return confirm('Apakah Anda yakin ingin keluar dari sistem?')" title="Keluar dari Sistem An Nahl Ops" class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-600 hover:text-white border border-rose-200 rounded-xl transition shadow-2xs active:scale-95">
                        <i class="fa-solid fa-right-from-bracket text-xs"></i>
                        <span>Logout</span>
                    </a>
                </div>
            </div>
        </header>

        <!-- Main Body Content -->
        <div class="p-4 sm:p-8 flex-1 space-y-6">

            <!-- TAB 0: DASHBOARD UTAMA (OVERVIEW) -->
            <div id="tab-dashboard" class="tab-content space-y-6">

                <!-- Taste Skill: Executive Cockpit Hero Banner with Official Branding & OHS Index -->
                <div class="relative overflow-hidden rounded-3xl bg-white border border-slate-200/90 shadow-sm p-6 sm:p-7">
                    <!-- Subtle ambient background -->
                    <div class="absolute -right-20 -top-20 w-80 h-80 rounded-full bg-emerald-50/70 pointer-events-none blur-3xl"></div>
                    <div class="absolute -left-20 -bottom-20 w-80 h-80 rounded-full bg-slate-50/80 pointer-events-none blur-3xl"></div>

                    <div class="relative z-10 space-y-5">
                        <!-- Top Row: Logo + Headings + OHS Score Card -->
                        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-5">
                            <div class="flex items-start gap-4 sm:gap-5 flex-1 min-w-0">
                                <div class="p-2.5 sm:p-3 bg-slate-50 rounded-2xl border border-slate-200 shadow-2xs shrink-0 flex items-center justify-center">
                                    <img src="/static/logo.png?v=20260930_opt" alt="Sekolah Islam An Nahl" class="brand-logo-hero" style="height:52px;width:auto;max-width:60px;max-height:56px;object-fit:contain;display:block;">
                                </div>
                                <div class="space-y-1.5 flex-1 min-w-0">
                                    <div class="inline-flex items-center gap-2 px-3 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[11px] font-bold border border-emerald-200">
                                        <span class="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
                                        <span>Executive Command Center &bull; IT & General Affairs</span>
                                    </div>
                                    <h1 class="text-xl sm:text-2xl font-extrabold text-slate-800 tracking-tight leading-snug">
                                        Bismillah, Selamat Datang di Command Center An Nahl Ops
                                    </h1>
                                    <p class="text-xs sm:text-sm text-slate-500 font-medium max-w-2xl leading-relaxed">
                                        Pusat kendali 4 unit kerja koordinator lapangan (IT, OB, Gardener, Security), tata kelola Sarpras closed-loop, pemeliharaan Green Ops, dan habit tracker ibadah civitas.
                                    </p>
                                </div>
                            </div>

                            <!-- Operational Health Score (OHS) Card -->
                            <div class="w-full lg:w-72 p-4 bg-gradient-to-br from-slate-50 to-emerald-50/50 rounded-2xl border border-emerald-200/80 shadow-2xs space-y-2.5 shrink-0">
                                <div class="flex items-center justify-between">
                                    <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                        <i class="fa-solid fa-heart-pulse text-emerald-600"></i> OHS Indeks
                                    </span>
                                    <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border {{ analytics.ohs.badge_class }}">
                                        <span class="w-1.5 h-1.5 rounded-full {{ analytics.ohs.dot_class }} animate-ping"></span>
                                        {{ analytics.ohs.category }}
                                    </span>
                                </div>
                                <div class="flex items-baseline gap-2">
                                    <span class="text-3xl font-extrabold text-slate-800 tracking-tight">{{ analytics.ohs.score }}%</span>
                                    <span class="text-xs text-slate-500 font-medium">Skor Kesehatan Kampus</span>
                                </div>
                                <!-- 5 Mini Sub-Scores -->
                                <div class="space-y-1.5 pt-2 border-t border-slate-200/60 text-[10.5px]">
                                    <div class="flex justify-between items-center text-slate-600">
                                        <span class="truncate">Server & IT (20%)</span>
                                        <span class="font-bold text-slate-700">{{ analytics.ohs.scores.server }}%</span>
                                    </div>
                                    <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                        <div class="bg-emerald-600 h-1.5 rounded-full" style="width: {{ analytics.ohs.scores.server }}%;"></div>
                                    </div>

                                    <div class="flex justify-between items-center text-slate-600">
                                        <span class="truncate">Pos Standby (20%)</span>
                                        <span class="font-bold text-slate-700">{{ analytics.ohs.scores.pos }}%</span>
                                    </div>
                                    <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                        <div class="bg-sky-600 h-1.5 rounded-full" style="width: {{ analytics.ohs.scores.pos }}%;"></div>
                                    </div>

                                    <div class="flex justify-between items-center text-slate-600">
                                        <span class="truncate">Sanitasi & Checklist (20%)</span>
                                        <span class="font-bold text-slate-700">{{ analytics.ohs.scores.checklist }}%</span>
                                    </div>
                                    <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                        <div class="bg-purple-600 h-1.5 rounded-full" style="width: {{ analytics.ohs.scores.checklist }}%;"></div>
                                    </div>

                                    <div class="flex justify-between items-center text-slate-600">
                                        <span class="truncate">SLA Sarpras (20%)</span>
                                        <span class="font-bold text-slate-700">{{ analytics.ohs.scores.sarpras }}%</span>
                                    </div>
                                    <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                        <div class="bg-amber-600 h-1.5 rounded-full" style="width: {{ analytics.ohs.scores.sarpras }}%;"></div>
                                    </div>

                                    <div class="flex justify-between items-center text-slate-600">
                                        <span class="truncate">Mutabaah Civitas (20%)</span>
                                        <span class="font-bold text-slate-700">{{ analytics.ohs.scores.mutabaah }}%</span>
                                    </div>
                                    <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                        <div class="bg-teal-600 h-1.5 rounded-full" style="width: {{ analytics.ohs.scores.mutabaah }}%;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Middle Row: Executive One-Liner Briefing (Human-Friendly Narration) -->
                        <div class="p-3.5 bg-slate-50/90 rounded-2xl border border-slate-200/90 flex items-start gap-3">
                            <div class="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 text-sm mt-0.5 shadow-2xs">
                                <i class="fa-solid fa-wand-magic-sparkles"></i>
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2 mb-0.5">
                                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-emerald-700">Ringkasan Eksekutif Operasional Kampus Hari Ini</span>
                                    <span class="text-[10px] text-slate-400">&bull; {{ current_time }} WIB</span>
                                </div>
                                <p class="text-xs sm:text-[13px] text-slate-700 font-medium leading-relaxed">
                                    {{ analytics.executive_briefing }}
                                </p>
                            </div>
                        </div>

                        <!-- Bottom Row: 4 Live Dynamic Unit Coordinator Status Cards -->
                        <div class="pt-3 border-t border-slate-100 grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                            {% for ucard in analytics.unit_cards %}
                            <div class="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-200/80 hover:bg-white hover:border-emerald-300 hover:shadow-xs transition cursor-pointer group"
                                 onclick="{% if ucard.title == 'Unit IT' %}showTab('tab-kuma'){% elif ucard.title == 'Unit Office Boy' %}showTab('tab-kebersihan'){% elif ucard.title == 'Unit Gardener' %}showTab('tab-standby'){% else %}showTab('tab-standby'){% endif %}">
                                <div class="w-10 h-10 rounded-xl {{ ucard.bg_color }} text-white flex items-center justify-center text-sm shrink-0 shadow-xs group-hover:scale-105 transition">
                                    <i class="fa-solid {{ ucard.icon }} {{ ucard.text_accent }}"></i>
                                </div>
                                <div class="min-w-0 flex-1">
                                    <div class="flex items-center justify-between">
                                        <span class="text-xs font-bold text-slate-800 truncate group-hover:text-emerald-700 transition">{{ ucard.title }}</span>
                                        <span class="text-[10px] font-bold text-slate-600">{{ ucard.metric_value }}</span>
                                    </div>
                                    <p class="text-[10.5px] text-slate-500 font-medium truncate mt-0.5">{{ ucard.metric_label }}</p>
                                    <div class="flex items-center gap-1.5 mt-1">
                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                                        <span class="text-[10px] font-semibold {{ ucard.status_color }} truncate">{{ ucard.status_tag }}</span>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>

                    </div>
                </div>

                <!-- Row 2: 5 Top Summary Metric Cards -->
                <div class="grid grid-cols-2 md:grid-cols-5 gap-3 sm:gap-4">
                    <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                        <div>
                            <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Memory Server</p>
                            <h3 class="text-base sm:text-xl font-bold text-slate-800 mt-1">{{ stats.mem_str.split('/')[0] }}</h3>
                            <p class="text-[10px] sm:text-xs text-slate-400 mt-1">Penggunaan: {{ stats.mem_pct }}%</p>
                        </div>
                        <div class="p-2.5 sm:p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                            <i class="fa-solid fa-microchip text-lg sm:text-2xl"></i>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                        <div>
                            <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Kapasitas Disk (`/`)</p>
                            <h3 class="text-base sm:text-xl font-bold text-slate-800 mt-1">{{ stats.disk_str.split('/')[0] }}</h3>
                            <p class="text-[10px] sm:text-xs text-slate-400 mt-1">Terpakai: {{ stats.disk_pct }}%</p>
                        </div>
                        <div class="p-2.5 sm:p-3 bg-blue-50 text-blue-600 rounded-xl">
                            <i class="fa-solid fa-hard-drive text-lg sm:text-2xl"></i>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between cursor-pointer hover:border-emerald-300 transition" onclick="showTab('tab-kuma')">
                        <div>
                            <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Infrastruktur Server</p>
                            <h3 class="text-base sm:text-xl font-bold text-slate-800 mt-1">{{ analytics.stats_overview.server_online }}/{{ analytics.stats_overview.server_total }} Host</h3>
                            <p class="text-[10px] sm:text-xs text-emerald-600 mt-1"><i class="fa-solid fa-circle-check mr-1"></i>Ping Avg {{ analytics.stats_overview.server_avg_latency }}ms</p>
                        </div>
                        <div class="p-2.5 sm:p-3 bg-rose-50 text-rose-600 rounded-xl">
                            <i class="fa-solid fa-tower-broadcast text-lg sm:text-2xl"></i>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between cursor-pointer hover:border-emerald-300 transition" onclick="showTab('tab-standby')">
                        <div>
                            <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Kesiagaan Pos</p>
                            <h3 class="text-base sm:text-xl font-bold text-slate-800 mt-1">{{ analytics.stats_overview.standby_on_time }}/{{ analytics.stats_overview.standby_points_total }} Pos</h3>
                            <p class="text-[10px] sm:text-xs text-sky-600 mt-1"><i class="fa-solid fa-location-dot mr-1"></i>{{ analytics.stats_overview.standby_total_today }} Log Hari Ini</p>
                        </div>
                        <div class="p-2.5 sm:p-3 bg-sky-50 text-sky-600 rounded-xl">
                            <i class="fa-solid fa-street-view text-lg sm:text-2xl"></i>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between cursor-pointer hover:border-emerald-300 transition col-span-2 sm:col-span-1" onclick="showTab('tab-tasks')">
                        <div>
                            <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Tiket & Sarpras</p>
                            <h3 class="text-base sm:text-xl font-bold text-slate-800 mt-1">{{ analytics.stats_overview.tasks_pending }} Pending</h3>
                            <p class="text-[10px] sm:text-xs text-emerald-600 mt-1"><i class="fa-solid fa-check-double mr-1"></i>{{ analytics.stats_overview.tasks_done }} Selesai</p>
                        </div>
                        <div class="p-2.5 sm:p-3 bg-purple-50 text-purple-600 rounded-xl">
                            <i class="fa-solid fa-toolbox text-lg sm:text-2xl"></i>
                        </div>
                    </div>
                </div>

                <!-- Row 3: Urgent Action Center & Green Ops Row -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Left: Urgent Action Center (2/3 width) -->
                    <div class="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs p-5 sm:p-6 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                            <div>
                                <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                    <i class="fa-solid fa-triangle-exclamation text-amber-500"></i>
                                    Pusat Aksi Cepat & Eskalasi Masalah
                                </h3>
                                <p class="text-xs text-slate-500 mt-0.5">Daftar isu operasional mendesak yang membutuhkan perhatian pimpinan atau koordinator lapangan</p>
                            </div>
                            <span class="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg">
                                {{ analytics.urgent_items|length }} Perlu Perhatian
                            </span>
                        </div>

                        {% if analytics.urgent_items %}
                        <div class="space-y-3">
                            {% for item in analytics.urgent_items %}
                            <div class="p-3.5 bg-slate-50 hover:bg-slate-100/80 rounded-xl border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition">
                                <div class="space-y-1 flex-1 min-w-0">
                                    <div class="flex items-center gap-2">
                                        <span class="px-2 py-0.5 text-[10px] font-extrabold uppercase rounded-md border {{ item.badge_color }}">
                                            {{ item.badge }}
                                        </span>
                                        <h4 class="text-xs sm:text-sm font-bold text-slate-800 truncate">{{ item.title }}</h4>
                                    </div>
                                    <p class="text-xs text-slate-600 line-clamp-1">{{ item.desc }}</p>
                                </div>
                                <button onclick="showTab('{{ item.link_tab }}')" class="px-3 py-1.5 text-xs font-bold text-emerald-700 bg-white border border-emerald-200 hover:bg-emerald-50 rounded-lg shrink-0 shadow-2xs flex items-center gap-1.5 transition">
                                    <span>{{ item.action_text }}</span>
                                    <i class="fa-solid fa-arrow-right text-[10px]"></i>
                                </button>
                            </div>
                            {% endfor %}
                        </div>
                        {% else %}
                        <div class="p-6 bg-emerald-50/50 rounded-xl border border-emerald-200 text-center space-y-2">
                            <i class="fa-solid fa-circle-check text-emerald-600 text-3xl"></i>
                            <h4 class="text-sm font-bold text-emerald-800">Alhamdulillah, Seluruh Layanan & Pos Normal</h4>
                            <p class="text-xs text-emerald-600">Tidak ada alert kritis atau tiket sarpras darurat yang tertunda hari ini.</p>
                        </div>
                        {% endif %}
                    </div>

                    <!-- Right: Green Ops & Dampak Efisiensi Kampus (1/3 width) -->
                    <div class="bg-gradient-to-br from-emerald-900 to-slate-900 text-white rounded-2xl shadow-xs p-5 sm:p-6 space-y-4 flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between border-b border-emerald-800/80 pb-3 mb-4">
                                <h3 class="font-bold text-sm text-emerald-300 flex items-center gap-2">
                                    <i class="fa-solid fa-seedling text-emerald-400"></i>
                                    Green Ops & Efisiensi
                                </h3>
                                <span class="text-[10px] font-bold px-2 py-0.5 bg-emerald-800/80 text-emerald-200 rounded-md">Bulan Ini</span>
                            </div>
                            <p class="text-xs text-slate-300 leading-relaxed mb-4">
                                Kontribusi nyata digitalisasi inspeksi PWA, deteksi kran bocor, dan checklist paperless bagi kelestarian lingkungan sekolah.
                            </p>

                            <div class="space-y-3">
                                <div class="p-3 bg-white/10 rounded-xl border border-white/10 flex items-center justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-sm">
                                            <i class="fa-solid fa-droplet"></i>
                                        </div>
                                        <div>
                                            <p class="text-[11px] text-slate-300">Air Bersih Diselamatkan</p>
                                            <h4 class="text-base font-extrabold text-white mt-0.5">{{ analytics.eco_metrics.water_saved_liters }} Liter</h4>
                                        </div>
                                    </div>
                                    <span class="text-[10px] text-cyan-300 font-semibold">Toren & Kran</span>
                                </div>

                                <div class="p-3 bg-white/10 rounded-xl border border-white/10 flex items-center justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm">
                                            <i class="fa-solid fa-file-circle-check"></i>
                                        </div>
                                        <div>
                                            <p class="text-[11px] text-slate-300">Kertas Formulir Dihemat</p>
                                            <h4 class="text-base font-extrabold text-white mt-0.5">{{ analytics.eco_metrics.paper_saved_sheets }} Lembar</h4>
                                        </div>
                                    </div>
                                    <span class="text-[10px] text-emerald-300 font-semibold">100% QR PWA</span>
                                </div>

                                <div class="p-3 bg-white/10 rounded-xl border border-white/10 flex items-center justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center text-sm">
                                            <i class="fa-solid fa-cloud"></i>
                                        </div>
                                        <div>
                                            <p class="text-[11px] text-slate-300">Jejak Karbon Terpangkas</p>
                                            <h4 class="text-base font-extrabold text-white mt-0.5">{{ analytics.eco_metrics.co2_saved_kg }} kg CO₂e</h4>
                                        </div>
                                    </div>
                                    <span class="text-[10px] text-amber-300 font-semibold">Eco-Friendly</span>
                                </div>
                            </div>
                        </div>

                        <div class="pt-3 border-t border-emerald-800/60 flex items-center justify-between text-[11px] text-emerald-300">
                            <span>Target ISO 21001 & 14001</span>
                            <button onclick="showTab('tab-checklist')" class="hover:underline font-semibold text-white">Lihat Detail Checklist →</button>
                        </div>
                    </div>
                </div>

                <!-- Row 4: Interactive Charts on Main Dashboard -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Chart 1: Kecepatan Closed-Loop Sarpras -->
                    <div class="bg-white rounded-2xl shadow-xs border border-slate-200 p-6 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                            <div>
                                <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                    <i class="fa-solid fa-chart-column text-emerald-600"></i>
                                    Kecepatan Closed-Loop Tiket Sarpras (7 Hari)
                                </h3>
                                <p class="text-xs text-slate-500 mt-0.5">Perbandingan tiket masuk vs tiket terselesaikan tepat waktu</p>
                            </div>
                            <button onclick="showTab('tab-tasks')" class="text-xs text-emerald-600 hover:underline font-semibold">Kelola Tiket →</button>
                        </div>
                        <div class="h-64">
                            <canvas id="dashVelocityChart"></canvas>
                        </div>
                    </div>

                    <!-- Chart 2: Kesiagaan Pos & Partisipasi Mutabaah -->
                    <div class="bg-white rounded-2xl shadow-xs border border-slate-200 p-6 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                            <div>
                                <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                    <i class="fa-solid fa-chart-line text-sky-600"></i>
                                    Tren Kesiagaan Pos & Ibadah Petugas (7 Hari)
                                </h3>
                                <p class="text-xs text-slate-500 mt-0.5">Kedisiplinan check-in pos siaga & pelaporan mutabaah yaumiyah</p>
                            </div>
                            <button onclick="showTab('tab-analytics')" class="text-xs text-emerald-600 hover:underline font-semibold">Lihat Analitik Full →</button>
                        </div>
                        <div class="h-64">
                            <canvas id="dashMutabaahChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Row 5: Live Activity Timeline & Feed Operasional Terkini -->
                <div class="bg-white rounded-2xl shadow-xs border border-slate-200 p-6 space-y-4">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div>
                            <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-clock-rotate-left text-slate-600"></i>
                                Feed Aktivitas Operasional Terkini
                            </h3>
                            <p class="text-xs text-slate-500 mt-0.5">Aliran pembaruan real-time dari pos siaga, laporan kebersihan, dan mutabaah ibadah</p>
                        </div>
                        <span class="text-xs text-slate-400"><i class="fa-solid fa-rss text-emerald-600 mr-1"></i>Real-time Feed</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {% for event in analytics.timeline_events %}
                        <div class="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/70 hover:bg-white hover:shadow-xs transition flex items-start gap-3">
                            <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border text-xs {{ event.color }}">
                                <i class="fa-solid {{ event.icon }}"></i>
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center justify-between gap-1">
                                    <span class="text-[10px] font-extrabold uppercase px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-600">{{ event.unit }}</span>
                                    <span class="text-[10px] text-slate-400 font-mono">{{ event.time[11:16] }}</span>
                                </div>
                                <h4 class="text-xs font-bold text-slate-800 truncate mt-1">{{ event.title }}</h4>
                                <p class="text-[11px] text-slate-500 truncate mt-0.5">{{ event.desc }}</p>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

            </div>

            <!-- TAB 0.1: UPTIME KUMA STYLE MONITORING & ALERTS -->

                        <!-- TAB: SERVER LIST & DETAIL -->
            <div id="tab-server" class="tab-content hidden space-y-6">
                <!-- Server List View (default) -->
                <div id="server-list-view" class="space-y-6">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-6">
                            <div>
                                <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                    <i class="fa-solid fa-server text-blue-600"></i>
                                    Daftar Server Terhubung
                                </h2>
                                <p class="text-xs text-slate-500 mt-1">Klik card server untuk melihat detail real-time (CPU, Memory, Disk, Proses, Network)</p>
                            </div>
                        </div>

                        <!-- Server Cards Grid -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" id="server-cards-grid">
                            {% for host in monitored_hosts %}
                            <div class="server-card p-4 rounded-xl border border-slate-200 bg-white hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
                                 onclick="showServerDetail('{{ host.id }}')"
                                 data-host-id="{{ host.id }}"
                                 data-host-name="{{ host.name }}"
                                 data-host-ip="{{ host.host }}"
                                 data-host-category="{{ host.category or 'Server' }}"
                                 data-host-type="{{ host.type }}"
                                 data-host-port="{{ host.port or '' }}"
                                 data-host-last-check="{{ host.last_check or '-' }}">
                                <div class="flex items-start justify-between mb-3">
                                    <span class="px-2.5 py-0.5 text-[10px] font-bold tracking-wide uppercase bg-slate-100 text-slate-600 rounded-md group-hover:bg-blue-50 group-hover:text-blue-700 transition">
                                        {{ host.category or 'Server' }}
                                    </span>
                                    <div class="w-2 h-2 rounded-full {% if host.last_status == 'ONLINE' %}bg-emerald-500{% else %}bg-rose-500{% endif %} animate-pulse"></div>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-800 group-hover:text-blue-700 transition truncate">{{ host.name }}</h3>
                                <p class="text-xs font-mono text-slate-500 mt-1 truncate">{{ host.host }}{% if host.port %}:{{ host.port }}{% endif %}</p>
                                <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                                    <span><i class="fa-solid fa-signal mr-1"></i>{{ host.latency_ms or 0 }} ms</span>
                                    <span><i class="fa-solid fa-clock mr-1"></i>{{ host.last_check or '-' }}</span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                <!-- Server Detail View (shown when card clicked) -->
                <div id="server-detail-view" class="hidden space-y-6">
                    <!-- Back button -->
                    <button onclick="showServerList()" class="px-4 py-2 text-sm font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1.5 transition">
                        <i class="fa-solid fa-arrow-left"></i> Kembali ke Daftar Server
                    </button>

                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6" id="server-detail-content">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                            <div>
                                <h2 class="text-base font-bold text-slate-800 flex items-center gap-2" id="detail-server-name">
                                    <i class="fa-solid fa-server text-blue-600"></i>
                                    Server Detail
                                </h2>
                                <p class="text-xs text-slate-500 mt-1" id="detail-server-meta">IP: - | Kategori: -</p>
                            </div>
                            <button onclick="refreshServerDetail()" class="px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-arrows-rotate"></i> Refresh
                            </button>
                        </div>

                        <!-- Status Badge -->
                        <div class="flex items-center gap-3 p-4 bg-slate-50 rounded-lg" id="detail-status-badge">
                            <div class="w-3 h-3 rounded-full bg-slate-400" id="detail-status-indicator"></div>
                            <span class="text-sm font-medium text-slate-700" id="detail-status-text">Memuat status...</span>
                            <span class="ml-auto text-xs text-slate-500" id="detail-last-check">Terakhir cek: -</span>
                        </div>

                        <!-- CPU & Load Cards -->
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4" id="detail-cpu-cards">
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">CPU Usage</p>
                                    <h3 id="detail-cpu-pct" class="text-xl font-bold text-slate-800 mt-1">--%</h3>
                                </div>
                                <div class="p-3 bg-blue-50 text-blue-600 rounded-xl">
                                    <i class="fa-solid fa-microchip text-2xl"></i>
                                </div>
                            </div>
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">CPU Cores</p>
                                    <h3 id="detail-cpu-cores" class="text-xl font-bold text-slate-800 mt-1">--</h3>
                                </div>
                                <div class="p-3 bg-purple-50 text-purple-600 rounded-xl">
                                    <i class="fa-solid fa-cpu-chip text-2xl"></i>
                                </div>
                            </div>
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">Load Avg (1m)</p>
                                    <h3 id="detail-load-1m" class="text-xl font-bold text-slate-800 mt-1">--</h3>
                                </div>
                                <div class="p-3 bg-orange-50 text-orange-600 rounded-xl">
                                    <i class="fa-solid fa-wave-square text-2xl"></i>
                                </div>
                            </div>
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">Uptime</p>
                                    <h3 id="detail-uptime" class="text-xl font-bold text-slate-800 mt-1">--</h3>
                                </div>
                                <div class="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                                    <i class="fa-solid fa-clock text-2xl"></i>
                                </div>
                            </div>
                        </div>

                        <!-- Memory & Disk Cards -->
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4" id="detail-mem-disk-cards">
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">Memory Used</p>
                                    <h3 id="detail-mem-used" class="text-xl font-bold text-slate-800 mt-1">-- GB</h3>
                                    <p class="text-[10px] text-slate-400 mt-1" id="detail-mem-pct">--%</p>
                                </div>
                                <div class="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                                    <i class="fa-solid fa-memory text-2xl"></i>
                                </div>
                            </div>
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">Memory Total</p>
                                    <h3 id="detail-mem-total" class="text-xl font-bold text-slate-800 mt-1">-- GB</h3>
                                </div>
                                <div class="p-3 bg-teal-50 text-teal-600 rounded-xl">
                                    <i class="fa-solid fa-database text-2xl"></i>
                                </div>
                            </div>
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">Disk Used</p>
                                    <h3 id="detail-disk-used" class="text-xl font-bold text-slate-800 mt-1">-- GB</h3>
                                    <p class="text-[10px] text-slate-400 mt-1" id="detail-disk-pct">--%</p>
                                </div>
                                <div class="p-3 bg-blue-50 text-blue-600 rounded-xl">
                                    <i class="fa-solid fa-hard-drive text-2xl"></i>
                                </div>
                            </div>
                            <div class="bg-white rounded-xl shadow-xs p-4 border border-slate-200 flex items-center justify-between">
                                <div>
                                    <p class="text-[11px] text-slate-500 font-medium">Disk Total</p>
                                    <h3 id="detail-disk-total" class="text-xl font-bold text-slate-800 mt-1">-- GB</h3>
                                </div>
                                <div class="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
                                    <i class="fa-solid fa-server text-2xl"></i>
                                </div>
                            </div>
                        </div>

                        <!-- Load Average Detail -->
                        <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4">
                            <h3 class="font-semibold text-sm text-slate-800 mb-3 flex items-center gap-2">
                                <i class="fa-solid fa-chart-area text-orange-600"></i>
                                Load Average Detail
                            </h3>
                            <div class="grid grid-cols-3 gap-4 text-center">
                                <div class="p-3 bg-slate-50 rounded-lg">
                                    <p class="text-[10px] text-slate-500">1 Menit</p>
                                    <p id="detail-load-1m-d" class="text-2xl font-bold text-slate-800">--</p>
                                </div>
                                <div class="p-3 bg-slate-50 rounded-lg">
                                    <p class="text-[10px] text-slate-500">5 Menit</p>
                                    <p id="detail-load-5m-d" class="text-2xl font-bold text-slate-800">--</p>
                                </div>
                                <div class="p-3 bg-slate-50 rounded-lg">
                                    <p class="text-[10px] text-slate-500">15 Menit</p>
                                    <p id="detail-load-15m-d" class="text-2xl font-bold text-slate-800">--</p>
                                </div>
                            </div>
                        </div>

                        <!-- Top Processes Table (htop-like) -->
                        <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6">
                            <h3 class="font-semibold text-sm text-slate-800 mb-4 flex items-center gap-2">
                                <i class="fa-solid fa-list-check text-rose-600"></i>
                                Top 10 Proses by CPU (ps aux --sort=-%cpu)
                            </h3>
                            <div class="overflow-x-auto">
                                <table class="w-full text-xs" id="detail-process-table">
                                    <thead>
                                        <tr class="border-b border-slate-200 text-left text-slate-500">
                                            <th class="pb-2 px-2">USER</th>
                                            <th class="pb-2 px-2">PID</th>
                                            <th class="pb-2 px-2">%CPU</th>
                                            <th class="pb-2 px-2">%MEM</th>
                                            <th class="pb-2 px-2">VSZ</th>
                                            <th class="pb-2 px-2">RSS</th>
                                            <th class="pb-2 px-2">TTY</th>
                                            <th class="pb-2 px-2">STAT</th>
                                            <th class="pb-2 px-2">START</th>
                                            <th class="pb-2 px-2">TIME</th>
                                            <th class="pb-2 px-2">COMMAND</th>
                                        </tr>
                                    </thead>
                                    <tbody id="detail-process-tbody">
                                        <tr><td colspan="11" class="text-center text-slate-400 py-4">Memuat...</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Network Interfaces -->
                        <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6">
                            <h3 class="font-semibold text-sm text-slate-800 mb-4 flex items-center gap-2">
                                <i class="fa-solid fa-network-wired text-indigo-600"></i>
                                Network Interfaces (ip -br addr show)
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-3" id="detail-net-interfaces">
                                <div class="text-center text-slate-400 py-4">Memuat...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>            <!-- / TAB: SERVER LIST & DETAIL -->

            <!-- TAB 0.1: UPTIME KUMA MONITOR -->
            <div id="tab-kuma" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-6">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-tower-broadcast text-rose-600"></i>
                                Target Monitoring (Uptime Kuma)
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">Kelola target yang dipantau oleh Uptime Kuma + notifikasi WA ke grup LaporPak / AIS_Umum</p>
                        </div>
                        <button onclick="toggleModal('modal-add-host')" class="px-4 py-2 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition shadow-xs flex items-center gap-1.5">
                            <i class="fa-solid fa-plus"></i> Tambah Target Monitor
                        </button>
                    </div>

                    <!-- Target Monitoring Grid -->
                    {% if monitored_hosts %}
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {% for host in monitored_hosts %}
                        <div class="p-4 rounded-xl border border-slate-200 bg-white hover:border-rose-300 hover:shadow-md transition-all">
                            <div class="flex items-start justify-between mb-3">
                                <span class="px-2.5 py-0.5 text-[10px] font-bold uppercase bg-slate-100 text-slate-600 rounded-md">{{ host.category or 'Server' }}</span>
                                <div class="w-2 h-2 rounded-full {% if host.last_status == 'ONLINE' %}bg-emerald-500{% else %}bg-rose-500{% endif %} animate-pulse"></div>
                            </div>
                            <h3 class="font-semibold text-sm text-slate-800 truncate">{{ host.name }}</h3>
                            <p class="text-xs font-mono text-slate-500 mt-1 truncate">{{ host.host }}{% if host.port %}:{{ host.port }}{% endif %}</p>
                            <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                                <span><i class="fa-solid fa-signal mr-1"></i>{{ host.latency_ms or 0 }} ms</span>
                                <span><i class="fa-solid fa-clock mr-1"></i>{{ host.last_check or '-' }}</span>
                            </div>
                            <div class="flex gap-2 mt-3">
                                <button type="button" onclick="editHost('{{ host.id }}')" class="flex-1 px-2.5 py-1.5 text-[10px] text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition">
                                    <i class="fa-solid fa-pen mr-1"></i>Edit
                                </button>
                                <form action="/delete_host" method="POST" onsubmit="return confirm('Hapus target monitor ini?')" class="flex-1">
                                    <input type="hidden" name="host_id" value="{{ host.id }}">
                                    <button type="submit" class="w-full px-2.5 py-1.5 text-[10px] text-rose-600 hover:bg-rose-50 rounded border border-rose-200 transition">
                                        <i class="fa-solid fa-trash mr-1"></i>Hapus
                                    </button>
                                </form>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="p-8 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl">
                        <i class="fa-solid fa-tower-broadcast text-3xl mb-2 text-slate-300"></i>
                        <p class="text-sm">Belum ada target monitor. Klik tombol <strong>Tambah Target Monitor</strong> di atas untuk memulai!</p>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- TAB 0.2: ANALYTICS & TREN KINERJA -->
            <div id="tab-analytics" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div>
                        <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-emerald-600"></i>
                            Grafik Analitik & Tren Kinerja Operasional
                        </h2>
                        <p class="text-xs text-slate-500 mt-1">Analisis visual keaktifan ibadah petugas, sebaran laporan kebersihan, dan progres tiket operasional</p>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Chart 1: Mutabaah Trend -->
                        <div class="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                                <i class="fa-solid fa-chart-column text-teal-600"></i>
                                Tren Keaktifan Mutabaah Yaumiyah (7 Hari)
                            </h3>
                            <div class="h-64 bg-white p-3 rounded-xl border border-slate-100">
                                <canvas id="fullMutabaahChart"></canvas>
                            </div>
                        </div>

                        <!-- Chart 2: Kebersihan Unit Distribution -->
                        <div class="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                                <i class="fa-solid fa-chart-pie text-purple-600"></i>
                                Sebaran Laporan Kebersihan per Unit
                            </h3>
                            <div class="h-64 bg-white p-3 rounded-xl border border-slate-100 flex justify-center">
                                <canvas id="fullKebersihanChart"></canvas>
                            </div>
                        </div>

                        <!-- Chart 3: Journal Activity Categories -->
                        <div class="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                                <i class="fa-solid fa-book text-emerald-600"></i>
                                Distribusi Jurnal Kegiatan Mr Slam
                            </h3>
                            <div class="h-64 bg-white p-3 rounded-xl border border-slate-100">
                                <canvas id="fullJournalChart"></canvas>
                            </div>
                        </div>

                        <!-- Chart 4: Task Ticket Status -->
                        <div class="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                                <i class="fa-solid fa-list-check text-blue-600"></i>
                                Status Tiket Pekerjaan Operasional
                            </h3>
                            <div class="h-64 bg-white p-3 rounded-xl border border-slate-100 flex justify-center">
                                <canvas id="fullTaskChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 0.5: JURNAL KEGIATAN HARIAN & SUPERVISI -->
            <div id="tab-journal" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-book text-emerald-600"></i>
                                {% if user_role == 'manager' %}
                                Jurnal Kegiatan Operasional & Supervisi 4 Unit
                                {% else %}
                                Jurnal Kegiatan Harian Unit {{ user_unit }}
                                {% endif %}
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">
                                {% if user_role == 'manager' %}
                                Dokumentasi hasil kerja, penugasan lapangan, dan supervisi harian Koordinator IT, OB, Gardener, dan Security
                                {% else %}
                                Dokumentasi kegiatan, progres pekerjaan, dan hasil kerja tim {{ user_unit }} hari ini
                                {% endif %}
                            </p>
                        </div>
                        <div class="flex items-center gap-2">
                            <a href="/export/journal" class="px-3 py-2 bg-teal-600 text-white text-xs font-semibold rounded-xl hover:bg-teal-700 transition shadow-xs flex items-center gap-1.5" title="Export Jurnal ke Excel">
                                <i class="fa-solid fa-file-excel"></i> Export Excel
                            </a>
                            <button onclick="toggleModal('modal-add-journal')" class="px-3.5 py-2 bg-emerald-600 text-white text-xs font-bold rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-plus"></i> Catat Jurnal Baru
                            </button>
                        </div>
                    </div>

                    <!-- TOOLBAR: FILTER UNIT, SEARCH & VIEW MODE SWITCHER -->
                    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 bg-slate-50/90 p-3 rounded-2xl border border-slate-200 text-xs">
                        <!-- Filter Unit -->
                        {% if user_role == 'manager' %}
                        <div class="flex flex-wrap items-center gap-1.5">
                            <span class="font-bold text-slate-600 text-[11px] uppercase tracking-wider mr-1">Unit:</span>
                            <button type="button" onclick="filterJournalsByUnit('ALL')" class="journal-filter-btn px-2.5 py-1 rounded-lg font-bold bg-emerald-600 text-white transition text-xs cursor-pointer shadow-2xs" data-unit="ALL">Semua Unit</button>
                            <button type="button" onclick="filterJournalsByUnit('IT')" class="journal-filter-btn px-2.5 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs cursor-pointer" data-unit="IT">IT</button>
                            <button type="button" onclick="filterJournalsByUnit('OB')" class="journal-filter-btn px-2.5 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs cursor-pointer" data-unit="OB">Office Boy</button>
                            <button type="button" onclick="filterJournalsByUnit('GARDENER')" class="journal-filter-btn px-2.5 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs cursor-pointer" data-unit="GARDENER">Gardener</button>
                            <button type="button" onclick="filterJournalsByUnit('SECURITY')" class="journal-filter-btn px-2.5 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs cursor-pointer" data-unit="SECURITY">Security</button>
                        </div>
                        {% else %}
                        <div class="flex items-center gap-2">
                            <span class="font-bold text-slate-700">Unit: {{ user_unit }}</span>
                        </div>
                        {% endif %}

                        <div class="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                            <!-- Input Search Live -->
                            <div class="relative flex-1 sm:w-64">
                                <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                                <input type="text" id="journal-search-input" onkeyup="searchJournals()" placeholder="Cari kegiatan / PIC / hasil..." class="w-full bg-white border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-emerald-500 shadow-2xs">
                            </div>

                            <!-- Switcher Mode Tabel vs Kartu -->
                            <div class="flex items-center bg-slate-200/80 p-0.5 rounded-xl border border-slate-300/60 shrink-0">
                                <button type="button" onclick="switchJournalView('table')" id="btn-journal-view-table" class="px-2.5 py-1 rounded-lg font-bold text-slate-800 bg-white shadow-2xs transition flex items-center gap-1 cursor-pointer">
                                    <i class="fa-solid fa-table-list text-emerald-600"></i>
                                    <span>Tabel</span>
                                </button>
                                <button type="button" onclick="switchJournalView('cards')" id="btn-journal-view-cards" class="px-2.5 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-800 transition flex items-center gap-1 cursor-pointer">
                                    <i class="fa-solid fa-grip"></i>
                                    <span>Kartu</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- 1. TAMPILAN TABEL JURNAL (DEFAULT UNTUK LAPTOP / DESKTOP) -->
                    <div id="journal-view-table" class="overflow-x-auto border border-slate-200 rounded-2xl bg-white shadow-xs">
                        <table class="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                                    <th class="py-3 px-3.5 w-32">Waktu & Tanggal</th>
                                    <th class="py-3 px-3 w-36">Unit & Penulis</th>
                                    <th class="py-3 px-4 min-w-[260px]">Aktivitas & Uraian Pekerjaan</th>
                                    <th class="py-3 px-3.5 min-w-[150px]">Hasil / Output</th>
                                    <th class="py-3 px-4 min-w-[220px]">Supervisi Pimpinan</th>
                                    <th class="py-3 px-3 w-28 text-center">Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="journal-table-tbody" class="divide-y divide-slate-100 text-slate-700">
                                {% for j in journals %}
                                <tr class="journal-row hover:bg-slate-50/80 transition" data-unit="{{ j.unit_code or 'ALL' }}">
                                    <!-- Waktu & Tanggal -->
                                    <td class="py-3 px-3.5 align-top">
                                        <span class="font-bold text-slate-800 block">{{ j.date }}</span>
                                        <span class="text-[11px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200 inline-block mt-0.5">
                                            <i class="fa-regular fa-clock text-slate-400 mr-0.5"></i>{{ j.time }} WIB
                                        </span>
                                    </td>

                                    <!-- Unit & Penulis -->
                                    <td class="py-3 px-3 align-top">
                                        {% if j.unit_code == 'IT' %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200 rounded-md block w-fit">Unit IT</span>
                                        {% elif j.unit_code == 'OB' %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-teal-100 text-teal-800 border border-teal-200 rounded-md block w-fit">Unit OB</span>
                                        {% elif j.unit_code == 'GARDENER' %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 rounded-md block w-fit">Unit Gardener</span>
                                        {% elif j.unit_code == 'SECURITY' %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200 rounded-md block w-fit">Unit Security</span>
                                        {% else %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-md block w-fit">{{ j.category or 'Manajemen' }}</span>
                                        {% endif %}
                                        <span class="text-xs text-slate-700 font-semibold block mt-1">
                                            <i class="fa-solid fa-user-pen text-slate-400 mr-1"></i>{{ j.author_nama or 'Mr Slam' }}
                                        </span>
                                    </td>

                                    <!-- Aktivitas & Uraian Pekerjaan -->
                                    <td class="py-3 px-4 align-top">
                                        <h4 class="font-bold text-slate-800 text-xs mb-1">{{ j.title }}</h4>
                                        <p class="text-slate-600 text-[11px] leading-relaxed whitespace-pre-line bg-slate-50/70 p-2 rounded-lg border border-slate-100">{{ j.description }}</p>
                                    </td>

                                    <!-- Hasil / Output -->
                                    <td class="py-3 px-3.5 align-top">
                                        {% if j.output %}
                                        <div class="bg-emerald-50/70 border border-emerald-100 rounded-lg p-2 text-[11px] text-emerald-900 leading-snug">
                                            <span class="font-bold text-emerald-800 block text-[10px] mb-0.5">
                                                <i class="fa-solid fa-flag-checkered text-emerald-600 mr-1"></i>Output:
                                            </span>
                                            {{ j.output }}
                                        </div>
                                        {% else %}
                                        <span class="text-slate-400 italic text-[11px]">-</span>
                                        {% endif %}
                                    </td>

                                    <!-- Supervisi Pimpinan -->
                                    <td class="py-3 px-4 align-top">
                                        {% if j.supervisor_feedback %}
                                        <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-2.5 text-[11px] space-y-1">
                                            <div class="flex items-center justify-between text-emerald-800 font-bold text-[10px]">
                                                <span><i class="fa-solid fa-user-shield text-emerald-600 mr-1"></i>{{ j.supervisor_feedback_by or 'Mr Slam' }}</span>
                                                <span class="text-slate-400 font-normal">{{ j.supervisor_feedback_at or '' }}</span>
                                            </div>
                                            <p class="text-emerald-950 leading-relaxed">{{ j.supervisor_feedback }}</p>
                                        </div>
                                        {% else %}
                                            {% if user_role == 'manager' %}
                                            <button type="button" onclick="openSupervisorFeedbackModal('{{ j.id }}', '{{ j.title|replace("'", "\\'") }}', '{{ j.author_nama|replace("'", "\\'") }}', '')"
                                                    class="px-2.5 py-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-600 hover:text-white border border-emerald-200 rounded-lg transition flex items-center gap-1 cursor-pointer">
                                                <i class="fa-solid fa-comment-dots"></i> Beri Supervisi
                                            </button>
                                            {% else %}
                                            <span class="text-slate-400 italic text-[11px]">Belum ada catatan</span>
                                            {% endif %}
                                        {% endif %}
                                    </td>

                                    <!-- Aksi -->
                                    <td class="py-3 px-3 align-top text-center">
                                        <div class="flex items-center justify-center space-x-1">
                                            {% if user_role == 'manager' and j.supervisor_feedback %}
                                            <button type="button" onclick="openSupervisorFeedbackModal('{{ j.id }}', '{{ j.title|replace("'", "\\'") }}', '{{ j.author_nama|replace("'", "\\'") }}', '{{ (j.supervisor_feedback or '')|replace("'", "\\'") }}')" 
                                                    class="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition cursor-pointer" 
                                                    title="Edit Catatan Supervisi">
                                                <i class="fa-solid fa-comment-dots"></i>
                                            </button>
                                            {% endif %}
                                            {% if user_role == 'manager' or j.author_username == session.get('ops_username') %}
                                            <button type="button" onclick="openEditJournalModal(this)"
                                                    data-id="{{ j.id }}"
                                                    data-title="{{ j.title }}"
                                                    data-category="{{ j.category or '' }}"
                                                    data-unit="{{ j.unit_code or 'ALL' }}"
                                                    data-date="{{ j.date }}"
                                                    data-time="{{ j.time }}"
                                                    data-desc="{{ j.description or '' }}"
                                                    data-output="{{ j.output or '' }}"
                                                    class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition text-xs cursor-pointer" title="Edit Jurnal">
                                                <i class="fa-solid fa-pen-to-square"></i>
                                            </button>
                                            <form action="/delete_journal" method="POST" class="inline" onsubmit="return confirm('Apakah Anda yakin ingin menghapus jurnal ini?')">
                                                <input type="hidden" name="journal_id" value="{{ j.id }}">
                                                <button type="submit" class="p-1.5 text-slate-300 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition text-xs cursor-pointer" title="Hapus Jurnal">
                                                    <i class="fa-solid fa-trash-can"></i>
                                                </button>
                                            </form>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="6" class="p-8 text-center text-slate-400">
                                        <i class="fa-solid fa-book-open text-3xl mb-2 text-slate-300"></i>
                                        <p class="text-sm">Belum ada catatan jurnal kegiatan.</p>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    <!-- 2. TAMPILAN KARTU JURNAL (ALTERNATIF / MOBILE MODE) -->
                    <div class="space-y-4 hidden" id="journal-view-cards">
                        {% for j in journals %}
                        <div class="journal-card p-5 rounded-2xl border border-slate-200 bg-white hover:border-slate-300 transition space-y-3 shadow-xs" data-unit="{{ j.unit_code or 'ALL' }}">
                            <div class="flex items-start justify-between">
                                <div class="space-y-1">
                                    <div class="flex flex-wrap items-center gap-2">
                                        {% if j.unit_code == 'IT' %}
                                        <span class="px-2.5 py-0.5 text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200 rounded-md">Unit IT</span>
                                        {% elif j.unit_code == 'OB' %}
                                        <span class="px-2.5 py-0.5 text-xs font-bold bg-teal-100 text-teal-800 border border-teal-200 rounded-md">Unit OB</span>
                                        {% elif j.unit_code == 'GARDENER' %}
                                        <span class="px-2.5 py-0.5 text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 rounded-md">Unit Gardener</span>
                                        {% elif j.unit_code == 'SECURITY' %}
                                        <span class="px-2.5 py-0.5 text-xs font-bold bg-indigo-100 text-indigo-800 border border-indigo-200 rounded-md">Unit Security</span>
                                        {% else %}
                                        <span class="px-2.5 py-0.5 text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-md">{{ j.category or 'Manajemen' }}</span>
                                        {% endif %}
                                        
                                        <span class="text-xs text-slate-600 font-semibold"><i class="fa-solid fa-user-pen mr-1 text-slate-400"></i>{{ j.author_nama or 'Mr Slam' }}</span>
                                        <span class="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200"><i class="fa-regular fa-clock mr-1 text-slate-400"></i>{{ j.date }} • {{ j.time }} WIB</span>
                                    </div>
                                    <h3 class="text-base font-bold text-slate-800 pt-1">{{ j.title }}</h3>
                                </div>
                                <div class="flex items-center space-x-2">
                                    {% if user_role == 'manager' %}
                                    <button type="button" onclick="openSupervisorFeedbackModal('{{ j.id }}', '{{ j.title|replace("'", "\\'") }}', '{{ j.author_nama|replace("'", "\\'") }}', '{{ (j.supervisor_feedback or '')|replace("'", "\\'") }}')" 
                                            class="px-2.5 py-1 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-600 hover:text-white border border-emerald-200 rounded-lg transition flex items-center gap-1 cursor-pointer" 
                                            title="Berikan Catatan Supervisi">
                                        <i class="fa-solid fa-comment-dots"></i>
                                        <span>{% if j.supervisor_feedback %}Edit Supervisi{% else %}Beri Supervisi{% endif %}</span>
                                    </button>
                                    {% endif %}
                                    {% if user_role == 'manager' or j.author_username == session.get('ops_username') %}
                                    <button type="button" onclick="openEditJournalModal(this)"
                                            data-id="{{ j.id }}"
                                            data-title="{{ j.title }}"
                                            data-category="{{ j.category or '' }}"
                                            data-unit="{{ j.unit_code or 'ALL' }}"
                                            data-date="{{ j.date }}"
                                            data-time="{{ j.time }}"
                                            data-desc="{{ j.description or '' }}"
                                            data-output="{{ j.output or '' }}"
                                            class="p-1.5 text-slate-400 hover:text-blue-600 transition text-xs cursor-pointer" title="Edit Jurnal">
                                        <i class="fa-solid fa-pen-to-square"></i>
                                    </button>
                                    <form action="/delete_journal" method="POST" class="inline" onsubmit="return confirm('Apakah Anda yakin ingin menghapus jurnal ini?')">
                                        <input type="hidden" name="journal_id" value="{{ j.id }}">
                                        <button type="submit" class="p-1.5 text-slate-300 hover:text-rose-600 transition text-xs cursor-pointer" title="Hapus Jurnal">
                                            <i class="fa-solid fa-trash-can"></i>
                                        </button>
                                    </form>
                                    {% endif %}
                                </div>
                            </div>

                            <p class="text-xs text-slate-700 leading-relaxed whitespace-pre-line bg-slate-50/80 p-3.5 rounded-xl border border-slate-100">{{ j.description }}</p>

                            {% if j.output %}
                            <div class="flex items-center space-x-2 text-xs text-slate-600 pt-0.5">
                                <span class="font-bold text-slate-700 flex items-center gap-1"><i class="fa-solid fa-flag-checkered text-emerald-600"></i>Hasil / Output:</span>
                                <span>{{ j.output }}</span>
                            </div>
                            {% endif %}

                            <!-- Catatan Supervisi Pimpinan (Mr. Slam) jika ada -->
                            {% if j.supervisor_feedback %}
                            <div class="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5 space-y-1 text-xs">
                                <div class="flex items-center justify-between text-emerald-800 font-bold">
                                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-user-shield text-emerald-600"></i>Catatan Supervisi ({{ j.supervisor_feedback_by or 'Mr Slam' }}):</span>
                                    <span class="text-[10px] text-emerald-600 font-normal">{{ j.supervisor_feedback_at or '' }}</span>
                                </div>
                                <p class="text-emerald-900 leading-relaxed pl-5">{{ j.supervisor_feedback }}</p>
                            </div>
                            {% endif %}
                        </div>
                        {% else %}
                        <div class="p-8 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl">
                            <i class="fa-solid fa-book-open text-3xl mb-2 text-slate-300"></i>
                            <p class="text-sm">Belum ada catatan jurnal kegiatan. Klik tombol <b>Catat Jurnal Baru</b> di atas untuk mendokumentasikan pekerjaan hari ini.</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- TAB 1: TODO LIST KOORDINATOR & MANAJEMEN -->
            <div id="tab-todo" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-list-check text-emerald-600"></i>
                                {% if user_role == 'manager' %}
                                Agenda To-Do & Pendelegasian Tim Koordinator
                                {% else %}
                                Daftar To-Do Unit {{ user_unit }}
                                {% endif %}
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">
                                {% if user_role == 'manager' %}
                                Pantau dan kelola agenda prioritas seluruh koordinator (IT, OB, Gardener, Security)
                                {% else %}
                                Catat tugas mandiri dan evaluasi penyelesaian target harian tim {{ user_unit }}
                                {% endif %}
                            </p>
                        </div>
                        <button onclick="toggleModal('modal-add-todo')" class="px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5 shrink-0">
                            <i class="fa-solid fa-plus"></i> Tambah To-Do Baru
                        </button>
                    </div>

                    {% if user_role == 'manager' %}
                    <!-- Filter Unit untuk Manager -->
                    <div class="flex flex-wrap items-center gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-xs">
                        <span class="font-bold text-slate-600 text-[11px] uppercase tracking-wider px-2">Filter Unit:</span>
                        <button onclick="filterTodosByUnit('ALL')" class="todo-filter-btn px-3 py-1 rounded-lg font-bold bg-emerald-600 text-white transition text-xs" data-unit="ALL">Semua Unit</button>
                        <button onclick="filterTodosByUnit('IT')" class="todo-filter-btn px-3 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs" data-unit="IT">IT</button>
                        <button onclick="filterTodosByUnit('OB')" class="todo-filter-btn px-3 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs" data-unit="OB">Office Boy</button>
                        <button onclick="filterTodosByUnit('GARDENER')" class="todo-filter-btn px-3 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs" data-unit="GARDENER">Gardener</button>
                        <button onclick="filterTodosByUnit('SECURITY')" class="todo-filter-btn px-3 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs" data-unit="SECURITY">Security</button>
                        <button onclick="filterTodosByUnit('Umum')" class="todo-filter-btn px-3 py-1 rounded-lg font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition text-xs" data-unit="Umum">Umum / Mr Slam</button>
                    </div>
                    {% endif %}

                    <div class="space-y-3" id="todos-container">
                        {% for todo in todos %}
                        <div class="todo-item p-4 rounded-xl border border-slate-200 flex items-center justify-between transition hover:border-slate-300 {% if todo.completed %}bg-slate-50/80{% else %}bg-white shadow-xs{% endif %}" data-unit="{{ todo.unit_code or todo.category or 'ALL' }}">
                            <div class="flex items-center space-x-3 min-w-0 flex-1">
                                <form action="/toggle_todo" method="POST" class="inline shrink-0">
                                    <input type="hidden" name="todo_id" value="{{ todo.id }}">
                                    <button type="submit" class="text-lg transition {% if todo.completed %}text-emerald-600{% else %}text-slate-300 hover:text-emerald-500{% endif %}" title="Tandai Selesai / Belum">
                                        <i class="fa-{% if todo.completed %}solid fa-circle-check{% else %}regular fa-circle{% endif %}"></i>
                                    </button>
                                </form>
                                <div class="min-w-0 flex-1">
                                    <p class="text-sm font-semibold {% if todo.completed %}line-through text-slate-400{% else %}text-slate-800{% endif %} truncate">
                                        {{ todo.title }}
                                    </p>
                                    <div class="flex flex-wrap items-center gap-2 text-xs mt-1">
                                        <span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-bold text-[10px] border border-slate-200">
                                            {{ todo.unit_code or todo.category or 'Umum' }}
                                        </span>
                                        {% if todo.due_date %}
                                        <span class="text-slate-400 text-[11px]"><i class="fa-regular fa-calendar mr-1"></i>Target: {{ todo.due_date }}</span>
                                        {% endif %}
                                        {% if todo.priority == 'Tinggi' %}
                                        <span class="px-1.5 py-0.5 text-[10px] font-bold bg-rose-100 text-rose-700 rounded">Tinggi</span>
                                        {% elif todo.priority == 'Sedang' %}
                                        <span class="px-1.5 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-700 rounded">Sedang</span>
                                        {% endif %}
                                        <span class="text-slate-400 text-[10px]"><i class="fa-regular fa-user mr-1"></i>{{ todo.created_by or 'Manajemen' }}</span>
                                    </div>
                                </div>
                            </div>
                            {% if user_role == 'manager' or todo.created_by == user_nama or todo.created_by == session.get('ops_username') %}
                            <form action="/delete_todo" method="POST" class="inline shrink-0 ml-2" onsubmit="return confirm('Hapus agenda to-do ini?')">
                                <input type="hidden" name="todo_id" value="{{ todo.id }}">
                                <button type="submit" class="p-2 text-slate-300 hover:text-rose-600 transition text-xs" title="Hapus To-Do">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </form>
                            {% else %}
                            <span class="p-2 text-slate-300 text-xs shrink-0 ml-2" title="Ditugaskan oleh Pimpinan (Hanya Pimpinan yang dapat menghapus)">
                                <i class="fa-solid fa-lock text-slate-300"></i>
                            </span>
                            {% endif %}
                        </div>
                        {% else %}
                        <div class="p-8 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl">
                            <i class="fa-regular fa-clipboard text-3xl mb-2 text-slate-300"></i>
                            <p class="text-sm">Belum ada daftar To-Do. Klik tombol <b>Tambah To-Do Baru</b> di atas untuk mulai mencatat!</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- TAB 2: TASKS & TIKET OPERASIONAL TERPADU -->
            <div id="tab-tasks" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-clipboard-list text-emerald-600"></i>
                                {% if user_role == 'manager' %}
                                Manajemen Tiket & Tugas Operasional 4 Unit
                                {% else %}
                                Daftar Tiket & Tugas Unit {{ user_unit }}
                                {% endif %}
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">
                                {% if user_role == 'manager' %}
                                Pendelegasian pekerjaan, target SLA, dan pemantauan tindak lanjut lapangan (IT, OB, Gardener, Security)
                                {% else %}
                                Pantau dan perbarui status penyelesaian tiket pekerjaan tim {{ user_unit }}
                                {% endif %}
                            </p>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="toggleModal('modal-add-task')" class="px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5 shrink-0">
                                <i class="fa-solid fa-plus"></i> Disposisi Tugas Baru
                            </button>
                        </div>
                    </div>

                    <!-- 4 Summary Metric Cards Tiket -->
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div class="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex items-center space-x-3 shadow-2xs">
                            <div class="w-10 h-10 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-sm shrink-0">
                                <i class="fa-solid fa-ticket"></i>
                            </div>
                            <div>
                                <span class="block text-[11px] text-slate-500 font-medium">Total Tiket</span>
                                <span class="text-lg font-bold text-slate-800" id="task-metric-total">{{ tasks|length }}</span>
                            </div>
                        </div>
                        <div class="bg-amber-50/70 border border-amber-200/70 rounded-2xl p-4 flex items-center space-x-3 shadow-2xs">
                            <div class="w-10 h-10 rounded-xl bg-amber-200 text-amber-800 flex items-center justify-center font-bold text-sm shrink-0">
                                <i class="fa-solid fa-clock"></i>
                            </div>
                            <div>
                                <span class="block text-[11px] text-amber-700 font-medium">Pending</span>
                                <span class="text-lg font-bold text-amber-800" id="task-metric-pending">
                                    {{ tasks|selectattr('status', 'equalto', 'Pending')|list|length }}
                                </span>
                            </div>
                        </div>
                        <div class="bg-blue-50/70 border border-blue-200/70 rounded-2xl p-4 flex items-center space-x-3 shadow-2xs">
                            <div class="w-10 h-10 rounded-xl bg-blue-200 text-blue-800 flex items-center justify-center font-bold text-sm shrink-0">
                                <i class="fa-solid fa-spinner animate-spin"></i>
                            </div>
                            <div>
                                <span class="block text-[11px] text-blue-700 font-medium">Dalam Proses</span>
                                <span class="text-lg font-bold text-blue-800" id="task-metric-proses">
                                    {{ tasks|selectattr('status', 'equalto', 'Proses')|list|length }}
                                </span>
                            </div>
                        </div>
                        <div class="bg-emerald-50/70 border border-emerald-200/70 rounded-2xl p-4 flex items-center space-x-3 shadow-2xs">
                            <div class="w-10 h-10 rounded-xl bg-emerald-200 text-emerald-800 flex items-center justify-center font-bold text-sm shrink-0">
                                <i class="fa-solid fa-circle-check"></i>
                            </div>
                            <div>
                                <span class="block text-[11px] text-emerald-700 font-medium">Selesai</span>
                                <span class="text-lg font-bold text-emerald-800" id="task-metric-selesai">
                                    {{ tasks|selectattr('status', 'equalto', 'Selesai')|list|length }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Filter & Search Bar -->
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                        <div class="flex flex-wrap items-center gap-2">
                            {% if user_role == 'manager' %}
                            <select id="tasks-filter-unit" onchange="filterTasksTable()" class="p-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700">
                                <option value="ALL">Semua Unit</option>
                                <option value="IT">Unit IT</option>
                                <option value="OB">Unit Office Boy</option>
                                <option value="GARDENER">Unit Gardener</option>
                                <option value="SECURITY">Unit Security</option>
                            </select>
                            {% endif %}
                            <select id="tasks-filter-status" onchange="filterTasksTable()" class="p-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700">
                                <option value="ALL">Semua Status</option>
                                <option value="Pending">Pending</option>
                                <option value="Proses">Dalam Proses</option>
                                <option value="Selesai">Selesai</option>
                            </select>
                        </div>
                        <div class="w-full sm:w-64">
                            <input type="text" id="tasks-search" onkeyup="filterTasksTable()" placeholder="Cari tiket, judul, instruksi..." class="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs">
                        </div>
                    </div>

                    <div class="overflow-x-auto">
                        <table id="table-tasks" class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs">
                                    <th class="p-3">No. Tiket</th>
                                    <th class="p-3">Unit & Penanggung Jawab</th>
                                    <th class="p-3">Judul Pekerjaan & Instruksi</th>
                                    <th class="p-3">Prioritas</th>
                                    <th class="p-3">Target SLA</th>
                                    <th class="p-3">Status</th>
                                    <th class="p-3">Catatan Progres</th>
                                    <th class="p-3 text-right">Aksi</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 text-xs">
                                {% for task in tasks %}
                                <tr class="task-row hover:bg-slate-50/50 transition" 
                                    data-unit="{{ task.unit_code or task.unit or 'IT' }}"
                                    data-status="{{ task.status or 'Pending' }}"
                                    data-search="{{ (task.id + ' ' + (task.unit_code or task.unit or '') + ' ' + task.title + ' ' + (task.description or '') + ' ' + (task.progress_notes or ''))|lower }}">
                                    <td class="p-3 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                                        <span class="font-bold text-slate-700">{{ task.id }}</span>
                                        <span class="block text-[10px] text-slate-400">{{ task.created_at }}</span>
                                    </td>
                                    <td class="p-3 whitespace-nowrap">
                                        <span class="font-bold text-slate-800">{{ task.unit_code or task.unit }}</span>
                                        {% if task.sub_scope %}
                                        <span class="block text-[10px] text-slate-500 font-medium">({{ task.sub_scope }})</span>
                                        {% endif %}
                                        {% if task.assigned_name %}
                                        <span class="block text-[10px] text-slate-400">PIC: {{ task.assigned_name }}</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 max-w-xs sm:max-w-md">
                                        <div class="flex items-center gap-1.5 flex-wrap mb-1">
                                            {% if task.source == 'kebersihan_log' %}
                                            <span class="px-2 py-0.5 text-[9px] font-bold bg-purple-100 text-purple-700 rounded-md border border-purple-200">
                                                <i class="fa-solid fa-broom mr-1"></i> Dari Kebersihan
                                            </span>
                                            {% endif %}
                                            <span class="text-slate-400 text-[10px]">Kat: {{ task.category }}</span>
                                        </div>
                                        <p class="font-bold text-slate-800 leading-snug">{{ task.title }}</p>
                                        {% if task.description %}
                                        <p class="text-[11px] text-slate-500 mt-1 line-clamp-2">{{ task.description }}</p>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 whitespace-nowrap">
                                        {% if task.priority == 'Tinggi' %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200 rounded-md">Tinggi</span>
                                        {% elif task.priority == 'Sedang' %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-700 border border-amber-200 rounded-md">Sedang</span>
                                        {% else %}
                                        <span class="px-2 py-0.5 text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 rounded-md">Rendah</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 whitespace-nowrap text-slate-600 font-mono text-[11px]">
                                        {{ task.due_date or '-' }}
                                    </td>
                                    <td class="p-3 whitespace-nowrap">
                                        {% if task.status == 'Selesai' %}
                                        <span class="px-2.5 py-1 text-[11px] font-bold bg-emerald-100 text-emerald-700 rounded-full border border-emerald-200">
                                            <i class="fa-solid fa-check mr-1"></i> Selesai
                                        </span>
                                        {% elif task.status == 'Proses' %}
                                        <span class="px-2.5 py-1 text-[11px] font-bold bg-blue-100 text-blue-700 rounded-full border border-blue-200">
                                            <i class="fa-solid fa-spinner mr-1 animate-spin"></i> Proses
                                        </span>
                                        {% else %}
                                        <span class="px-2.5 py-1 text-[11px] font-bold bg-amber-100 text-amber-700 rounded-full border border-amber-200">
                                            <i class="fa-solid fa-hourglass-start mr-1"></i> Pending
                                        </span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 max-w-xs text-[11px] text-slate-600">
                                        {% if task.progress_notes %}
                                        <span class="italic bg-slate-50 p-1.5 rounded-lg border border-slate-100 block">{{ task.progress_notes }}</span>
                                        {% if task.completed_at %}
                                        <span class="text-[10px] text-emerald-600 block mt-0.5 font-mono">Selesai: {{ task.completed_at }}</span>
                                        {% endif %}
                                        {% else %}
                                        <span class="text-slate-300">-</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 text-right whitespace-nowrap space-x-1">
                                        <button data-id="{{ task.id }}" data-title="{{ task.title }}" data-unit="{{ task.unit_code or task.unit }}" onclick="openCreatePengadaanModalFromTaskBtn(this)" 
                                                class="px-2 py-1.5 text-xs font-bold text-amber-700 bg-amber-50 hover:bg-amber-600 hover:text-white border border-amber-200 rounded-xl transition shadow-2xs" 
                                                title="Ajukan Pengadaan Material / Sparepart untuk Tugas Ini">
                                            <i class="fa-solid fa-cart-plus"></i>
                                            <span class="hidden sm:inline ml-1">+ Pengadaan</span>
                                        </button>
                                        <button onclick="openUpdateTaskModal('{{ task.id }}', '{{ task.title|replace("'", "\\'") }}', '{{ task.status }}', '{{ (task.progress_notes or '')|replace("'", "\\'") }}')" 
                                                class="px-2.5 py-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-600 hover:text-white border border-emerald-200 rounded-xl transition shadow-2xs" 
                                                title="Perbarui Status & Catatan Progres">
                                            <i class="fa-solid fa-pen-to-square"></i>
                                            <span class="hidden sm:inline ml-1">Update</span>
                                        </button>
                                        {% if user_role == 'manager' %}
                                        <button onclick="deleteOpsTask('{{ task.id }}')" class="p-1.5 text-slate-300 hover:text-rose-600 transition text-xs" title="Hapus Tiket">
                                            <i class="fa-solid fa-trash-can"></i>
                                        </button>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="8" class="p-8 text-center text-slate-400">Belum ada daftar tiket atau tugas. Klik <b>Disposisi Tugas Baru</b> di atas!</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB 3: MUTABAAH LOGS WITH FILTER -->
            <div id="tab-mutabaah" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-kaaba text-teal-600"></i>
                            Log Masuk Mutabaah Yaumiyah Petugas (WhatsApp)
                        </h2>
                        <div class="flex items-center gap-3">
                            <a href="/export/mutabaah" class="px-3.5 py-1.5 bg-teal-600 text-white text-xs font-semibold rounded-lg hover:bg-teal-700 transition shadow-xs flex items-center gap-1.5" title="Export ke Excel">
                                <i class="fa-solid fa-file-excel"></i> Export Excel
                            </a>
                            <span id="mutabaah-count-badge" class="px-3 py-1 bg-teal-50 text-teal-700 text-xs font-bold rounded-full border border-teal-200">
                                Total: {{ mutabaah_logs|length }} Laporan
                            </span>
                        </div>
                    </div>

                    <!-- Filter Control Bar -->
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Cari Nama / Kata Kunci</label>
                            <input type="text" id="mutabaah-search" onkeyup="filterMutabaahTable()" placeholder="Ketik nama petugas..." class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Filter Unit</label>
                            <select id="mutabaah-filter-unit" onchange="filterMutabaahTable()" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                                <option value="">Semua Unit</option>
                                <option value="OB">OB</option>
                                <option value="Security">Security</option>
                                <option value="Gardener">Gardener</option>
                                <option value="PGTK">PGTK</option>
                                <option value="SD">SD</option>
                                <option value="SMP">SMP</option>
                                <option value="SMA">SMA</option>
                            </select>
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Filter Tanggal</label>
                            <input type="date" id="mutabaah-filter-date" onchange="filterMutabaahTable()" class="w-full p-2 bg-white border border-slate-200 rounded-lg" value="{{ today_date }}">
                        </div>
                    </div>

                    <div class="overflow-x-auto">
                        <table id="table-mutabaah" class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                                    <th class="p-3">Waktu</th>
                                    <th class="p-3">Nama Petugas</th>
                                    <th class="p-3">Unit</th>
                                    <th class="p-2 sm:p-3">Sholat</th>
                                    <th class="p-3">Tilawah</th>
                                    <th class="p-2 sm:p-3">Dzikir</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                {% for log in mutabaah_logs|reverse %}
                                <tr class="mutabaah-row hover:bg-slate-50/50" 
                                    data-nama="{{ log.nama|lower }}" 
                                    data-unit="{{ log.unit }}" 
                                    data-date="{{ log.wibDate or log.timestamp[:10] }}">
                                    <td class="p-3 text-xs font-mono text-slate-500">{{ log.wibDate or log.timestamp[:10] }}</td>
                                    <td class="p-3 font-semibold text-slate-800">{{ log.nama }}</td>
                                    <td class="p-3 text-xs font-medium text-slate-600">{{ log.unit }}</td>
                                    <td class="p-3 text-xs text-slate-700">{{ log.sholat }}</td>
                                    <td class="p-3 text-xs text-slate-700">{{ log.tilawah }}</td>
                                    <td class="p-3 text-xs text-slate-700">{{ log.dzikir }}</td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="6" class="p-6 text-center text-slate-400">Belum ada log mutabaah.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB STANDBY: KESIAGAAN POS & GEOTAGGING -->
            <div id="tab-standby" class="tab-content hidden space-y-6">
                <!-- Header & Action Bar -->
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base sm:text-lg font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-satellite-dish text-sky-600"></i>
                                Pusat Komando Kesiagaan Pos & Standby Lapangan
                            </h2>
                            <p class="text-xs text-slate-500 mt-0.5">Pemantauan kedisiplinan kembali ke pos (OB, Gardener, Security) pasca istirahat pagi & siang dengan geotagging.</p>
                        </div>
                        <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                            <button type="button" onclick="loadStandbyRadar()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                                <i class="fa-solid fa-arrows-rotate"></i> Refresh Radar
                            </button>
                            <a href="/standby/print-qr" target="_blank" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-qrcode"></i> Cetak Stiker QR Pos
                            </a>
                            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'koordinator_security'] %}
                            <button type="button" onclick="openModalCreateStandbyPoint()" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                                <i class="fa-solid fa-plus"></i> Tambah Titik Pos
                            </button>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Metric Summary Cards -->
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 sm:p-4">
                            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Pos Terdaftar</span>
                            <span id="stat-standby-total" class="text-xl sm:text-2xl font-black text-slate-800">0</span>
                            <span class="text-[10px] text-slate-400 block mt-0.5">OB, Gardener, Security</span>
                        </div>
                        <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-3 sm:p-4">
                            <span class="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">🟢 Standby Tepat Waktu</span>
                            <span id="stat-standby-ontime" class="text-xl sm:text-2xl font-black text-emerald-700">0</span>
                            <span class="text-[10px] text-emerald-600 block mt-0.5">Dalam radius & sebelum cut-off</span>
                        </div>
                        <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 sm:p-4">
                            <span class="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">🟡 Terlambat Lapor</span>
                            <span id="stat-standby-late" class="text-xl sm:text-2xl font-black text-amber-700">0</span>
                            <span class="text-[10px] text-amber-600 block mt-0.5">Lapor melewati cut-off waktu</span>
                        </div>
                        <div class="bg-rose-50 border border-rose-200 rounded-xl p-3 sm:p-4">
                            <span class="text-[11px] font-bold text-rose-700 uppercase tracking-wider block">🔴 Pos Kosong / Belum Siaga</span>
                            <span id="stat-standby-empty" class="text-xl sm:text-2xl font-black text-rose-700">0</span>
                            <span class="text-[10px] text-rose-600 block mt-0.5">Perlu atensi & cek lapangan</span>
                        </div>
                    </div>

                    <!-- Filter & Sub-Nav Bar -->
                    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-50 p-2 sm:p-3 rounded-xl border border-slate-200 text-xs">
                        <!-- Sesi Toggle -->
                        <div class="flex items-center space-x-1 bg-white p-1 rounded-lg border border-slate-200 shadow-2xs">
                            <button type="button" onclick="switchStandbySession('PAGI')" id="btn-sess-pagi" class="px-3 py-1 rounded-md font-bold transition text-emerald-700 bg-emerald-50 cursor-pointer">
                                <i class="fa-regular fa-sun mr-1"></i> Istirahat Pagi
                            </button>
                            <button type="button" onclick="switchStandbySession('SIANG')" id="btn-sess-siang" class="px-3 py-1 rounded-md font-bold transition text-slate-500 hover:text-slate-800 cursor-pointer">
                                <i class="fa-solid fa-cloud-sun mr-1"></i> Istirahat Siang (Ishoma)
                            </button>
                        </div>

                        <!-- Unit Filter -->
                        <div class="flex items-center gap-2">
                            <label class="text-slate-500 font-semibold shrink-0">Filter Unit:</label>
                            <select id="filter-standby-unit" onchange="loadStandbyRadar()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                                <option value="ALL">Semua Unit (OB, Gardener, Security)</option>
                                <option value="OB">Office Boy (OB)</option>
                                <option value="GARDENER">Gardener (Taman & Ecopark)</option>
                                <option value="SECURITY">Security (Keamanan & Pos)</option>
                            </select>
                        </div>

                        <!-- View Switcher Tabs -->
                        <div class="flex items-center space-x-1">
                            <button type="button" onclick="switchStandbySubView('radar')" id="btn-subview-radar" class="px-2.5 py-1 rounded-md font-semibold bg-white text-slate-800 shadow-2xs border border-slate-200 cursor-pointer">
                                <i class="fa-solid fa-tower-broadcast mr-1 text-emerald-600"></i> Radar Siaga
                            </button>
                            <button type="button" onclick="switchStandbySubView('points')" id="btn-subview-points" class="px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-800 cursor-pointer">
                                <i class="fa-solid fa-map-pin mr-1 text-sky-600"></i> Kelola Pos
                            </button>
                            <button type="button" onclick="switchStandbySubView('logs')" id="btn-subview-logs" class="px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-800 cursor-pointer">
                                <i class="fa-solid fa-clock-rotate-left mr-1 text-indigo-600"></i> Riwayat Check-in
                            </button>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 1: RADAR SIAGA REAL-TIME -->
                <div id="standby-subview-radar" class="space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden">
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-4">Titik Pos & Kode</th>
                                        <th class="py-3 px-4">Unit Kerja</th>
                                        <th class="py-3 px-4">Personel Ditugaskan</th>
                                        <th class="py-3 px-4">Batas Cut-off</th>
                                        <th class="py-3 px-4">Laporan Masuk</th>
                                        <th class="py-3 px-4">Jarak & Radius</th>
                                        <th class="py-3 px-4">Status Siaga</th>
                                        <th class="py-3 px-4 text-center">Aksi Cepat</th>
                                    </tr>
                                </thead>
                                <tbody id="standby-radar-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="8" class="text-center py-6 text-slate-400">Memuat status radar...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 2: KELOLA TITIK POS & PENUGASAN -->
                <div id="standby-subview-points" class="hidden space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden p-4 sm:p-6 space-y-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="font-bold text-sm text-slate-800">Daftar Titik Pos Standby & Parameter Geofencing</h3>
                                <p class="text-[11px] text-slate-500">Radius toleransi dan jam wajib siaga dapat disesuaikan per unit/pos.</p>
                            </div>
                            <button type="button" onclick="openModalCreateStandbyPoint()" class="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold hover:bg-emerald-700 flex items-center gap-1.5 cursor-pointer">
                                <i class="fa-solid fa-plus"></i> Tambah Pos Baru
                            </button>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-3">Kode & Nama Pos</th>
                                        <th class="py-3 px-3">Unit</th>
                                        <th class="py-3 px-3">Koordinat GPS</th>
                                        <th class="py-3 px-3">Radius</th>
                                        <th class="py-3 px-3">Batas Pagi</th>
                                        <th class="py-3 px-3">Batas Siang</th>
                                        <th class="py-3 px-3">Target Alert (WA & Group)</th>
                                        <th class="py-3 px-3">Personel</th>
                                        <th class="py-3 px-3 text-center">Aksi</th>
                                    </tr>
                                </thead>
                                <tbody id="standby-points-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="9" class="text-center py-6 text-slate-400">Memuat daftar pos...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 3: RIWAYAT LOG CHECK-IN STANDBY -->
                <div id="standby-subview-logs" class="hidden space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
                        <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
                            <div>
                                <h3 class="font-bold text-sm text-slate-800">Riwayat Check-in Standby Geotagging</h3>
                                <p class="text-[11px] text-slate-500">Rekap transaksi kehadiran personel berbasis lokasi GPS.</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <input type="date" id="filter-standby-log-date" onchange="loadStandbyLogs()" class="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800">
                                <select id="filter-standby-log-status" onchange="loadStandbyLogs()" class="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800">
                                    <option value="ALL">Semua Status</option>
                                    <option value="TEPAT_WAKTU">Tepat Waktu</option>
                                    <option value="TERLAMBAT">Terlambat</option>
                                    <option value="DILUAR_RADIUS">Di Luar Radius</option>
                                </select>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-3">Waktu Lapor</th>
                                        <th class="py-3 px-3">Sesi</th>
                                        <th class="py-3 px-3">Pos & Kode</th>
                                        <th class="py-3 px-3">Petugas</th>
                                        <th class="py-3 px-3">Jarak GPS</th>
                                        <th class="py-3 px-3">Status</th>
                                        <th class="py-3 px-3">Kanal</th>
                                    </tr>
                                </thead>
                                <tbody id="standby-logs-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="7" class="text-center py-6 text-slate-400">Memuat riwayat log...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>


            <!-- TAB CHECKLIST: CHECKLIST PEMELIHARAAN OB & GREEN OPS -->
            <div id="tab-checklist" class="tab-content hidden space-y-6">
                <!-- Header & Action Bar -->
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base sm:text-lg font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-clipboard-check text-emerald-600"></i>
                                Monitoring Checklist Pemeliharaan & Green Operations
                            </h2>
                            <p class="text-xs text-slate-500 mt-0.5">Sistem inspeksi terpadu 100% paperless, pencegahan kebocoran air, dan closed-loop tiket perbaikan sarpras.</p>
                        </div>
                        <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                            <button type="button" onclick="loadChecklistDashboard()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                                <i class="fa-solid fa-arrows-rotate"></i> Refresh Data
                            </button>
                            <a href="/checklist/print-qr" target="_blank" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-qrcode"></i> Cetak Stiker QR Akrilik
                            </a>
                            {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'pic_sarpras'] %}
                            <button type="button" onclick="openModalCreateChecklistTemplate()" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                                <i class="fa-solid fa-plus"></i> Tambah Butir Checklist
                            </button>
                            <button type="button" onclick="openModalCreateChecklistZone()" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                                <i class="fa-solid fa-plus"></i> Tambah Titik Zona
                            </button>
                            {% endif %}
                        </div>
                    </div>

                    <!-- 4 Summary Metric Cards -->
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                        <div class="bg-slate-50 border border-slate-200/80 rounded-xl p-3 sm:p-4">
                            <span class="text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider block">Titik Terkontrol Hari Ini</span>
                            <div class="mt-1 flex items-baseline gap-2">
                                <span id="stat-chk-controlled" class="text-xl sm:text-2xl font-black text-slate-800">0 / 0</span>
                                <span class="text-[10px] text-slate-400 font-semibold">titik</span>
                            </div>
                            <span class="text-[10px] text-slate-500 mt-1 block">Shift Pagi, Siang & Sore</span>
                        </div>

                        <div class="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-3 sm:p-4">
                            <span class="text-[10px] sm:text-xs font-bold text-emerald-700 uppercase tracking-wider block">Kepatuhan & Kebersihan</span>
                            <div class="mt-1 flex items-baseline gap-2">
                                <span id="stat-chk-compliance" class="text-xl sm:text-2xl font-black text-emerald-700">0%</span>
                                <span class="text-[10px] text-emerald-600 font-semibold">prima</span>
                            </div>
                            <span class="text-[10px] text-emerald-600 mt-1 block">Inspeksi terisi & beres</span>
                        </div>

                        <div class="bg-rose-50/60 border border-rose-200/80 rounded-xl p-3 sm:p-4">
                            <span class="text-[10px] sm:text-xs font-bold text-rose-700 uppercase tracking-wider block">Tiket Sarpras Aktif</span>
                            <div class="mt-1 flex items-baseline gap-2">
                                <span id="stat-chk-open-tickets" class="text-xl sm:text-2xl font-black text-rose-700">0</span>
                                <span class="text-[10px] text-rose-600 font-semibold">tiket</span>
                            </div>
                            <span class="text-[10px] text-rose-600 mt-1 block">Kerusakan dalam antrean perbaikan</span>
                        </div>

                        <div class="bg-teal-50/60 border border-teal-200/80 rounded-xl p-3 sm:p-4">
                            <span class="text-[10px] sm:text-xs font-bold text-teal-700 uppercase tracking-wider block">Dampak Green Ops</span>
                            <div class="mt-1 flex items-baseline gap-2">
                                <span id="stat-chk-green-impact" class="text-xl sm:text-2xl font-black text-teal-700">0 L</span>
                                <span class="text-[10px] text-teal-600 font-semibold">air dicegah</span>
                            </div>
                            <span id="stat-chk-paper-sub" class="text-[10px] text-teal-600 mt-1 block">0 lembar kertas dihemat</span>
                        </div>
                    </div>

                    <!-- Sub-Navigation Pills -->
                    <div class="flex items-center justify-between gap-3 border-t border-slate-100 pt-3 flex-wrap">
                        <div class="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-bold flex-wrap">
                            <button type="button" onclick="switchChecklistSubview('radar')" id="btn-chk-sub-radar"
                                class="chk-sub-tab px-3.5 py-1.5 rounded-lg bg-white text-emerald-700 shadow-xs transition cursor-pointer">
                                <i class="fa-solid fa-table-cells mr-1.5"></i> Radar Shift & Zona
                            </button>
                            <button type="button" onclick="switchChecklistSubview('tickets')" id="btn-chk-sub-tickets"
                                class="chk-sub-tab px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition cursor-pointer">
                                <i class="fa-solid fa-wrench mr-1.5"></i> Tiket Sarpras Closed-Loop
                            </button>
                            <button type="button" onclick="switchChecklistSubview('green')" id="btn-chk-sub-green"
                                class="chk-sub-tab px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition cursor-pointer">
                                <i class="fa-solid fa-leaf mr-1.5"></i> Green Operations Index
                            </button>
                            <button type="button" onclick="switchChecklistSubview('zones')" id="btn-chk-sub-zones"
                                class="chk-sub-tab px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition cursor-pointer">
                                <i class="fa-solid fa-location-dot mr-1.5"></i> Master Zona & QR
                            </button>
                            <button type="button" onclick="switchChecklistSubview('templates')" id="btn-chk-sub-templates"
                                class="chk-sub-tab px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition cursor-pointer">
                                <i class="fa-solid fa-list-check mr-1.5"></i> Kelola Butir Checklist Dinamis
                            </button>
                        </div>

                        <!-- Filter Unit Cepat -->
                        <div class="flex items-center gap-2">
                            <label class="text-[11px] font-bold text-slate-500">Filter Unit:</label>
                            <select id="filter-chk-unit" onchange="loadChecklistDashboard()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                                <option value="">Semua Unit (OB & Gardener)</option>
                                <option value="OB">Unit Office Boy (OB)</option>
                                <option value="GARDENER">Unit Gardener & Ecopark</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 1: RADAR SHIFT & ZONA -->
                <div id="chk-subview-radar" class="space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden">
                        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                            <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                                <i class="fa-solid fa-layer-group text-emerald-600"></i>
                                Status Pemeliharaan Shift Hari Ini
                            </h3>
                            <span class="text-xs text-slate-400 font-mono" id="chk-radar-date">Hari Ini</span>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs text-slate-600">
                                <thead class="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider font-bold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-4">Gedung / Sektor</th>
                                        <th class="py-3 px-4">Titik & Zona Pemeliharaan</th>
                                        <th class="py-3 px-3 text-center">Pagi (06:30-08:30)</th>
                                        <th class="py-3 px-3 text-center">Siang 1 (Sanitasi)</th>
                                        <th class="py-3 px-3 text-center">Siang 2 (Sanitasi)</th>
                                        <th class="py-3 px-3 text-center">Sore (Closing/Hemat)</th>
                                        <th class="py-3 px-4 text-center">Aksi Cepat</th>
                                    </tr>
                                </thead>
                                <tbody id="chk-radar-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="7" class="text-center py-8 text-slate-400">Memuat data radar checklist...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 2: TIKET SARPRAS CLOSED-LOOP -->
                <div id="chk-subview-tickets" class="hidden space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
                            <div>
                                <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                                    <i class="fa-solid fa-wrench text-rose-600"></i>
                                    Daftar Tiket Kerusakan Fasilitas (Closed-Loop)
                                </h3>
                                <p class="text-[11px] text-slate-500 mt-0.5">Tiket diterbitkan otomatis dari checklist jika ditemukan kran bocor, kloset macet, atau saklar rusak.</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <select id="filter-chk-ticket-status" onchange="loadChecklistTickets()" class="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800">
                                    <option value="">Semua Status Tiket</option>
                                    <option value="OPEN" selected>Aktif (OPEN & IN_PROGRESS)</option>
                                    <option value="RESOLVED">Selesai (RESOLVED)</option>
                                </select>
                            </div>
                        </div>

                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs text-slate-600">
                                <thead class="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider font-bold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-3">ID Tiket</th>
                                        <th class="py-3 px-3">Prioritas & Kategori</th>
                                        <th class="py-3 px-4">Lokasi / Zona</th>
                                        <th class="py-3 px-4">Rincian Masalah Kerusakan</th>
                                        <th class="py-3 px-3">Pelapor (OB)</th>
                                        <th class="py-3 px-3">Target SLA</th>
                                        <th class="py-3 px-3">Status</th>
                                        <th class="py-3 px-3 text-center">Aksi</th>
                                    </tr>
                                </thead>
                                <tbody id="chk-tickets-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="8" class="text-center py-8 text-slate-400">Memuat tiket sarpras...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 3: GREEN OPERATIONS INDEX -->
                <div id="chk-subview-green" class="hidden space-y-6">
                    <div class="bg-gradient-to-br from-emerald-900 to-teal-900 text-white rounded-2xl p-6 sm:p-8 shadow-md relative overflow-hidden" style="background: linear-gradient(135deg, #064e3b 0%, #0f766e 100%) !important; color: #ffffff !important;">
                        <div class="relative z-10 max-w-2xl">
                            <span class="inline-block px-3 py-1 bg-emerald-500/30 text-emerald-200 border border-emerald-400/40 rounded-full text-[10px] font-bold uppercase tracking-wider mb-2" style="background-color: rgba(16, 185, 129, 0.25) !important; color: #a7f3d0 !important; border: 1px solid rgba(52, 211, 153, 0.4) !important;">
                                🌿 Ekosistem Sekolah Berwawasan Lingkungan
                            </span>
                            <h3 class="text-xl sm:text-2xl font-black mt-1 text-white" style="color: #ffffff !important;">Green Operations Index & Konservasi Sumber Daya</h3>
                            <p class="text-xs mt-2 leading-relaxed" style="color: #d1fae5 !important;">
                                Rekapitulasi dampak positif operasional paperless, penghematan air bersih melalui deteksi dini kebocoran, serta efisiensi energi listrik malam hari di An Nahl Islamic School.
                            </p>
                        </div>
                        <i class="fa-solid fa-leaf text-8xl absolute right-4 bottom-2 -rotate-12 pointer-events-none" style="color: rgba(16, 185, 129, 0.15) !important;"></i>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div class="bg-white rounded-2xl border border-slate-200 p-5 space-y-3 shadow-xs">
                            <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center text-lg">
                                <i class="fa-solid fa-file-circle-check"></i>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Kertas Diselamatkan</span>
                                <div class="mt-1 flex items-baseline gap-2">
                                    <span id="green-metric-paper" class="text-2xl font-black text-slate-800">0</span>
                                    <span class="text-xs text-slate-400 font-semibold">lembar form</span>
                                </div>
                                <p class="text-[11px] text-slate-500 mt-1">Setara dengan <strong id="green-metric-rim" class="text-amber-600">0</strong> rim kertas HVS dan 0 plastik binder.</p>
                            </div>
                        </div>

                        <div class="bg-white rounded-2xl border border-slate-200 p-5 space-y-3 shadow-xs">
                            <div class="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center text-lg">
                                <i class="fa-solid fa-faucet-drip"></i>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Air Bersih Diselamatkan</span>
                                <div class="mt-1 flex items-baseline gap-2">
                                    <span id="green-metric-water" class="text-2xl font-black text-sky-600">0</span>
                                    <span class="text-xs text-sky-600 font-semibold">Liter</span>
                                </div>
                                <p class="text-[11px] text-slate-500 mt-1">Dari <strong id="green-metric-leaks" class="text-slate-800">0</strong> titik kran/toilet bocor yang diperbaiki cepat (&lt;2 jam).</p>
                            </div>
                        </div>

                        <div class="bg-white rounded-2xl border border-slate-200 p-5 space-y-3 shadow-xs">
                            <div class="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center text-lg">
                                <i class="fa-solid fa-bolt"></i>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Efisiensi Energi Listrik</span>
                                <div class="mt-1 flex items-baseline gap-2">
                                    <span id="green-metric-energy" class="text-2xl font-black text-teal-700">0</span>
                                    <span class="text-xs text-teal-600 font-semibold">kWh</span>
                                </div>
                                <p class="text-[11px] text-slate-500 mt-1">Dari <strong id="green-metric-shutoff" class="text-slate-800">0</strong> checklist closing malam hari (AC & lampu OFF).</p>
                            </div>
                        </div>

                        <div class="bg-white rounded-2xl border border-slate-200 p-5 space-y-3 shadow-xs">
                            <div class="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg">
                                <i class="fa-solid fa-recycle"></i>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Sampah Daun Terolah</span>
                                <div class="mt-1 flex items-baseline gap-2">
                                    <span id="green-metric-waste" class="text-2xl font-black text-emerald-700">0</span>
                                    <span class="text-xs text-emerald-600 font-semibold">Kg Serasah</span>
                                </div>
                                <p class="text-[11px] text-slate-500 mt-1">100% Zero Burning diolah menjadi kompos organik sekolah.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 4: MASTER ZONA & CETAK QR -->
                <div id="chk-subview-zones" class="hidden space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
                            <div>
                                <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                                    <i class="fa-solid fa-qrcode text-indigo-600"></i>
                                    Master Titik Kontrol & Manajemen Stiker QR
                                </h3>
                                <p class="text-[11px] text-slate-500 mt-0.5">Daftar lokasi fisik pintu toilet, ruang kelas, taman dan kandang ecopark yang terpasang stiker QR.</p>
                            </div>
                            <a href="/checklist/print-qr" target="_blank" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-print"></i> Cetak Semua Stiker QR
                            </a>
                        </div>

                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs text-slate-600">
                                <thead class="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider font-bold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-3">ID Titik</th>
                                        <th class="py-3 px-3">Unit & Sektor</th>
                                        <th class="py-3 px-4">Nama Zona Pemeliharaan</th>
                                        <th class="py-3 px-3">Koordinat GPS</th>
                                        <th class="py-3 px-3">Radius</th>
                                        <th class="py-3 px-3 text-center">Status</th>
                                        <th class="py-3 px-4 text-center">Aksi Manajemen</th>
                                    </tr>
                                </thead>
                                <tbody id="chk-zones-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="7" class="text-center py-8 text-slate-400">Memuat master zona...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUBVIEW 5: KELOLA BUTIR CHECKLIST DINAMIS -->
                <div id="chk-subview-templates" class="hidden space-y-4">
                    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
                            <div>
                                <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                                    <i class="fa-solid fa-list-check text-teal-600"></i>
                                    Kelola Parameter & Butir Checklist Lapangan (Dinamis)
                                </h3>
                                <p class="text-[11px] text-slate-500 mt-0.5">Kustomisasi butir inspeksi OB & Gardener secara real-time. Perubahan langsung aktif di aplikasi micro-checkin mobile saat scan QR.</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <span id="chk-templates-count-badge" class="px-2.5 py-1 bg-teal-50 text-teal-700 font-mono text-[11px] font-bold rounded-lg border border-teal-200">
                                    0 Butir
                                </span>
                                {% if user_role in ['manager', 'koordinator_ob', 'koordinator_gardener', 'pic_sarpras'] %}
                                <button type="button" onclick="openModalCreateChecklistTemplate()" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                                    <i class="fa-solid fa-plus"></i> Tambah Butir Baru
                                </button>
                                {% endif %}
                            </div>
                        </div>

                        <!-- Filter Bar for Checklist Templates -->
                        <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                            <div>
                                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Filter Unit</label>
                                <select id="filter-chk-tpl-unit" onchange="loadChecklistTemplates()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500">
                                    <option value="">Semua Unit</option>
                                    <option value="OB">Unit Office Boy (OB)</option>
                                    <option value="GARDENER">Unit Gardener & Ecopark</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Filter Sub-Lingkup</label>
                                <select id="filter-chk-tpl-subscope" onchange="loadChecklistTemplates()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500">
                                    <option value="">Semua Sub-Lingkup</option>
                                    <option value="INDOOR_SANITASI">Indoor Sanitasi & Toilet</option>
                                    <option value="TAMAN_LANSKAP">Taman & Lanskap Luar</option>
                                    <option value="AGRO_TERNAK">Agro Sayur & Ecopark Ternak</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Filter Shift</label>
                                <select id="filter-chk-tpl-shift" onchange="loadChecklistTemplates()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500">
                                    <option value="">Semua Shift</option>
                                    <option value="PAGI">Pagi (06:30 - 08:30)</option>
                                    <option value="SIANG_1">Siang 1 (08:30 - 12:30)</option>
                                    <option value="SIANG_2">Siang 2 (12:30 - 16:00)</option>
                                    <option value="SORE">Sore (16:00 - 18:00)</option>
                                    <option value="ALL_DAY">Sepanjang Hari (All Day)</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Status Keaktifan</label>
                                <select id="filter-chk-tpl-active" onchange="loadChecklistTemplates()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500">
                                    <option value="">Semua Status</option>
                                    <option value="1">Hanya Aktif</option>
                                    <option value="0">Hanya Non-Aktif (Arsip)</option>
                                </select>
                            </div>
                        </div>

                        <!-- Template Items Table -->
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs text-slate-600">
                                <thead class="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider font-bold border-b border-slate-200">
                                    <tr>
                                        <th class="py-3 px-3 w-14 text-center">Urut</th>
                                        <th class="py-3 px-3">Unit & Lingkup</th>
                                        <th class="py-3 px-3">Shift Tugas</th>
                                        <th class="py-3 px-4">Pertanyaan & Panduan Inspeksi</th>
                                        <th class="py-3 px-3 text-center">Klasifikasi</th>
                                        <th class="py-3 px-3 text-center">Status</th>
                                        <th class="py-3 px-4 text-center">Aksi</th>
                                    </tr>
                                </thead>
                                <tbody id="chk-templates-tbody" class="divide-y divide-slate-100">
                                    <tr><td colspan="7" class="text-center py-8 text-slate-400">Memuat butir checklist...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB PEMELIHARAAN SARPRAS (PM ISO FM-UMUM-AIS-03-02) -->
            {{ tab_pemeliharaan_html | safe }}

            <!-- TAB EVALUASI & RAPOR PERSONIL OB & GARDENER -->
            {{ tab_evaluasi_html | safe }}

            <!-- TAB 4: KEBERSIHAN LOGS WITH FILTER -->
            <div id="tab-kebersihan" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-broom text-purple-600"></i>
                            Log Laporan Kebersihan & Maintenance OB (+ Foto Drive)
                        </h2>
                        <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                            <button type="button" onclick="syncDrivePhotos()" id="btn-sync-photos" class="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition shadow-xs flex items-center gap-1.5" title="Sinkronkan Foto Drive dari Google Sheet">
                                <i class="fa-solid fa-arrows-rotate"></i> <span>Sinkron Foto Drive</span>
                            </button>
                            <a href="/export/kebersihan" class="px-3 py-1.5 bg-purple-600 text-white text-xs font-semibold rounded-lg hover:bg-purple-700 transition shadow-xs flex items-center gap-1.5" title="Export ke Excel">
                                <i class="fa-solid fa-file-excel"></i> <span>Export Excel</span>
                            </a>
                            <span id="kebersihan-count-badge" class="px-3 py-1 bg-purple-50 text-purple-700 text-xs font-bold rounded-full border border-purple-200">
                                Total: {{ kebersihan_logs|length }} Laporan
                            </span>
                        </div>
                    </div>

                    <!-- Filter Control Bar -->
                    <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 sm:gap-3 bg-slate-50 p-2 sm:p-3.5 rounded-xl border border-slate-200 text-xs">
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Cari Nama / Area / Ket.</label>
                            <input type="text" id="kebersihan-search" onkeyup="filterKebersihanTable()" placeholder="Ketik pencarian..." class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Filter Unit</label>
                            <select id="kebersihan-filter-unit" onchange="filterKebersihanTable()" class="w-full p-2 bg-white border border-slate-200 rounded-lg text-xs font-medium">
                                <option value="">Semua Unit</option>
                                <option value="OB">Office Boy (OB)</option>
                                <option value="Gardener">Gardener (Taman & Ecopark)</option>
                                <option value="Security">Security</option>
                                <option value="General Affairs">General Affairs</option>
                            </select>
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Filter Tanggal</label>
                            <input type="date" id="kebersihan-filter-date" onchange="filterKebersihanTable()" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Bukti Foto</label>
                            <select id="kebersihan-filter-photo" onchange="filterKebersihanTable()" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                                <option value="">Semua</option>
                                <option value="with_photo">Ada Foto Drive</option>
                                <option value="no_photo">Tanpa Foto</option>
                            </select>
                        </div>
                    </div>

                    <div class="overflow-x-auto">
                        <table id="table-kebersihan" class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs">
                                    <th class="p-3">Waktu</th>
                                    <th class="p-3">Nama Petugas</th>
                                    <th class="p-3">Unit</th>
                                    <th class="p-3">Area</th>
                                    <th class="p-3">Keterangan</th>
                                    <th class="p-3">Bukti Foto Drive</th>
                                    <th class="p-3 text-center">Tindak Lanjut</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 text-xs">
                                {% for log in kebersihan_logs|reverse %}
                                {% set p_link = log.photoUrl or log.photo_url or log.driveUrl or log.drive_url or log.foto_url %}
                                {% set has_any_photo = p_link or log.local_photo_url or log.hasImage or log.imageBase64 %}
                                <tr class="kebersihan-row hover:bg-slate-50/50"
                                    data-search="{{ (log.nama + ' ' + log.area + ' ' + log.keterangan)|lower }}"
                                    data-unit="{{ log.unit }}"
                                    data-date="{{ log.wibDate or log.timestamp[:10] }}"
                                    data-hasphoto="{% if has_any_photo %}true{% else %}false{% endif %}">
                                    <td class="p-3 text-xs font-mono text-slate-500 whitespace-nowrap">{{ log.wibDate or log.timestamp[:10] }}</td>
                                    <td class="p-3 font-semibold text-slate-800">{{ log.nama }}</td>
                                    <td class="p-3 text-xs whitespace-nowrap">
                                        {% set u_clean = (log.unit or 'OB')|trim %}
                                        {% if 'garden' in u_clean|lower %}
                                        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                                            <i class="fa-solid fa-leaf text-amber-600 text-[10px]"></i>
                                            <span>Gardener</span>
                                        </span>
                                        {% elif 'secur' in u_clean|lower %}
                                        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-sky-50 text-sky-800 border border-sky-200">
                                            <i class="fa-solid fa-shield-halved text-sky-600 text-[10px]"></i>
                                            <span>Security</span>
                                        </span>
                                        {% else %}
                                        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                                            <i class="fa-solid fa-broom text-emerald-600 text-[10px]"></i>
                                            <span>{{ u_clean }}</span>
                                        </span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 text-xs font-bold text-slate-700">{{ log.area }}</td>
                                    <td class="p-3 text-xs text-slate-700 leading-relaxed">{{ log.keterangan }}</td>
                                    <td class="p-3 text-xs whitespace-nowrap">
                                        {% set is_vid = log.hasVideo or log.mediaType == 'video' or (log.local_photo_url and log.local_photo_url.endswith('.mp4')) %}
                                        {% if p_link and p_link != '-' and not p_link.startswith('Error') %}
                                        <a href="{{ p_link }}" target="_blank" rel="noopener noreferrer"
                                           class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-600 hover:text-white transition shadow-2xs group"
                                           title="Buka Media di Google Drive">
                                            <i class="fa-brands fa-google-drive text-blue-600 group-hover:text-white"></i>
                                            <span>{% if is_vid %}Video Drive{% else %}Foto Drive{% endif %}</span>
                                            <i class="fa-solid fa-arrow-up-right-from-square text-[10px] opacity-70 group-hover:text-white"></i>
                                        </a>
                                        {% elif log.local_photo_url %}
                                        <a href="{{ log.local_photo_url }}" target="_blank" rel="noopener noreferrer"
                                           class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold {% if is_vid %}bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-600{% else %}bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-600{% endif %} hover:text-white transition shadow-2xs group"
                                           title="Lihat Bukti Lapangan">
                                            <i class="fa-solid {% if is_vid %}fa-video text-purple-600{% else %}fa-image text-emerald-600{% endif %} group-hover:text-white"></i>
                                            <span>{% if is_vid %}Putar Video{% else %}Lihat Foto{% endif %}</span>
                                            <i class="fa-solid fa-arrow-up-right-from-square text-[10px] opacity-70 group-hover:text-white"></i>
                                        </a>
                                        {% elif log.hasImage or log.hasVideo or log.imageBase64 %}
                                        <div class="inline-flex items-center gap-1.5">
                                            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium {% if is_vid %}bg-purple-50 text-purple-700 border border-purple-200{% else %}bg-amber-50 text-amber-700 border border-amber-200{% endif %}" title="Media dilampirkan via WhatsApp (Tersimpan di Sheet/Drive)">
                                                <i class="fa-solid {% if is_vid %}fa-video text-purple-500{% else %}fa-camera text-amber-500{% endif %}"></i>
                                                <span>{% if is_vid %}Video Terlampir{% else %}Foto Terlampir{% endif %}</span>
                                            </span>
                                            <button type="button" onclick="openSetPhotoModal('{{ log.timestamp }}', '{{ log.nama|replace("'", "\\'") }}', '{{ log.area|replace("'", "\\'") }}', '')"
                                                    class="p-1 text-slate-400 hover:text-blue-600 transition rounded" title="Tautkan / Edit Link Drive">
                                                <i class="fa-solid fa-link text-xs"></i>
                                            </button>
                                        </div>
                                        {% else %}
                                        <span class="inline-flex items-center gap-1 text-slate-400 text-xs">
                                            <i class="fa-solid fa-minus text-slate-300"></i>
                                            <span>Tanpa Foto</span>
                                        </span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 text-center whitespace-nowrap">
                                        <button type="button" onclick="openConvertKebersihanModal('{{ log.nama|replace("'", "\\'") }}', '{{ log.unit|replace("'", "\\'") }}', '{{ log.area|replace("'", "\\'") }}', '{{ log.keterangan|replace("'", "\\'") }}')" 
                                                class="px-2.5 py-1 text-xs font-bold bg-emerald-50 text-emerald-700 hover:bg-emerald-600 hover:text-white rounded-lg transition border border-emerald-200 inline-flex items-center gap-1.5 shadow-2xs" 
                                                title="Disposisikan temuan kerusakan ini menjadi Tiket Tugas">
                                            <i class="fa-solid fa-clipboard-check"></i>
                                            <span>Jadikan Tiket</span>
                                        </button>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="7" class="p-6 text-center text-slate-400">Belum ada log laporan kebersihan.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB 6: CETAK LAPORAN -->
            <div id="tab-report" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-file-lines text-emerald-600"></i>
                                Report Builder - Cetak Laporan Operasional
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">Sesuaikan rentang tanggal, filter unit, dan pilih sumber data untuk membuat laporan operasional terpadu</p>
                        </div>
                    </div>

                    <!-- Panel Filter -->
                    <div class="no-print bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <!-- a) Pilih Sumber Data (checkbox) -->
                            <div class="md:col-span-3">
                                <label class="block font-semibold text-slate-700 text-xs mb-2">Pilih Sumber Data Laporan:</label>
                                <div class="flex flex-wrap gap-4 sm:gap-6 text-xs">
                                    <label class="inline-flex items-center space-x-2 cursor-pointer">
                                        <input type="checkbox" id="chk-mutabaah" checked class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300">
                                        <span class="text-slate-700 font-medium"><i class="fa-solid fa-hands-praying text-teal-600 mr-1"></i>Mutabaah</span>
                                    </label>
                                    <label class="inline-flex items-center space-x-2 cursor-pointer">
                                        <input type="checkbox" id="chk-kebersihan" checked class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300">
                                        <span class="text-slate-700 font-medium"><i class="fa-solid fa-broom text-purple-600 mr-1"></i>Kebersihan</span>
                                    </label>
                                    <label class="inline-flex items-center space-x-2 cursor-pointer">
                                        <input type="checkbox" id="chk-journal" checked class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300">
                                        <span class="text-slate-700 font-medium"><i class="fa-solid fa-book text-emerald-600 mr-1"></i>Jurnal</span>
                                    </label>
                                    <label class="inline-flex items-center space-x-2 cursor-pointer">
                                        <input type="checkbox" id="chk-tasks" checked class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300">
                                        <span class="text-slate-700 font-medium"><i class="fa-solid fa-clipboard-list text-blue-600 mr-1"></i>Tiket Pekerjaan</span>
                                    </label>
                                </div>
                            </div>

                            <!-- b) Rentang Tanggal -->
                            <div>
                                <label class="block font-semibold text-slate-700 text-xs mb-1">Dari Tanggal (Start)</label>
                                <input type="date" id="report-start" class="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-xs font-mono">
                            </div>
                            <div>
                                <label class="block font-semibold text-slate-700 text-xs mb-1">Sampai Tanggal (End)</label>
                                <input type="date" id="report-end" class="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-xs font-mono">
                            </div>

                            <!-- c) Filter tambahan opsional: Unit -->
                            <div>
                                <label class="block font-semibold text-slate-700 text-xs mb-1">Filter Unit (Opsional)</label>
                                <select id="report-unit" class="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-xs">
                                    <option value="">Semua Unit</option>
                                    <option value="OB">OB</option>
                                    <option value="Security">Security</option>
                                    <option value="Gardener">Gardener</option>
                                    <option value="PGTK">PGTK</option>
                                    <option value="SD">SD</option>
                                    <option value="SMP">SMP</option>
                                    <option value="SMA">SMA</option>
                                </select>
                            </div>
                        </div>

                        <!-- d) Tombol Aksi -->
                        <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-200">
                            <div class="flex flex-wrap items-center gap-2">
                                <button onclick="generateReport()" class="px-4 py-2 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                                    <i class="fa-solid fa-arrows-rotate mr-1"></i> Generate Pratinjau
                                </button>
                                <button onclick="downloadExcelPeriod()" class="px-4 py-2 bg-teal-600 text-white text-xs font-semibold rounded-lg hover:bg-teal-700 transition shadow-xs flex items-center gap-1.5" title="Download Excel Periode">
                                    <i class="fa-solid fa-file-excel mr-1"></i> Download Excel Periode
                                </button>
                            </div>
                            <button onclick="window.print()" class="px-4 py-2 bg-slate-600 text-white text-xs font-semibold rounded-lg hover:bg-slate-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-print mr-1"></i> Cetak / Save PDF
                            </button>
                        </div>
                    </div>

                    <!-- Area Pratinjau -->
                    <div id="report-preview-area" class="space-y-6">
                        <div class="p-8 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl">
                            <i class="fa-solid fa-spinner fa-spin text-3xl mb-2 text-emerald-600"></i>
                            <p class="text-sm">Menyiapkan pratinjau laporan...</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB: SAPA AIS / LAPORPAK -->
            <div id="tab-sapaais" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-bullhorn text-emerald-600"></i>
                                LaporPak (Sapa Ais) — Daftar Tiket WhatsApp
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">Daftar keluhan, permintaan fasilitas/IT, dan tiket layanan civitas sekolah</p>
                        </div>
                        <div class="flex items-center gap-3">
                            <button onclick="loadSapaAis(1)" class="px-3.5 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-arrows-rotate"></i> Refresh
                            </button>
                            <a href="https://wa.me/628121648686" target="_blank" class="px-3.5 py-1.5 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-lg hover:bg-emerald-100 transition border border-emerald-200 flex items-center gap-1.5">
                                <i class="fa-solid fa-comment"></i> Buka WA Bot
                            </a>
                        </div>
                    </div>

                    <!-- Filter Bar -->
                    <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Filter Status</label>
                            <select id="sapaais-filter-status" onchange="loadSapaAis(1)" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                                <option value="">Semua Status</option>
                                <option value="BARU">BARU</option>
                                <option value="DITERIMA">DITERIMA</option>
                                <option value="SELESAI">SELESAI</option>
                            </select>
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Filter Kategori</label>
                            <select id="sapaais-filter-kategori" onchange="loadSapaAis(1)" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                                <option value="">Semua Kategori</option>
                                <option value="IT">IT</option>
                                <option value="FASILITAS">FASILITAS</option>
                                <option value="KEBERSIHAN">KEBERSIHAN</option>
                                <option value="BELAJAR">BELAJAR</option>
                                <option value="LAINNYA">LAINNYA</option>
                            </select>
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Dari Tanggal</label>
                            <input type="date" id="sapaais-filter-from" onchange="loadSapaAis(1)" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                        </div>
                        <div>
                            <label class="block font-semibold text-slate-600 mb-1">Sampai Tanggal</label>
                            <input type="date" id="sapaais-filter-to" onchange="loadSapaAis(1)" class="w-full p-2 bg-white border border-slate-200 rounded-lg">
                        </div>
                    </div>

                    <!-- Stats Cards -->
                    <div id="sapaais-stats" class="grid grid-cols-2 md:grid-cols-5 gap-3 sm:gap-4 min-h-[40px] sm:min-h-[60px]">
                        <div class="text-center py-4 text-slate-400 text-sm hidden" id="sapaais-loading-stats">
                            <i class="fa-solid fa-spinner fa-spin mr-1"></i>Memuat...
                        </div>
                    </div>

                    <!-- Per Kategori -->
                    <div id="sapaais-cats-wrap" class="bg-slate-50 rounded-xl border border-slate-200 p-4 hidden">
                        <h3 class="font-bold text-xs mb-2 text-slate-700 flex items-center gap-1.5">
                            <i class="fa-solid fa-folder-open text-emerald-600"></i> Distribusi Per Kategori
                        </h3>
                        <div id="sapaais-cats" class="bg-white rounded-lg border border-slate-200 overflow-hidden divide-y divide-slate-100 min-h-[40px]"></div>
                    </div>

                    <!-- Table -->
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase">
                                    <th class="p-3">ID Tiket</th>
                                    <th class="p-3">Kategori</th>
                                    <th class="p-3">Lokasi</th>
                                    <th class="p-3">Deskripsi</th>
                                    <th class="p-3">Status</th>
                                    <th class="p-3">PIC</th>
                                    <th class="p-3">SLA</th>
                                    <th class="p-3">Foto</th>
                                    <th class="p-3">Waktu Masuk</th>
                                </tr>
                            </thead>
                            <tbody id="sapaais-tbody" class="divide-y divide-slate-100 min-h-[60px]">
                                <tr><td colspan="9" class="p-4 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat data Sapa Ais...</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Pagination -->
                    <div id="sapaais-pagination" class="flex items-center justify-between pt-2 border-t border-slate-100"></div>
                </div>
            </div>

            <!-- TAB: MUTABA'AH DIRI -->
            <div id="tab-mutubaah" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <!-- Header -->
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-book-open text-teal-600"></i>
                                Mutaba'ah Diri Pimpinan & Civitas
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">Program peningkatan kualitas diri: tilawah Al-Qur'an, pemahaman bacaan sholat, dan target dzikir yaumiyah civitas An Nahl</p>
                        </div>
                        <div class="flex flex-wrap items-center gap-2">
                            <a href="https://ais-survey.ametriyadhi.com/mutabaah/peserta" target="_blank" class="px-3.5 py-1.5 bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold rounded-lg hover:bg-teal-100 transition shadow-xs flex items-center gap-1.5" title="Buka Pengaturan Peserta & WhatsApp di SAS">
                                <i class="fa-solid fa-users-gear text-teal-600"></i> Kelola Peserta & WA
                            </a>
                            <button onclick="toggleModal('modal-add-mutubaah')" class="px-3.5 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-plus"></i> Input Mutaba'ah
                            </button>
                            <button onclick="loadMutubaahData()" class="px-3.5 py-1.5 bg-teal-600 text-white text-xs font-semibold rounded-lg hover:bg-teal-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-arrows-rotate"></i> Refresh Data
                            </button>
                            <button onclick="exportMutubaahCSV()" class="px-3.5 py-1.5 bg-slate-600 text-white text-xs font-semibold rounded-lg hover:bg-slate-700 transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-file-csv"></i> Export CSV
                            </button>
                        </div>
                    </div>
                    
                    <!-- Filter Bar -->
                    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/80 flex flex-col md:flex-row gap-3 items-center justify-between">
                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 w-full md:w-auto flex-1">
                            <div>
                                <label class="block text-[11px] font-semibold text-slate-600 mb-1">Pilih Peserta:</label>
                                <select id="mutubaah-filter-peserta" onchange="loadMutubaahData()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-teal-500">
                                    <option value="all">Semua Peserta</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[11px] font-semibold text-slate-600 mb-1">Unit Kerja:</label>
                                <select id="mutubaah-filter-unit" onchange="loadMutubaahData()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-teal-500">
                                    <option value="all">Semua Unit</option>
                                    <option value="SMA">SMA Islam An Nahl</option>
                                    <option value="SMP">SMP Islam An Nahl</option>
                                    <option value="SD">SD Islam An Nahl</option>
                                    <option value="PGTK">PG-TK Islam An Nahl</option>
                                    <option value="UMUM & ECOPARK">Umum & Ecopark</option>
                                    <option value="IT">IT & Sistem</option>
                                    <option value="OB">Office Boy (OB)</option>
                                    <option value="GARDENER">Gardener / Taman</option>
                                    <option value="SECURITY">Security / Keamanan</option>
                                    <option value="SDM">SDM & Kepegawaian</option>
                                    <option value="SARPRAS">Sarana & Prasarana</option>
                                    <option value="PENGADAAN">Pengadaan Barang</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[11px] font-semibold text-slate-600 mb-1">Dari Tanggal:</label>
                                <input type="date" id="mutubaah-filter-from" onchange="loadMutubaahData()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-teal-500">
                            </div>
                            <div>
                                <label class="block text-[11px] font-semibold text-slate-600 mb-1">Sampai Tanggal:</label>
                                <input type="date" id="mutubaah-filter-to" onchange="loadMutubaahData()" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-teal-500">
                            </div>
                        </div>
                        <button onclick="resetMutubaahFilter()" class="text-xs text-slate-500 hover:text-rose-600 font-medium whitespace-nowrap self-end md:self-center">
                            <i class="fa-solid fa-rotate-left mr-1"></i>Reset
                        </button>
                    </div>

                    <!-- Metric / Summary Cards -->
                    <div id="mutubaah-summary" class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                        <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                            <div>
                                <p class="text-[11px] sm:text-xs text-slate-500 font-medium" id="mutubaah-lbl-card1">Juz Terakhir</p>
                                <h3 class="text-base sm:text-xl font-bold text-teal-700 mt-1" id="mutubaah-tilawah-hari">-</h3>
                            </div>
                            <div class="p-2.5 sm:p-3 bg-teal-50 text-teal-600 rounded-xl">
                                <i class="fa-solid fa-book-quran text-lg sm:text-2xl"></i>
                            </div>
                        </div>
                        <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                            <div>
                                <p class="text-[11px] sm:text-xs text-slate-500 font-medium" id="mutubaah-lbl-card2">Khatam Ke</p>
                                <h3 class="text-base sm:text-xl font-bold text-blue-700 mt-1" id="mutubaah-khatam">-</h3>
                            </div>
                            <div class="p-2.5 sm:p-3 bg-blue-50 text-blue-600 rounded-xl">
                                <i class="fa-solid fa-award text-lg sm:text-2xl"></i>
                            </div>
                        </div>
                        <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                            <div>
                                <p class="text-[11px] sm:text-xs text-slate-500 font-medium" id="mutubaah-lbl-card3">Faham Sholat</p>
                                <h3 class="text-base sm:text-xl font-bold text-purple-700 mt-1" id="mutubaah-sholat">-%</h3>
                            </div>
                            <div class="p-2.5 sm:p-3 bg-purple-50 text-purple-600 rounded-xl">
                                <i class="fa-solid fa-person-praying text-lg sm:text-2xl"></i>
                            </div>
                        </div>
                        <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                            <div>
                                <p class="text-[11px] sm:text-xs text-slate-500 font-medium" id="mutubaah-lbl-card4">Total Dzikir</p>
                                <h3 class="text-base sm:text-xl font-bold text-rose-700 mt-1" id="mutubaah-dzikir">-</h3>
                            </div>
                            <div class="p-2.5 sm:p-3 bg-rose-50 text-rose-600 rounded-xl">
                                <i class="fa-solid fa-hands-holding-circle text-lg sm:text-2xl"></i>
                            </div>
                        </div>
                    </div>

                    <!-- Table -->
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase">
                                    <th class="p-3">Tanggal</th>
                                    <th class="p-3">Nama & Jabatan</th>
                                    <th class="p-3">Unit</th>
                                    <th class="p-3">Juz Tilawah</th>
                                    <th class="p-3">Khatam</th>
                                    <th class="p-3">Faham Sholat</th>
                                    <th class="p-3">Total Dzikir</th>
                                    <th class="p-3">Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="mutubaah-tbody" class="divide-y divide-slate-100 min-h-[60px]">
                                <tr><td colspan="8" class="p-4 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat data Mutabaah Diri...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- MODAL: INPUT MUTABA'AH DIRI LANGSUNG -->
            <div id="modal-add-mutubaah" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 hidden p-4">
                <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-book-open text-teal-600"></i>
                            Input Laporan Mutaba'ah Diri
                        </h3>
                        <button onclick="toggleModal('modal-add-mutubaah')" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <form onsubmit="submitMutubaahForm(event)" class="space-y-3.5 mt-4 text-xs">
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Nama Peserta *</label>
                                <input type="text" id="mut-input-nama" required placeholder="Contoh: Ust. Japar Siddiq" class="w-full border border-slate-300 rounded-lg p-2 text-xs focus:ring-1 focus:ring-teal-500">
                            </div>
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Unit Kerja *</label>
                                <select id="mut-input-unit" required class="w-full border border-slate-300 rounded-lg p-2 text-xs focus:ring-1 focus:ring-teal-500">
                                    <option value="SMA">SMA Islam An Nahl</option>
                                    <option value="SMP">SMP Islam An Nahl</option>
                                    <option value="SD">SD Islam An Nahl</option>
                                    <option value="PGTK">PG-TK Islam An Nahl</option>
                                    <option value="UMUM & ECOPARK" selected>Umum & Ecopark</option>
                                    <option value="IT">IT & Sistem</option>
                                    <option value="OB">Office Boy (OB)</option>
                                    <option value="GARDENER">Gardener</option>
                                    <option value="SECURITY">Security</option>
                                    <option value="SDM">SDM & Kepegawaian</option>
                                    <option value="SARPRAS">Sarpras</option>
                                    <option value="PENGADAAN">Pengadaan</option>
                                </select>
                            </div>
                        </div>

                        <div class="grid grid-cols-3 gap-3">
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Tanggal</label>
                                <input type="date" id="mut-input-tanggal" class="w-full border border-slate-300 rounded-lg p-2 text-xs">
                            </div>
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Usia</label>
                                <input type="number" id="mut-input-usia" value="40" class="w-full border border-slate-300 rounded-lg p-2 text-xs">
                            </div>
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Juz Tilawah *</label>
                                <input type="text" id="mut-input-tilawah" required placeholder="Misal: 1 atau 4-6" class="w-full border border-slate-300 rounded-lg p-2 text-xs">
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Khatam Ke</label>
                                <input type="number" id="mut-input-khatam" value="1" min="0" class="w-full border border-slate-300 rounded-lg p-2 text-xs">
                            </div>
                            <div>
                                <label class="block font-semibold text-slate-700 mb-1">Faham Sholat (%)</label>
                                <input type="text" id="mut-input-sholat" value="95%" placeholder="95%" class="w-full border border-slate-300 rounded-lg p-2 text-xs">
                            </div>
                        </div>

                        <div class="border-t border-slate-100 pt-3">
                            <p class="font-bold text-slate-700 mb-2 flex items-center gap-1.5"><i class="fa-solid fa-hands-holding-circle text-teal-600"></i> Target Dzikir Yaumiyah</p>
                            <div class="grid grid-cols-2 gap-2 text-slate-600">
                                <div>
                                    <label class="block text-[11px] mb-0.5">1. Doa Orang Tua</label>
                                    <input type="number" id="mut-input-dzikir1" value="300" class="w-full border border-slate-200 rounded p-1.5 text-xs font-mono">
                                </div>
                                <div>
                                    <label class="block text-[11px] mb-0.5">2. Doa Nabi Yunus</label>
                                    <input type="number" id="mut-input-dzikir2" value="300" class="w-full border border-slate-200 rounded p-1.5 text-xs font-mono">
                                </div>
                                <div>
                                    <label class="block text-[11px] mb-0.5">3. Hauqolah</label>
                                    <input type="number" id="mut-input-dzikir3" value="300" class="w-full border border-slate-200 rounded p-1.5 text-xs font-mono">
                                </div>
                                <div>
                                    <label class="block text-[11px] mb-0.5">4. Hasballah</label>
                                    <input type="number" id="mut-input-dzikir4" value="300" class="w-full border border-slate-200 rounded p-1.5 text-xs font-mono">
                                </div>
                                <div class="col-span-2">
                                    <label class="block text-[11px] mb-0.5">5. Sholawat Nabi</label>
                                    <input type="number" id="mut-input-dzikir5" value="300" class="w-full border border-slate-200 rounded p-1.5 text-xs font-mono">
                                </div>
                            </div>
                        </div>

                        <div class="flex justify-end gap-2 border-t border-slate-100 pt-3 mt-4">
                            <button type="button" onclick="toggleModal('modal-add-mutubaah')" class="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-semibold">Batal</button>
                            <button type="submit" class="px-4 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-paper-plane"></i> Simpan Mutaba'ah
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- TAB: MANAJEMEN USER (KHUSUS MANAGER) -->
            <div id="tab-users" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-users-gear text-emerald-600"></i>
                                Manajemen Pengguna & Koordinator Unit
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">Kelola akun akses, penugasan koordinator untuk 4 unit kerja, dan pengaturan keamanan</p>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="loadOpsUsers()" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center gap-1.5">
                                <i class="fa-solid fa-arrows-rotate"></i> Refresh
                            </button>
                            <button onclick="toggleModal('modal-add-ops-user')" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5">
                                <i class="fa-solid fa-user-plus"></i> Tambah Koordinator
                            </button>
                        </div>
                    </div>

                    <!-- Summary Cards -->
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                        <div class="bg-slate-50 rounded-xl p-4 border border-slate-200/80">
                            <p class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Akun</p>
                            <h3 class="text-xl font-bold text-slate-800 mt-1" id="ops-stat-total-users">-</h3>
                            <span class="text-[10px] text-slate-400">Terdaftar di sistem</span>
                        </div>
                        <div class="bg-emerald-50/60 rounded-xl p-4 border border-emerald-200/80">
                            <p class="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Koordinator Aktif</p>
                            <h3 class="text-xl font-bold text-emerald-700 mt-1" id="ops-stat-active-users">-</h3>
                            <span class="text-[10px] text-emerald-600">Dapat login & bertugas</span>
                        </div>
                        <div class="bg-blue-50/60 rounded-xl p-4 border border-blue-200/80">
                            <p class="text-[11px] font-semibold text-blue-700 uppercase tracking-wider">Unit Terintegrasi</p>
                            <h3 class="text-xl font-bold text-blue-700 mt-1">4 Unit</h3>
                            <span class="text-[10px] text-blue-600">IT, OB, Gardener, Security</span>
                        </div>
                        <div class="bg-purple-50/60 rounded-xl p-4 border border-purple-200/80">
                            <p class="text-[11px] font-semibold text-purple-700 uppercase tracking-wider">Keamanan Sandi</p>
                            <h3 class="text-xl font-bold text-purple-700 mt-1">Bcrypt Hash</h3>
                            <span class="text-[10px] text-purple-600">Enkripsi berstandar tinggi</span>
                        </div>
                    </div>

                    <!-- Table Users -->
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase">
                                    <th class="p-3.5">Pengguna</th>
                                    <th class="p-3.5">Unit Kerja</th>
                                    <th class="p-3.5">Role Akses</th>
                                    <th class="p-3.5">Kontak WhatsApp</th>
                                    <th class="p-3.5">Status</th>
                                    <th class="p-3.5">Terakhir Login</th>
                                    <th class="p-3.5 text-center">Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="ops-users-tbody" class="divide-y divide-slate-100">
                                <tr>
                                    <td colspan="7" class="p-6 text-center text-slate-400">
                                        <i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat daftar pengguna...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB: MANAJEMEN ROLE & HAK AKSES (KHUSUS MANAGER) -->
            <div id="tab-roles" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-shield-halved text-emerald-600"></i>
                                Manajemen Role & Hak Akses (RBAC Matrix)
                            </h2>
                            <p class="text-xs text-slate-500 mt-1">Konfigurasi izin akses modul dan visibilitas tab untuk pimpinan serta 4 unit koordinator</p>
                        </div>
                        <button onclick="loadOpsRoles()" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center gap-1.5">
                            <i class="fa-solid fa-arrows-rotate"></i> Refresh Matrix
                        </button>
                    </div>

                    <!-- Role Cards Overview -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="ops-roles-cards-container">
                        <!-- Rendered by JS -->
                    </div>

                    <!-- Permission Matrix Table -->
                    <div class="mt-6 border border-slate-200 rounded-xl overflow-hidden shadow-xs">
                        <div class="bg-slate-50 p-3.5 border-b border-slate-200 flex items-center justify-between">
                            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Matriks Hak Akses Modul Operasional</h3>
                            <span class="text-[11px] text-slate-500"><i class="fa-solid fa-circle-info mr-1 text-emerald-600"></i>Terproteksi secara real-time pada sesi pengguna</span>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse text-xs">
                                <thead>
                                    <tr class="bg-slate-100/70 border-b border-slate-200 text-slate-600 font-semibold uppercase">
                                        <th class="p-3">Fitur / Tab Modul</th>
                                        <th class="p-3 text-center">Manager (Mr. Slam)</th>
                                        <th class="p-3 text-center">Koord. IT</th>
                                        <th class="p-3 text-center">Koord. OB</th>
                                        <th class="p-3 text-center">Koord. Gardener</th>
                                        <th class="p-3 text-center">Koord. Security</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100 text-slate-700">
                                    <tr class="hover:bg-slate-50/80">
                                        <td class="p-3 font-semibold flex items-center gap-2"><i class="fa-solid fa-gauge text-emerald-600 w-4"></i> Dashboard Utama</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Semua Unit</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800">Unit IT</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-teal-100 text-teal-800">Unit OB</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800">Gardener</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">Security</span></td>
                                    </tr>
                                    <tr class="hover:bg-slate-50/80">
                                        <td class="p-3 font-semibold flex items-center gap-2"><i class="fa-solid fa-clipboard-list text-slate-600 w-4"></i> Pendelegasian Tugas (Tasks)</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Buat & Disposisi</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700">Update Progres</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700">Update Progres</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700">Update Progres</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700">Update Progres</span></td>
                                    </tr>
                                    <tr class="hover:bg-slate-50/80">
                                        <td class="p-3 font-semibold flex items-center gap-2"><i class="fa-solid fa-book text-amber-600 w-4"></i> Jurnal Harian Koordinator</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Baca Semua & Feedback</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">Input Harian IT</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">Input Harian OB</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">Input Harian Gardener</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">Input Harian Security</span></td>
                                    </tr>
                                    <tr class="hover:bg-slate-50/80">
                                        <td class="p-3 font-semibold flex items-center gap-2"><i class="fa-solid fa-broom text-teal-600 w-4"></i> Log Kebersihan & Foto Sarpras</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Kontrol & Buat Tiket</span></td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-teal-100 text-teal-800 font-medium">Indoor & Toilet</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-medium">Outdoor & Taman</span></td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                    </tr>
                                    <tr class="hover:bg-slate-50/80">
                                        <td class="p-3 font-semibold flex items-center gap-2"><i class="fa-solid fa-hands-praying text-emerald-600 w-4"></i> Log Mutabaah Yaumiyah Ibadah</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Rekap Global</span></td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-teal-100 text-teal-800">Anggota OB</span></td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">Anggota Security</span></td>
                                    </tr>
                                    <tr class="hover:bg-slate-50/80">
                                        <td class="p-3 font-semibold flex items-center gap-2"><i class="fa-solid fa-server text-blue-600 w-4"></i> Server & Uptime Kuma</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Akses Penuh</span></td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium">Akses Monitoring</span></td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                        <td class="p-3 text-center text-slate-300">-</td>
                                    </tr>
                                    <tr class="hover:bg-slate-50/80 bg-slate-50/50">
                                        <td class="p-3 font-bold flex items-center gap-2 text-emerald-900"><i class="fa-solid fa-users-gear text-emerald-700 w-4"></i> Manajemen User & Role Akses</td>
                                        <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-emerald-600 text-white font-bold">Khusus Manager</span></td>
                                        <td class="p-3 text-center text-slate-300"><i class="fa-solid fa-lock text-slate-300"></i></td>
                                        <td class="p-3 text-center text-slate-300"><i class="fa-solid fa-lock text-slate-300"></i></td>
                                        <td class="p-3 text-center text-slate-300"><i class="fa-solid fa-lock text-slate-300"></i></td>
                                        <td class="p-3 text-center text-slate-300"><i class="fa-solid fa-lock text-slate-300"></i></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB: PENGADAAN BARANG & LOGISTIK SARPRAS -->
            <div id="tab-pengadaan" class="tab-content hidden space-y-6">
                <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                        <div>
                            <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                                <i class="fa-solid fa-cart-shopping text-amber-500"></i>
                                {% if user_role == 'manager' %}
                                Pengadaan Barang, Material & Logistik Sarpras
                                {% elif user_role == 'pic_pengadaan' %}
                                Modul Pengadaan & Pembelanjaan Logistik
                                {% elif user_role == 'pic_sarpras' %}
                                Pengajuan Material & Suku Cadang Sarpras
                                {% else %}
                                Permohonan Pengadaan Unit {{ user_unit }}
                                {% endif %}
                            </h2>
                            <p class="text-xs text-slate-500 mt-0.5">
                                Alur pengajuan suku cadang/material, persetujuan pimpinan, pembelanjaan oleh PIC Pengadaan, dan serah-terima ke teknisi lapangan.
                            </p>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="toggleModal('modal-add-pengadaan')" class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5 shrink-0">
                                <i class="fa-solid fa-plus"></i> Ajukan Pengadaan Baru
                            </button>
                        </div>
                    </div>

                    <!-- 5 Kartu Metrik Ringkasan Pengadaan -->
                    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                        <div class="bg-slate-50 border border-slate-200/80 p-4 rounded-xl">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-slate-500">Total Pengajuan</span>
                                <i class="fa-solid fa-list-check text-slate-400"></i>
                            </div>
                            <div class="text-2xl font-black text-slate-800 mt-2" id="proc-metric-total">{{ proc_stats.total if proc_stats else 0 }}</div>
                            <span class="text-[10px] text-slate-400">Permohonan tercatat</span>
                        </div>

                        <div class="bg-amber-50/60 border border-amber-200/80 p-4 rounded-xl">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-amber-700">Menunggu Approval</span>
                                <i class="fa-solid fa-hourglass-half text-amber-500"></i>
                            </div>
                            <div class="text-2xl font-black text-amber-700 mt-2" id="proc-metric-pending">{{ proc_stats.diajukan if proc_stats else 0 }}</div>
                            <span class="text-[10px] text-amber-600">Perlu persetujuan pimpinan</span>
                        </div>

                        <div class="bg-blue-50/60 border border-blue-200/80 p-4 rounded-xl">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-blue-700">Disetujui / PO Beli</span>
                                <i class="fa-solid fa-bag-shopping text-blue-500"></i>
                            </div>
                            <div class="text-2xl font-black text-blue-700 mt-2" id="proc-metric-proses">{{ (proc_stats.disetujui + proc_stats.proses_beli) if proc_stats else 0 }}</div>
                            <span class="text-[10px] text-blue-600">Tugas PIC Pengadaan</span>
                        </div>

                        <div class="bg-emerald-50/60 border border-emerald-200/80 p-4 rounded-xl">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-emerald-700">Barang Tiba / Selesai</span>
                                <i class="fa-solid fa-circle-check text-emerald-500"></i>
                            </div>
                            <div class="text-2xl font-black text-emerald-700 mt-2" id="proc-metric-selesai">{{ proc_stats.selesai if proc_stats else 0 }}</div>
                            <span class="text-[10px] text-emerald-600">Diserahkan ke teknisi</span>
                        </div>

                        <div class="bg-slate-900 text-white p-4 rounded-xl col-span-2 lg:col-span-1 border border-slate-800">
                            <div class="flex items-center justify-between text-slate-300">
                                <span class="text-xs font-bold">Total Anggaran</span>
                                <i class="fa-solid fa-coins text-amber-400"></i>
                            </div>
                            <div class="text-base font-black text-amber-400 mt-2 truncate">
                                Rp {{ "{:,.0f}".format(proc_stats.total_est_cost if proc_stats else 0) }}
                            </div>
                            <span class="text-[10px] text-slate-400 block truncate">
                                Realisasi: Rp {{ "{:,.0f}".format(proc_stats.total_act_cost if proc_stats else 0) }}
                            </span>
                        </div>
                    </div>

                    <!-- Filter Bar & Search -->
                    <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                        <div class="flex flex-wrap items-center gap-2">
                            {% if user_role in ['manager', 'pic_pengadaan'] %}
                            <div class="flex items-center gap-1.5">
                                <span class="font-bold text-slate-600 text-[11px] uppercase">Unit:</span>
                                <select id="proc-filter-unit" onchange="filterProcurementsTable()" class="p-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium">
                                    <option value="ALL">Semua Unit</option>
                                    <option value="SARPRAS">SARPRAS</option>
                                    <option value="IT">IT</option>
                                    <option value="OB">Office Boy</option>
                                    <option value="GARDENER">Gardener</option>
                                    <option value="SECURITY">Security</option>
                                    <option value="Umum">Umum</option>
                                </select>
                            </div>
                            {% endif %}

                            <div class="flex items-center gap-1.5">
                                <span class="font-bold text-slate-600 text-[11px] uppercase">Status:</span>
                                <select id="proc-filter-status" onchange="filterProcurementsTable()" class="p-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium">
                                    <option value="ALL">Semua Status</option>
                                    <option value="Diajukan">Diajukan (Menunggu Approval)</option>
                                    <option value="Disetujui">Disetujui Pimpinan</option>
                                    <option value="Proses Beli">Proses Pembelian</option>
                                    <option value="Barang Tiba">Barang Tiba</option>
                                    <option value="Diserahkan">Diserahkan / Selesai</option>
                                    <option value="Ditolak">Ditolak</option>
                                </select>
                            </div>
                        </div>

                        <div class="relative w-full md:w-64">
                            <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                            <input type="text" id="proc-search" oninput="filterProcurementsTable()" placeholder="Cari nama barang / no PR / nota..." class="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none">
                        </div>
                    </div>

                    <!-- Tabel Daftar Pengadaan -->
                    <div class="overflow-x-auto border border-slate-200 rounded-xl">
                        <table class="w-full text-left border-collapse text-xs">
                            <thead>
                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                                    <th class="p-3 whitespace-nowrap">No. PR & Tanggal</th>
                                    <th class="p-3 whitespace-nowrap">Pemohon & Unit</th>
                                    <th class="p-3">Barang / Material & Kuantitas</th>
                                    <th class="p-3 whitespace-nowrap">Ref Tiket</th>
                                    <th class="p-3 whitespace-nowrap">Est. Biaya / Realisasi</th>
                                    <th class="p-3 whitespace-nowrap">Vendor & Nota</th>
                                    <th class="p-3 text-center whitespace-nowrap">Status</th>
                                    <th class="p-3 text-center whitespace-nowrap">Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="proc-table-body" class="divide-y divide-slate-100">
                                {% for p in procurements %}
                                <tr class="proc-row hover:bg-slate-50/60 transition" data-status="{{ p.status }}" data-unit="{{ p.unit_code }}" data-search="{{ (p.id ~ ' ' ~ p.title ~ ' ' ~ (p.vendor_info or '') ~ ' ' ~ (p.receipt_no or '') ~ ' ' ~ (p.ticket_ref or ''))|lower }}">
                                    <td class="p-3 font-mono">
                                        <span class="font-bold text-slate-800">{{ p.id }}</span>
                                        <span class="block text-[10px] text-slate-400">{{ p.requested_at[:10] if p.requested_at else '-' }}</span>
                                    </td>
                                    <td class="p-3">
                                        <span class="px-2 py-0.5 rounded font-bold text-[10px] border border-slate-200 bg-slate-100 text-slate-700">{{ p.unit_code }}</span>
                                        <span class="block text-[11px] font-semibold text-slate-600 mt-0.5">{{ p.requested_by or 'Staf' }}</span>
                                    </td>
                                    <td class="p-3">
                                        <p class="font-bold text-slate-800 leading-snug">{{ p.title }}</p>
                                        <div class="flex items-center gap-2 mt-0.5 text-[11px] text-slate-500">
                                            <span><i class="fa-solid fa-box mr-1 text-slate-400"></i>{{ p.quantity or '1 unit' }}</span>
                                            <span class="text-slate-300">|</span>
                                            <span class="text-[10px] px-1.5 py-0.2 rounded {% if p.urgency == 'Tinggi' %}bg-rose-100 text-rose-700 font-bold{% elif p.urgency == 'Sedang' %}bg-amber-100 text-amber-700{% else %}bg-slate-100 text-slate-600{% endif %}">
                                                Urgensi: {{ p.urgency }}
                                            </span>
                                        </div>
                                        {% if p.notes %}
                                        <p class="text-[10px] text-slate-400 italic mt-1 line-clamp-1">"{{ p.notes }}"</p>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 font-mono text-[11px]">
                                        {% if p.ticket_ref %}
                                        <span class="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded font-semibold">{{ p.ticket_ref }}</span>
                                        {% else %}
                                        <span class="text-slate-300 italic">-</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 whitespace-nowrap">
                                        <span class="text-slate-800 font-bold">Rp {{ "{:,.0f}".format(p.estimated_cost or 0) }}</span>
                                        {% if p.actual_cost and p.actual_cost > 0 %}
                                        <span class="block text-[10px] text-emerald-700 font-semibold">Real: Rp {{ "{:,.0f}".format(p.actual_cost) }}</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3">
                                        {% if p.vendor_info or p.receipt_no %}
                                        <span class="font-semibold text-slate-700 block text-[11px]">{{ p.vendor_info or '-' }}</span>
                                        <span class="text-[10px] text-slate-500 font-mono">Nota: {{ p.receipt_no or '-' }}</span>
                                        {% else %}
                                        <span class="text-slate-300 italic text-[11px]">-</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 text-center whitespace-nowrap">
                                        {% if p.status == 'Diajukan' %}
                                        <span class="px-2.5 py-1 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-full border border-amber-200">
                                            <i class="fa-solid fa-hourglass-start mr-1"></i>Diajukan
                                        </span>
                                        {% elif p.status == 'Disetujui' %}
                                        <span class="px-2.5 py-1 text-[10px] font-bold bg-blue-100 text-blue-800 rounded-full border border-blue-200">
                                            <i class="fa-solid fa-thumbs-up mr-1"></i>Disetujui
                                        </span>
                                        {% elif p.status == 'Proses Beli' %}
                                        <span class="px-2.5 py-1 text-[10px] font-bold bg-indigo-100 text-indigo-800 rounded-full border border-indigo-200">
                                            <i class="fa-solid fa-truck-fast mr-1"></i>Proses Beli
                                        </span>
                                        {% elif p.status in ['Barang Tiba', 'Diserahkan', 'Selesai'] %}
                                        <span class="px-2.5 py-1 text-[10px] font-bold bg-emerald-100 text-emerald-800 rounded-full border border-emerald-200">
                                            <i class="fa-solid fa-circle-check mr-1"></i>{{ p.status }}
                                        </span>
                                        {% elif p.status == 'Ditolak' %}
                                        <span class="px-2.5 py-1 text-[10px] font-bold bg-rose-100 text-rose-800 rounded-full border border-rose-200">
                                            <i class="fa-solid fa-ban mr-1"></i>Ditolak
                                        </span>
                                        {% else %}
                                        <span class="px-2.5 py-1 text-[10px] font-bold bg-slate-100 text-slate-700 rounded-full">{{ p.status }}</span>
                                        {% endif %}
                                    </td>
                                    <td class="p-3 text-center whitespace-nowrap">
                                        <div class="flex items-center justify-center gap-1.5">
                                            {% if user_role == 'manager' and p.status == 'Diajukan' %}
                                            <button data-id="{{ p.id }}" data-title="{{ p.title }}" data-cost="{{ p.estimated_cost or 0 }}" data-req="{{ p.requested_by or 'Staf' }}" onclick="openApproveModalFromBtn(this)" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-xs flex items-center gap-1 shadow-xs" title="Verifikasi / Setujui Pengadaan">
                                                <i class="fa-solid fa-check"></i> Verifikasi
                                            </button>
                                            {% endif %}

                                            {% if user_role in ['manager', 'pic_pengadaan'] and p.status in ['Disetujui', 'Proses Beli', 'Barang Tiba'] %}
                                            <button data-id="{{ p.id }}" data-title="{{ p.title }}" data-status="{{ p.status }}" data-cost="{{ p.estimated_cost or 0 }}" data-act="{{ p.actual_cost or 0 }}" data-vendor="{{ p.vendor_info or '' }}" data-receipt="{{ p.receipt_no or '' }}" data-notes="{{ p.notes or '' }}" onclick="openUpdateModalFromBtn(this)" class="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs flex items-center gap-1 shadow-xs" title="Update Status Pengadaan">
                                                <i class="fa-solid fa-pen-to-square"></i> Update
                                            </button>
                                            {% endif %}

                                            {% if user_role == 'manager' %}
                                            <button onclick="deletePengadaan('{{ p.id }}')" class="p-1 text-slate-300 hover:text-rose-600 transition" title="Hapus Pengadaan">
                                                <i class="fa-solid fa-trash-can"></i>
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="8" class="p-8 text-center text-slate-400 italic">
                                        <i class="fa-solid fa-cart-flatbed text-3xl mb-2 text-slate-300 block"></i>
                                        Belum ada data pengadaan barang. Klik tombol <b>Ajukan Pengadaan Baru</b> di atas untuk membuat permohonan.
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>

    </main>

    <!-- Modal Add User (Khusus Manager) -->
    <div id="modal-add-ops-user" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-user-plus text-emerald-600"></i> Tambah Koordinator Baru
                </h3>
                <button onclick="toggleModal('modal-add-ops-user')" class="text-slate-400 hover:text-slate-600 p-1">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <form onsubmit="submitAddOpsUser(event)" class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Username Login *</label>
                    <input type="text" id="add-user-username" placeholder="Contoh: koord_it / koord_ob" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Password Awal *</label>
                    <input type="password" id="add-user-password" placeholder="Minimal 6 karakter" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none" required minlength="6">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Nama Lengkap Koordinator *</label>
                    <input type="text" id="add-user-nama" placeholder="Contoh: Aji Kurnia / Azril" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Unit Kerja *</label>
                        <select id="add-user-unit" onchange="toggleSubScopeField('add')" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                            <option value="IT">IT</option>
                            <option value="OB">Office Boy</option>
                            <option value="GARDENER">Gardener</option>
                            <option value="SECURITY">Security</option>
                            <option value="SARPRAS">SARPRAS (Perbaikan Fasilitas)</option>
                            <option value="PENGADAAN">PENGADAAN (Logistik & Belanja)</option>
                            <option value="ALL">ALL (Manajemen)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Role Akses *</label>
                        <select id="add-user-role" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                            <option value="koordinator_it">Koordinator IT</option>
                            <option value="koordinator_ob">Koordinator OB</option>
                            <option value="koordinator_gardener">Koordinator Gardener</option>
                            <option value="koordinator_security">Koordinator Security</option>
                            <option value="pic_sarpras">PIC Perbaikan Sarpras</option>
                            <option value="pic_pengadaan">PIC Pengadaan</option>
                            <option value="manager">Manager (Super Admin)</option>
                        </select>
                    </div>
                </div>
                <div id="add-user-subscope-container" class="hidden">
                    <label class="block text-xs font-semibold text-emerald-700 mb-1">Sub-Lingkup Gardener</label>
                    <select id="add-user-subscope" class="w-full p-2.5 text-xs border border-emerald-200 bg-emerald-50/50 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        <option value="TAMAN_ECOPARK">1. Kebersihan Taman/Ecopark, Luar & Buah</option>
                        <option value="SAYURAN_TERNAK">2. Sayuran & Ternak Edukasi</option>
                        <option value="TAMAN_ECOPARK_TERNAK">Semua Sub-Lingkup Gardener</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">No. WhatsApp (Notifikasi Pendelegasian)</label>
                    <input type="text" id="add-user-wa" placeholder="Contoh: 628123456789" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-add-ops-user')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 font-medium">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700 transition shadow-xs">Simpan Koordinator</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Edit User -->
    <div id="modal-edit-ops-user" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-user-pen text-blue-600"></i> Edit Data Koordinator
                </h3>
                <button onclick="toggleModal('modal-edit-ops-user')" class="text-slate-400 hover:text-slate-600 p-1">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <form onsubmit="submitEditOpsUser(event)" class="space-y-3">
                <input type="hidden" id="edit-user-id">
                <div>
                    <label class="block text-xs font-semibold text-slate-400 mb-1">Username (Tidak dapat diubah)</label>
                    <input type="text" id="edit-user-username" disabled class="w-full p-2.5 text-xs bg-slate-100 border border-slate-200 rounded-lg text-slate-500 font-mono">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Nama Lengkap *</label>
                    <input type="text" id="edit-user-nama" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Unit Kerja *</label>
                        <select id="edit-user-unit" onchange="toggleSubScopeField('edit')" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required>
                            <option value="IT">IT</option>
                            <option value="OB">Office Boy</option>
                            <option value="GARDENER">Gardener</option>
                            <option value="SECURITY">Security</option>
                            <option value="SARPRAS">SARPRAS (Perbaikan Fasilitas)</option>
                            <option value="PENGADAAN">PENGADAAN (Logistik & Belanja)</option>
                            <option value="ALL">ALL (Manajemen)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Role Akses *</label>
                        <select id="edit-user-role" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required>
                            <option value="koordinator_it">Koordinator IT</option>
                            <option value="koordinator_ob">Koordinator OB</option>
                            <option value="koordinator_gardener">Koordinator Gardener</option>
                            <option value="koordinator_security">Koordinator Security</option>
                            <option value="pic_sarpras">PIC Perbaikan Sarpras</option>
                            <option value="pic_pengadaan">PIC Pengadaan</option>
                            <option value="manager">Manager (Super Admin)</option>
                        </select>
                    </div>
                </div>
                <div id="edit-user-subscope-container" class="hidden">
                    <label class="block text-xs font-semibold text-emerald-700 mb-1">Sub-Lingkup Gardener</label>
                    <select id="edit-user-subscope" class="w-full p-2.5 text-xs border border-emerald-200 bg-emerald-50/50 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                        <option value="TAMAN_ECOPARK">1. Kebersihan Taman/Ecopark, Luar & Buah</option>
                        <option value="SAYURAN_TERNAK">2. Sayuran & Ternak Edukasi</option>
                        <option value="TAMAN_ECOPARK_TERNAK">Semua Sub-Lingkup Gardener</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">No. WhatsApp</label>
                    <input type="text" id="edit-user-wa" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                </div>
                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-edit-ops-user')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 font-medium">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition shadow-xs">Simpan Perubahan</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Reset Password -->
    <div id="modal-reset-ops-password" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-key text-amber-600"></i> Reset Password User
                </h3>
                <button onclick="toggleModal('modal-reset-ops-password')" class="text-slate-400 hover:text-slate-600 p-1">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <form onsubmit="submitResetOpsPassword(event)" class="space-y-3">
                <input type="hidden" id="reset-user-id">
                <p class="text-xs text-slate-600">Reset sandi untuk akun <span id="reset-user-name-display" class="font-bold text-slate-800"></span>:</p>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Password Baru *</label>
                    <input type="password" id="reset-user-password" placeholder="Minimal 6 karakter" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none" required minlength="6">
                </div>
                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-reset-ops-password')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 font-medium">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-amber-600 text-white font-bold rounded-lg hover:bg-amber-700 transition shadow-xs">Reset Password</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Add Host (Uptime Kuma Style) -->
    <div id="modal-add-host" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 class="text-base font-bold text-slate-800">Tambah Target Monitor (CCTV/Server/App)</h3>
            <form action="/add_host" method="POST" class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Nama Perangkat / Layanan</label>
                    <input type="text" name="name" placeholder="Misal: CCTV Gerbang Utama / Server Portal SD" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Kategori Perangkat</label>
                    <select name="category" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                        <option value="CCTV / NVR">CCTV / NVR</option>
                        <option value="Server">Server</option>
                        <option value="Aplikasi Web">Aplikasi Web</option>
                        <option value="Network / Router">Network / Router</option>
                    </select>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Host / IP / URL</label>
                        <input type="text" name="host" placeholder="192.168.1.100 atau domain" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Tipe Pengecekan</label>
                        <select name="type" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                            <option value="ping">Ping (ICMP)</option>
                            <option value="port">Port Check</option>
                            <option value="http">HTTP Web Check</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Port (Opsional jika tipe Port Check)</label>
                    <input type="text" name="port" placeholder="Misal: 554 (RTSP), 80, 443" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                </div>
                <div class="flex justify-end space-x-2 pt-2">
                    <button type="button" onclick="toggleModal('modal-add-host')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700">Simpan Target</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Edit Host (Uptime Kuma Style) -->
    <div id="modal-edit-host" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 class="text-base font-bold text-slate-800">Edit Target Monitor</h3>
            <form action="/edit_host" method="POST" class="space-y-3">
                <input type="hidden" name="host_id" id="edit-host-id">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Nama Perangkat / Layanan</label>
                    <input type="text" name="name" id="edit-host-name" placeholder="Misal: CCTV Gerbang Utama / Server Portal SD" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Kategori Perangkat</label>
                    <select name="category" id="edit-host-category" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                        <option value="CCTV / NVR">CCTV / NVR</option>
                        <option value="Server">Server</option>
                        <option value="Aplikasi Web">Aplikasi Web</option>
                        <option value="Network / Router">Network / Router</option>
                        <option value="Server / Docker">Server / Docker</option>
                        <option value="Workstation">Workstation</option>
                    </select>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Host / IP / URL</label>
                        <input type="text" name="host" id="edit-host-host" placeholder="192.168.1.100 atau domain" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Tipe Pengecekan</label>
                        <select name="type" id="edit-host-type" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                            <option value="ping">Ping (ICMP)</option>
                            <option value="port">Port Check</option>
                            <option value="http">HTTP Web Check</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Port (Opsional jika tipe Port Check)</label>
                    <input type="text" name="port" id="edit-host-port" placeholder="Misal: 554 (RTSP), 80, 443" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                </div>
                <div class="flex justify-end space-x-2 pt-2">
                    <button type="button" onclick="toggleModal('modal-edit-host')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700">Update Target</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Add Journal -->
    <div id="modal-add-journal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 class="text-base font-bold text-slate-800">Catat Jurnal Kegiatan Harian</h3>
            <form action="/add_journal" method="POST" class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Judul / Topik Kegiatan</label>
                    <input type="text" name="title" placeholder="Misal: Rapat Evaluasi Mutu KBM & IT" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Kategori</label>
                        <select name="category" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                            <option value="IT Manager">IT Manager</option>
                            <option value="Kabag Umum">Kabag Umum</option>
                            <option value="Mutu & Pengembangan">Mutu & Pengembangan</option>
                            <option value="Rapat & Koordinasi">Rapat & Koordinasi</option>
                            <option value="Supervisi Lapangan">Supervisi Lapangan</option>
                            <option value="Operasional">Operasional</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Tanggal</label>
                        <input type="date" name="date" value="{{ today_date }}" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Waktu / Jam (WIB)</label>
                        <input type="time" name="time" value="{{ current_time }}" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                    </div>
                </div>
                {% if user_role == 'manager' %}
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Unit Sasaran / Bidang</label>
                    <select name="unit_code" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                        <option value="ALL">Semua Unit (Manajemen)</option>
                        <option value="IT">Unit IT</option>
                        <option value="OB">Unit Office Boy (OB)</option>
                        <option value="GARDENER">Unit Gardener / Lingkungan</option>
                        <option value="SECURITY">Unit Security / Keamanan</option>
                    </select>
                </div>
                {% else %}
                <input type="hidden" name="unit_code" value="{{ user_unit }}">
                {% endif %}
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Deskripsi Kegiatan / Hasil Rapat</label>
                    <textarea name="description" rows="4" placeholder="Tuliskan ringkasan aktivitas, pembahasan, atau keputusan..." class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required></textarea>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Hasil / Output Pekerjaan</label>
                    <input type="text" name="output" placeholder="Misal: Draf SOP disetujui, Perbaikan Selesai 100%" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                </div>
                <div class="flex justify-end space-x-2 pt-2">
                    <button type="button" onclick="toggleModal('modal-add-journal')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700">Simpan Jurnal</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Edit Journal -->
    <div id="modal-edit-journal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-pen-to-square text-emerald-600"></i> Edit Jurnal Kegiatan Harian
            </h3>
            <form action="/edit_journal" method="POST" class="space-y-3">
                <input type="hidden" name="journal_id" id="edit-journal-id">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Judul / Topik Kegiatan</label>
                    <input type="text" name="title" id="edit-journal-title" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Kategori</label>
                        <select name="category" id="edit-journal-category" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                            <option value="IT Manager">IT Manager</option>
                            <option value="Kabag Umum">Kabag Umum</option>
                            <option value="Mutu & Pengembangan">Mutu & Pengembangan</option>
                            <option value="Rapat & Koordinasi">Rapat & Koordinasi</option>
                            <option value="Supervisi Lapangan">Supervisi Lapangan</option>
                            <option value="Operasional">Operasional</option>
                            <option value="Unit IT">Unit IT</option>
                            <option value="Unit OB">Unit OB</option>
                            <option value="Unit Gardener">Unit Gardener</option>
                            <option value="Unit Security">Unit Security</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Tanggal</label>
                        <input type="date" name="date" id="edit-journal-date" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Waktu / Jam (WIB)</label>
                        <input type="time" name="time" id="edit-journal-time" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required>
                    </div>
                </div>
                {% if user_role == 'manager' %}
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Unit Sasaran / Bidang</label>
                    <select name="unit_code" id="edit-journal-unit" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                        <option value="ALL">Semua Unit (Manajemen)</option>
                        <option value="IT">Unit IT</option>
                        <option value="OB">Unit Office Boy (OB)</option>
                        <option value="GARDENER">Unit Gardener / Lingkungan</option>
                        <option value="SECURITY">Unit Security / Keamanan</option>
                    </select>
                </div>
                {% else %}
                <input type="hidden" name="unit_code" id="edit-journal-unit" value="{{ user_unit }}">
                {% endif %}
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Deskripsi Kegiatan / Hasil Rapat</label>
                    <textarea name="description" id="edit-journal-desc" rows="4" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg" required></textarea>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Hasil / Output Pekerjaan</label>
                    <input type="text" name="output" id="edit-journal-output" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg">
                </div>
                <div class="flex justify-end space-x-2 pt-2">
                    <button type="button" onclick="toggleModal('modal-edit-journal')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700">Simpan Perubahan</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Add Todo -->
    <div id="modal-add-todo" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-square-check text-emerald-600"></i> Tambah To-Do / Pendelegasian Unit
            </h3>
            <form action="/add_todo" method="POST" class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Judul / Kegiatan To-Do *</label>
                    <input type="text" name="title" placeholder="Misal: Pengecekan APAR / Briefing OB Gedung SD" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Unit Pendelegasian *</label>
                        {% if user_role == 'manager' %}
                        <select name="category" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                            <option value="IT">IT</option>
                            <option value="OB">Office Boy</option>
                            <option value="GARDENER">Gardener (Taman/Ecopark)</option>
                            <option value="SECURITY">Security</option>
                            <option value="Umum">Umum</option>
                            <option value="Personal">Personal Mr. Slam</option>
                        </select>
                        {% else %}
                        <input type="text" name="category" value="{{ user_unit }}" readonly class="w-full p-2.5 text-xs bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-semibold cursor-not-allowed">
                        {% endif %}
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Prioritas</label>
                        <select name="priority" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                            <option value="Sedang">Sedang</option>
                            <option value="Tinggi">Tinggi (Penting)</option>
                            <option value="Rendah">Rendah</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Target Tanggal Selesai</label>
                    <input type="date" name="due_date" class="w-full p-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div class="flex justify-end space-x-2 pt-2">
                    <button type="button" onclick="toggleModal('modal-add-todo')" class="px-4 py-2 text-xs bg-slate-100 text-slate-600 rounded-lg">Batal</button>
                    <button type="submit" class="px-4 py-2 text-xs bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700">Simpan To-Do</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Add Task (Pendelegasian Tugas) -->
    <div id="modal-add-task" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50 overflow-y-auto">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 my-8">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-clipboard-list text-emerald-600"></i> Disposisi & Pendelegasian Tugas
                </h3>
                <button type="button" onclick="toggleModal('modal-add-task')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>
            <form id="form-add-task" onsubmit="submitAddTask(event)" class="space-y-3 text-xs">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Unit Tujuan *</label>
                        <select name="unit_code" id="add-task-unit" onchange="toggleAddTaskSubScope()" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                            <option value="SARPRAS">SARPRAS (Perbaikan Fisik & Fasilitas)</option>
                            <option value="IT">IT (Infrastruktur, Server & AV)</option>
                            <option value="OB">Office Boy (Kebersihan & Sanitasi)</option>
                            <option value="GARDENER">Gardener (Taman & Lingkungan)</option>
                            <option value="SECURITY">Security (Keamanan & Pos Jaga)</option>
                            <option value="PENGADAAN">PENGADAAN (Logistik & Pembelian)</option>
                        </select>
                    </div>
                    <div id="add-task-subscope-box" class="hidden">
                        <label class="block font-semibold text-slate-700 mb-1">Sub-Lingkup Gardener</label>
                        <select name="sub_scope" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-semibold text-slate-700">
                            <option value="TAMAN_ECOPARK">Taman, Ecopark, Area Luar & Buah</option>
                            <option value="SAYURAN_TERNAK">Sayuran & Ternak Edukasi</option>
                        </select>
                    </div>
                    <div id="add-task-prio-box">
                        <label class="block font-semibold text-slate-700 mb-1">Tingkat Prioritas</label>
                        <select name="priority" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-semibold text-slate-700">
                            <option value="Sedang">Sedang</option>
                            <option value="Tinggi">Tinggi (Darurat / Mendesak)</option>
                            <option value="Rendah">Rendah (Rutin)</option>
                        </select>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Kategori Pekerjaan *</label>
                        <input type="text" name="category" placeholder="Misal: Sanitasi / Jaringan / Perawatan" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-medium" required>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Target Selesai (SLA)</label>
                        <input type="date" name="due_date" value="{{ today_date }}" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-medium">
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Judul Tugas / Instruksi Kerja *</label>
                    <input type="text" name="title" placeholder="Misal: Perbaikan kran bocor kolam renang / Servis AC ruang guru" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-bold text-slate-800" required>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Deskripsi / Detail Penugasan</label>
                    <textarea name="description" rows="3" placeholder="Tuliskan lokasi rinci, alat yang dibutuhkan, dan instruksi khusus..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700"></textarea>
                </div>

                <div class="flex items-center space-x-2 pt-1 bg-emerald-50/50 p-2.5 rounded-xl border border-emerald-100">
                    <input type="checkbox" id="add-task-send-wa" name="send_wa" checked class="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500">
                    <label for="add-task-send-wa" class="text-[11px] font-bold text-emerald-900 cursor-pointer">
                        <i class="fa-brands fa-whatsapp text-emerald-600 mr-1"></i>
                        Kirim notifikasi pendelegasian langsung ke WhatsApp Koordinator Unit
                    </label>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-add-task')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-add-task" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-paper-plane"></i>
                        <span>Disposisikan Tugas</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Convert Kebersihan to Task -->
    <div id="modal-convert-kebersihan-task" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50 overflow-y-auto">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 my-8">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-clipboard-check text-purple-600"></i>
                    Disposisi Laporan Kebersihan ke Tiket
                </h3>
                <button type="button" onclick="toggleModal('modal-convert-kebersihan-task')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>
            
            <!-- Ringkasan Temuan Lapangan -->
            <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1 text-xs">
                <div class="flex items-center justify-between text-slate-600">
                    <span><i class="fa-solid fa-user mr-1 text-slate-400"></i>Pelapor: <b id="convert-pelapor" class="text-slate-800">-</b></span>
                    <span id="convert-unit-asal" class="px-2 py-0.5 bg-slate-200 text-slate-700 rounded font-bold text-[10px]">OB</span>
                </div>
                <p class="text-slate-700"><b>Area:</b> <span id="convert-area">-</span></p>
                <p class="text-slate-600 italic">" <span id="convert-keterangan">-</span> "</p>
            </div>

            <form id="form-convert-kebersihan" onsubmit="submitConvertKebersihan(event)" class="space-y-3 text-xs">
                <input type="hidden" id="convert-hidden-pelapor" name="pelapor_nama">
                <input type="hidden" id="convert-hidden-area" name="area">
                <input type="hidden" id="convert-hidden-keterangan" name="keterangan">

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Unit Penanggung Jawab *</label>
                        <select id="convert-unit-code" name="unit_code" onchange="toggleConvertSubScope()" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-bold text-slate-800 focus:ring-2 focus:ring-emerald-500 focus:outline-none" required>
                            <option value="SARPRAS">SARPRAS (Perbaikan Fisik & Fasilitas)</option>
                            <option value="OB" selected>Office Boy (Kebersihan / Sanitasi)</option>
                            <option value="IT">IT (Infrastruktur / Perangkat)</option>
                            <option value="GARDENER">Gardener (Taman & Lingkungan)</option>
                            <option value="SECURITY">Security (Keamanan & Pos)</option>
                            <option value="PENGADAAN">PENGADAAN (Material / Pembelian)</option>
                        </select>
                    </div>
                    <div id="convert-subscope-container" class="hidden">
                        <label class="block font-semibold text-slate-700 mb-1">Sub-Lingkup Gardener</label>
                        <select id="convert-subscope" name="sub_scope" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-semibold text-slate-700">
                            <option value="TAMAN_ECOPARK">Taman, Ecopark, Area Luar & Buah</option>
                            <option value="SAYURAN_TERNAK">Sayuran & Ternak Edukasi</option>
                        </select>
                    </div>
                    <div id="convert-priority-container">
                        <label class="block font-semibold text-slate-700 mb-1">Tingkat Prioritas *</label>
                        <select name="priority" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-semibold text-slate-700">
                            <option value="Tinggi">Tinggi (Darurat / Mengganggu KBM)</option>
                            <option value="Sedang" selected>Sedang (Harus Selesai Hari Ini)</option>
                            <option value="Rendah">Rendah (Pekerjaan Rutin)</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Target Selesai (SLA)</label>
                    <input type="date" name="due_date" value="{{ today_date }}" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl font-medium">
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Instruksi Tambahan untuk Koordinator</label>
                    <textarea name="instructions" rows="3" placeholder="Contoh: Segera bawa peralatan pipa, pastikan air dimatikan dulu sebelum dibongkar..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700"></textarea>
                </div>

                <div class="flex items-center space-x-2 pt-1 bg-emerald-50/50 p-2.5 rounded-xl border border-emerald-100">
                    <input type="checkbox" id="convert-send-wa" name="send_wa" checked class="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500">
                    <label for="convert-send-wa" class="text-[11px] font-bold text-emerald-900 cursor-pointer">
                        <i class="fa-brands fa-whatsapp text-emerald-600 mr-1"></i>
                        Kirim notifikasi tugas langsung ke WhatsApp Koordinator Unit
                    </label>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-convert-kebersihan-task')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-convert" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-paper-plane"></i>
                        <span>Disposisikan & Buat Tiket</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Set Link Foto Drive Kebersihan -->
    <div id="modal-set-kebersihan-photo" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 border border-slate-100">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-brands fa-google-drive text-blue-600"></i>
                    <span>Tautkan Link Foto Google Drive</span>
                </h3>
                <button type="button" onclick="toggleModal('modal-set-kebersihan-photo')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-base"></i>
                </button>
            </div>
            <form id="form-set-kebersihan-photo" onsubmit="submitSetPhoto(event)" class="space-y-3 text-xs">
                <input type="hidden" id="set-photo-timestamp">
                <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 space-y-1">
                    <div>
                        <span class="text-slate-500">Petugas:</span>
                        <strong id="set-photo-nama" class="text-slate-800 ml-1"></strong>
                    </div>
                    <div>
                        <span class="text-slate-500">Area:</span>
                        <strong id="set-photo-area" class="text-slate-800 ml-1"></strong>
                    </div>
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">URL Foto Google Drive:</label>
                    <input type="url" id="set-photo-url" required placeholder="https://drive.google.com/file/d/.../view" class="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-xs font-mono">
                    <p class="text-[11px] text-slate-400 mt-1">Masukkan URL file foto Google Drive dari hasil share atau Google Sheet.</p>
                </div>
                <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-set-kebersihan-photo')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-set-photo" class="px-4 py-2 text-xs font-semibold bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition flex items-center gap-1.5 shadow-xs">
                        <i class="fa-solid fa-save"></i> <span>Simpan Link</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Update Task Status & Progress Notes -->
    <div id="modal-update-ops-task" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-pen-to-square text-emerald-600"></i>
                    Update Progres Tiket
                </h3>
                <button type="button" onclick="toggleModal('modal-update-ops-task')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>

            <form id="form-update-task" onsubmit="submitUpdateOpsTask(event)" class="space-y-3 text-xs">
                <input type="hidden" id="update-task-id" name="task_id">

                <div>
                    <span class="block text-[11px] text-slate-500 font-semibold mb-0.5">Judul Pekerjaan:</span>
                    <p id="update-task-title" class="font-bold text-slate-800 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">-</p>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Status Pengerjaan *</label>
                    <div class="grid grid-cols-3 gap-2">
                        <label class="cursor-pointer">
                            <input type="radio" name="status" value="Pending" id="status-pending" class="peer sr-only">
                            <div class="p-2.5 text-center rounded-xl border border-slate-200 peer-checked:border-amber-500 peer-checked:bg-amber-50 peer-checked:text-amber-800 font-bold text-xs transition">
                                <i class="fa-solid fa-hourglass-start block mb-1"></i> Pending
                            </div>
                        </label>
                        <label class="cursor-pointer">
                            <input type="radio" name="status" value="Proses" id="status-proses" class="peer sr-only">
                            <div class="p-2.5 text-center rounded-xl border border-slate-200 peer-checked:border-blue-500 peer-checked:bg-blue-50 peer-checked:text-blue-800 font-bold text-xs transition">
                                <i class="fa-solid fa-spinner block mb-1 animate-spin"></i> Proses
                            </div>
                        </label>
                        <label class="cursor-pointer">
                            <input type="radio" name="status" value="Selesai" id="status-selesai" class="peer sr-only">
                            <div class="p-2.5 text-center rounded-xl border border-slate-200 peer-checked:border-emerald-500 peer-checked:bg-emerald-50 peer-checked:text-emerald-800 font-bold text-xs transition">
                                <i class="fa-solid fa-check block mb-1"></i> Selesai
                            </div>
                        </label>
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan Progres / Hasil Lapangan</label>
                    <textarea id="update-task-notes" name="progress_notes" rows="3" placeholder="Contoh: Sudah diganti kran baru ukuran 1/2 inch, air mengalir normal..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700"></textarea>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-update-ops-task')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-update-task" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-floppy-disk"></i>
                        <span>Simpan Perubahan</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Supervisor Feedback -->
    <div id="modal-supervisor-feedback" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-comment-dots text-emerald-600"></i>
                    Catatan Supervisi Pimpinan
                </h3>
                <button type="button" onclick="toggleModal('modal-supervisor-feedback')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>

            <form id="form-supervisor-feedback" onsubmit="submitSupervisorFeedback(event)" class="space-y-3 text-xs">
                <input type="hidden" id="feedback-journal-id" name="journal_id">

                <div>
                    <span class="block text-[11px] text-slate-500 font-semibold mb-0.5">Jurnal Kegiatan:</span>
                    <p id="feedback-journal-title" class="font-bold text-slate-800 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">-</p>
                    <span id="feedback-journal-author" class="text-[10px] text-slate-400 block mt-1">Oleh: -</span>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan Supervisi / Evaluasi / Apresiasi *</label>
                    <textarea id="feedback-text" name="feedback" rows="4" placeholder="Tuliskan arahan, tindak lanjut, atau apresiasi atas kinerja yang dilaporkan..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700" required></textarea>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-supervisor-feedback')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-feedback" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-check"></i>
                        <span>Simpan Catatan Supervisi</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Add Pengadaan -->
    <div id="modal-add-pengadaan" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-cart-plus text-amber-600"></i>
                    Ajukan Pengadaan Barang / Suku Cadang
                </h3>
                <button type="button" onclick="toggleModal('modal-add-pengadaan')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>

            <form id="form-add-pengadaan" onsubmit="submitCreatePengadaan(event)" class="space-y-3 text-xs">
                <input type="hidden" id="add-proc-ticket-ref" name="ticket_ref">

                <div id="add-proc-ticket-banner" class="hidden bg-blue-50 border border-blue-200 text-blue-800 p-2.5 rounded-xl flex items-center justify-between">
                    <div>
                        <span class="font-bold block text-[11px]"><i class="fa-solid fa-link mr-1"></i>Terhubung dengan Tiket:</span>
                        <span id="add-proc-ticket-label" class="font-mono text-[11px] font-bold"></span>
                    </div>
                    <button type="button" onclick="clearTicketRefPengadaan()" class="text-xs text-blue-500 hover:text-blue-700 underline font-semibold">Lepas Kaitan</button>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nama Barang / Material / Suku Cadang *</label>
                    <input type="text" id="add-proc-title" name="title" placeholder="Misal: Kran Shower 1/2 inch Stainless & Pipa PVC 2 Batang" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700 font-semibold" required>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Kuantitas / Satuan *</label>
                        <input type="text" id="add-proc-quantity" name="quantity" placeholder="Contoh: 2 Unit / 5 Pcs / 1 Roll" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700" required>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Kategori Pengadaan</label>
                        <select name="category" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700">
                            <option value="Material Sarpras">Material Sarpras / Perbaikan</option>
                            <option value="Elektronik/IT">Elektronik & Jaringan IT</option>
                            <option value="Sanitasi/Kebersihan">Sanitasi & Kimia Kebersihan</option>
                            <option value="Taman & Pakan Ternak">Taman, Sayuran & Pakan Ternak</option>
                            <option value="Perlengkapan Security">Perlengkapan Security</option>
                            <option value="ATK & Operasional">ATK & Operasional Kantor</option>
                        </select>
                    </div>
                </div>

                <div class="grid grid-cols-3 gap-2">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Unit Pemohon *</label>
                        {% if user_role in ['manager', 'pic_pengadaan'] %}
                        <select id="add-proc-unit" name="unit_code" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700">
                            <option value="SARPRAS">SARPRAS</option>
                            <option value="IT">IT</option>
                            <option value="OB">Office Boy</option>
                            <option value="GARDENER">Gardener</option>
                            <option value="SECURITY">Security</option>
                            <option value="Umum">Umum</option>
                        </select>
                        {% else %}
                        <input type="text" name="unit_code" value="{{ user_unit }}" readonly class="w-full p-2.5 bg-slate-100 border border-slate-200 rounded-xl text-slate-700 font-bold cursor-not-allowed">
                        {% endif %}
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Est. Biaya (Rp)</label>
                        <input type="number" id="add-proc-cost" name="estimated_cost" placeholder="Rp" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700 font-mono">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Urgensi</label>
                        <select name="urgency" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700">
                            <option value="Sedang">Sedang</option>
                            <option value="Tinggi">Tinggi (Mendesak)</option>
                            <option value="Rendah">Rendah</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan / Keterangan Kebutuhan</label>
                    <textarea id="add-proc-notes" name="notes" rows="2" placeholder="Jelaskan kebutuhan, lokasi pemasangan, atau spesifikasi barang..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700"></textarea>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-add-pengadaan')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-add-proc" class="px-5 py-2 text-xs font-bold bg-amber-600 text-white rounded-xl hover:bg-amber-700 transition shadow-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-paper-plane"></i>
                        <span>Kirim Pengajuan</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Approve Pengadaan (Manager) -->
    <div id="modal-approve-pengadaan" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-stamp text-emerald-600"></i>
                    Verifikasi Persetujuan Pengadaan
                </h3>
                <button type="button" onclick="toggleModal('modal-approve-pengadaan')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>

            <div class="space-y-3 text-xs">
                <input type="hidden" id="approve-proc-id">

                <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                    <div class="flex justify-between">
                        <span class="text-slate-400">No. Pengajuan:</span>
                        <span id="approve-proc-id-label" class="font-mono font-bold text-slate-800"></span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">Barang:</span>
                        <span id="approve-proc-title" class="font-bold text-slate-800 text-right"></span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">Pemohon:</span>
                        <span id="approve-proc-req" class="text-slate-700"></span>
                    </div>
                    <div class="flex justify-between border-t border-slate-200 pt-1 mt-1">
                        <span class="font-bold text-slate-600">Est. Biaya:</span>
                        <span id="approve-proc-cost" class="font-bold text-emerald-700 text-sm"></span>
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan / Arahan Pimpinan</label>
                    <textarea id="approve-proc-note" rows="3" placeholder="Contoh: Disetujui, utamakan merk standar mutu atau cari toko terdekat..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700"></textarea>
                </div>

                <div class="flex justify-between pt-3 border-t border-slate-100">
                    <button type="button" onclick="submitApprovePengadaan('reject')" class="px-4 py-2 text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl transition flex items-center gap-1">
                        <i class="fa-solid fa-ban"></i> Tolak
                    </button>
                    <div class="flex items-center gap-2">
                        <button type="button" onclick="toggleModal('modal-approve-pengadaan')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                        <button type="button" onclick="submitApprovePengadaan('approve')" class="px-5 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition shadow-xs flex items-center gap-1.5">
                            <i class="fa-solid fa-check"></i> Setujui Pengadaan
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Update Pengadaan (PIC Pengadaan / Manager) -->
    <div id="modal-update-pengadaan" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-pen-to-square text-blue-600"></i>
                    Update Status & Nota Pengadaan
                </h3>
                <button type="button" onclick="toggleModal('modal-update-pengadaan')" class="text-slate-400 hover:text-slate-600">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>

            <form id="form-update-pengadaan" onsubmit="submitUpdatePengadaan(event)" class="space-y-3 text-xs">
                <input type="hidden" id="update-proc-id" name="proc_id">

                <div class="p-3 bg-blue-50/60 border border-blue-100 rounded-xl">
                    <span class="block text-[11px] text-blue-800 font-bold" id="update-proc-title">-</span>
                    <span class="text-[10px] text-blue-600 block mt-0.5">Est. Biaya: <b id="update-proc-est-cost">Rp 0</b></span>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Status Pengerjaan Pengadaan *</label>
                    <div class="grid grid-cols-3 gap-2">
                        <label class="p-2 border rounded-xl flex items-center gap-2 cursor-pointer has-[:checked]:bg-indigo-50 has-[:checked]:border-indigo-500 has-[:checked]:text-indigo-900">
                            <input type="radio" name="status" id="proc-status-proses" value="Proses Beli" class="text-indigo-600">
                            <span class="font-bold text-[11px]">Proses Beli</span>
                        </label>
                        <label class="p-2 border rounded-xl flex items-center gap-2 cursor-pointer has-[:checked]:bg-blue-50 has-[:checked]:border-blue-500 has-[:checked]:text-blue-900">
                            <input type="radio" name="status" id="proc-status-tiba" value="Barang Tiba" class="text-blue-600">
                            <span class="font-bold text-[11px]">Barang Tiba</span>
                        </label>
                        <label class="p-2 border rounded-xl flex items-center gap-2 cursor-pointer has-[:checked]:bg-emerald-50 has-[:checked]:border-emerald-500 has-[:checked]:text-emerald-900">
                            <input type="radio" name="status" id="proc-status-selesai" value="Diserahkan" class="text-emerald-600">
                            <span class="font-bold text-[11px]">Diserahkan</span>
                        </label>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Realisasi Biaya (Rp)</label>
                        <input type="number" id="update-proc-act-cost" name="actual_cost" placeholder="Sesuai nota" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700 font-mono font-bold">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">No. Nota / Kwitansi</label>
                        <input type="text" id="update-proc-receipt" name="receipt_no" placeholder="No bon/nota" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700 font-mono">
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nama Toko / Vendor Pembelian</label>
                    <input type="text" id="update-proc-vendor" name="vendor_info" placeholder="Misal: TB Sumber Makmur / Toko Listrik Terang" class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700">
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan Serah Terima / Keterangan</label>
                    <textarea id="update-proc-notes" name="notes" rows="2" placeholder="Barang diserahkan ke teknisi / kondisi barang..." class="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-slate-700"></textarea>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-update-pengadaan')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition">Batal</button>
                    <button type="submit" id="btn-submit-update-proc" class="px-5 py-2 text-xs font-bold bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition shadow-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-floppy-disk"></i>
                        <span>Simpan Perubahan</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL TAMBAH / EDIT TITIK POS STANDBY -->
    <div id="modal-create-standby-point" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center border-b border-slate-100 pb-3">
                <h3 id="modal-standby-title" class="font-bold text-sm text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-map-location-dot text-emerald-600"></i>
                    <span>Tambah Titik Pos Standby Baru</span>
                </h3>
                <button type="button" onclick="toggleModal('modal-create-standby-point')" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
            </div>

            <form id="form-standby-point" onsubmit="saveStandbyPoint(event)" class="space-y-3.5 text-xs">
                <input type="hidden" id="standby-point-id" value="">

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Kode Pos (Unik) *</label>
                        <input type="text" id="standby-point-code" required placeholder="POS-OB-SD03" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono font-bold uppercase focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Unit Kerja *</label>
                        <select id="standby-point-unit" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-emerald-500">
                            <option value="OB">Office Boy (OB)</option>
                            <option value="GARDENER">Gardener (Taman/Ecopark)</option>
                            <option value="SECURITY">Security (Keamanan)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Status Pos *</label>
                        <select id="standby-point-active" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-emerald-500">
                            <option value="1">Aktif (Radar)</option>
                            <option value="0">Non-Aktif (Arsip)</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nama Titik Pos Standby *</label>
                    <input type="text" id="standby-point-name" required placeholder="Contoh: Gedung SD Lantai 3 & Laboratorium" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-emerald-500">
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Deskripsi / Sub-Lingkup Area</label>
                    <input type="text" id="standby-point-subscope" placeholder="Misal: Koridor Kelas 5-6 & Ruang Lab Komputer" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:bg-white focus:outline-none focus:border-emerald-500">
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Latitude GPS *</label>
                        <input type="number" step="any" id="standby-point-lat" required placeholder="-6.347800" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Longitude GPS *</label>
                        <input type="number" step="any" id="standby-point-lon" required placeholder="106.964600" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                </div>

                <div class="flex items-center justify-between bg-sky-50 p-2 rounded-xl border border-sky-100 text-[11px] text-sky-800">
                    <span>Gunakan titik koordinat saat ini:</span>
                    <button type="button" onclick="fillCurrentLocationToPointForm()" class="px-2.5 py-1 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-lg transition flex items-center gap-1">
                        <i class="fa-solid fa-crosshairs"></i> Ambil GPS HP Saya
                    </button>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Toleransi Radius Geofence (Meter) *</label>
                        <input type="number" id="standby-point-radius" required value="35" min="10" max="200" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-emerald-500">
                        <span class="text-[10px] text-slate-400">Default: 35m (Gedung) / 50-60m (Outdoor)</span>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Menit Pengingat (T-X Menit) *</label>
                        <input type="number" id="standby-point-nudge" required value="5" min="1" max="30" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-emerald-500">
                        <span class="text-[10px] text-slate-400">Waktu broadcast sebelum cut-off</span>
                    </div>
                </div>

                <div class="border-t border-slate-100 pt-2 grid grid-cols-2 gap-3">
                    <div class="space-y-1">
                        <span class="font-bold text-slate-700 block text-[11px] uppercase">Jadwal Sesi Pagi</span>
                        <div class="grid grid-cols-2 gap-1.5">
                            <div>
                                <span class="text-[9px] text-slate-400 block">Mulai</span>
                                <input type="time" id="standby-point-morning-start" value="09:45" class="w-full p-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold">
                            </div>
                            <div>
                                <span class="text-[9px] text-slate-400 block font-bold text-rose-600">Cut-off *</span>
                                <input type="time" id="standby-point-morning-cutoff" value="10:00" required class="w-full p-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-rose-600">
                            </div>
                        </div>
                    </div>
                    <div class="space-y-1">
                        <span class="font-bold text-slate-700 block text-[11px] uppercase">Jadwal Sesi Siang</span>
                        <div class="grid grid-cols-2 gap-1.5">
                            <div>
                                <span class="text-[9px] text-slate-400 block">Mulai</span>
                                <input type="time" id="standby-point-noon-start" value="12:45" class="w-full p-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold">
                            </div>
                            <div>
                                <span class="text-[9px] text-slate-400 block font-bold text-rose-600">Cut-off *</span>
                                <input type="time" id="standby-point-noon-cutoff" value="13:00" required class="w-full p-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-rose-600">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="border-t border-slate-100 pt-2 space-y-2">
                    <span class="font-bold text-slate-700 block text-[11px] uppercase">Target Notifikasi & Eskalasi Pos Kosong</span>
                    <div>
                        <label class="block text-[11px] text-slate-600 font-semibold mb-0.5">No. WhatsApp Pribadi Koordinator</label>
                        <input type="tel" id="standby-point-personal-wa" placeholder="Contoh: 6289516458570" class="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800">
                    </div>
                    <div>
                        <label class="block text-[11px] text-slate-600 font-semibold mb-0.5">JID Group WhatsApp Unit</label>
                        <input type="text" id="standby-point-group-jid" placeholder="Contoh: 120363133177081285@g.us" class="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono text-[11px]">
                    </div>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-create-standby-point')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-standby-point" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-floppy-disk"></i>
                        <span>Simpan Titik Pos</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL PENUGASAN PERSONEL POS STANDBY -->
    <div id="modal-assign-standby" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex justify-between items-center border-b border-slate-100 pb-3">
                <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-user-plus text-sky-600"></i>
                    <span>Tugaskan Personel ke Titik Pos</span>
                </h3>
                <button type="button" onclick="toggleModal('modal-assign-standby')" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
            </div>

            <form id="form-assign-standby" onsubmit="saveStandbyAssignment(event)" class="space-y-3.5 text-xs">
                <input type="hidden" id="assign-point-id" value="">

                <div>
                    <span class="text-[10px] text-slate-400 uppercase font-bold block">Titik Pos Terpilih:</span>
                    <p id="assign-point-display" class="font-bold text-slate-800 text-sm mt-0.5">-</p>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nama Lengkap Personel *</label>
                    <input type="text" id="assign-petugas-name" required placeholder="Contoh: Kusmawan" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-emerald-500">
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nomor WhatsApp Personel *</label>
                    <input type="tel" id="assign-petugas-wa" required placeholder="Contoh: 081220795285 atau 6281220795285" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono focus:bg-white focus:outline-none focus:border-emerald-500">
                    <span class="text-[10px] text-slate-400">Digunakan untuk pencocokan otomatis saat lapor via WhatsApp.</span>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Unit Kerja *</label>
                    <select id="assign-unit-code" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-emerald-500">
                        <option value="OB">Office Boy (OB)</option>
                        <option value="GARDENER">Gardener (Taman & Ecopark)</option>
                        <option value="SECURITY">Security (Keamanan)</option>
                    </select>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-assign-standby')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-assign" class="px-5 py-2 text-xs font-bold bg-sky-600 text-white rounded-xl hover:bg-sky-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-user-check"></i>
                        <span>Simpan Penugasan</span>
                    </button>
                </div>
            </form>
        </div>
    </div>


    <!-- MODAL TAMBAH / EDIT ZONA PEMELIHARAAN -->
    <div id="modal-create-checklist-zone" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center border-b border-slate-100 pb-3">
                <h3 id="modal-chk-zone-title" class="font-bold text-sm text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-plus-circle text-emerald-600"></i>
                    <span>Tambah Titik Zona Pemeliharaan</span>
                </h3>
                <button type="button" onclick="toggleModal('modal-create-checklist-zone')" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
            </div>

            <form id="form-checklist-zone" onsubmit="saveChecklistZone(event)" class="space-y-3.5 text-xs">
                <input type="hidden" id="chk-zone-original-id" value="">

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">ID Titik Zona *</label>
                        <input type="text" id="chk-zone-id" required placeholder="ZONE-OB-TOILET-SD4" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono font-bold uppercase focus:bg-white focus:outline-none focus:border-emerald-500">
                        <span id="chk-zone-id-hint" class="text-[10px] text-slate-400 hidden">ID unik tidak dapat diubah saat edit</span>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Unit Kerja *</label>
                        <select id="chk-zone-unit" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-emerald-500">
                            <option value="OB">Office Boy (OB / Indoor)</option>
                            <option value="GARDENER">Gardener (Taman / Ecopark)</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nama Zona Pemeliharaan *</label>
                    <input type="text" id="chk-zone-name" required placeholder="Contoh: Toilet Siswa Gedung SD Lt 4" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-emerald-500">
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Gedung / Sektor *</label>
                        <input type="text" id="chk-zone-building" required placeholder="Gedung SD / Ecopark" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Sub-Lingkup *</label>
                        <select id="chk-zone-subscope" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:outline-none focus:border-emerald-500">
                            <option value="INDOOR_SANITASI">Indoor Sanitasi & Toilet</option>
                            <option value="TAMAN_LANSKAP">Taman & Lanskap Luar</option>
                            <option value="AGRO_TERNAK">Agro Sayur & Ecopark Ternak</option>
                        </select>
                    </div>
                </div>

                <div class="grid grid-cols-3 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Latitude *</label>
                        <input type="number" step="any" id="chk-zone-lat" value="-6.339295" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono text-xs focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Longitude *</label>
                        <input type="number" step="any" id="chk-zone-lng" value="106.964365" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-mono text-xs focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Radius (meter) *</label>
                        <input type="number" id="chk-zone-radius" value="45" min="10" max="150" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold text-xs focus:bg-white focus:outline-none focus:border-emerald-500">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3 pt-1">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Status Keaktifan *</label>
                        <select id="chk-zone-active" class="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-emerald-500">
                            <option value="1">Aktif (Muncul di Checklist & Radar)</option>
                            <option value="0">Non-Aktif (Diarsipkan)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Bantuan Titik Koordinat</label>
                        <button type="button" onclick="fillCurrentGpsToChecklistZone()" class="w-full p-2 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 font-semibold rounded-xl flex items-center justify-center gap-1.5 transition text-xs cursor-pointer">
                            <i class="fa-solid fa-crosshairs text-emerald-600"></i>
                            <span>Gunakan GPS Sekarang</span>
                        </button>
                    </div>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-create-checklist-zone')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-chk-zone" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-floppy-disk"></i>
                        <span id="btn-save-chk-zone-text">Simpan Titik Zona</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL TAMBAH / EDIT BUTIR CHECKLIST DINAMIS -->
    <div id="modal-manage-checklist-template" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center border-b border-slate-100 pb-3">
                <h3 id="modal-chk-tpl-title" class="font-bold text-sm text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-list-check text-teal-600"></i>
                    <span>Tambah Butir Checklist Baru</span>
                </h3>
                <button type="button" onclick="toggleModal('modal-manage-checklist-template')" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
            </div>

            <form id="form-checklist-template" onsubmit="saveChecklistTemplate(event)" class="space-y-3.5 text-xs">
                <input type="hidden" id="chk-tpl-id" value="">

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Unit Kerja *</label>
                        <select id="chk-tpl-unit" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-teal-500">
                            <option value="OB">Office Boy (OB / Indoor)</option>
                            <option value="GARDENER">Gardener (Taman & Ecopark)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Sub-Lingkup Area *</label>
                        <select id="chk-tpl-subscope" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:outline-none focus:border-teal-500">
                            <option value="INDOOR_SANITASI">Indoor Sanitasi & Toilet</option>
                            <option value="TAMAN_LANSKAP">Taman & Lanskap Luar</option>
                            <option value="AGRO_TERNAK">Agro Sayur & Ecopark Ternak</option>
                        </select>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Shift Tugas *</label>
                        <select id="chk-tpl-shift" required class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-teal-500">
                            <option value="PAGI">Pagi (06:30 - 08:30)</option>
                            <option value="SIANG_1">Siang 1 (08:30 - 12:30)</option>
                            <option value="SIANG_2">Siang 2 (12:30 - 16:00)</option>
                            <option value="SORE">Sore (16:00 - 18:00)</option>
                            <option value="ALL_DAY">Sepanjang Hari (All Day)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Nomor Urutan Tampil</label>
                        <input type="number" id="chk-tpl-order" value="1" min="1" max="99" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-bold focus:bg-white focus:outline-none focus:border-teal-500" placeholder="Auto jika kosong">
                    </div>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Pertanyaan / Butir Checklist *</label>
                    <textarea id="chk-tpl-label" rows="2" required placeholder="Contoh: Kran wastafel/bak mengalir lancar & tidak bocor" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:outline-none focus:border-teal-500"></textarea>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Panduan / Petunjuk Inspeksi Lapangan (Help Text)</label>
                    <textarea id="chk-tpl-help" rows="2" placeholder="Contoh: Cek dinding bak & sambungan pipa fleksibel untuk mencegah air terbuang" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:bg-white focus:outline-none focus:border-teal-500"></textarea>
                </div>

                <div class="grid grid-cols-2 gap-3 pt-1">
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Klasifikasi Lingkungan *</label>
                        <select id="chk-tpl-eco" class="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-teal-500">
                            <option value="0">Standar Pemeliharaan</option>
                            <option value="1">🌱 Eco-Critical (Hemat Air/Energi/Kompos)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block font-semibold text-slate-700 mb-1">Status Keaktifan *</label>
                        <select id="chk-tpl-active" class="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold focus:bg-white focus:outline-none focus:border-teal-500">
                            <option value="1">Aktif (Tampil di Form Petugas)</option>
                            <option value="0">Non-Aktif (Diarsipkan)</option>
                        </select>
                    </div>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-manage-checklist-template')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-chk-tpl" class="px-5 py-2 text-xs font-bold bg-teal-600 text-white rounded-xl hover:bg-teal-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-floppy-disk"></i>
                        <span id="btn-save-chk-tpl-text">Simpan Butir Checklist</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL SELESAIKAN TIKET SARPRAS -->
    <div id="modal-resolve-checklist-ticket" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center hidden p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex justify-between items-center border-b border-slate-100 pb-3">
                <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-circle-check text-emerald-600"></i>
                    <span>Selesaikan Perbaikan Fasilitas</span>
                </h3>
                <button type="button" onclick="toggleModal('modal-resolve-checklist-ticket')" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
            </div>

            <form id="form-resolve-ticket" onsubmit="submitResolveTicket(event)" class="space-y-3.5 text-xs">
                <input type="hidden" id="resolve-ticket-id" value="">

                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="text-[10px] text-slate-400 uppercase font-bold">ID Tiket:</span>
                    <p id="resolve-ticket-display" class="font-mono font-bold text-slate-800 text-sm">-</p>
                    <p id="resolve-ticket-desc" class="text-slate-600 text-xs mt-1">-</p>
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Nama Teknisi Sarpras *</label>
                    <input type="text" id="resolve-tech-name" required value="{{ user_nama }}" class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-semibold">
                </div>

                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan Tindakan Perbaikan *</label>
                    <textarea id="resolve-notes" rows="2" required placeholder="Contoh: Kran diganti baru merk Onda, sambungan selang di-seal tape..."
                        class="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800"></textarea>
                </div>

                <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button type="button" onclick="toggleModal('modal-resolve-checklist-ticket')" class="px-4 py-2 text-xs font-semibold bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-submit-resolve" class="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-check-double"></i>
                        <span>Konfirmasi Selesai</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        const titles = {
            'tab-dashboard': 'Dashboard Utama',
            'tab-standby': 'Kesiagaan Pos & Standby Geotagging',
            'tab-checklist': 'Monitoring Checklist OB & Green Ops',
            'tab-kuma': 'Infrastructure Uptime Kuma Monitor & WA Alert',
            'tab-analytics': 'Grafik Analitik & Tren Kinerja Operasional',
            'tab-journal': 'Jurnal Kegiatan Harian Mr Slam',
            'tab-todo': 'Personal To-Do List Mr Slam',
            'tab-tasks': 'Tiket & Tugas Operasional',
            'tab-mutabaah': 'Log Mutabaah Yaumiyah (WhatsApp)',
            'tab-kebersihan': 'Log Laporan Kebersihan & Foto Drive',
            'tab-report': 'Report Builder - Cetak Laporan Operasional',
            'tab-server': 'Server',
            'tab-sapaais': 'LaporPak (Sapa Ais) — Tiket WhatsApp',
            'tab-mutubaah': 'Mutabaah Diri Civitas & Pimpinan',
            'tab-users': 'Manajemen Pengguna & Koordinator Unit',
            'tab-roles': 'Manajemen Role & Hak Akses (RBAC Matrix)',
            'tab-pengadaan': 'Pengadaan Barang & Logistik Sarpras',
            'tab-pemeliharaan': 'Pemeliharaan Sarpras & Fasilitas (ISO FM-UMUM-AIS-03-02)',
            'tab-evaluasi': 'Rapor & Analisa Kedisiplinan Personil (OB & Gardener)',
        };

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const backdrop = document.getElementById('sidebar-backdrop');
            const mainContent = document.getElementById('main-content');

            const isMobile = window.innerWidth < 768;

            if (isMobile) {
                if (sidebar.classList.contains('-translate-x-full')) {
                    sidebar.classList.remove('-translate-x-full');
                    backdrop.classList.remove('hidden');
                } else {
                    sidebar.classList.add('-translate-x-full');
                    backdrop.classList.add('hidden');
                }
            } else {
                if (sidebar.classList.contains('md:translate-x-0')) {
                    sidebar.classList.remove('md:translate-x-0');
                    sidebar.classList.add('-translate-x-full');
                    mainContent.classList.remove('md:ml-64');
                    mainContent.classList.add('md:ml-0');
                } else {
                    sidebar.classList.add('md:translate-x-0');
                    sidebar.classList.remove('-translate-x-full');
                    mainContent.classList.add('md:ml-64');
                    mainContent.classList.remove('md:ml-0');
                }
            }
        }

        function showTab(tabId) {
            const target = document.getElementById(tabId);
            if (!target) {
                console.warn("Tab target tidak ditemukan:", tabId);
                return;
            }

            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => {
                el.classList.remove('bg-emerald-600', 'text-white');
                el.classList.add('text-slate-400', 'hover:bg-slate-800', 'hover:text-white');
            });

            target.classList.remove('hidden');
            const activeBtn = document.getElementById('btn-' + tabId);
            if (activeBtn) {
                activeBtn.classList.remove('text-slate-400', 'hover:bg-slate-800', 'hover:text-white');
                activeBtn.classList.add('bg-emerald-600', 'text-white');
            }

            if (titles && titles[tabId]) {
                const titleEl = document.getElementById('page-title');
                if (titleEl) titleEl.innerText = titles[tabId];
            }

            // Auto-load Sapa Ais data when its tab is opened
            if (tabId === 'tab-sapaais') {
                loadSapaAis(1);
            }
            // Auto-load Mutabaah Diri Mr. Slam data when its tab is opened
            if (tabId === 'tab-mutubaah') {
                loadMutubaahData();
            }
            // Auto-load Ops Users data when its tab is opened
            if (tabId === 'tab-users') {
                loadOpsUsers();
            }
            // Auto-load Ops Roles data when its tab is opened
            if (tabId === 'tab-roles') {
                loadOpsRoles();
            }
            if (tabId === 'tab-kebersihan') {
                filterKebersihanTable();
            }
            if (tabId === 'tab-standby') {
                loadStandbyRadar();
            }
            if (tabId === 'tab-checklist') {
                loadChecklistDashboard();
            }
            if (tabId === 'tab-pemeliharaan') {
                loadPmData();
            }
            if (tabId === 'tab-evaluasi') {
                loadEvaluasiData();
            }

            if (window.innerWidth < 768) {
                const sidebar = document.getElementById('sidebar');
                const backdrop = document.getElementById('sidebar-backdrop');
                sidebar.classList.add('-translate-x-full');
                backdrop.classList.add('hidden');
            }
        }

        function toggleModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.classList.toggle('hidden');
        }

        // ============ SISTEM KESIAGAAN POS & STANDBY GEOTAGGING ============
        let currentStandbySession = 'PAGI';
        let cachedStandbyPoints = [];

        function switchStandbySession(sess) {
            currentStandbySession = sess;
            const btnPagi = document.getElementById('btn-sess-pagi');
            const btnSiang = document.getElementById('btn-sess-siang');
            if (sess === 'PAGI') {
                btnPagi.className = "px-3 py-1 rounded-md font-bold transition text-emerald-700 bg-emerald-50 cursor-pointer";
                btnSiang.className = "px-3 py-1 rounded-md font-bold transition text-slate-500 hover:text-slate-800 cursor-pointer";
            } else {
                btnSiang.className = "px-3 py-1 rounded-md font-bold transition text-emerald-700 bg-emerald-50 cursor-pointer";
                btnPagi.className = "px-3 py-1 rounded-md font-bold transition text-slate-500 hover:text-slate-800 cursor-pointer";
            }
            loadStandbyRadar();
        }

        function switchStandbySubView(view) {
            document.getElementById('standby-subview-radar').classList.add('hidden');
            document.getElementById('standby-subview-points').classList.add('hidden');
            document.getElementById('standby-subview-logs').classList.add('hidden');

            document.getElementById('btn-subview-radar').className = "px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-800 cursor-pointer";
            document.getElementById('btn-subview-points').className = "px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-800 cursor-pointer";
            document.getElementById('btn-subview-logs').className = "px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-800 cursor-pointer";

            if (view === 'radar') {
                document.getElementById('standby-subview-radar').classList.remove('hidden');
                document.getElementById('btn-subview-radar').className = "px-2.5 py-1 rounded-md font-semibold bg-white text-slate-800 shadow-2xs border border-slate-200 cursor-pointer";
                loadStandbyRadar();
            } else if (view === 'points') {
                document.getElementById('standby-subview-points').classList.remove('hidden');
                document.getElementById('btn-subview-points').className = "px-2.5 py-1 rounded-md font-semibold bg-white text-slate-800 shadow-2xs border border-slate-200 cursor-pointer";
                loadStandbyPoints();
            } else if (view === 'logs') {
                document.getElementById('standby-subview-logs').classList.remove('hidden');
                document.getElementById('btn-subview-logs').className = "px-2.5 py-1 rounded-md font-semibold bg-white text-slate-800 shadow-2xs border border-slate-200 cursor-pointer";
                loadStandbyLogs();
            }
        }

        function loadStandbyRadar() {
            const tbody = document.getElementById('standby-radar-tbody');
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat data kesiagaan pos...</td></tr>';

            const unit = document.getElementById('filter-standby-unit') ? document.getElementById('filter-standby-unit').value : 'ALL';
            const url = `/api/ops/standby/radar?session=${currentStandbySession}&unit=${encodeURIComponent(unit)}`;

            fetch(url)
                .then(r => r.json())
                .then(data => {
                    if (!data.success) throw new Error(data.error || 'Gagal memuat radar');
                    
                    const s = data.summary;
                    document.getElementById('stat-standby-total').innerText = s.total_points;
                    document.getElementById('stat-standby-ontime').innerText = s.standby_on_time;
                    document.getElementById('stat-standby-late').innerText = s.standby_late;
                    document.getElementById('stat-standby-empty').innerText = s.empty_points;

                    if (data.radar && data.radar.length > 0) {
                        data.radar.forEach(r => {
                            const idx = cachedStandbyPoints.findIndex(p => p.id === r.point.id);
                            if (idx >= 0) cachedStandbyPoints[idx] = r.point;
                            else cachedStandbyPoints.push(r.point);
                        });
                    }

                    if (data.radar.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-slate-400">Tidak ada pos terdaftar untuk filter ini.</td></tr>';
                        return;
                    }

                    let html = '';
                    data.radar.forEach(item => {
                        const p = item.point;
                        const log = item.latest_log;

                        let statusBadge = '';
                        if (item.badge_status === 'ON_TIME') {
                            statusBadge = `<span class="px-2.5 py-1 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded-full border border-emerald-300 inline-flex items-center gap-1">
                                <i class="fa-solid fa-circle-check"></i> Siaga On-Time
                            </span>`;
                        } else if (item.badge_status === 'LATE') {
                            statusBadge = `<span class="px-2.5 py-1 bg-amber-100 text-amber-800 text-[10px] font-bold rounded-full border border-amber-300 inline-flex items-center gap-1">
                                <i class="fa-solid fa-clock-rotate-left"></i> Terlambat
                            </span>`;
                        } else if (item.badge_status === 'OUT_OF_RANGE') {
                            statusBadge = `<span class="px-2.5 py-1 bg-rose-100 text-rose-800 text-[10px] font-bold rounded-full border border-rose-300 inline-flex items-center gap-1">
                                <i class="fa-solid fa-triangle-exclamation"></i> Di Luar Radius
                            </span>`;
                        } else {
                            statusBadge = `<span class="px-2.5 py-1 bg-rose-50 text-rose-700 text-[10px] font-bold rounded-full border border-rose-200 inline-flex items-center gap-1 animate-pulse">
                                <i class="fa-solid fa-circle-xmark"></i> Belum Siaga / Kosong
                            </span>`;
                        }

                        const unitColor = {
                            'OB': 'bg-teal-50 text-teal-700 border-teal-200',
                            'GARDENER': 'bg-amber-50 text-amber-700 border-amber-200',
                            'SECURITY': 'bg-indigo-50 text-indigo-700 border-indigo-200'
                        }[p.unit_code] || 'bg-slate-50 text-slate-700 border-slate-200';

                        const laporTime = log ? `<span class="font-bold text-slate-800">${log.checkin_time} WIB</span><span class="block text-[10px] text-slate-400 font-mono">${log.channel === 'WA_LOCATION' ? 'WhatsApp' : 'Scan QR'}</span>` : '<span class="text-slate-400 italic">Belum ada</span>';
                        const jarakInfo = log ? `<span class="font-bold ${log.distance_meters <= p.radius_meters ? 'text-emerald-700' : 'text-rose-600'}">${log.distance_meters}m</span> / max ${p.radius_meters}m` : `<span class="text-slate-400">Toleransi: ${p.radius_meters}m</span>`;

                        const safeName = (p.name || '').replace(/'/g, "\\'");

                        html += `
                        <tr class="hover:bg-slate-50/80 transition">
                            <td class="py-3 px-4">
                                <span class="font-bold text-slate-800 block">${p.name}</span>
                                <span class="text-[10px] text-slate-500 font-mono">${p.code} ${p.sub_scope ? '• ' + p.sub_scope : ''}</span>
                            </td>
                            <td class="py-3 px-4">
                                <span class="px-2 py-0.5 text-[10px] font-bold rounded border ${unitColor}">${p.unit_code}</span>
                            </td>
                            <td class="py-3 px-4 text-slate-700 font-medium">${item.assigned_names}</td>
                            <td class="py-3 px-4">
                                <span class="font-bold text-slate-800">${item.cutoff_time} WIB</span>
                            </td>
                            <td class="py-3 px-4">${laporTime}</td>
                            <td class="py-3 px-4">${jarakInfo}</td>
                            <td class="py-3 px-4">${statusBadge}</td>
                            <td class="py-3 px-4 text-center">
                                <div class="inline-flex items-center gap-1">
                                    <a href="/standby/c/${p.id}" target="_blank" title="Buka Halaman Check-in" class="p-1.5 text-slate-500 hover:text-emerald-600 rounded-lg hover:bg-emerald-50 transition">
                                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                                    </a>
                                    <a href="/standby/print-qr?point_id=${p.id}" target="_blank" title="Cetak Stiker Pos" class="p-1.5 text-slate-500 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition">
                                        <i class="fa-solid fa-qrcode"></i>
                                    </a>
                                    <button type="button" onclick="openModalEditStandbyPoint('${p.id}')" title="Edit Parameter Pos" class="p-1.5 text-slate-500 hover:text-amber-600 rounded-lg hover:bg-amber-50 transition cursor-pointer">
                                        <i class="fa-solid fa-pen-to-square"></i>
                                    </button>
                                    <button type="button" onclick="deleteStandbyPoint('${p.id}', '${safeName}')" title="Hapus Titik Pos" class="p-1.5 text-slate-500 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition cursor-pointer">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>`;
                    });
                    tbody.innerHTML = html;
                })
                .catch(err => {
                    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-rose-500 font-semibold">Gagal memuat radar: ${err.message}</td></tr>`;
                });
        }

        function loadStandbyPoints() {
            const tbody = document.getElementById('standby-points-tbody');
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-6 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat master pos...</td></tr>';

            fetch('/api/ops/standby/points')
                .then(r => r.json())
                .then(data => {
                    if (!data.success) throw new Error(data.error || 'Gagal memuat pos');
                    cachedStandbyPoints = data.points;

                    if (data.points.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-6 text-slate-400">Belum ada titik pos terdaftar.</td></tr>';
                        return;
                    }

                    let html = '';
                    data.points.forEach(p => {
                        const safeName = (p.name || '').replace(/'/g, "\\'");
                        const assignees = p.assignments && p.assignments.length > 0 
                            ? p.assignments.map(a => `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 rounded text-[10px] text-slate-700 mr-1 mb-1">${a.petugas_name} <button onclick="deleteStandbyAssignment(${a.id})" class="text-rose-500 hover:text-rose-700 font-bold">&times;</button></span>`).join('') 
                            : '<span class="text-slate-400 italic">Belum ada</span>';

                        const inactiveBadge = p.is_active === 0 ? '<span class="ml-1.5 px-1.5 py-0.5 bg-rose-100 text-rose-700 text-[9px] font-bold rounded">Non-Aktif</span>' : '';

                        html += `
                        <tr class="hover:bg-slate-50 transition ${p.is_active === 0 ? 'opacity-60 bg-slate-50/50' : ''}">
                            <td class="py-3 px-3">
                                <div class="flex items-center">
                                    <span class="font-bold text-slate-800">${p.name}</span>
                                    ${inactiveBadge}
                                </div>
                                <span class="text-[10px] text-emerald-700 font-mono font-semibold">${p.code} ${p.sub_scope ? '• ' + p.sub_scope : ''}</span>
                            </td>
                            <td class="py-3 px-3"><span class="px-2 py-0.5 bg-slate-100 rounded font-bold text-[10px] text-slate-700">${p.unit_code}</span></td>
                            <td class="py-3 px-3 font-mono text-[10px] text-slate-500">${p.latitude.toFixed(6)}, ${p.longitude.toFixed(6)}</td>
                            <td class="py-3 px-3 font-bold text-slate-700">${p.radius_meters}m</td>
                            <td class="py-3 px-3 font-medium text-slate-700">${p.morning_start} - <b class="text-rose-600">${p.morning_cutoff}</b></td>
                            <td class="py-3 px-3 font-medium text-slate-700">${p.noon_start} - <b class="text-rose-600">${p.noon_cutoff}</b></td>
                            <td class="py-3 px-3 text-[10px]">
                                <div>WA: <span class="font-mono text-slate-700 font-semibold">${p.target_personal_wa || '-'}</span></div>
                                <div class="truncate max-w-[120px] text-slate-400" title="${p.target_group_jid || ''}">G: ${p.target_group_jid ? p.target_group_jid.split('@')[0] : '-'}</div>
                            </td>
                            <td class="py-3 px-3">
                                <div>${assignees}</div>
                                <button type="button" onclick="openModalAssignStandby('${p.id}', '${safeName}', '${p.unit_code}')" class="text-[10px] text-sky-600 hover:text-sky-800 font-bold underline mt-1 block cursor-pointer">+ Tugaskan</button>
                            </td>
                            <td class="py-3 px-3 text-center">
                                <div class="inline-flex items-center gap-1">
                                    <button type="button" onclick="openModalEditStandbyPoint('${p.id}')" title="Edit Pos" class="p-1.5 text-slate-500 hover:text-amber-600 rounded hover:bg-amber-50 cursor-pointer">
                                        <i class="fa-solid fa-pen-to-square"></i>
                                    </button>
                                    <a href="/standby/print-qr?point_id=${p.id}" target="_blank" title="Cetak QR" class="p-1.5 text-slate-500 hover:text-indigo-600 rounded hover:bg-indigo-50">
                                        <i class="fa-solid fa-qrcode"></i>
                                    </a>
                                    <button type="button" onclick="deleteStandbyPoint('${p.id}', '${safeName}')" title="Hapus Pos" class="p-1.5 text-slate-500 hover:text-rose-600 rounded hover:bg-rose-50 cursor-pointer">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>`;
                    });
                    tbody.innerHTML = html;
                })
                .catch(err => {
                    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-6 text-rose-500 font-semibold">Gagal memuat titik pos: ${err.message}</td></tr>`;
                });
        }

        function loadStandbyLogs() {
            const tbody = document.getElementById('standby-logs-tbody');
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat riwayat log...</td></tr>';

            const dateInput = document.getElementById('filter-standby-log-date');
            if (dateInput && !dateInput.value) {
                const now = new Date();
                const y = now.getFullYear();
                const m = String(now.getMonth() + 1).padStart(2, '0');
                const d = String(now.getDate()).padStart(2, '0');
                dateInput.value = `${y}-${m}-${d}`;
            }

            const dateVal = dateInput ? dateInput.value : '';
            const statusVal = document.getElementById('filter-standby-log-status') ? document.getElementById('filter-standby-log-status').value : 'ALL';
            const url = `/api/ops/standby/logs?date=${encodeURIComponent(dateVal)}&status=${encodeURIComponent(statusVal)}`;

            fetch(url)
                .then(r => r.json())
                .then(data => {
                    if (!data.success) throw new Error(data.error || 'Gagal memuat log');
                    if (data.logs.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400">Belum ada transaksi check-in untuk tanggal ini.</td></tr>';
                        return;
                    }

                    let html = '';
                    data.logs.forEach(l => {
                        let stBadge = '';
                        if (l.status === 'TEPAT_WAKTU') {
                            stBadge = `<span class="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded">Tepat Waktu</span>`;
                        } else if (l.status === 'TERLAMBAT') {
                            stBadge = `<span class="px-2 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded">Terlambat (+${Math.abs(l.minutes_diff)}m)</span>`;
                        } else {
                            stBadge = `<span class="px-2 py-0.5 bg-rose-100 text-rose-800 text-[10px] font-bold rounded">Di Luar Radius</span>`;
                        }

                        html += `
                        <tr class="hover:bg-slate-50 transition">
                            <td class="py-3 px-3 font-mono font-bold text-slate-800">${l.checkin_time} WIB</td>
                            <td class="py-3 px-3"><span class="px-1.5 py-0.5 bg-slate-100 rounded text-[10px] font-semibold">${l.session_type}</span></td>
                            <td class="py-3 px-3">
                                <span class="font-bold text-slate-800 block">${l.point_name}</span>
                                <span class="text-[10px] font-mono text-slate-500">${l.point_code}</span>
                            </td>
                            <td class="py-3 px-3 font-semibold text-slate-800">${l.petugas_name}</td>
                            <td class="py-3 px-3 font-mono font-semibold ${l.distance_meters <= l.radius_allowed ? 'text-emerald-700' : 'text-rose-600'}">${l.distance_meters}m (max ${l.radius_allowed}m)</td>
                            <td class="py-3 px-3">${stBadge}</td>
                            <td class="py-3 px-3 text-[10px] text-slate-500 font-mono">${l.channel === 'WA_LOCATION' ? 'WhatsApp' : 'Scan QR Web'}</td>
                        </tr>`;
                    });
                    tbody.innerHTML = html;
                })
                .catch(err => {
                    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-rose-500 font-semibold">Gagal memuat log: ${err.message}</td></tr>`;
                });
        }

        function openModalCreateStandbyPoint() {
            document.getElementById('modal-standby-title').innerHTML = '<i class="fa-solid fa-map-location-dot text-emerald-600"></i><span>Tambah Titik Pos Standby Baru</span>';
            document.getElementById('standby-point-id').value = '';
            document.getElementById('standby-point-code').value = '';
            document.getElementById('standby-point-code').disabled = false;
            document.getElementById('standby-point-unit').value = 'OB';
            if (document.getElementById('standby-point-active')) {
                document.getElementById('standby-point-active').value = '1';
            }
            document.getElementById('standby-point-name').value = '';
            document.getElementById('standby-point-subscope').value = '';
            document.getElementById('standby-point-lat').value = '-6.347800';
            document.getElementById('standby-point-lon').value = '106.964600';
            document.getElementById('standby-point-radius').value = '35';
            document.getElementById('standby-point-nudge').value = '5';
            document.getElementById('standby-point-morning-start').value = '09:45';
            document.getElementById('standby-point-morning-cutoff').value = '10:00';
            document.getElementById('standby-point-noon-start').value = '12:45';
            document.getElementById('standby-point-noon-cutoff').value = '13:00';
            document.getElementById('standby-point-personal-wa').value = '';
            document.getElementById('standby-point-group-jid').value = '';
            toggleModal('modal-create-standby-point');
        }

        async function openModalEditStandbyPoint(pointId) {
            let p = cachedStandbyPoints.find(item => item.id === pointId);
            if (!p) {
                try {
                    const res = await fetch(`/api/ops/standby/points/${encodeURIComponent(pointId)}`);
                    const data = await res.json();
                    if (data.success && data.point) {
                        p = data.point;
                        cachedStandbyPoints.push(p);
                    }
                } catch (e) {
                    console.error("Gagal mengambil detail pos:", e);
                }
            }

            if (!p) {
                alert("Data titik pos tidak ditemukan!");
                return;
            }

            document.getElementById('modal-standby-title').innerHTML = '<i class="fa-solid fa-pen-to-square text-amber-600"></i><span>Edit Titik Pos Standby</span>';
            document.getElementById('standby-point-id').value = p.id;
            document.getElementById('standby-point-code').value = p.code;
            document.getElementById('standby-point-code').disabled = false;
            document.getElementById('standby-point-unit').value = p.unit_code;
            if (document.getElementById('standby-point-active')) {
                document.getElementById('standby-point-active').value = (p.is_active !== undefined) ? String(p.is_active) : '1';
            }
            document.getElementById('standby-point-name').value = p.name;
            document.getElementById('standby-point-subscope').value = p.sub_scope || '';
            document.getElementById('standby-point-lat').value = p.latitude;
            document.getElementById('standby-point-lon').value = p.longitude;
            document.getElementById('standby-point-radius').value = p.radius_meters;
            document.getElementById('standby-point-nudge').value = p.nudge_minutes;
            document.getElementById('standby-point-morning-start').value = p.morning_start;
            document.getElementById('standby-point-morning-cutoff').value = p.morning_cutoff;
            document.getElementById('standby-point-noon-start').value = p.noon_start;
            document.getElementById('standby-point-noon-cutoff').value = p.noon_cutoff;
            document.getElementById('standby-point-personal-wa').value = p.target_personal_wa || '';
            document.getElementById('standby-point-group-jid').value = p.target_group_jid || '';
            toggleModal('modal-create-standby-point');
        }

        function fillCurrentLocationToPointForm() {
            if (!navigator.geolocation) {
                alert("Browser tidak mendukung GPS.");
                return;
            }
            navigator.geolocation.getCurrentPosition(
                pos => {
                    document.getElementById('standby-point-lat').value = pos.coords.latitude.toFixed(6);
                    document.getElementById('standby-point-lon').value = pos.coords.longitude.toFixed(6);
                    alert(`Koordinat GPS berhasil diambil! Akurasi: ±${Math.round(pos.coords.accuracy)}m`);
                },
                err => alert("Gagal mengambil lokasi GPS: " + err.message),
                { enableHighAccuracy: true }
            );
        }

        async function saveStandbyPoint(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-save-standby-point');
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...`;

            const pointId = document.getElementById('standby-point-id').value;
            const payload = {
                code: document.getElementById('standby-point-code').value.trim().toUpperCase(),
                unit_code: document.getElementById('standby-point-unit').value,
                is_active: document.getElementById('standby-point-active') ? (document.getElementById('standby-point-active').value === '1') : true,
                name: document.getElementById('standby-point-name').value.trim(),
                sub_scope: document.getElementById('standby-point-subscope').value.trim(),
                latitude: parseFloat(document.getElementById('standby-point-lat').value),
                longitude: parseFloat(document.getElementById('standby-point-lon').value),
                radius_meters: parseInt(document.getElementById('standby-point-radius').value) || 35,
                nudge_minutes: parseInt(document.getElementById('standby-point-nudge').value) || 5,
                morning_start: document.getElementById('standby-point-morning-start').value,
                morning_cutoff: document.getElementById('standby-point-morning-cutoff').value,
                noon_start: document.getElementById('standby-point-noon-start').value,
                noon_cutoff: document.getElementById('standby-point-noon-cutoff').value,
                target_personal_wa: document.getElementById('standby-point-personal-wa').value.trim(),
                target_group_jid: document.getElementById('standby-point-group-jid').value.trim()
            };

            const url = pointId ? `/api/ops/standby/points/${encodeURIComponent(pointId)}/edit` : `/api/ops/standby/points/create`;

            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    alert(data.message || "Titik pos berhasil disimpan!");
                    toggleModal('modal-create-standby-point');
                    loadStandbyPoints();
                    loadStandbyRadar();
                } else {
                    alert("Gagal: " + (data.error || 'Terjadi kesalahan sistem'));
                }
            } catch (err) {
                alert("Koneksi gagal: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-floppy-disk"></i><span>Simpan Titik Pos</span>`;
            }
        }

        async function deleteStandbyPoint(pointId, pointName) {
            if (!confirm(`Apakah Anda yakin ingin menghapus titik pos "${pointName}"?\n\nPerhatian: Seluruh riwayat dan penugasan personel terkait titik pos ini akan ikut terhapus.`)) return;
            try {
                const res = await fetch(`/api/ops/standby/points/${encodeURIComponent(pointId)}/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.success) {
                    alert(data.message || "Titik pos berhasil dihapus!");
                    loadStandbyPoints();
                    loadStandbyRadar();
                } else {
                    alert("Gagal menghapus: " + (data.error || 'Terjadi kesalahan sistem'));
                }
            } catch (err) {
                alert("Koneksi gagal: " + err.message);
            }
        }

        function openModalAssignStandby(pointId, pointName, unitCode) {
            document.getElementById('assign-point-id').value = pointId;
            document.getElementById('assign-point-display').innerText = `${pointName} (${unitCode})`;
            document.getElementById('assign-unit-code').value = unitCode;
            document.getElementById('assign-petugas-name').value = '';
            document.getElementById('assign-petugas-wa').value = '';
            toggleModal('modal-assign-standby');
        }

        async function saveStandbyAssignment(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-save-assign');
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...`;

            const payload = {
                point_id: document.getElementById('assign-point-id').value,
                petugas_name: document.getElementById('assign-petugas-name').value.trim(),
                no_wa: document.getElementById('assign-petugas-wa').value.trim(),
                unit_code: document.getElementById('assign-unit-code').value
            };

            try {
                const res = await fetch('/api/ops/standby/assignments/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    alert(data.message);
                    toggleModal('modal-assign-standby');
                    loadStandbyPoints();
                    loadStandbyRadar();
                } else {
                    alert("Gagal: " + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert("Koneksi gagal: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-user-check"></i><span>Simpan Penugasan</span>`;
            }
        }

        async function deleteStandbyAssignment(assignId) {
            if (!confirm("Hapus penugasan personel ini dari titik pos?")) return;
            try {
                const res = await fetch(`/api/ops/standby/assignments/${assignId}/delete`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    loadStandbyPoints();
                    loadStandbyRadar();
                } else {
                    alert("Gagal: " + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert("Koneksi gagal: " + err.message);
            }
        }

        // ============ Ops User & Role Management ============
        function toggleSubScopeField(prefix) {
            const unit = document.getElementById(prefix + '-user-unit').value;
            const container = document.getElementById(prefix + '-user-subscope-container');
            if (unit === 'GARDENER') {
                container.classList.remove('hidden');
            } else {
                container.classList.add('hidden');
            }
        }

        let cachedOpsUsers = [];

        function loadOpsUsers() {
            const tbody = document.getElementById('ops-users-tbody');
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="7" class="p-6 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat pengguna...</td></tr>';
            
            fetch('/api/ops/users')
                .then(r => {
                    if (!r.ok) throw new Error('Gagal memuat pengguna');
                    return r.json();
                })
                .then(users => {
                    cachedOpsUsers = users;
                    const elTotal = document.getElementById('ops-stat-total-users');
                    if (elTotal) elTotal.innerText = users.length;
                    const activeCount = users.filter(u => u.is_active === 1).length;
                    const elActive = document.getElementById('ops-stat-active-users');
                    if (elActive) elActive.innerText = activeCount;

                    if (users.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" class="p-6 text-center text-slate-400">Belum ada user koordinator terdaftar.</td></tr>';
                        return;
                    }

                    let html = '';
                    users.forEach(u => {
                        const unitBadgeColor = {
                            'IT': 'bg-blue-100 text-blue-800 border-blue-200',
                            'OB': 'bg-teal-100 text-teal-800 border-teal-200',
                            'GARDENER': 'bg-amber-100 text-amber-800 border-amber-200',
                            'SECURITY': 'bg-indigo-100 text-indigo-800 border-indigo-200',
                            'ALL': 'bg-emerald-100 text-emerald-800 border-emerald-200'
                        }[u.unit_code] || 'bg-slate-100 text-slate-800 border-slate-200';

                        let subScopeHtml = '';
                        if (u.sub_scope) {
                            const subText = u.sub_scope === 'TAMAN_ECOPARK' ? 'Taman/Ecopark' : (u.sub_scope === 'SAYURAN_TERNAK' ? 'Sayuran & Ternak' : 'Semua Sub-Lingkup');
                            subScopeHtml = `<span class="block text-[10px] text-slate-500 mt-0.5"><i class="fa-solid fa-tag mr-1 text-slate-400"></i>${subText}</span>`;
                        }

                        const statusBadge = u.is_active === 1
                            ? `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800"><i class="fa-solid fa-check mr-1 text-[8px]"></i>Aktif</span>`
                            : `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-100 text-rose-800"><i class="fa-solid fa-xmark mr-1 text-[8px]"></i>Nonaktif</span>`;

                        const waLink = u.no_wa
                            ? `<a href="https://wa.me/${u.no_wa}" target="_blank" class="inline-flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 font-mono"><i class="fa-brands fa-whatsapp text-emerald-500"></i>${u.no_wa}</a>`
                            : `<span class="text-xs text-slate-400">-</span>`;

                        const lastLogin = u.last_login ? `<span class="text-xs text-slate-600">${u.last_login}</span>` : `<span class="text-xs text-slate-400 italic">Belum pernah</span>`;

                        html += `
                            <tr class="hover:bg-slate-50/80 transition">
                                <td class="p-3.5">
                                    <div class="flex items-center space-x-3">
                                        <div class="w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-xs shrink-0">
                                            ${(u.nama_lengkap || u.username).substring(0,2).toUpperCase()}
                                        </div>
                                        <div>
                                            <div class="font-bold text-xs text-slate-800">${u.nama_lengkap}</div>
                                            <div class="text-[11px] text-slate-400 font-mono">@${u.username}</div>
                                        </div>
                                    </div>
                                </td>
                                <td class="p-3.5">
                                    <span class="inline-block px-2.5 py-0.5 text-[11px] font-bold rounded-lg border ${unitBadgeColor}">${u.unit_code}</span>
                                    ${subScopeHtml}
                                </td>
                                <td class="p-3.5">
                                    <span class="text-xs font-medium text-slate-700">${u.role_name || u.role_code}</span>
                                </td>
                                <td class="p-3.5">${waLink}</td>
                                <td class="p-3.5">${statusBadge}</td>
                                <td class="p-3.5">${lastLogin}</td>
                                <td class="p-3.5 text-center">
                                    <div class="flex items-center justify-center space-x-1.5">
                                        <button onclick="openEditOpsUser(${u.id})" title="Edit User" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition">
                                            <i class="fa-solid fa-pen-to-square text-xs"></i>
                                        </button>
                                        <button onclick="openResetOpsPassword(${u.id}, '${u.username}')" title="Reset Password" class="p-1.5 text-amber-600 hover:bg-amber-50 rounded-lg transition">
                                            <i class="fa-solid fa-key text-xs"></i>
                                        </button>
                                        ${u.username !== 'admin' ? `
                                            <button onclick="toggleOpsUserStatus(${u.id})" title="${u.is_active === 1 ? 'Nonaktifkan' : 'Aktifkan'}" class="p-1.5 ${u.is_active === 1 ? 'text-rose-600 hover:bg-rose-50' : 'text-emerald-600 hover:bg-emerald-50'} rounded-lg transition">
                                                <i class="fa-solid ${u.is_active === 1 ? 'fa-user-slash' : 'fa-user-check'} text-xs"></i>
                                            </button>
                                        ` : ''}
                                    </div>
                                </td>
                            </tr>
                        `;
                    });
                    tbody.innerHTML = html;
                })
                .catch(err => {
                    tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-rose-500"><i class="fa-solid fa-triangle-exclamation mr-2"></i>Error: ${err.message}</td></tr>`;
                });
        }

        function submitAddOpsUser(e) {
            e.preventDefault();
            const payload = {
                username: document.getElementById('add-user-username').value.trim(),
                password: document.getElementById('add-user-password').value.trim(),
                nama_lengkap: document.getElementById('add-user-nama').value.trim(),
                unit_code: document.getElementById('add-user-unit').value,
                role_code: document.getElementById('add-user-role').value,
                sub_scope: document.getElementById('add-user-unit').value === 'GARDENER' ? document.getElementById('add-user-subscope').value : '',
                no_wa: document.getElementById('add-user-wa').value.trim()
            };

            fetch('/api/ops/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) {
                    alert('Gagal menambah user: ' + res.error);
                } else {
                    toggleModal('modal-add-ops-user');
                    loadOpsUsers();
                    e.target.reset();
                    alert('Koordinator baru berhasil didaftarkan!');
                }
            })
            .catch(err => alert('Terjadi kesalahan: ' + err.message));
        }

        function openEditOpsUser(userId) {
            const user = cachedOpsUsers.find(u => u.id === userId);
            if (!user) return;
            document.getElementById('edit-user-id').value = user.id;
            document.getElementById('edit-user-username').value = user.username;
            document.getElementById('edit-user-nama').value = user.nama_lengkap;
            document.getElementById('edit-user-unit').value = user.unit_code;
            document.getElementById('edit-user-role').value = user.role_code;
            document.getElementById('edit-user-wa').value = user.no_wa || '';
            toggleSubScopeField('edit');
            if (user.sub_scope) {
                document.getElementById('edit-user-subscope').value = user.sub_scope;
            }
            toggleModal('modal-edit-ops-user');
        }

        function submitEditOpsUser(e) {
            e.preventDefault();
            const userId = document.getElementById('edit-user-id').value;
            const payload = {
                nama_lengkap: document.getElementById('edit-user-nama').value.trim(),
                unit_code: document.getElementById('edit-user-unit').value,
                role_code: document.getElementById('edit-user-role').value,
                sub_scope: document.getElementById('edit-user-unit').value === 'GARDENER' ? document.getElementById('edit-user-subscope').value : '',
                no_wa: document.getElementById('edit-user-wa').value.trim()
            };

            fetch(`/api/ops/users/${userId}/edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) {
                    alert('Gagal memperbarui: ' + res.error);
                } else {
                    toggleModal('modal-edit-ops-user');
                    loadOpsUsers();
                    alert('Data user berhasil diperbarui!');
                }
            })
            .catch(err => alert('Terjadi kesalahan: ' + err.message));
        }

        function toggleOpsUserStatus(userId) {
            if (!confirm('Apakah Anda yakin ingin mengubah status aktif user ini?')) return;
            fetch(`/api/ops/users/${userId}/toggle-status`, { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    if (res.error) {
                        alert(res.error);
                    } else {
                        loadOpsUsers();
                    }
                })
                .catch(err => alert('Error: ' + err.message));
        }

        function openResetOpsPassword(userId, username) {
            document.getElementById('reset-user-id').value = userId;
            document.getElementById('reset-user-name-display').innerText = '@' + username;
            document.getElementById('reset-user-password').value = '';
            toggleModal('modal-reset-ops-password');
        }

        function submitResetOpsPassword(e) {
            e.preventDefault();
            const userId = document.getElementById('reset-user-id').value;
            const newPassword = document.getElementById('reset-user-password').value.trim();
            fetch(`/api/ops/users/${userId}/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_password: newPassword })
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) {
                    alert('Gagal reset password: ' + res.error);
                } else {
                    toggleModal('modal-reset-ops-password');
                    alert('Password berhasil direset!');
                }
            })
            .catch(err => alert('Terjadi kesalahan: ' + err.message));
        }

        function loadOpsRoles() {
            const container = document.getElementById('ops-roles-cards-container');
            if (!container) return;
            container.innerHTML = '<div class="col-span-3 p-6 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat data role...</div>';
            
            fetch('/api/ops/roles')
                .then(r => r.json())
                .then(roles => {
                    let html = '';
                    roles.forEach(r => {
                        const permCount = Array.isArray(r.permissions) ? r.permissions.length : 0;
                        html += `
                            <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-xs hover:border-emerald-300 transition">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-xs font-bold text-slate-800 font-mono">${r.role_code}</span>
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">${permCount} Izin</span>
                                </div>
                                <h4 class="text-sm font-bold text-emerald-700">${r.role_name}</h4>
                                <p class="text-xs text-slate-500 mt-1 leading-relaxed">${r.description || '-'}</p>
                            </div>
                        `;
                    });
                    container.innerHTML = html;
                })
                .catch(err => {
                    container.innerHTML = `<div class="col-span-3 p-6 text-center text-rose-500"><i class="fa-solid fa-triangle-exclamation mr-2"></i>Gagal memuat role: ${err.message}</div>`;
                });
        }

        // ============ Mutabaah Diri Pimpinan & Civitas Loader ============
        let mutubaahPesertaLoaded = false;

        function populateMutubaahPesertaFilter() {
            if (mutubaahPesertaLoaded) return;
            fetch('/api/mutubaah/peserta')
                .then(r => r.json())
                .then(pesertaList => {
                    const sel = document.getElementById('mutubaah-filter-peserta');
                    if (!sel) return;
                    const curVal = sel.value;
                    let opts = '<option value="all">Semua Peserta</option>';
                    pesertaList.forEach(p => {
                        opts += `<option value="${p.nama}">${p.nama} (${p.unit || '-'})</option>`;
                    });
                    sel.innerHTML = opts;
                    sel.value = curVal || 'all';
                    mutubaahPesertaLoaded = true;
                })
                .catch(() => {});
        }

        function resetMutubaahFilter() {
            if (document.getElementById('mutubaah-filter-peserta')) document.getElementById('mutubaah-filter-peserta').value = 'all';
            if (document.getElementById('mutubaah-filter-unit')) document.getElementById('mutubaah-filter-unit').value = 'all';
            if (document.getElementById('mutubaah-filter-from')) document.getElementById('mutubaah-filter-from').value = '';
            if (document.getElementById('mutubaah-filter-to')) document.getElementById('mutubaah-filter-to').value = '';
            loadMutubaahData();
        }

        function loadMutubaahData() {
            populateMutubaahPesertaFilter();
            const tbody = document.getElementById('mutubaah-tbody');
            if (!tbody) return;
            tbody.innerHTML = '<tr><td colspan="8" class="p-4 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat data Mutabaah Diri...</td></tr>';

            const peserta = document.getElementById('mutubaah-filter-peserta')?.value || 'all';
            const unit = document.getElementById('mutubaah-filter-unit')?.value || 'all';
            const fromDate = document.getElementById('mutubaah-filter-from')?.value || '';
            const toDate = document.getElementById('mutubaah-filter-to')?.value || '';

            const params = new URLSearchParams();
            params.set('limit', '200');
            if (peserta && peserta !== 'all') params.set('nama', peserta);
            if (unit && unit !== 'all') params.set('unit', unit);
            if (fromDate) params.set('from', fromDate);
            if (toDate) params.set('to', toDate);

            fetch('/api/mutubaah/laporan?' + params.toString())
                .then(r => r.json())
                .then(data => {
                    if (!Array.isArray(data) || data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" class="p-6 text-center text-slate-400">Tidak ada laporan mutabaah yang sesuai filter.</td></tr>';
                        document.getElementById('mutubaah-tilawah-hari').innerText = '-';
                        document.getElementById('mutubaah-khatam').innerText = '-';
                        document.getElementById('mutubaah-sholat').innerText = '-%';
                        document.getElementById('mutubaah-dzikir').innerText = '-';
                        return;
                    }

                    const isSingle = (peserta && peserta !== 'all');
                    const latest = data[0];

                    if (isSingle) {
                        document.getElementById('mutubaah-lbl-card1').innerText = 'Juz Terakhir';
                        document.getElementById('mutubaah-tilawah-hari').innerText = latest.tilawah ? 'Juz ' + latest.tilawah : '-';

                        document.getElementById('mutubaah-lbl-card2').innerText = 'Khatam Ke';
                        document.getElementById('mutubaah-khatam').innerText = latest.khatam_ke !== undefined ? 'Ke-' + latest.khatam_ke : '-';

                        document.getElementById('mutubaah-lbl-card3').innerText = 'Faham Sholat';
                        document.getElementById('mutubaah-sholat').innerText = latest.faham_sholat ? (String(latest.faham_sholat).includes('%') ? latest.faham_sholat : latest.faham_sholat + '%') : '-';

                        document.getElementById('mutubaah-lbl-card4').innerText = 'Dzikir Terakhir';
                        const totalDzikir = latest.total_dzikir || ((latest.doa_orang_tua||0) + (latest.doa_nabi_yunus||0) + (latest.hauqolah||0) + (latest.hasballah||0) + (latest.sholawat||0));
                        document.getElementById('mutubaah-dzikir').innerText = totalDzikir.toLocaleString('id-ID');
                    } else {
                        document.getElementById('mutubaah-lbl-card1').innerText = 'Total Laporan';
                        document.getElementById('mutubaah-tilawah-hari').innerText = data.length + ' Catatan';

                        const distinctUsers = new Set(data.map(d => d.nama)).size;
                        document.getElementById('mutubaah-lbl-card2').innerText = 'Peserta Aktif';
                        document.getElementById('mutubaah-khatam').innerText = distinctUsers + ' Orang';

                        document.getElementById('mutubaah-lbl-card3').innerText = 'Juz Masuk Terakhir';
                        document.getElementById('mutubaah-sholat').innerText = latest.tilawah ? 'Juz ' + latest.tilawah : '-';

                        document.getElementById('mutubaah-lbl-card4').innerText = 'Total Akumulasi Dzikir';
                        const grandTotalDzikir = data.reduce((acc, cur) => acc + (cur.total_dzikir || 0), 0);
                        document.getElementById('mutubaah-dzikir').innerText = grandTotalDzikir.toLocaleString('id-ID');
                    }

                    const getUnitBadge = (u) => {
                        const unitCode = String(u || '').toUpperCase();
                        if (unitCode.includes('SMA')) return 'bg-blue-100 text-blue-800 border-blue-200';
                        if (unitCode.includes('SMP')) return 'bg-amber-100 text-amber-800 border-amber-200';
                        if (unitCode.includes('SD')) return 'bg-emerald-100 text-emerald-800 border-emerald-200';
                        if (unitCode.includes('TK') || unitCode.includes('PG')) return 'bg-purple-100 text-purple-800 border-purple-200';
                        if (unitCode.includes('IT')) return 'bg-sky-100 text-sky-800 border-sky-200';
                        if (unitCode.includes('OB')) return 'bg-teal-100 text-teal-800 border-teal-200';
                        if (unitCode.includes('GARDEN')) return 'bg-lime-100 text-lime-800 border-lime-200';
                        if (unitCode.includes('SECURITY')) return 'bg-indigo-100 text-indigo-800 border-indigo-200';
                        if (unitCode.includes('SDM')) return 'bg-pink-100 text-pink-800 border-pink-200';
                        return 'bg-slate-100 text-slate-800 border-slate-200';
                    };

                    tbody.innerHTML = data.map(l => {
                        const totalDzikir = l.total_dzikir || ((l.doa_orang_tua||0) + (l.doa_nabi_yunus||0) + (l.hauqolah||0) + (l.hasballah||0) + (l.sholawat||0));
                        const dzikirDetail = `1. Doa Orang Tua: ${l.doa_orang_tua||0}\\n2. Doa Nabi Yunus: ${l.doa_nabi_yunus||0}\\n3. Hauqolah: ${l.hauqolah||0}\\n4. Hasballah: ${l.hasballah||0}\\n5. Sholawat: ${l.sholawat||0}`;
                        const unitBadge = getUnitBadge(l.unit);
                        return `
                            <tr class="hover:bg-slate-50/50 transition">
                                <td class="p-3 font-mono text-xs text-slate-500 whitespace-nowrap">${l.tanggal || '-'}</td>
                                <td class="p-3">
                                    <div class="font-semibold text-slate-800 text-xs">${l.nama || 'Civitas'}</div>
                                    <div class="text-[10px] text-slate-400 font-medium">${l.jabatan || 'Pimpinan'}</div>
                                </td>
                                <td class="p-3 whitespace-nowrap">
                                    <span class="inline-block px-2 py-0.5 text-[10px] font-bold rounded-md border ${unitBadge}">${l.unit || 'UMUM'}</span>
                                </td>
                                <td class="p-3 text-xs font-semibold text-emerald-700 whitespace-nowrap">${l.tilawah ? 'Juz ' + l.tilawah : '-'}</td>
                                <td class="p-3 text-xs font-semibold text-blue-700 whitespace-nowrap">${l.khatam_ke !== undefined ? 'Ke-' + l.khatam_ke : '-'}</td>
                                <td class="p-3 text-xs text-purple-700 font-medium whitespace-nowrap">${l.faham_sholat ? (String(l.faham_sholat).includes('%') ? l.faham_sholat : l.faham_sholat + '%') : '-'}</td>
                                <td class="p-3 text-xs font-bold text-rose-700 whitespace-nowrap" title="${dzikirDetail}">${totalDzikir.toLocaleString('id-ID')}</td>
                                <td class="p-3 text-xs whitespace-nowrap">
                                    <button onclick="alert('📿 Detail Dzikir (${l.nama} - ${l.tanggal}):\\n\\n${dzikirDetail}')" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition">
                                        <i class="fa-solid fa-eye mr-1"></i> Rincian
                                    </button>
                                </td>
                            </tr>
                        `;
                    }).join('');
                })
                .catch(err => {
                    tbody.innerHTML = '<tr><td colspan="8" class="p-6 text-center text-rose-500">Gagal memuat data: ' + err.message + '</td></tr>';
                });
        }

        function submitMutubaahForm(e) {
            e.preventDefault();
            const nama = document.getElementById('mut-input-nama').value.trim();
            const unit = document.getElementById('mut-input-unit').value;
            const tanggal = document.getElementById('mut-input-tanggal').value || new Date().toISOString().slice(0,10);
            const usia = parseInt(document.getElementById('mut-input-usia').value) || 40;
            const tilawah = document.getElementById('mut-input-tilawah').value.trim();
            const khatam_ke = parseInt(document.getElementById('mut-input-khatam').value) || 0;
            const faham_sholat = document.getElementById('mut-input-sholat').value.trim();
            const doa_orang_tua = parseInt(document.getElementById('mut-input-dzikir1').value) || 0;
            const doa_nabi_yunus = parseInt(document.getElementById('mut-input-dzikir2').value) || 0;
            const hauqolah = parseInt(document.getElementById('mut-input-dzikir3').value) || 0;
            const hasballah = parseInt(document.getElementById('mut-input-dzikir4').value) || 0;
            const sholawat = parseInt(document.getElementById('mut-input-dzikir5').value) || 0;

            const payload = {
                nama, unit, tanggal, usia, tilawah, khatam_ke, faham_sholat,
                dzikir: { doa_orang_tua, doa_nabi_yunus, hauqolah, hasballah, sholawat }
            };

            fetch('/api/mutubaah/laporan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) {
                    alert('Gagal menyimpan laporan: ' + res.error);
                } else {
                    alert('Alhamdulillah! Laporan mutabaah berhasil disimpan untuk ' + (res.nama || nama));
                    toggleModal('modal-add-mutubaah');
                    document.getElementById('mut-input-tilawah').value = '';
                    loadMutubaahData();
                }
            })
            .catch(err => alert('Terjadi kesalahan: ' + err.message));
        }

        function exportMutubaahCSV() {
            const peserta = document.getElementById('mutubaah-filter-peserta')?.value || 'all';
            const unit = document.getElementById('mutubaah-filter-unit')?.value || 'all';
            const fromDate = document.getElementById('mutubaah-filter-from')?.value || '';
            const toDate = document.getElementById('mutubaah-filter-to')?.value || '';

            const params = new URLSearchParams();
            params.set('limit', '2000');
            if (peserta && peserta !== 'all') params.set('nama', peserta);
            if (unit && unit !== 'all') params.set('unit', unit);
            if (fromDate) params.set('from', fromDate);
            if (toDate) params.set('to', toDate);

            fetch('/api/mutubaah/laporan?' + params.toString())
                .then(r => r.json())
                .then(data => {
                    if (!Array.isArray(data) || data.length === 0) {
                        alert('Tidak ada data untuk diekspor');
                        return;
                    }
                    let csv = 'ID,Tanggal,Nama,Unit,Jabatan,Usia,Tilawah,Khatam Ke,Faham Sholat,Doa Orang Tua,Doa Nabi Yunus,Hauqolah,Hasballah,Sholawat,Total Dzikir\\n';
                    data.forEach(r => {
                        const total = r.total_dzikir || ((r.doa_orang_tua||0)+(r.doa_nabi_yunus||0)+(r.hauqolah||0)+(r.hasballah||0)+(r.sholawat||0));
                        csv += `"${r.id||''}","${r.tanggal||''}","${r.nama||''}","${r.unit||'UMUM'}","${r.jabatan||'Pimpinan'}","${r.usia||''}","${r.tilawah||''}","${r.khatam_ke||''}","${r.faham_sholat||''}","${r.doa_orang_tua||0}","${r.doa_nabi_yunus||0}","${r.hauqolah||0}","${r.hasballah||0}","${r.sholawat||0}","${total}"\\n`;
                    });
                    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.setAttribute('href', url);
                    const fileSuffix = unit !== 'all' ? unit : (peserta !== 'all' ? peserta : 'Civitas');
                    link.setAttribute('download', `Mutabaah_Diri_${fileSuffix}_${new Date().toISOString().slice(0,10)}.csv`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
        }

        // ============ Sapa Ais / LaporPak Loader ============
        let sapaaisCurrentPage = 1;
        const SAPAAIS_LIMIT = 20;

        function loadSapaAis(page) {
            sapaaisCurrentPage = page || 1;
            const status = document.getElementById('sapaais-filter-status').value;
            const kategori = document.getElementById('sapaais-filter-kategori').value;
            const dateFrom = document.getElementById('sapaais-filter-from').value;
            const dateTo = document.getElementById('sapaais-filter-to').value;

            const params = new URLSearchParams();
            params.set('limit', SAPAAIS_LIMIT);
            params.set('offset', (sapaaisCurrentPage - 1) * SAPAAIS_LIMIT);
            if (status) params.set('status', status);
            if (kategori) params.set('kategori', kategori);
            if (dateFrom) params.set('date_from', dateFrom);
            if (dateTo) params.set('date_to', dateTo);

            const tbody = document.getElementById('sapaais-tbody');
            tbody.innerHTML = '<tr><td colspan="9" class="p-4 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat data Sapa Ais...</td></tr>';

            fetch('/api/sapaais/data?' + params.toString())
                .then(r => r.json())
                .then(res => {
                    if (!res.success) throw new Error('Gagal memuat');
                    renderSapaAisStats(res.stats);
                    renderSapaAisCats(res.cat_stats);
                    renderSapaAisTable(res.data);
                    renderSapaAisPagination(res.page, res.total_pages, res.total);
                })
                .catch(err => {
                    tbody.innerHTML = '<tr><td colspan="9" class="p-6 text-center text-rose-500">Error: ' + err.message + '</td></tr>';
                });
        }

        function statusBadge(status) {
            const map = {
                'BARU': 'bg-rose-50 text-rose-700 border border-rose-200',
                'DITERIMA': 'bg-amber-50 text-amber-700 border border-amber-200',
                'SELESAI': 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            };
            const cls = map[status] || 'bg-slate-100 text-slate-700 border border-slate-200';
            return `<span class="text-xs px-2.5 py-0.5 font-semibold rounded-md ${cls}">${status}</span>`;
        }

        function slaBadge(deadline) {
            if (!deadline) return '<span class="text-xs text-slate-400">-</span>';
            try {
                const d = new Date(deadline);
                const now = new Date();
                const hrs = (d - now) / 3600000;
                if (hrs <= 0) return '<span class="text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-700 font-bold">⚠ LEWAT</span>';
                if (hrs <= 24) return `<span class="text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">${hrs.toFixed(1)} jam</span>`;
                return `<span class="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">${(hrs/24).toFixed(1)} hr</span>`;
            } catch(e) {
                return '<span class="text-xs text-slate-400">-</span>';
            }
        }

        function renderSapaAisStats(s) {
            const wrap = document.getElementById('sapaais-stats');
            const loading = document.getElementById('sapaais-loading-stats');
            if (loading) loading.classList.add('hidden');
            if (!s || s.total === 0) {
                wrap.innerHTML = '<div class="col-span-5 text-center py-2 text-slate-400 text-sm">Belum ada laporan tiket</div>';
                return;
            }
            wrap.innerHTML = `
                <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                    <div>
                        <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Tiket Baru</p>
                        <h3 class="text-base sm:text-xl font-bold text-rose-600 mt-1">${s.baru}</h3>
                    </div>
                    <div class="p-2.5 sm:p-3 bg-rose-50 text-rose-600 rounded-xl">
                        <i class="fa-solid fa-circle-exclamation text-lg sm:text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                    <div>
                        <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Diterima</p>
                        <h3 class="text-base sm:text-xl font-bold text-amber-600 mt-1">${s.diterima}</h3>
                    </div>
                    <div class="p-2.5 sm:p-3 bg-amber-50 text-amber-600 rounded-xl">
                        <i class="fa-solid fa-spinner text-lg sm:text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                    <div>
                        <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Selesai</p>
                        <h3 class="text-base sm:text-xl font-bold text-emerald-600 mt-1">${s.selesai}</h3>
                    </div>
                    <div class="p-2.5 sm:p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                        <i class="fa-solid fa-circle-check text-lg sm:text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                    <div>
                        <p class="text-[11px] sm:text-xs text-slate-500 font-medium">Total Tiket</p>
                        <h3 class="text-base sm:text-xl font-bold text-slate-800 mt-1">${s.total}</h3>
                    </div>
                    <div class="p-2.5 sm:p-3 bg-slate-100 text-slate-600 rounded-xl">
                        <i class="fa-solid fa-ticket text-lg sm:text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-xl shadow-xs p-4 sm:p-5 border border-slate-200 flex items-center justify-between">
                    <div>
                        <p class="text-[11px] sm:text-xs text-slate-500 font-medium">SLA Lewat</p>
                        <h3 class="text-base sm:text-xl font-bold text-rose-600 mt-1">${s.overdue}</h3>
                    </div>
                    <div class="p-2.5 sm:p-3 bg-rose-50 text-rose-600 rounded-xl">
                        <i class="fa-solid fa-triangle-exclamation text-lg sm:text-2xl"></i>
                    </div>
                </div>
            `;
        }

        function renderSapaAisCats(cats) {
            const wrap = document.getElementById('sapaais-cats-wrap');
            const el = document.getElementById('sapaais-cats');
            if (!cats || !cats.length) {
                wrap.classList.add('hidden');
                el.innerHTML = '';
                return;
            }
            wrap.classList.remove('hidden');
            el.innerHTML = cats.map(c => `
                <div class="flex items-center justify-between py-2.5 px-4 text-xs">
                    <span class="font-medium text-slate-700">${c.kategori}</span>
                    <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">${c.jml}</span>
                </div>
            `).join('');
        }

        function renderSapaAisTable(rows) {
            const tbody = document.getElementById('sapaais-tbody');
            if (!rows || !rows.length) {
                tbody.innerHTML = '<tr><td colspan="9" class="p-6 text-center text-slate-400">Tidak ada tiket laporan</td></tr>';
                return;
            }
            tbody.innerHTML = rows.map(r => {
                const foto = r.foto_url
                    ? `<a href="${r.foto_url}" target="_blank" class="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded border border-emerald-200 text-xs font-semibold inline-flex items-center gap-1"><i class="fa-solid fa-image"></i> Foto</a>`
                    : '<span class="text-slate-400 text-xs">-</span>';
                const desc = (r.deskripsi || '').substring(0, 80) + ((r.deskripsi || '').length > 80 ? '...' : '');
                const created = (r.created_at || '').substring(0, 16).replace('T', ' ');
                return `<tr class="hover:bg-slate-50/50 transition">
                    <td class="p-3 font-mono text-xs font-semibold text-slate-700">${r.id}</td>
                    <td class="p-3 text-xs font-medium text-slate-600">${r.kategori || '-'}</td>
                    <td class="p-3 text-xs text-slate-800 max-w-xs truncate">${r.lokasi || '-'}</td>
                    <td class="p-3 text-xs text-slate-700 max-w-xs truncate">${desc}</td>
                    <td class="p-3 text-xs">${statusBadge(r.status)}</td>
                    <td class="p-3 text-xs font-medium text-slate-600">${r.pic_nama || '-'}</td>
                    <td class="p-3 text-xs">${slaBadge(r.sla_deadline)}</td>
                    <td class="p-3 text-xs">${foto}</td>
                    <td class="p-3 text-xs font-mono text-slate-500">${created}</td>
                </tr>`;
            }).join('');
        }

        function renderSapaAisPagination(page, totalPages, total) {
            const el = document.getElementById('sapaais-pagination');
            if (totalPages <= 1) {
                el.innerHTML = `<span class="text-xs text-slate-500 font-medium">Total: ${total} laporan</span>`;
                return;
            }
            const prev = page > 1
                ? `<button onclick="loadSapaAis(${page-1})" class="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold hover:bg-slate-50 transition">Sebelumnya</button>`
                : `<span class="px-3 py-1.5 border border-slate-100 rounded-lg text-xs text-slate-300">Sebelumnya</span>`;
            const next = page < totalPages
                ? `<button onclick="loadSapaAis(${page+1})" class="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold hover:bg-slate-50 transition">Selanjutnya</button>`
                : `<span class="px-3 py-1.5 border border-slate-100 rounded-lg text-xs text-slate-300">Selanjutnya</span>`;
            el.innerHTML = `<span class="text-xs text-slate-500 font-medium">Halaman ${page} dari ${totalPages} | Total: ${total} tiket</span><div class="flex gap-2">${prev}${next}</div>`;
        }

        // ============ End Sapa Ais Loader ============

        // Data hosts dari server (di-render sebagai JSON oleh Jinja)
        const HOSTS_DATA = {
            {% for host in monitored_hosts %}
            "{{ host.id }}": {
                name: {{ host.name | tojson }},
                category: {{ (host.category or 'Server') | tojson }},
                host: {{ host.host | tojson }},
                type: {{ host.type | tojson }},
                port: {{ (host.port or '') | tojson }}
            },
            {% endfor %}
        };

        function editHost(hostId) {
            const h = HOSTS_DATA[hostId];
            if (!h) {
                console.error("Host not found for id:", hostId);
                return;
            }
            document.getElementById('edit-host-id').value = hostId;
            document.getElementById('edit-host-name').value = h.name || '';
            document.getElementById('edit-host-category').value = h.category || 'Server';
            document.getElementById('edit-host-host').value = h.host || '';
            document.getElementById('edit-host-type').value = h.type || 'ping';
            document.getElementById('edit-host-port').value = h.port || '';
            toggleModal('modal-edit-host');
        }
        const openEditHost = editHost;

        function filterMutabaahTable() {
            const search = document.getElementById('mutabaah-search').value.toLowerCase();
            const unit = document.getElementById('mutabaah-filter-unit').value.toLowerCase();
            const date = document.getElementById('mutabaah-filter-date').value;

            const rows = document.querySelectorAll('.mutabaah-row');
            let visibleCount = 0;

            rows.forEach(row => {
                const rNama = row.getAttribute('data-nama') || '';
                const rUnit = (row.getAttribute('data-unit') || '').toLowerCase();
                const rDate = row.getAttribute('data-date') || '';

                const matchSearch = !search || rNama.includes(search);
                const matchUnit = !unit || rUnit === unit;
                const matchDate = !date || rDate === date;

                if (matchSearch && matchUnit && matchDate) {
                    row.classList.remove('hidden');
                    visibleCount++;
                } else {
                    row.classList.add('hidden');
                }
            });

            document.getElementById('mutabaah-count-badge').innerText = 'Total: ' + visibleCount + ' Laporan Filtered';
        }

        // Filter runs via showTab override when mutabaah tab is shown

        function filterKebersihanTable() {
            const search = document.getElementById('kebersihan-search').value.toLowerCase();
            const unit = (document.getElementById('kebersihan-filter-unit').value || '').toLowerCase();
            const date = document.getElementById('kebersihan-filter-date').value;
            const photoOpt = document.getElementById('kebersihan-filter-photo').value;

            const rows = document.querySelectorAll('.kebersihan-row');
            let visibleCount = 0;

            rows.forEach(row => {
                const rSearch = row.getAttribute('data-search') || '';
                const rUnit = (row.getAttribute('data-unit') || '').toLowerCase();
                const rDate = row.getAttribute('data-date') || '';
                const rPhoto = row.getAttribute('data-hasphoto') === 'true';

                const matchSearch = !search || rSearch.includes(search);
                const matchUnit = !unit || rUnit.includes(unit) || (unit === 'ob' && (rUnit.startsWith('ob') || rUnit.includes('ob')));
                const matchDate = !date || rDate === date;

                let matchPhoto = true;
                if (photoOpt === 'with_photo') matchPhoto = rPhoto;
                else if (photoOpt === 'no_photo') matchPhoto = !rPhoto;

                if (matchSearch && matchUnit && matchDate && matchPhoto) {
                    row.classList.remove('hidden');
                    visibleCount++;
                } else {
                    row.classList.add('hidden');
                }
            });

            document.getElementById('kebersihan-count-badge').innerText = 'Total: ' + visibleCount + ' Laporan Filtered';
        }

        // ===== WA BOT STATUS CHECKER =====
        async function checkBotStatus() {
            try {
                const res = await fetch('/api/bot/status');
                const data = await res.json();
                const badgeEl = document.getElementById('bot-status-badge');
                if (!badgeEl) return;
                if (data.hasQR || data.status === 'Waiting for Scan') {
                    badgeEl.innerHTML = `<a href="/bot-qr" target="_blank" class="px-2.5 py-1 bg-amber-100 text-amber-800 font-bold rounded-full border border-amber-300 animate-pulse flex items-center gap-1.5 text-[11px] hover:bg-amber-200 transition" title="WhatsApp Bot Butuh Scan QR"><i class="fa-brands fa-whatsapp text-amber-600"></i> Scan QR Bot</a>`;
                } else if (data.status === 'Connected') {
                    badgeEl.innerHTML = `<a href="/bot-qr" target="_blank" class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-medium rounded-full border border-emerald-200 flex items-center gap-1 text-[11px] hover:bg-emerald-100 transition" title="WhatsApp Bot Online"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> WA Bot Online</a>`;
                } else {
                    badgeEl.innerHTML = `<a href="/bot-qr" target="_blank" class="px-2 py-0.5 bg-rose-50 text-rose-700 font-medium rounded-full border border-rose-200 flex items-center gap-1 text-[11px] hover:bg-rose-100 transition" title="WhatsApp Bot Disconnected"><span class="w-2 h-2 rounded-full bg-rose-500"></span> WA Bot Offline</a>`;
                }
            } catch (e) {}
        }
        checkBotStatus();
        setInterval(checkBotStatus, 15000);

        // ===== CHART.JS INITIALIZATION =====
        window.addEventListener('DOMContentLoaded', () => {
            try {
                if (typeof Chart === 'undefined') {
                    console.warn("Chart.js belum dimuat.");
                } else {
                    const mutabaahDates = {{ chart_data.mutabaah_dates | tojson }};
                    const mutabaahCounts = {{ chart_data.mutabaah_counts | tojson }};
                    const kebersihanUnits = {{ chart_data.kebersihan_units | tojson }};
                    const kebersihanCounts = {{ chart_data.kebersihan_counts | tojson }};
                    const journalCategories = {{ chart_data.journal_categories | tojson }};
                    const journalCounts = {{ chart_data.journal_counts | tojson }};
                    const taskStats = {{ chart_data.task_stats | tojson }};
                    const trendDates = {{ chart_data.trend_dates | tojson }};
                    const tasksCreated = {{ chart_data.tasks_created | tojson }};
                    const tasksResolved = {{ chart_data.tasks_resolved | tojson }};
                    const standbyCompliance = {{ chart_data.standby_compliance | tojson }};

                    const colors = ['#0d9488', '#8b5cf6', '#3b82f6', '#f59e0b', '#ef4444', '#10b981', '#6366f1'];

                    // Dashboard Velocity Closed-Loop Chart
                    const elDashVelocity = document.getElementById('dashVelocityChart');
                    if (elDashVelocity) {
                        new Chart(elDashVelocity, {
                            type: 'bar',
                            data: {
                                labels: trendDates.length ? trendDates : mutabaahDates,
                                datasets: [
                                    {
                                        label: 'Tiket Masuk',
                                        data: tasksCreated.length ? tasksCreated : [0,0,0,0,0,0,1],
                                        backgroundColor: '#f59e0b',
                                        borderRadius: 6
                                    },
                                    {
                                        label: 'Tiket Selesai',
                                        data: tasksResolved.length ? tasksResolved : [0,0,0,0,0,0,0],
                                        backgroundColor: '#10b981',
                                        borderRadius: 6
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        ticks: { precision: 0 }
                                    }
                                }
                            }
                        });
                    }

                    // Dashboard Preview Mutabaah & Pos Standby
                    const elDashMut = document.getElementById('dashMutabaahChart');
                    if (elDashMut) {
                        new Chart(elDashMut, {
                            type: 'line',
                            data: {
                                labels: trendDates.length ? trendDates : mutabaahDates,
                                datasets: [
                                    {
                                        label: 'Pos Standby On-Time',
                                        data: standbyCompliance.length ? standbyCompliance : [0,0,0,0,0,0,7],
                                        borderColor: '#0284c7',
                                        backgroundColor: 'rgba(2, 132, 199, 0.1)',
                                        fill: true,
                                        tension: 0.3,
                                        borderWidth: 2.5
                                    },
                                    {
                                        label: 'Laporan Mutabaah',
                                        data: mutabaahCounts,
                                        borderColor: '#0d9488',
                                        backgroundColor: 'rgba(13, 148, 136, 0.1)',
                                        fill: true,
                                        tension: 0.3,
                                        borderWidth: 2.5
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        ticks: { precision: 0 }
                                    }
                                }
                            }
                        });
                    }

                    // Dashboard Preview Kebersihan
                    const elDashKeb = document.getElementById('dashKebersihanChart');
                    if (elDashKeb) {
                        new Chart(elDashKeb, {
                            type: 'doughnut',
                            data: {
                                labels: kebersihanUnits,
                                datasets: [{ data: kebersihanCounts, backgroundColor: colors }]
                            },
                            options: { responsive: true, maintainAspectRatio: false }
                        });
                    }

                    // Full Mutabaah Bar Chart
                    const elFullMut = document.getElementById('fullMutabaahChart');
                    if (elFullMut) {
                        new Chart(elFullMut, {
                            type: 'bar',
                            data: {
                                labels: mutabaahDates,
                                datasets: [{
                                    label: 'Jumlah Laporan Petugas',
                                    data: mutabaahCounts,
                                    backgroundColor: '#0d9488',
                                    borderRadius: 8
                                }]
                            },
                            options: { responsive: true, maintainAspectRatio: false }
                        });
                    }

                    // Full Kebersihan Doughnut Chart
                    const elFullKeb = document.getElementById('fullKebersihanChart');
                    if (elFullKeb) {
                        new Chart(elFullKeb, {
                            type: 'doughnut',
                            data: {
                                labels: kebersihanUnits,
                                datasets: [{ data: kebersihanCounts, backgroundColor: colors }]
                            },
                            options: { responsive: true, maintainAspectRatio: false }
                        });
                    }

                    // Full Journal Bar Chart
                    const elFullJour = document.getElementById('fullJournalChart');
                    if (elFullJour) {
                        new Chart(elFullJour, {
                            type: 'bar',
                            data: {
                                labels: journalCategories,
                                datasets: [{
                                    label: 'Catatan Jurnal',
                                    data: journalCounts,
                                    backgroundColor: '#10b981',
                                    borderRadius: 8
                                }]
                            },
                            options: { responsive: true, maintainAspectRatio: false }
                        });
                    }

                    // Full Task Status Chart
                    const elFullTask = document.getElementById('fullTaskChart');
                    if (elFullTask) {
                        new Chart(elFullTask, {
                            type: 'pie',
                            data: {
                                labels: ['Pending', 'Proses', 'Selesai'],
                                datasets: [{
                                    data: [taskStats.pending, taskStats.proses, taskStats.selesai],
                                    backgroundColor: ['#f59e0b', '#3b82f6', '#10b981']
                                }]
                            },
                            options: { responsive: true, maintainAspectRatio: false }
                        });
                    }
                }
            } catch (err) {
                console.warn("Chart.js render caught exception:", err);
            }

            // Set default dates for report (start = 7 days ago, end = today)
            const today = new Date();
            const padZero = num => String(num).padStart(2, '0');
            const formatDate = d => `${d.getFullYear()}-${padZero(d.getMonth() + 1)}-${padZero(d.getDate())}`;

            const startElem = document.getElementById('report-start');
            const endElem = document.getElementById('report-end');
            if (startElem && endElem) {
                const endStr = formatDate(today);
                const startObj = new Date();
                startObj.setDate(today.getDate() - 7);
                const startStr = formatDate(startObj);
                startElem.value = startStr;
                endElem.value = endStr;
                generateReport();
            }

            // Auto open tab if specified in URL query (?tab=...) or hash (#...)
            const urlParams = new URLSearchParams(window.location.search);
            const tabParam = urlParams.get('tab');
            const hashParam = window.location.hash.replace('#', '');
            const targetTab = tabParam || hashParam;
            if (targetTab && document.getElementById(targetTab)) {
                showTab(targetTab);
            }
        });

        function generateReport() {
            const startElem = document.getElementById('report-start');
            const endElem = document.getElementById('report-end');
            const unitElem = document.getElementById('report-unit');
            const previewArea = document.getElementById('report-preview-area');
            
            if (!previewArea) return;

            const start = startElem ? startElem.value : '';
            const end = endElem ? endElem.value : '';
            const unit = unitElem ? unitElem.value : '';

            const chkMutabaah = document.getElementById('chk-mutabaah') ? document.getElementById('chk-mutabaah').checked : false;
            const chkKebersihan = document.getElementById('chk-kebersihan') ? document.getElementById('chk-kebersihan').checked : false;
            const chkJournal = document.getElementById('chk-journal') ? document.getElementById('chk-journal').checked : false;
            const chkTasks = document.getElementById('chk-tasks') ? document.getElementById('chk-tasks').checked : false;

            if (!chkMutabaah && !chkKebersihan && !chkJournal && !chkTasks) {
                previewArea.innerHTML = `
                    <div class="p-8 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl bg-white">
                        <i class="fa-solid fa-triangle-exclamation text-3xl mb-2 text-amber-500"></i>
                        <p class="text-sm font-semibold text-slate-700">Tidak ada sumber data yang dipilih</p>
                        <p class="text-xs text-slate-400 mt-1">Silakan centang minimal satu sumber data (Mutabaah, Kebersihan, Jurnal, atau Tiket).</p>
                    </div>
                `;
                return;
            }

            previewArea.innerHTML = `
                <div class="p-8 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl bg-white">
                    <i class="fa-solid fa-spinner fa-spin text-3xl mb-2 text-emerald-600"></i>
                    <p class="text-sm font-semibold text-slate-700">Mengambil data laporan...</p>
                </div>
            `;

            const fetchMutabaah = chkMutabaah 
                ? fetch(`/api/report/mutabaah?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&unit=${encodeURIComponent(unit)}`).then(r => r.json())
                : Promise.resolve(null);

            const fetchKebersihan = chkKebersihan 
                ? fetch(`/api/report/kebersihan?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&unit=${encodeURIComponent(unit)}`).then(r => r.json())
                : Promise.resolve(null);

            const fetchJournal = chkJournal 
                ? fetch(`/api/report/journal?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`).then(r => r.json())
                : Promise.resolve(null);

            const fetchTasks = chkTasks 
                ? fetch(`/api/report/tasks?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&unit=${encodeURIComponent(unit)}`).then(r => r.json())
                : Promise.resolve(null);

            Promise.all([fetchMutabaah, fetchKebersihan, fetchJournal, fetchTasks])
                .then(([mutabaahData, kebersihanData, journalData, tasksData]) => {
                    let html = '';

                    const periodText = (start && end) ? `${start} s/d ${end}` : (start ? `Mulai ${start}` : (end ? `Sampai ${end}` : 'Semua Periode'));
                    const unitText = unit || 'Semua Unit';
                    const printDate = new Date().toLocaleString('id-ID', { dateStyle: 'full', timeStyle: 'short' });

                    html += `
                        <div class="p-6 bg-slate-900 text-white rounded-2xl shadow-xs space-y-4">
                            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                                <div>
                                    <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded-md border border-emerald-800">Laporan Resmi Operasional</span>
                                    <h3 class="text-lg font-bold text-white mt-1.5">SEKOLAH ISLAM AN NAHL</h3>
                                    <p class="text-xs text-slate-300">Divisi IT, Sarpras & General Affairs</p>
                                </div>
                                <div class="text-left sm:text-right text-xs text-slate-400 space-y-1">
                                    <p><span class="text-slate-500">Periode:</span> <span class="font-semibold text-slate-200">${periodText}</span></p>
                                    <p><span class="text-slate-500">Unit:</span> <span class="font-semibold text-slate-200">${unitText}</span></p>
                                    <p><span class="text-slate-500">Dicetak:</span> <span class="font-mono text-slate-300">${printDate}</span></p>
                                </div>
                            </div>

                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
                                ${mutabaahData ? `
                                <div class="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700/60">
                                    <p class="text-[11px] text-slate-400 font-medium flex items-center gap-1.5"><i class="fa-solid fa-hands-praying text-teal-400"></i> Mutabaah</p>
                                    <p class="text-xl font-bold text-teal-300 mt-1">${mutabaahData.count} <span class="text-xs font-normal text-slate-400">log</span></p>
                                </div>` : ''}
                                ${kebersihanData ? `
                                <div class="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700/60">
                                    <p class="text-[11px] text-slate-400 font-medium flex items-center gap-1.5"><i class="fa-solid fa-broom text-purple-400"></i> Kebersihan</p>
                                    <p class="text-xl font-bold text-purple-300 mt-1">${kebersihanData.count} <span class="text-xs font-normal text-slate-400">laporan</span></p>
                                </div>` : ''}
                                ${journalData ? `
                                <div class="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700/60">
                                    <p class="text-[11px] text-slate-400 font-medium flex items-center gap-1.5"><i class="fa-solid fa-book text-emerald-400"></i> Jurnal Kerja</p>
                                    <p class="text-xl font-bold text-emerald-300 mt-1">${journalData.count} <span class="text-xs font-normal text-slate-400">catatan</span></p>
                                </div>` : ''}
                                ${tasksData ? `
                                <div class="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700/60">
                                    <p class="text-[11px] text-slate-400 font-medium flex items-center gap-1.5"><i class="fa-solid fa-clipboard-list text-blue-400"></i> Tiket Tugas</p>
                                    <p class="text-xl font-bold text-blue-300 mt-1">${tasksData.count} <span class="text-xs font-normal text-slate-400">pekerjaan</span></p>
                                </div>` : ''}
                            </div>
                        </div>
                    `;

                    if (mutabaahData) {
                        html += `
                            <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs space-y-3 p-5">
                                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                                    <h4 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                        <i class="fa-solid fa-hands-praying text-teal-600"></i>
                                        Log Mutabaah Yaumiyah (${mutabaahData.count} Data)
                                    </h4>
                                    ${mutabaahData.per_unit && Object.keys(mutabaahData.per_unit).length > 0 ? `
                                    <div class="flex flex-wrap gap-1.5">
                                        ${Object.entries(mutabaahData.per_unit).map(([u, c]) => `
                                            <span class="px-2 py-0.5 text-[10px] font-semibold bg-teal-50 text-teal-700 rounded-md border border-teal-100">${u}: ${c}</span>
                                        `).join('')}
                                    </div>` : ''}
                                </div>
                                ${mutabaahData.rows.length === 0 ? `
                                    <div class="p-4 text-center text-slate-400 text-xs italic">Tidak ada data pada periode ini.</div>
                                ` : `
                                    <div class="overflow-x-auto">
                                        <table class="w-full text-left border-collapse text-xs">
                                            <thead>
                                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                                                    <th class="p-2.5">Tanggal WIB</th>
                                                    <th class="p-2.5">Nama Petugas</th>
                                                    <th class="p-2.5">Unit</th>
                                                    <th class="p-2.5">Sholat</th>
                                                    <th class="p-2.5">Tilawah</th>
                                                    <th class="p-2.5">Dzikir</th>
                                                </tr>
                                            </thead>
                                            <tbody class="divide-y divide-slate-100">
                                                ${mutabaahData.rows.map(r => `
                                                    <tr class="hover:bg-slate-50/50">
                                                        <td class="p-2.5 font-mono text-slate-500 whitespace-nowrap">${r.tanggal || '-'}</td>
                                                        <td class="p-2.5 font-semibold text-slate-800">${r.nama || '-'}</td>
                                                        <td class="p-2.5 text-slate-600">${r.unit || '-'}</td>
                                                        <td class="p-2.5 text-slate-700">${r.sholat || '-'}</td>
                                                        <td class="p-2.5 text-slate-700">${r.tilawah || '-'}</td>
                                                        <td class="p-2.5 text-slate-700">${r.dzikir || '-'}</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                `}
                            </div>
                        `;
                    }

                    if (kebersihanData) {
                        html += `
                            <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs space-y-3 p-5">
                                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                                    <h4 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                        <i class="fa-solid fa-broom text-purple-600"></i>
                                        Log Laporan Kebersihan OB (${kebersihanData.count} Data)
                                    </h4>
                                    ${kebersihanData.per_unit && Object.keys(kebersihanData.per_unit).length > 0 ? `
                                    <div class="flex flex-wrap gap-1.5">
                                        ${Object.entries(kebersihanData.per_unit).map(([u, c]) => `
                                            <span class="px-2 py-0.5 text-[10px] font-semibold bg-purple-50 text-purple-700 rounded-md border border-purple-100">${u}: ${c}</span>
                                        `).join('')}
                                    </div>` : ''}
                                </div>
                                ${kebersihanData.rows.length === 0 ? `
                                    <div class="p-4 text-center text-slate-400 text-xs italic">Tidak ada data pada periode ini.</div>
                                ` : `
                                    <div class="overflow-x-auto">
                                        <table class="w-full text-left border-collapse text-xs">
                                            <thead>
                                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                                                    <th class="p-2.5">Tanggal WIB</th>
                                                    <th class="p-2.5">Nama Petugas</th>
                                                    <th class="p-2.5">Unit</th>
                                                    <th class="p-2.5">Area</th>
                                                    <th class="p-2.5">Keterangan</th>
                                                    <th class="p-2.5">Bukti Foto</th>
                                                </tr>
                                            </thead>
                                            <tbody class="divide-y divide-slate-100">
                                                ${kebersihanData.rows.map(r => `
                                                    <tr class="hover:bg-slate-50/50">
                                                        <td class="p-2.5 font-mono text-slate-500 whitespace-nowrap">${r.tanggal || '-'}</td>
                                                        <td class="p-2.5 font-semibold text-slate-800">${r.nama || '-'}</td>
                                                        <td class="p-2.5 text-slate-600">${r.unit || '-'}</td>
                                                        <td class="p-2.5 font-bold text-slate-700">${r.area || '-'}</td>
                                                        <td class="p-2.5 text-slate-700">${r.keterangan || '-'}</td>
                                                        <td class="p-2.5">
                                                            ${r.ada_foto ? `
                                                                <span class="inline-flex items-center text-emerald-600 font-semibold text-[11px]">
                                                                    <i class="fa-solid fa-cloud-arrow-up mr-1"></i> Drive Sync
                                                                </span>
                                                            ` : `<span class="text-slate-400 text-[11px]">Tanpa Foto</span>`}
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                `}
                            </div>
                        `;
                    }

                    if (journalData) {
                        html += `
                            <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs space-y-3 p-5">
                                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                                    <h4 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                        <i class="fa-solid fa-book text-emerald-600"></i>
                                        Jurnal Kegiatan Harian (${journalData.count} Catatan)
                                    </h4>
                                </div>
                                ${journalData.rows.length === 0 ? `
                                    <div class="p-4 text-center text-slate-400 text-xs italic">Tidak ada data pada periode ini.</div>
                                ` : `
                                    <div class="overflow-x-auto">
                                        <table class="w-full text-left border-collapse text-xs">
                                            <thead>
                                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                                                    <th class="p-2.5">Waktu</th>
                                                    <th class="p-2.5">Kategori</th>
                                                    <th class="p-2.5">Judul Kegiatan</th>
                                                    <th class="p-2.5">Deskripsi Ringkas</th>
                                                    <th class="p-2.5">Output / Hasil</th>
                                                </tr>
                                            </thead>
                                            <tbody class="divide-y divide-slate-100">
                                                ${journalData.rows.map(r => `
                                                    <tr class="hover:bg-slate-50/50">
                                                        <td class="p-2.5 font-mono text-slate-500 whitespace-nowrap">${r.tanggal || '-'} ${r.jam ? `(${r.jam})` : ''}</td>
                                                        <td class="p-2.5"><span class="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded">${r.kategori || '-'}</span></td>
                                                        <td class="p-2.5 font-bold text-slate-800">${r.judul || '-'}</td>
                                                        <td class="p-2.5 text-slate-600 max-w-xs">${r.deskripsi || '-'}</td>
                                                        <td class="p-2.5 text-slate-700">${r.output || '-'}</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                `}
                            </div>
                        `;
                    }

                    if (tasksData) {
                        html += `
                            <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs space-y-3 p-5">
                                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                                    <h4 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                                        <i class="fa-solid fa-clipboard-list text-blue-600"></i>
                                        Tiket & Tugas Operasional (${tasksData.count} Pekerjaan)
                                    </h4>
                                </div>
                                ${tasksData.rows.length === 0 ? `
                                    <div class="p-4 text-center text-slate-400 text-xs italic">Tidak ada data pada periode ini.</div>
                                ` : `
                                    <div class="overflow-x-auto">
                                        <table class="w-full text-left border-collapse text-xs">
                                            <thead>
                                                <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                                                    <th class="p-2.5">Waktu Dibuat</th>
                                                    <th class="p-2.5">Unit</th>
                                                    <th class="p-2.5">Kategori</th>
                                                    <th class="p-2.5">Judul Pekerjaan</th>
                                                    <th class="p-2.5">Prioritas</th>
                                                    <th class="p-2.5">Status</th>
                                                </tr>
                                            </thead>
                                            <tbody class="divide-y divide-slate-100">
                                                ${tasksData.rows.map(r => `
                                                    <tr class="hover:bg-slate-50/50">
                                                        <td class="p-2.5 font-mono text-slate-500 whitespace-nowrap">${r.created_at || '-'}</td>
                                                        <td class="p-2.5 font-semibold text-slate-700">${r.unit || '-'}</td>
                                                        <td class="p-2.5 text-slate-500">${r.category || '-'}</td>
                                                        <td class="p-2.5 font-bold text-slate-800">${r.title || '-'}</td>
                                                        <td class="p-2.5">
                                                            ${r.priority === 'Tinggi' ? '<span class="px-2 py-0.5 text-[10px] font-bold bg-rose-100 text-rose-700 rounded">Tinggi</span>' :
                                                              (r.priority === 'Sedang' ? '<span class="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-700 rounded">Sedang</span>' :
                                                              '<span class="px-2 py-0.5 text-[10px] font-bold bg-slate-100 text-slate-600 rounded">Rendah</span>')}
                                                        </td>
                                                        <td class="p-2.5">
                                                            ${r.status === 'Selesai' ? '<span class="px-2.5 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-700 rounded-full">Selesai</span>' :
                                                              (r.status === 'Proses' ? '<span class="px-2.5 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-700 rounded-full">Proses</span>' :
                                                              '<span class="px-2.5 py-0.5 text-[10px] font-semibold bg-amber-100 text-amber-700 rounded-full">Pending</span>')}
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                `}
                            </div>
                        `;
                    }

                    previewArea.innerHTML = html;
                })
                .catch(err => {
                    console.error(err);
                    previewArea.innerHTML = `
                        <div class="p-8 text-center text-rose-500 border border-rose-200 bg-rose-50 rounded-xl">
                            <i class="fa-solid fa-circle-exclamation text-3xl mb-2"></i>
                            <p class="text-sm font-semibold">Gagal memuat pratinjau laporan</p>
                            <p class="text-xs text-rose-400 mt-1">${err.message || 'Terjadi kesalahan sistem.'}</p>
                        </div>
                    `;
                });
        }


        async function refreshServerStats() {
            try {
                const resp = await fetch("/api/server/stats/" + currentServerId);
                const data = await resp.json();
                
                // CPU cards
                document.getElementById("cpu-pct").textContent = (data.cpu_pct || 0).toFixed(1) + "%";
                document.getElementById("cpu-cores").textContent = data.cpu_cores || "--";
                document.getElementById("load-1m").textContent = (data.load_avg && data.load_avg[0]) ? data.load_avg[0].toFixed(2) : "--";
                document.getElementById("server-uptime").textContent = data.uptime || "--";
                
                // Memory cards
                document.getElementById("mem-used").textContent = (data.mem_used_gb || 0).toFixed(1) + " GB";
                document.getElementById("mem-total").textContent = (data.mem_total_gb || 0).toFixed(1) + " GB";
                document.getElementById("mem-pct").textContent = (data.mem_pct || 0).toFixed(1) + "%";
                
                // Disk cards
                document.getElementById("disk-used").textContent = (data.disk_used_gb || 0).toFixed(1) + " GB";
                document.getElementById("disk-total").textContent = (data.disk_total_gb || 0).toFixed(1) + " GB";
                document.getElementById("disk-pct").textContent = (data.disk_pct || 0).toFixed(1) + "%";
                
                // Load detail
                document.getElementById("load-1m-detail").textContent = (data.load_avg && data.load_avg[0]) ? data.load_avg[0].toFixed(2) : "--";
                document.getElementById("load-5m-detail").textContent = (data.load_avg && data.load_avg[1]) ? data.load_avg[1].toFixed(2) : "--";
                document.getElementById("load-15m-detail").textContent = (data.load_avg && data.load_avg[2]) ? data.load_avg[2].toFixed(2) : "--";
                
                // Process table
                const tbody = document.getElementById("process-tbody");
                if (data.top_processes && data.top_processes.length > 0) {
                    tbody.innerHTML = data.top_processes.map(p => `<tr class="border-b border-slate-100 hover:bg-slate-50">
                        <td class="py-1 px-2 font-mono text-xs">${p.user}</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.pid}</td>
                        <td class="py-1 px-2 font-mono text-xs text-rose-600 font-semibold">${p.cpu.toFixed(1)}%</td>
                        <td class="py-1 px-2 font-mono text-xs text-blue-600">${p.mem.toFixed(1)}%</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.vsz}</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.rss}</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.tty}</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.stat}</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.start}</td>
                        <td class="py-1 px-2 font-mono text-xs">${p.time}</td>
                        <td class="py-1 px-2 font-mono text-xs max-w-xs truncate block">${p.command}</td>
                    </tr>`).join("");
                } else {
                    tbody.innerHTML = `<tr><td colspan="11" class="text-center text-slate-400 py-4">Tidak ada data proses</td></tr>`;
                }
                
                // Network interfaces
                const netDiv = document.getElementById("net-interfaces");
                if (data.net_interfaces && data.net_interfaces.length > 0) {
                    netDiv.innerHTML = data.net_interfaces.map(n => `<div class="p-3 bg-slate-50 rounded-lg text-left">
                        <p class="font-semibold text-sm text-slate-800">${n.name} <span class="text-[10px] px-1.5 py-0.5 rounded ${n.status === "UP" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}">${n.status}</span></p>
                        <p class="text-xs text-slate-500 font-mono mt-1">${n.ip || "No IP"}</p>
                    </div>`).join("");
                } else {
                    netDiv.innerHTML = `<div class="col-span-full text-center text-slate-400 py-4">Tidak ada interface</div>`;
                }
            } catch (err) {
                console.error("Gagal memuat server stats:", err);
            }
        }

        // Server List/Detail View Functions
        let serverDetailInterval = null;
        let currentServerId = null;

        function showServerDetail(hostId) {
            // Hide list view, show detail view
            document.getElementById('server-list-view').classList.add('hidden');
            document.getElementById('server-detail-view').classList.remove('hidden');
            currentServerId = hostId;

            // Update header
            const card = document.querySelector('.server-card[data-host-id="' + hostId + '"]');
            if (card) {
                document.getElementById('detail-server-name').innerHTML =
                    '<i class="fa-solid fa-server text-blue-600"></i> ' + card.dataset.hostName;
                document.getElementById('detail-server-meta').textContent =
                    'IP: ' + card.dataset.hostIp + ' | Kategori: ' + card.dataset.hostCategory;
            }

            // Load detail data
            refreshServerDetail();

            // Start auto-refresh
            if (serverDetailInterval) clearInterval(serverDetailInterval);
            serverDetailInterval = setInterval(refreshServerDetail, 10000);
        }

        function showServerList() {
            // Show list view, hide detail view
            document.getElementById('server-detail-view').classList.add('hidden');
            document.getElementById('server-list-view').classList.remove('hidden');
            currentServerId = null;

            // Stop auto-refresh
            if (serverDetailInterval) clearInterval(serverDetailInterval);
            serverDetailInterval = null;
        }

        async function refreshServerDetail() {
            if (!currentServerId) return;
            try {
                const resp = await fetch("/api/server/stats/" + currentServerId);
                const data = await resp.json();

                // Update status badge (simulated - in real scenario you'd check specific host)
                const card = document.querySelector('.server-card[data-host-id="' + currentServerId + '"]');
                if (card) {
                    const isOnline = card.querySelector('.w-2.h-2').classList.contains('bg-emerald-500');
                    document.getElementById('detail-status-indicator').className =
                        'w-3 h-3 rounded-full ' + (isOnline ? 'bg-emerald-500' : 'bg-rose-500');
                    document.getElementById('detail-status-text').textContent = isOnline ? 'ONLINE' : 'OFFLINE';
                    document.getElementById('detail-last-check').textContent =
                        'Terakhir cek: ' + (card.dataset.hostLastCheck || '-');
                }

                // CPU cards
                document.getElementById('detail-cpu-pct').textContent = (data.cpu_pct || 0).toFixed(1) + '%';
                document.getElementById('detail-cpu-cores').textContent = data.cpu_cores || '--';
                document.getElementById('detail-load-1m').textContent = (data.load_avg && data.load_avg[0]) ? data.load_avg[0].toFixed(2) : '--';
                document.getElementById('detail-uptime').textContent = data.uptime || '--';

                // Memory cards
                document.getElementById('detail-mem-used').textContent = (data.mem_used_gb || 0).toFixed(1) + ' GB';
                document.getElementById('detail-mem-total').textContent = (data.mem_total_gb || 0).toFixed(1) + ' GB';
                document.getElementById('detail-mem-pct').textContent = (data.mem_pct || 0).toFixed(1) + '%';

                // Disk cards
                document.getElementById('detail-disk-used').textContent = (data.disk_used_gb || 0).toFixed(1) + ' GB';
                document.getElementById('detail-disk-total').textContent = (data.disk_total_gb || 0).toFixed(1) + ' GB';
                document.getElementById('detail-disk-pct').textContent = (data.disk_pct || 0).toFixed(1) + '%';

                // Load detail
                document.getElementById('detail-load-1m-d').textContent = (data.load_avg && data.load_avg[0]) ? data.load_avg[0].toFixed(2) : '--';
                document.getElementById('detail-load-5m-d').textContent = (data.load_avg && data.load_avg[1]) ? data.load_avg[1].toFixed(2) : '--';
                document.getElementById('detail-load-15m-d').textContent = (data.load_avg && data.load_avg[2]) ? data.load_avg[2].toFixed(2) : '--';

                // Process table
                const tbody = document.getElementById('detail-process-tbody');
                if (data.top_processes && data.top_processes.length > 0) {
                    tbody.innerHTML = data.top_processes.map(p => '<tr class="border-b border-slate-100 hover:bg-slate-50">' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.user + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.pid + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs text-rose-600 font-semibold">' + p.cpu.toFixed(1) + '%</td>' +
                        '<td class="py-1 px-2 font-mono text-xs text-blue-600">' + p.mem.toFixed(1) + '%</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.vsz + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.rss + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.tty + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.stat + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.start + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs">' + p.time + '</td>' +
                        '<td class="py-1 px-2 font-mono text-xs max-w-xs truncate block">' + p.command + '</td>' +
                    '</tr>').join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="11" class="text-center text-slate-400 py-4">Tidak ada data proses</td></tr>';
                }

                // Network interfaces
                const netDiv = document.getElementById('detail-net-interfaces');
                if (data.net_interfaces && data.net_interfaces.length > 0) {
                    netDiv.innerHTML = data.net_interfaces.map(n => '<div class="p-3 bg-slate-50 rounded-lg text-left">' +
                        '<p class="font-semibold text-sm text-slate-800">' + n.name +
                        ' <span class="text-[10px] px-1.5 py-0.5 rounded ' +
                        (n.status === 'UP' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700') + '">' +
                        n.status + '</span></p>' +
                        '<p class="text-xs text-slate-500 font-mono mt-1">' + (n.ip || 'No IP') + '</p>' +
                    '</div>').join('');
                } else {
                    netDiv.innerHTML = '<div class="col-span-full text-center text-slate-400 py-4">Tidak ada interface</div>';
                }

            } catch (err) {
                console.error("Gagal memuat server detail:", err);
            }
        }

        // Keep original showTab for other tabs
        const originalShowTab = showTab;
        showTab = function(tabId) {
            originalShowTab(tabId);
            // Stop server detail refresh if leaving server tab
            if (tabId !== "tab-server") {
                if (serverDetailInterval) clearInterval(serverDetailInterval);
                serverDetailInterval = null;
                currentServerId = null;
                // Ensure list view is shown when re-entering
                document.getElementById('server-list-view').classList.remove('hidden');
                document.getElementById('server-detail-view').classList.add('hidden');
            }
        };
        function downloadExcelPeriod() {
            const start = document.getElementById('report-start')?.value || '';
            const end = document.getElementById('report-end')?.value || '';
            const unit = document.getElementById('report-unit')?.value || '';
            window.location.href = `/export/report?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&unit=${encodeURIComponent(unit)}`;
        }

        // ==================== OPS TASKS, KEBERSIHAN CONVERT & SUPERVISOR JS ====================

        function filterTasksTable() {
            const unitFilter = document.getElementById('tasks-filter-unit')?.value || 'ALL';
            const statusFilter = document.getElementById('tasks-filter-status')?.value || 'ALL';
            const query = (document.getElementById('tasks-search')?.value || '').trim().toLowerCase();

            const rows = document.querySelectorAll('.task-row');
            let total = 0, pending = 0, proses = 0, selesai = 0;

            rows.forEach(row => {
                const rUnit = row.getAttribute('data-unit') || '';
                const rStatus = row.getAttribute('data-status') || '';
                const rSearch = row.getAttribute('data-search') || '';

                const unitMatch = (unitFilter === 'ALL' || rUnit === unitFilter);
                const statusMatch = (statusFilter === 'ALL' || rStatus === statusFilter);
                const queryMatch = (!query || rSearch.includes(query));

                if (unitMatch && statusMatch && queryMatch) {
                    row.style.display = '';
                    total++;
                    if (rStatus === 'Pending') pending++;
                    else if (rStatus === 'Proses') proses++;
                    else if (rStatus === 'Selesai') selesai++;
                } else {
                    row.style.display = 'none';
                }
            });

            const mTotal = document.getElementById('task-metric-total');
            const mPending = document.getElementById('task-metric-pending');
            const mProses = document.getElementById('task-metric-proses');
            const mSelesai = document.getElementById('task-metric-selesai');

            if (mTotal) mTotal.innerText = total;
            if (mPending) mPending.innerText = pending;
            if (mProses) mProses.innerText = proses;
            if (mSelesai) mSelesai.innerText = selesai;
        }

        function filterTodosByUnit(unit) {
            const btns = document.querySelectorAll('.todo-filter-btn');
            btns.forEach(b => {
                if (b.getAttribute('data-unit') === unit) {
                    b.classList.remove('bg-white', 'text-slate-600', 'border', 'border-slate-200');
                    b.classList.add('bg-emerald-600', 'text-white');
                } else {
                    b.classList.remove('bg-emerald-600', 'text-white');
                    b.classList.add('bg-white', 'text-slate-600', 'border', 'border-slate-200');
                }
            });

            const items = document.querySelectorAll('.todo-item');
            items.forEach(it => {
                const itemUnit = it.getAttribute('data-unit') || '';
                if (unit === 'ALL' || itemUnit === unit || itemUnit === 'ALL') {
                    it.style.display = '';
                } else {
                    it.style.display = 'none';
                }
            });
        }

        let currentJournalUnit = 'ALL';
        let currentJournalView = 'table';

        function switchJournalView(mode) {
            currentJournalView = mode;
            const tableContainer = document.getElementById('journal-view-table');
            const cardsContainer = document.getElementById('journal-view-cards');
            const btnTable = document.getElementById('btn-journal-view-table');
            const btnCards = document.getElementById('btn-journal-view-cards');

            if (mode === 'table') {
                if (tableContainer) tableContainer.classList.remove('hidden');
                if (cardsContainer) cardsContainer.classList.add('hidden');
                if (btnTable) {
                    btnTable.className = "px-2.5 py-1 rounded-lg font-bold text-slate-800 bg-white shadow-2xs transition flex items-center gap-1 cursor-pointer";
                    btnTable.querySelector('i').className = "fa-solid fa-table-list text-emerald-600";
                }
                if (btnCards) {
                    btnCards.className = "px-2.5 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-800 transition flex items-center gap-1 cursor-pointer";
                    btnCards.querySelector('i').className = "fa-solid fa-grip text-slate-500";
                }
            } else {
                if (tableContainer) tableContainer.classList.add('hidden');
                if (cardsContainer) cardsContainer.classList.remove('hidden');
                if (btnCards) {
                    btnCards.className = "px-2.5 py-1 rounded-lg font-bold text-slate-800 bg-white shadow-2xs transition flex items-center gap-1 cursor-pointer";
                    btnCards.querySelector('i').className = "fa-solid fa-grip text-emerald-600";
                }
                if (btnTable) {
                    btnTable.className = "px-2.5 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-800 transition flex items-center gap-1 cursor-pointer";
                    btnTable.querySelector('i').className = "fa-solid fa-table-list text-slate-500";
                }
            }
        }

        function filterJournalsByUnit(unit) {
            currentJournalUnit = unit;
            const btns = document.querySelectorAll('.journal-filter-btn');
            btns.forEach(b => {
                if (b.getAttribute('data-unit') === unit) {
                    b.classList.remove('bg-white', 'text-slate-600', 'border', 'border-slate-200');
                    b.classList.add('bg-emerald-600', 'text-white');
                } else {
                    b.classList.remove('bg-emerald-600', 'text-white');
                    b.classList.add('bg-white', 'text-slate-600', 'border', 'border-slate-200');
                }
            });

            applyJournalFilters();
        }

        function searchJournals() {
            applyJournalFilters();
        }

        function applyJournalFilters() {
            const query = (document.getElementById('journal-search-input')?.value || '').toLowerCase().trim();
            const unit = currentJournalUnit;

            // 1. Filter Tabel Rows
            const rows = document.querySelectorAll('.journal-row');
            rows.forEach(r => {
                const rUnit = r.getAttribute('data-unit') || '';
                const text = r.innerText.toLowerCase();
                const unitMatch = (unit === 'ALL' || rUnit === unit || (unit === 'ALL' && rUnit === 'ALL'));
                const queryMatch = !query || text.includes(query);

                if (unitMatch && queryMatch) {
                    r.style.display = '';
                } else {
                    r.style.display = 'none';
                }
            });

            // 2. Filter Cards
            const cards = document.querySelectorAll('.journal-card');
            cards.forEach(c => {
                const cUnit = c.getAttribute('data-unit') || '';
                const text = c.innerText.toLowerCase();
                const unitMatch = (unit === 'ALL' || cUnit === unit || (unit === 'ALL' && cUnit === 'ALL'));
                const queryMatch = !query || text.includes(query);

                if (unitMatch && queryMatch) {
                    c.style.display = '';
                } else {
                    c.style.display = 'none';
                }
            });
        }

        function toggleAddTaskSubScope() {
            const unit = document.getElementById('add-task-unit')?.value;
            const subBox = document.getElementById('add-task-subscope-box');
            if (subBox) {
                if (unit === 'GARDENER') {
                    subBox.classList.remove('hidden');
                } else {
                    subBox.classList.add('hidden');
                }
            }
        }

        async function submitAddTask(e) {
            e.preventDefault();
            const form = document.getElementById('form-add-task');
            const btn = document.getElementById('btn-submit-add-task');
            const formData = new FormData(form);

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Menyimpan...';

            try {
                const res = await fetch('/api/ops/tasks/create', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    let alertMsg = '✅ ' + data.message + ' (ID: ' + data.id + ')';
                    if (data.wa_status) alertMsg += '\\n📲 Status WhatsApp: ' + data.wa_status;
                    alert(alertMsg);
                    window.location.href = '/?tab=tab-tasks';
                } else {
                    alert('❌ Gagal membuat tugas: ' + (data.error || 'Terjadi kesalahan sistem.'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Disposisikan Tugas</span>';
                }
            } catch (err) {
                alert('❌ Error koneksi: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Disposisikan Tugas</span>';
            }
        }

        function openConvertKebersihanModal(pelapor, unit, area, keterangan) {
            document.getElementById('convert-pelapor').innerText = pelapor || '-';
            document.getElementById('convert-unit-asal').innerText = unit || 'OB';
            document.getElementById('convert-area').innerText = area || '-';
            document.getElementById('convert-keterangan').innerText = keterangan || '-';

            document.getElementById('convert-hidden-pelapor').value = pelapor || '';
            document.getElementById('convert-hidden-area').value = area || '';
            document.getElementById('convert-hidden-keterangan').value = keterangan || '';

            const unitSelect = document.getElementById('convert-unit-code');
            if (unitSelect) {
                if (unit && unit.toLowerCase().includes('garden')) unitSelect.value = 'GARDENER';
                else if (unit && unit.toLowerCase().includes('sec')) unitSelect.value = 'SECURITY';
                else if (unit && unit.toLowerCase().includes('it')) unitSelect.value = 'IT';
                else unitSelect.value = 'OB';
            }

            toggleConvertSubScope();
            toggleModal('modal-convert-kebersihan-task');
        }

        function toggleConvertSubScope() {
            const unit = document.getElementById('convert-unit-code')?.value;
            const box = document.getElementById('convert-subscope-container');
            if (box) {
                if (unit === 'GARDENER') box.classList.remove('hidden');
                else box.classList.add('hidden');
            }
        }

        async function submitConvertKebersihan(e) {
            e.preventDefault();
            const form = document.getElementById('form-convert-kebersihan');
            const btn = document.getElementById('btn-submit-convert');
            const formData = new FormData(form);

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Memproses...';

            try {
                const res = await fetch('/api/ops/tasks/convert_kebersihan', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    let msg = '✅ ' + data.message;
                    if (data.wa_status) msg += '\\n📲 Notifikasi WA: ' + data.wa_status;
                    alert(msg);
                    window.location.href = '/?tab=tab-tasks';
                } else {
                    alert('❌ Gagal konversi tiket: ' + (data.error || 'Terjadi kesalahan sistem.'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Disposisikan & Buat Tiket</span>';
                }
            } catch (err) {
                alert('❌ Error koneksi: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Disposisikan & Buat Tiket</span>';
            }
        }

        function openSetPhotoModal(timestamp, nama, area, existingUrl) {
            document.getElementById('set-photo-timestamp').value = timestamp || '';
            document.getElementById('set-photo-nama').innerText = nama || '-';
            document.getElementById('set-photo-area').innerText = area || '-';
            document.getElementById('set-photo-url').value = existingUrl || '';
            toggleModal('modal-set-kebersihan-photo');
        }

        async function submitSetPhoto(e) {
            e.preventDefault();
            const timestamp = document.getElementById('set-photo-timestamp').value;
            const photoUrl = document.getElementById('set-photo-url').value.trim();
            const btn = document.getElementById('btn-submit-set-photo');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Menyimpan...';
            try {
                const res = await fetch('/api/kebersihan/update_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ timestamp, photo_url: photoUrl })
                });
                const data = await res.json();
                if (res.ok && data.status === 'ok') {
                    alert('✅ ' + (data.message || 'Link Foto Drive berhasil disimpan!'));
                    window.location.reload();
                } else {
                    alert('❌ Gagal: ' + (data.message || 'Terjadi kesalahan'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-save"></i> <span>Simpan Link</span>';
                }
            } catch(err) {
                alert('❌ Error koneksi: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-save"></i> <span>Simpan Link</span>';
            }
        }

        async function syncDrivePhotos() {
            const btn = document.getElementById('btn-sync-photos');
            const origHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> <span>Menyinkronkan...</span>';
            try {
                const res = await fetch('/api/kebersihan/sync_drive', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'ok') {
                    alert(`✅ ${data.message || 'Sinkronisasi berhasil!'}`);
                    window.location.reload();
                } else {
                    alert(`ℹ️ ${data.message || 'Gagal menyinkronkan foto dari Google Sheet.'}`);
                    btn.disabled = false;
                    btn.innerHTML = origHtml;
                }
            } catch(err) {
                alert('❌ Error: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
        }

        function openUpdateTaskModal(id, title, status, notes) {
            document.getElementById('update-task-id').value = id;
            document.getElementById('update-task-title').innerText = title || '-';
            document.getElementById('update-task-notes').value = notes || '';

            const pRadio = document.getElementById('status-pending');
            const prRadio = document.getElementById('status-proses');
            const sRadio = document.getElementById('status-selesai');

            if (status === 'Selesai' && sRadio) sRadio.checked = true;
            else if (status === 'Proses' && prRadio) prRadio.checked = true;
            else if (pRadio) pRadio.checked = true;

            toggleModal('modal-update-ops-task');
        }

        async function submitUpdateOpsTask(e) {
            e.preventDefault();
            const form = document.getElementById('form-update-task');
            const btn = document.getElementById('btn-submit-update-task');
            const taskId = document.getElementById('update-task-id').value;
            const formData = new FormData(form);

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Menyimpan...';

            try {
                const res = await fetch('/api/ops/tasks/' + taskId + '/update', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    window.location.href = '/?tab=tab-tasks';
                } else {
                    alert('❌ Gagal update: ' + (data.error || 'Terjadi kesalahan.'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span>Simpan Perubahan</span>';
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span>Simpan Perubahan</span>';
            }
        }

        async function deleteOpsTask(id) {
            if (!confirm('Apakah Anda yakin ingin menghapus tiket ini?')) return;
            try {
                const res = await fetch('/api/ops/tasks/' + id + '/delete', { method: 'POST' });
                const data = await res.json();
                if (res.ok && data.success) {
                    window.location.href = '/?tab=tab-tasks';
                } else {
                    alert('❌ Gagal menghapus: ' + (data.error || 'Gagal'));
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
            }
        }

        function openSupervisorFeedbackModal(id, title, author, existingFeedback) {
            document.getElementById('feedback-journal-id').value = id;
            document.getElementById('feedback-journal-title').innerText = title || '-';
            document.getElementById('feedback-journal-author').innerText = 'Oleh: ' + (author || 'Mr Slam');
            document.getElementById('feedback-text').value = existingFeedback || '';

            toggleModal('modal-supervisor-feedback');
        }

        async function submitSupervisorFeedback(e) {
            e.preventDefault();
            const form = document.getElementById('form-supervisor-feedback');
            const btn = document.getElementById('btn-submit-feedback');
            const journalId = document.getElementById('feedback-journal-id').value;
            const formData = new FormData(form);

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Menyimpan...';

            try {
                const res = await fetch('/api/ops/journals/' + journalId + '/feedback', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert('✅ ' + data.message);
                    window.location.href = '/?tab=tab-journal';
                } else {
                    alert('❌ Gagal: ' + (data.error || 'Terjadi kesalahan'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> <span>Simpan Catatan Supervisi</span>';
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-check"></i> <span>Simpan Catatan Supervisi</span>';
            }
        }

        function openEditJournalModal(btn) {
            document.getElementById('edit-journal-id').value = btn.dataset.id || '';
            document.getElementById('edit-journal-title').value = btn.dataset.title || '';
            if (document.getElementById('edit-journal-category')) {
                document.getElementById('edit-journal-category').value = btn.dataset.category || 'Operasional';
            }
            if (document.getElementById('edit-journal-unit')) {
                document.getElementById('edit-journal-unit').value = btn.dataset.unit || 'ALL';
            }
            document.getElementById('edit-journal-date').value = btn.dataset.date || '';
            document.getElementById('edit-journal-time').value = btn.dataset.time || '';
            document.getElementById('edit-journal-desc').value = btn.dataset.desc || '';
            document.getElementById('edit-journal-output').value = btn.dataset.output || '';
            toggleModal('modal-edit-journal');
        }

        // ==================== OPS PROCUREMENTS (PENGADAAN) JS ====================

        function filterProcurementsTable() {
            const unitFilter = document.getElementById('proc-filter-unit')?.value || 'ALL';
            const statusFilter = document.getElementById('proc-filter-status')?.value || 'ALL';
            const query = (document.getElementById('proc-search')?.value || '').trim().toLowerCase();

            const rows = document.querySelectorAll('.proc-row');
            let total = 0, pending = 0, proses = 0, selesai = 0;

            rows.forEach(row => {
                const rUnit = row.getAttribute('data-unit') || '';
                const rStatus = row.getAttribute('data-status') || '';
                const rSearch = row.getAttribute('data-search') || '';

                const unitMatch = (unitFilter === 'ALL' || rUnit === unitFilter);
                const statusMatch = (statusFilter === 'ALL' || rStatus === statusFilter);
                const queryMatch = (!query || rSearch.includes(query));

                if (unitMatch && statusMatch && queryMatch) {
                    row.style.display = '';
                    total++;
                    if (rStatus === 'Diajukan') pending++;
                    else if (rStatus === 'Disetujui' || rStatus === 'Proses Beli') proses++;
                    else if (rStatus === 'Barang Tiba' || rStatus === 'Diserahkan' || rStatus === 'Selesai') selesai++;
                } else {
                    row.style.display = 'none';
                }
            });

            const mTotal = document.getElementById('proc-metric-total');
            const mPending = document.getElementById('proc-metric-pending');
            const mProses = document.getElementById('proc-metric-proses');
            const mSelesai = document.getElementById('proc-metric-selesai');

            if (mTotal) mTotal.innerText = total;
            if (mPending) mPending.innerText = pending;
            if (mProses) mProses.innerText = proses;
            if (mSelesai) mSelesai.innerText = selesai;
        }

        function openCreatePengadaanModalFromTaskBtn(btn) {
            const taskId = btn.getAttribute('data-id');
            const taskTitle = btn.getAttribute('data-title');
            const unit = btn.getAttribute('data-unit');
            openCreatePengadaanModalFromTask(taskId, taskTitle, unit);
        }

        function openCreatePengadaanModalFromTask(taskId, taskTitle, unit) {
            document.getElementById('add-proc-ticket-ref').value = taskId || '';
            document.getElementById('add-proc-ticket-label').innerText = taskId + ' (' + taskTitle + ')';
            document.getElementById('add-proc-ticket-banner').classList.remove('hidden');

            document.getElementById('add-proc-title').value = 'Material: ' + taskTitle;

            const unitSelect = document.getElementById('add-proc-unit');
            if (unitSelect) {
                unitSelect.value = (unit && unit !== 'ALL') ? unit : 'SARPRAS';
            }

            toggleModal('modal-add-pengadaan');
        }

        function clearTicketRefPengadaan() {
            document.getElementById('add-proc-ticket-ref').value = '';
            document.getElementById('add-proc-ticket-banner').classList.add('hidden');
        }

        async function submitCreatePengadaan(e) {
            e.preventDefault();
            const form = document.getElementById('form-add-pengadaan');
            const btn = document.getElementById('btn-submit-add-proc');
            const formData = new FormData(form);

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Mengirim...';

            try {
                const res = await fetch('/api/ops/procurements/create', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    let msg = '✅ ' + data.message;
                    if (data.wa_status) msg += '\\n📲 WhatsApp: ' + data.wa_status;
                    alert(msg);
                    window.location.href = '/?tab=tab-pengadaan';
                } else {
                    alert('❌ Gagal: ' + (data.error || 'Terjadi kesalahan sistem'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Kirim Pengajuan</span>';
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Kirim Pengajuan</span>';
            }
        }

        function openApproveModalFromBtn(btn) {
            const id = btn.getAttribute('data-id');
            const title = btn.getAttribute('data-title');
            const estCost = btn.getAttribute('data-cost');
            const reqBy = btn.getAttribute('data-req');
            openApprovePengadaanModal(id, title, estCost, reqBy);
        }

        function openUpdateModalFromBtn(btn) {
            const id = btn.getAttribute('data-id');
            const title = btn.getAttribute('data-title');
            const status = btn.getAttribute('data-status');
            const estCost = btn.getAttribute('data-cost');
            const actCost = btn.getAttribute('data-act');
            const vendor = btn.getAttribute('data-vendor');
            const receipt = btn.getAttribute('data-receipt');
            const notes = btn.getAttribute('data-notes');
            openUpdatePengadaanModal(id, title, status, estCost, actCost, vendor, receipt, notes);
        }

        function openApprovePengadaanModal(id, title, estCost, reqBy) {
            document.getElementById('approve-proc-id').value = id;
            document.getElementById('approve-proc-id-label').innerText = id;
            document.getElementById('approve-proc-title').innerText = title;
            document.getElementById('approve-proc-req').innerText = reqBy;
            document.getElementById('approve-proc-cost').innerText = 'Rp ' + Number(estCost || 0).toLocaleString('id-ID');
            document.getElementById('approve-proc-note').value = '';

            toggleModal('modal-approve-pengadaan');
        }

        async function submitApprovePengadaan(action) {
            const id = document.getElementById('approve-proc-id').value;
            const note = document.getElementById('approve-proc-note').value;

            if (action === 'reject' && !confirm('Apakah Anda yakin ingin MENOLAK pengajuan pengadaan ini?')) return;

            try {
                const res = await fetch('/api/ops/procurements/' + id + '/approve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action, approver_note: note })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    let msg = '✅ ' + data.message;
                    if (data.wa_status) msg += '\\n📲 ' + data.wa_status;
                    alert(msg);
                    window.location.href = '/?tab=tab-pengadaan';
                } else {
                    alert('❌ Gagal: ' + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
            }
        }

        function openUpdatePengadaanModal(id, title, status, estCost, actCost, vendor, receipt, notes) {
            document.getElementById('update-proc-id').value = id;
            document.getElementById('update-proc-title').innerText = id + ' - ' + title;
            document.getElementById('update-proc-est-cost').innerText = 'Rp ' + Number(estCost || 0).toLocaleString('id-ID');
            document.getElementById('update-proc-act-cost').value = actCost || '';
            document.getElementById('update-proc-receipt').value = receipt || '';
            document.getElementById('update-proc-vendor').value = vendor || '';
            document.getElementById('update-proc-notes').value = notes || '';

            const rProses = document.getElementById('proc-status-proses');
            const rTiba = document.getElementById('proc-status-tiba');
            const rSelesai = document.getElementById('proc-status-selesai');

            if (status === 'Barang Tiba' && rTiba) rTiba.checked = true;
            else if ((status === 'Diserahkan' || status === 'Selesai') && rSelesai) rSelesai.checked = true;
            else if (rProses) rProses.checked = true;

            toggleModal('modal-update-pengadaan');
        }

        async function submitUpdatePengadaan(e) {
            e.preventDefault();
            const form = document.getElementById('form-update-pengadaan');
            const btn = document.getElementById('btn-submit-update-proc');
            const id = document.getElementById('update-proc-id').value;
            const formData = new FormData(form);

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Menyimpan...';

            try {
                const res = await fetch('/api/ops/procurements/' + id + '/update', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    let msg = '✅ ' + data.message;
                    if (data.wa_status) msg += '\\n📲 ' + data.wa_status;
                    alert(msg);
                    window.location.href = '/?tab=tab-pengadaan';
                } else {
                    alert('❌ Gagal: ' + (data.error || 'Terjadi kesalahan'));
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span>Simpan Perubahan</span>';
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span>Simpan Perubahan</span>';
            }
        }

        async function deletePengadaan(id) {
            if (!confirm('Apakah Anda yakin ingin menghapus pengajuan pengadaan ini?')) return;
            try {
                const res = await fetch('/api/ops/procurements/' + id + '/delete', { method: 'POST' });
                const data = await res.json();
                if (res.ok && data.success) {
                    window.location.href = '/?tab=tab-pengadaan';
                } else {
                    alert('❌ Gagal: ' + (data.error || 'Gagal'));
                }
            } catch (err) {
                alert('❌ Error: ' + err.message);
            }
        }

        // ============ SISTEM MONITORING CHECKLIST PEMELIHARAAN & GREEN OPS ============
        let currentChecklistSubview = 'radar';

        function switchChecklistSubview(subviewId) {
            currentChecklistSubview = subviewId;
            document.querySelectorAll('.chk-sub-tab').forEach(b => {
                b.className = "chk-sub-tab px-3.5 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition cursor-pointer";
            });
            document.getElementById(`btn-chk-sub-${subviewId}`).className = "chk-sub-tab px-3.5 py-1.5 rounded-lg bg-white text-emerald-700 shadow-xs transition cursor-pointer";

            document.getElementById('chk-subview-radar').classList.add('hidden');
            document.getElementById('chk-subview-tickets').classList.add('hidden');
            document.getElementById('chk-subview-green').classList.add('hidden');
            document.getElementById('chk-subview-zones').classList.add('hidden');
            document.getElementById('chk-subview-templates').classList.add('hidden');

            document.getElementById(`chk-subview-${subviewId}`).classList.remove('hidden');

            if (subviewId === 'radar') loadChecklistDashboard();
            if (subviewId === 'tickets') loadChecklistTickets();
            if (subviewId === 'green') loadChecklistGreenStats();
            if (subviewId === 'zones') loadChecklistZones();
            if (subviewId === 'templates') loadChecklistTemplates();
        }

        async function loadChecklistDashboard() {
            const unit = document.getElementById('filter-chk-unit').value;
            const url = `/api/ops/checklist/radar?unit=${encodeURIComponent(unit)}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                if (!data.success) return;

                // Update Metric Cards
                document.getElementById('stat-chk-controlled').innerText = `${data.filled_ok + data.filled_anomaly} / ${data.total_zones}`;
                document.getElementById('stat-chk-compliance').innerText = `${data.compliance_pct}%`;
                document.getElementById('stat-chk-open-tickets').innerText = data.open_tickets;
                document.getElementById('chk-radar-date').innerText = `Tanggal: ${data.date}`;

                // Render Radar Table
                const tbody = document.getElementById('chk-radar-tbody');
                if (!data.radar || data.radar.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400">Belum ada data zona pemeliharaan.</td></tr>';
                    return;
                }

                let html = '';
                data.radar.forEach(item => {
                    const z = item.zone;
                    const shifts = item.shifts;

                    function renderPill(sData) {
                        if (!sData.checked) {
                            return '<span class="inline-block px-2.5 py-1 rounded-md text-[10px] font-bold bg-slate-100 text-slate-400 border border-slate-200">Belum</span>';
                        }
                        if (sData.status === 'ALL_OK') {
                            return `<div class="inline-flex flex-col items-center"><span class="px-2.5 py-1 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">✓ NORMAL</span><span class="text-[9px] text-slate-400 mt-0.5">${sData.time} &bull; ${sData.petugas}</span></div>`;
                        }
                        return `<div class="inline-flex flex-col items-center"><span class="px-2.5 py-1 rounded-md text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">⚠️ RUSAK</span><span class="text-[9px] text-rose-600 font-mono mt-0.5 font-bold">${sData.ticket_id || 'TIKET'}</span></div>`;
                    }

                    html += `
                        <tr class="hover:bg-slate-50/80 transition">
                            <td class="py-3 px-4 font-bold text-slate-700">
                                <span class="text-[10px] font-black px-1.5 py-0.5 rounded ${z.unit_type === 'OB' ? 'bg-sky-100 text-sky-800' : 'bg-emerald-100 text-emerald-800'} uppercase mr-1">${z.unit_type}</span>
                                ${z.building_or_sector}
                            </td>
                            <td class="py-3 px-4 font-semibold text-slate-800">${z.zone_name}</td>
                            <td class="py-3 px-3 text-center">${renderPill(shifts.PAGI)}</td>
                            <td class="py-3 px-3 text-center">${renderPill(shifts.SIANG_1)}</td>
                            <td class="py-3 px-3 text-center">${renderPill(shifts.SIANG_2)}</td>
                            <td class="py-3 px-3 text-center">${renderPill(shifts.SORE)}</td>
                            <td class="py-3 px-4 text-center">
                                <div class="flex items-center justify-center gap-1.5">
                                    <a href="/c/${z.qr_token}" target="_blank" title="Buka Form Micro-Web" class="p-1.5 text-slate-500 hover:text-emerald-600 rounded-lg hover:bg-emerald-50 transition">
                                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                                    </a>
                                    <a href="/checklist/print-qr?zone_id=${z.id}" target="_blank" title="Cetak Stiker QR" class="p-1.5 text-slate-500 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition">
                                        <i class="fa-solid fa-qrcode"></i>
                                    </a>
                                    <button type="button" onclick="openModalEditChecklistZone('${z.id}')" title="Edit Titik Zona" class="p-1.5 text-slate-500 hover:text-amber-600 rounded-lg hover:bg-amber-50 transition cursor-pointer">
                                        <i class="fa-solid fa-pen-to-square"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;

                // Auto-refresh stats green
                loadChecklistGreenStats(false);
            } catch (err) {
                console.error("Gagal load checklist radar:", err);
            }
        }

        async function loadChecklistTickets() {
            const status = document.getElementById('filter-chk-ticket-status').value;
            const url = `/api/ops/checklist/tickets?status=${encodeURIComponent(status)}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                const tbody = document.getElementById('chk-tickets-tbody');
                if (!data.tickets || data.tickets.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-400">Tidak ada tiket kerusakan fasilitas saat ini.</td></tr>';
                    return;
                }

                let html = '';
                data.tickets.forEach(t => {
                    const isHigh = t.priority === 'HIGH' || t.priority === 'EMERGENCY';
                    const prioBadge = isHigh ? 
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">🚨 TINGGI</span>' : 
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">⚠️ SEDANG</span>';

                    const isResolved = t.status === 'RESOLVED';
                    const statusBadge = isResolved ?
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">✓ SELESAI</span>' :
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">⏳ OPEN</span>';

                    let actionBtn = '';
                    if (!isResolved) {
                        actionBtn = `<button type="button" onclick="openResolveTicketModal('${t.ticket_id}', '${escape(t.issue_description)}')" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[10px] font-bold shadow-xs flex items-center gap-1 cursor-pointer"><i class="fa-solid fa-wrench"></i> Selesaikan</button>`;
                    } else {
                        actionBtn = `<span class="text-[10px] text-slate-400 font-medium">Selesai: ${t.assigned_tech_name || 'Sarpras'}</span>`;
                    }

                    html += `
                        <tr class="hover:bg-slate-50 transition">
                            <td class="py-3 px-3 font-mono font-bold text-slate-900">${t.ticket_id}</td>
                            <td class="py-3 px-3 space-y-1">
                                ${prioBadge}
                                <div class="text-[10px] text-slate-500">${t.category}</div>
                            </td>
                            <td class="py-3 px-4">
                                <div class="font-bold text-slate-800">${t.zone_name || '-'}</div>
                                <div class="text-[10px] text-slate-400">${t.building_or_sector || '-'}</div>
                            </td>
                            <td class="py-3 px-4 text-slate-700 max-w-xs">
                                <p class="font-medium">${t.issue_description}</p>
                                ${t.photo_before_url ? `<a href="${t.photo_before_url}" target="_blank" class="text-[10px] text-indigo-600 underline hover:text-indigo-800 mt-1 inline-block"><i class="fa-solid fa-image"></i> Lihat Foto Bukti</a>` : ''}
                            </td>
                            <td class="py-3 px-3 font-semibold text-slate-800">${t.reporter_name}</td>
                            <td class="py-3 px-3 font-bold text-slate-700">${t.sla_hours} Jam</td>
                            <td class="py-3 px-3">${statusBadge}</td>
                            <td class="py-3 px-3 text-center">${actionBtn}</td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            } catch (err) {
                console.error("Gagal load tiket sarpras:", err);
            }
        }

        function openResolveTicketModal(ticketId, descEscaped) {
            document.getElementById('resolve-ticket-id').value = ticketId;
            document.getElementById('resolve-ticket-display').innerText = ticketId;
            document.getElementById('resolve-ticket-desc').innerText = unescape(descEscaped);
            toggleModal('modal-resolve-checklist-ticket');
        }

        async function submitResolveTicket(event) {
            event.preventDefault();
            const btn = document.getElementById('btn-submit-resolve');
            const ticketId = document.getElementById('resolve-ticket-id').value;
            const techName = document.getElementById('resolve-tech-name').value.trim();
            const notes = document.getElementById('resolve-notes').value.trim();

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

            try {
                const res = await fetch(`/api/ops/checklist/tickets/${encodeURIComponent(ticketId)}/resolve`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tech_name: techName, resolution_notes: notes })
                });
                const data = await res.json();
                if (data.success) {
                    toggleModal('modal-resolve-checklist-ticket');
                    loadChecklistTickets();
                    loadChecklistDashboard();
                } else {
                    alert('Gagal: ' + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-check-double"></i> Konfirmasi Selesai';
            }
        }

        async function loadChecklistGreenStats(updateCardsOnly = false) {
            try {
                const res = await fetch('/api/ops/checklist/green-stats');
                const data = await res.json();
                if (!data.success) return;
                const m = data.metrics;

                document.getElementById('stat-chk-green-impact').innerText = `${m.water_liters_saved.toLocaleString('id-ID')} L`;
                document.getElementById('stat-chk-paper-sub').innerText = `${m.paper_sheets_saved} lembar kertas dihemat`;

                if (!updateCardsOnly) {
                    document.getElementById('green-metric-paper').innerText = m.paper_sheets_saved;
                    document.getElementById('green-metric-rim').innerText = m.paper_rim_equivalent;
                    document.getElementById('green-metric-water').innerText = m.water_liters_saved.toLocaleString('id-ID');
                    document.getElementById('green-metric-leaks').innerText = m.leaks_resolved;
                    document.getElementById('green-metric-energy').innerText = m.kwh_electricity_saved;
                    document.getElementById('green-metric-shutoff').innerText = m.energy_closing_checks;
                    document.getElementById('green-metric-waste').innerText = m.organic_waste_kg;
                }
            } catch (err) {
                console.error("Gagal load green stats:", err);
            }
        }

        let cachedChecklistZones = [];

        async function loadChecklistZones() {
            try {
                const res = await fetch('/api/ops/checklist/zones');
                const data = await res.json();
                const tbody = document.getElementById('chk-zones-tbody');
                if (!data.zones || data.zones.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Belum ada titik zona master.</td></tr>';
                    return;
                }

                cachedChecklistZones = data.zones || [];
                let html = '';
                cachedChecklistZones.forEach(z => {
                    const statusBadge = (z.is_active === undefined || z.is_active == 1) ?
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">AKTIF</span>' :
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200">NON-AKTIF</span>';

                    html += `
                        <tr class="hover:bg-slate-50 transition">
                            <td class="py-3 px-3 font-mono font-bold text-slate-800 text-[11px]">${z.id}</td>
                            <td class="py-3 px-3 font-semibold text-slate-700">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-black ${z.unit_type === 'OB' ? 'bg-sky-100 text-sky-800' : 'bg-emerald-100 text-emerald-800'} uppercase mr-1">${z.unit_type}</span>
                                ${z.building_or_sector}
                            </td>
                            <td class="py-3 px-4 font-bold text-slate-800">${z.zone_name}</td>
                            <td class="py-3 px-3 font-mono text-[10px] text-slate-500">${Number(z.target_lat).toFixed(5)}, ${Number(z.target_lng).toFixed(5)}</td>
                            <td class="py-3 px-3 font-bold text-slate-700">${z.geofence_radius_m} m</td>
                            <td class="py-3 px-3 text-center">${statusBadge}</td>
                            <td class="py-3 px-4 text-center">
                                <div class="flex items-center justify-center gap-1.5 flex-wrap">
                                    <a href="/c/${z.qr_token}" target="_blank" title="Buka Form Micro-Web PWA" class="p-1.5 text-slate-500 hover:text-emerald-600 rounded-lg hover:bg-emerald-50 transition">
                                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                                    </a>
                                    <a href="/checklist/print-qr?zone_id=${z.id}" target="_blank" title="Cetak Stiker QR Akrilik" class="p-1.5 text-slate-500 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition">
                                        <i class="fa-solid fa-qrcode"></i>
                                    </a>
                                    <button type="button" onclick="openModalEditChecklistZone('${z.id}')" title="Edit Titik Zona" class="p-1.5 text-slate-500 hover:text-amber-600 rounded-lg hover:bg-amber-50 transition cursor-pointer">
                                        <i class="fa-solid fa-pen-to-square"></i>
                                    </button>
                                    <button type="button" onclick="deleteChecklistZone('${z.id}', '${escape(z.zone_name)}')" title="Hapus / Nonaktifkan Zona" class="p-1.5 text-slate-500 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition cursor-pointer">
                                        <i class="fa-solid fa-trash-can"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            } catch (err) {
                console.error("Gagal load checklist zones:", err);
            }
        }

        function openModalCreateChecklistZone() {
            document.getElementById('modal-chk-zone-title').innerHTML = '<i class="fa-solid fa-plus-circle text-emerald-600"></i><span>Tambah Titik Zona Pemeliharaan</span>';
            document.getElementById('chk-zone-original-id').value = '';
            document.getElementById('chk-zone-id').value = '';
            document.getElementById('chk-zone-id').disabled = false;
            document.getElementById('chk-zone-id-hint').classList.add('hidden');
            document.getElementById('chk-zone-unit').value = 'OB';
            document.getElementById('chk-zone-name').value = '';
            document.getElementById('chk-zone-building').value = '';
            document.getElementById('chk-zone-subscope').value = 'INDOOR_SANITASI';
            document.getElementById('chk-zone-lat').value = '-6.339295';
            document.getElementById('chk-zone-lng').value = '106.964365';
            document.getElementById('chk-zone-radius').value = '45';
            document.getElementById('chk-zone-active').value = '1';
            document.getElementById('btn-save-chk-zone-text').innerText = 'Simpan Titik Zona';
            toggleModal('modal-create-checklist-zone');
        }

        async function openModalEditChecklistZone(zoneId) {
            let z = cachedChecklistZones.find(item => item.id === zoneId);
            if (!z) {
                try {
                    const res = await fetch(`/api/ops/checklist/zones/${encodeURIComponent(zoneId)}`);
                    const data = await res.json();
                    if (data.success && data.zone) {
                        z = data.zone;
                        cachedChecklistZones.push(z);
                    }
                } catch (e) {
                    console.error("Gagal fetch detail zone:", e);
                }
            }

            if (!z) {
                alert("Data titik zona tidak ditemukan!");
                return;
            }

            document.getElementById('modal-chk-zone-title').innerHTML = '<i class="fa-solid fa-pen-to-square text-amber-600"></i><span>Edit Titik Zona Pemeliharaan</span>';
            document.getElementById('chk-zone-original-id').value = z.id;
            document.getElementById('chk-zone-id').value = z.id;
            document.getElementById('chk-zone-id').disabled = true;
            document.getElementById('chk-zone-id-hint').classList.remove('hidden');
            document.getElementById('chk-zone-unit').value = z.unit_type;
            document.getElementById('chk-zone-name').value = z.zone_name;
            document.getElementById('chk-zone-building').value = z.building_or_sector;
            document.getElementById('chk-zone-subscope').value = z.sub_scope || 'INDOOR_SANITASI';
            document.getElementById('chk-zone-lat').value = z.target_lat;
            document.getElementById('chk-zone-lng').value = z.target_lng;
            document.getElementById('chk-zone-radius').value = z.geofence_radius_m;
            document.getElementById('chk-zone-active').value = (z.is_active !== undefined) ? String(z.is_active) : '1';
            document.getElementById('btn-save-chk-zone-text').innerText = 'Perbarui Titik Zona';

            toggleModal('modal-create-checklist-zone');
        }

        function fillCurrentGpsToChecklistZone() {
            if (!navigator.geolocation) {
                alert("Browser tidak mendukung GPS.");
                return;
            }
            navigator.geolocation.getCurrentPosition(
                pos => {
                    document.getElementById('chk-zone-lat').value = pos.coords.latitude.toFixed(6);
                    document.getElementById('chk-zone-lng').value = pos.coords.longitude.toFixed(6);
                    alert(`Koordinat GPS terkunci: ${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`);
                },
                err => {
                    alert("Gagal mengunci GPS: " + err.message);
                },
                { enableHighAccuracy: true, timeout: 8000 }
            );
        }

        async function saveChecklistZone(event) {
            event.preventDefault();
            const originalId = document.getElementById('chk-zone-original-id').value.trim();
            const btn = document.getElementById('btn-save-chk-zone');
            
            const payload = {
                id: document.getElementById('chk-zone-id').value.trim(),
                unit_type: document.getElementById('chk-zone-unit').value,
                zone_name: document.getElementById('chk-zone-name').value.trim(),
                building_or_sector: document.getElementById('chk-zone-building').value.trim(),
                sub_scope: document.getElementById('chk-zone-subscope').value,
                target_lat: parseFloat(document.getElementById('chk-zone-lat').value),
                target_lng: parseFloat(document.getElementById('chk-zone-lng').value),
                geofence_radius_m: parseInt(document.getElementById('chk-zone-radius').value),
                is_active: parseInt(document.getElementById('chk-zone-active').value)
            };

            const url = originalId ? `/api/ops/checklist/zones/${encodeURIComponent(originalId)}/edit` : `/api/ops/checklist/zones/create`;

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    toggleModal('modal-create-checklist-zone');
                    loadChecklistZones();
                    loadChecklistDashboard();
                } else {
                    alert('Gagal: ' + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span id="btn-save-chk-zone-text">' + (originalId ? 'Perbarui Titik Zona' : 'Simpan Titik Zona') + '</span>';
            }
        }

        async function deleteChecklistZone(zoneId, zoneNameEscaped) {
            const name = unescape(zoneNameEscaped);
            if (!confirm(`Apakah Anda yakin ingin menghapus atau menonaktifkan titik zona "${name}" (${zoneId})?`)) {
                return;
            }

            try {
                const res = await fetch(`/api/ops/checklist/zones/${encodeURIComponent(zoneId)}/delete`, {
                    method: 'POST'
                });
                const data = await res.json();
                if (data.success) {
                    alert(data.message || 'Zona berhasil dihapus/dinonaktifkan.');
                    loadChecklistZones();
                    loadChecklistDashboard();
                } else {
                    alert('Gagal: ' + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }

        // ============ CHECKLIST TEMPLATES (DYNAMIC CRUD) ============
        let cachedChecklistTemplates = [];

        async function loadChecklistTemplates() {
            const unit = document.getElementById('filter-chk-tpl-unit')?.value || '';
            const subscope = document.getElementById('filter-chk-tpl-subscope')?.value || '';
            const shift = document.getElementById('filter-chk-tpl-shift')?.value || '';
            const active = document.getElementById('filter-chk-tpl-active')?.value || '';

            const params = new URLSearchParams();
            if (unit) params.append('unit', unit);
            if (subscope) params.append('sub_scope', subscope);
            if (shift) params.append('shift', shift);
            if (active !== '') params.append('is_active', active);

            const url = `/api/ops/checklist/templates?${params.toString()}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                const tbody = document.getElementById('chk-templates-tbody');
                const badge = document.getElementById('chk-templates-count-badge');

                if (!data.success) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500 font-semibold">Gagal memuat butir checklist.</td></tr>';
                    return;
                }

                cachedChecklistTemplates = data.templates || [];
                if (badge) badge.innerText = `${cachedChecklistTemplates.length} Butir`;

                if (cachedChecklistTemplates.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Tidak ada butir checklist yang cocok dengan filter.</td></tr>';
                    return;
                }

                let html = '';
                cachedChecklistTemplates.forEach(tpl => {
                    const isEco = tpl.is_eco_critical == 1;
                    const isActive = tpl.is_active == 1;

                    const unitBadge = tpl.unit_type === 'OB' ?
                        '<span class="px-1.5 py-0.5 rounded text-[10px] font-black bg-sky-100 text-sky-800 uppercase mr-1">OB</span>' :
                        '<span class="px-1.5 py-0.5 rounded text-[10px] font-black bg-emerald-100 text-emerald-800 uppercase mr-1">GARDENER</span>';

                    let shiftBadge = '';
                    if (tpl.shift_code === 'PAGI') shiftBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">🌅 Pagi</span>';
                    else if (tpl.shift_code === 'SIANG_1') shiftBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">☀️ Siang 1</span>';
                    else if (tpl.shift_code === 'SIANG_2') shiftBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">🌤️ Siang 2</span>';
                    else if (tpl.shift_code === 'SORE') shiftBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">🌆 Sore</span>';
                    else shiftBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">🕒 All Day</span>';

                    const ecoBadge = isEco ?
                        '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 inline-flex items-center gap-1 justify-center"><i class="fa-solid fa-leaf text-emerald-600"></i> Eco-Critical</span>' :
                        '<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-500 border border-slate-200">Standar</span>';

                    const statusBadge = isActive ?
                        `<button type="button" onclick="toggleChecklistTemplateActive(${tpl.id})" title="Klik untuk nonaktifkan" class="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200 transition cursor-pointer">✓ AKTIF</button>` :
                        `<button type="button" onclick="toggleChecklistTemplateActive(${tpl.id})" title="Klik untuk aktifkan" class="px-2.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-400 border border-slate-200 hover:bg-slate-200 transition cursor-pointer">NON-AKTIF</button>`;

                    let scopeName = tpl.sub_scope;
                    if (tpl.sub_scope === 'INDOOR_SANITASI') scopeName = 'Indoor & Toilet';
                    else if (tpl.sub_scope === 'TAMAN_LANSKAP') scopeName = 'Taman & Lanskap';
                    else if (tpl.sub_scope === 'AGRO_TERNAK') scopeName = 'Agro & Ternak';

                    html += `
                        <tr class="hover:bg-slate-50 transition ${isActive ? '' : 'opacity-60 bg-slate-50/50'}">
                            <td class="py-3 px-3 text-center font-bold text-slate-700 text-[11px]">${tpl.item_order}</td>
                            <td class="py-3 px-3 font-semibold text-slate-700">
                                <div>${unitBadge}</div>
                                <div class="text-[10px] text-slate-400 mt-0.5 font-medium">${scopeName}</div>
                            </td>
                            <td class="py-3 px-3 whitespace-nowrap">${shiftBadge}</td>
                            <td class="py-3 px-4">
                                <div class="font-bold text-slate-800 text-xs">${tpl.item_label}</div>
                                ${tpl.help_text ? `<div class="text-[11px] text-slate-500 mt-0.5 italic flex items-center gap-1"><i class="fa-solid fa-circle-info text-slate-400 text-[9px]"></i> ${tpl.help_text}</div>` : ''}
                            </td>
                            <td class="py-3 px-3 text-center whitespace-nowrap">${ecoBadge}</td>
                            <td class="py-3 px-3 text-center whitespace-nowrap">${statusBadge}</td>
                            <td class="py-3 px-4 text-center whitespace-nowrap">
                                <div class="flex items-center justify-center gap-1.5">
                                    <button type="button" onclick="openModalEditChecklistTemplate(${tpl.id})" title="Edit Butir" class="p-1.5 text-slate-500 hover:text-amber-600 rounded-lg hover:bg-amber-50 transition cursor-pointer">
                                        <i class="fa-solid fa-pen-to-square"></i>
                                    </button>
                                    <button type="button" onclick="deleteChecklistTemplate(${tpl.id}, '${escape(tpl.item_label)}')" title="Hapus Butir" class="p-1.5 text-slate-500 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition cursor-pointer">
                                        <i class="fa-solid fa-trash-can"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            } catch (err) {
                console.error("Gagal load checklist templates:", err);
            }
        }

        function openModalCreateChecklistTemplate() {
            document.getElementById('modal-chk-tpl-title').innerHTML = '<i class="fa-solid fa-plus-circle text-teal-600"></i><span>Tambah Butir Checklist Baru</span>';
            document.getElementById('chk-tpl-id').value = '';
            document.getElementById('chk-tpl-unit').value = 'OB';
            document.getElementById('chk-tpl-subscope').value = 'INDOOR_SANITASI';
            document.getElementById('chk-tpl-shift').value = 'PAGI';
            document.getElementById('chk-tpl-order').value = '';
            document.getElementById('chk-tpl-label').value = '';
            document.getElementById('chk-tpl-help').value = '';
            document.getElementById('chk-tpl-eco').value = '0';
            document.getElementById('chk-tpl-active').value = '1';
            document.getElementById('btn-save-chk-tpl-text').innerText = 'Simpan Butir Checklist';
            toggleModal('modal-manage-checklist-template');
        }

        async function openModalEditChecklistTemplate(templateId) {
            let tpl = cachedChecklistTemplates.find(t => t.id === templateId);
            if (!tpl) {
                try {
                    const res = await fetch(`/api/ops/checklist/templates/${templateId}`);
                    const data = await res.json();
                    if (data.success && data.template) {
                        tpl = data.template;
                    }
                } catch (e) {
                    console.error("Gagal fetch detail template:", e);
                }
            }

            if (!tpl) {
                alert("Data butir template tidak ditemukan!");
                return;
            }

            document.getElementById('modal-chk-tpl-title').innerHTML = '<i class="fa-solid fa-pen-to-square text-amber-600"></i><span>Edit Butir Checklist</span>';
            document.getElementById('chk-tpl-id').value = tpl.id;
            document.getElementById('chk-tpl-unit').value = tpl.unit_type;
            document.getElementById('chk-tpl-subscope').value = tpl.sub_scope || 'INDOOR_SANITASI';
            document.getElementById('chk-tpl-shift').value = tpl.shift_code;
            document.getElementById('chk-tpl-order').value = tpl.item_order;
            document.getElementById('chk-tpl-label').value = tpl.item_label;
            document.getElementById('chk-tpl-help').value = tpl.help_text || '';
            document.getElementById('chk-tpl-eco').value = String(tpl.is_eco_critical || 0);
            document.getElementById('chk-tpl-active').value = (tpl.is_active !== undefined) ? String(tpl.is_active) : '1';
            document.getElementById('btn-save-chk-tpl-text').innerText = 'Perbarui Butir Checklist';

            toggleModal('modal-manage-checklist-template');
        }

        async function saveChecklistTemplate(event) {
            event.preventDefault();
            const tplId = document.getElementById('chk-tpl-id').value.trim();
            const btn = document.getElementById('btn-save-chk-tpl');

            const payload = {
                unit_type: document.getElementById('chk-tpl-unit').value,
                sub_scope: document.getElementById('chk-tpl-subscope').value,
                shift_code: document.getElementById('chk-tpl-shift').value,
                item_order: parseInt(document.getElementById('chk-tpl-order').value) || 0,
                item_label: document.getElementById('chk-tpl-label').value.trim(),
                help_text: document.getElementById('chk-tpl-help').value.trim(),
                is_eco_critical: parseInt(document.getElementById('chk-tpl-eco').value) || 0,
                is_active: parseInt(document.getElementById('chk-tpl-active').value)
            };

            const url = tplId ? `/api/ops/checklist/templates/${tplId}/edit` : `/api/ops/checklist/templates/create`;

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    toggleModal('modal-manage-checklist-template');
                    loadChecklistTemplates();
                } else {
                    alert('Gagal: ' + (data.error || 'Terjadi kesalahan'));
                }
            } catch (err) {
                alert('Error koneksi: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span id="btn-save-chk-tpl-text">' + (tplId ? 'Perbarui Butir Checklist' : 'Simpan Butir Checklist') + '</span>';
            }
        }

        async function toggleChecklistTemplateActive(templateId) {
            try {
                const res = await fetch(`/api/ops/checklist/templates/${templateId}/toggle-active`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    loadChecklistTemplates();
                } else {
                    alert('Gagal: ' + (data.error || 'Gagal mengubah status'));
                }
            } catch (e) {
                alert('Error koneksi: ' + e.message);
            }
        }

        async function deleteChecklistTemplate(templateId, labelEscaped) {
            const label = unescape(labelEscaped);
            if (!confirm(`Apakah Anda yakin ingin menghapus butir checklist berikut dari sistem?\n\n"${label}"\n\n(Catatan: Jika hanya ingin menonaktifkan sementara, gunakan tombol status AKTIF/NON-AKTIF).`)) {
                return;
            }

            try {
                const res = await fetch(`/api/ops/checklist/templates/${templateId}/delete`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    loadChecklistTemplates();
                } else {
                    alert('Gagal: ' + (data.error || 'Gagal menghapus'));
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }

    </script>
    {{ pm_client_script | safe }}
    {{ evaluasi_client_script | safe }}
</body>
</html>
"""

@app.route("/")
@login_required
def index():
    user_id = session.get('ops_user_id')
    user_username = session.get('ops_username', '')
    user_nama = session.get('ops_nama', 'Mr Slam')
    user_role = session.get('ops_role_code', 'manager')
    user_role_name = session.get('ops_role_name', 'IT Manager & Kabag Umum')
    user_unit = session.get('ops_unit_code', 'ALL')
    user_sub_scope = session.get('ops_sub_scope', '')
    user_permissions = session.get('ops_permissions', ['all'])

    data = load_data()
    stats = get_server_stats()
    mutabaah_logs = [l for l in load_logs(MUTABAAH_LOGS_PATH) if l.get('type') not in ['mutubaah_personal', 'mutabaah_personal']]
    kebersihan_logs = load_logs(KEBERSIHAN_LOGS_PATH)

    today_str = now_wib().strftime("%Y-%m-%d")
    today_mutabaah = [l for l in mutabaah_logs if (l.get('wibDate') or l.get('timestamp', '')[:10]) == today_str]
    today_kebersihan = [l for l in kebersihan_logs if (l.get('wibDate') or l.get('timestamp', '')[:10]) == today_str]

    # Load from SQLite database with Role & Unit Scoping
    import sqlite3
    con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 1. Scoped Tasks
    if user_role == 'manager':
        cur.execute("SELECT * FROM ops_tasks ORDER BY CASE status WHEN 'Pending' THEN 1 WHEN 'Proses' THEN 2 ELSE 3 END, created_at DESC")
    else:
        cur.execute("SELECT * FROM ops_tasks WHERE unit_code = ? ORDER BY CASE status WHEN 'Pending' THEN 1 WHEN 'Proses' THEN 2 ELSE 3 END, created_at DESC", (user_unit,))
    tasks = [dict(r) for r in cur.fetchall()]
    for t in tasks:
        t["unit"] = t.get("unit_code") or t.get("unit") or "IT"

    # 2. Scoped Todos
    if user_role == 'manager':
        cur.execute("SELECT * FROM ops_todos ORDER BY completed ASC, CASE priority WHEN 'Tinggi' THEN 1 WHEN 'Sedang' THEN 2 ELSE 3 END, created_at DESC")
    else:
        cur.execute("SELECT * FROM ops_todos WHERE unit_code = ? ORDER BY completed ASC, CASE priority WHEN 'Tinggi' THEN 1 WHEN 'Sedang' THEN 2 ELSE 3 END, created_at DESC", (user_unit,))
    todos = []
    for r in cur.fetchall():
        d = dict(r)
        d["completed"] = bool(d["completed"])
        todos.append(d)

    # 3. Scoped Journals
    if user_role == 'manager':
        cur.execute("SELECT * FROM ops_journals ORDER BY date DESC, time DESC, created_at DESC LIMIT 100")
    else:
        cur.execute("""
            SELECT * FROM ops_journals 
            WHERE (unit_code = ? OR author_username = ?)
              AND unit_code != 'ALL'
              AND (author_username IS NULL OR author_username != 'admin')
            ORDER BY date DESC, time DESC, created_at DESC LIMIT 100
        """, (user_unit, user_username))
    journals_sorted = [dict(r) for r in cur.fetchall()]

    # 4. Scoped Procurements
    if user_role in ['manager', 'pic_pengadaan']:
        cur.execute("SELECT * FROM ops_procurements ORDER BY CASE status WHEN 'Diajukan' THEN 1 WHEN 'Disetujui' THEN 2 WHEN 'Proses Beli' THEN 3 WHEN 'Barang Tiba' THEN 4 ELSE 5 END, requested_at DESC")
    else:
        cur.execute("SELECT * FROM ops_procurements WHERE unit_code = ? ORDER BY CASE status WHEN 'Diajukan' THEN 1 WHEN 'Disetujui' THEN 2 WHEN 'Proses Beli' THEN 3 WHEN 'Barang Tiba' THEN 4 ELSE 5 END, requested_at DESC", (user_unit,))
    procurements = [dict(r) for r in cur.fetchall()]

    proc_stats = {
        "total": len(procurements),
        "diajukan": len([p for p in procurements if p.get("status") == "Diajukan"]),
        "disetujui": len([p for p in procurements if p.get("status") == "Disetujui"]),
        "proses_beli": len([p for p in procurements if p.get("status") == "Proses Beli"]),
        "selesai": len([p for p in procurements if p.get("status") in ["Barang Tiba", "Diserahkan", "Selesai"]]),
        "total_est_cost": sum(p.get("estimated_cost") or 0 for p in procurements),
        "total_act_cost": sum(p.get("actual_cost") or 0 for p in procurements)
    }

    con.close()

    monitored_hosts = data.get("monitored_hosts", [])
    pending_todos = [t for t in todos if not t.get("completed")]
    done_todos = [t for t in todos if t.get("completed")]

    # Prepare Chart Data (Last 7 Days Mutabaah)
    chart_dates = []
    chart_m_counts = []
    for i in range(6, -1, -1):
        dt = (now_wib() - timedelta(days=i)).strftime("%Y-%m-%d")
        chart_dates.append(dt)
        c = len([l for l in mutabaah_logs if (l.get('wibDate') or l.get('timestamp', '')[:10]) == dt])
        chart_m_counts.append(c)

    kebersihan_unit_counts = {}
    for l in kebersihan_logs:
        u = l.get("unit", "OB")
        kebersihan_unit_counts[u] = kebersihan_unit_counts.get(u, 0) + 1

    if not kebersihan_unit_counts:
        kebersihan_unit_counts = {"OB": 0, "General Affairs": 0}

    journal_cat_counts = {}
    for j in journals_sorted:
        c = j.get("category", "Lainnya")
        journal_cat_counts[c] = journal_cat_counts.get(c, 0) + 1

    if not journal_cat_counts:
        journal_cat_counts = {"IT Manager": 0, "Kabag Umum": 0}

    task_stats = {
        "pending": len([t for t in tasks if t.get("status") == "Pending"]),
        "proses": len([t for t in tasks if t.get("status") == "Proses"]),
        "selesai": len([t for t in tasks if t.get("status") == "Selesai"])
    }

    # Load Analytics Summary Engine
    import ops_analytics
    analytics = ops_analytics.get_dashboard_analytics_summary(
        monitored_hosts=monitored_hosts,
        mutabaah_logs=mutabaah_logs,
        kebersihan_logs=kebersihan_logs,
        tasks=tasks,
        procurements=procurements,
        today_str=today_str
    )

    chart_data = {
        "mutabaah_dates": chart_dates,
        "mutabaah_counts": chart_m_counts,
        "kebersihan_units": list(kebersihan_unit_counts.keys()),
        "kebersihan_counts": list(kebersihan_unit_counts.values()),
        "journal_categories": list(journal_cat_counts.keys()),
        "journal_counts": list(journal_cat_counts.values()),
        "task_stats": task_stats,
        "trend_dates": analytics.get("trend_data", {}).get("dates", []),
        "tasks_created": analytics.get("trend_data", {}).get("tasks_created", []),
        "tasks_resolved": analytics.get("trend_data", {}).get("tasks_resolved", []),
        "standby_compliance": analytics.get("trend_data", {}).get("standby_compliance", []),
        "ohs_scores": analytics.get("ohs", {}).get("scores", {})
    }

    report_lines = [
        "==================================================",
        "LAPORAN HARIAN IT & BAGIAN UMUM - AN NAHL",
        f"Tanggal : {now_wib().strftime('%d %B %Y')}",
        "Penanggung Jawab: Mr Slam (IT Manager & Kabag Umum)",
        "==================================================\n",
        f"1. JURNAL KEGIATAN HARIAN      : {len(journals_sorted)} Catatan Tersimpan",
        f"2. TOTAL MUTABAAH HARIAN MASUK : {len(today_mutabaah)} Petugas",
        f"3. TOTAL LAPORAN KEBERSIHAN    : {len(today_kebersihan)} Laporan\n",
        "4. TIKET & TUGAS PEKERJAAN:"
    ]
    for idx, t in enumerate(tasks, 1):
        report_lines.append(f"   [{t.get('status')}] [{t.get('unit')}] {t.get('title')} (Prio: {t.get('priority')})")

    report_lines.append(f"\n5. INFRASTRUKTUR SERVER:")
    report_lines.append(f"   - Memory : {stats['mem_str']}")
    report_lines.append(f"   - Disk   : {stats['disk_str']}")
    report_lines.append(f"   - Uptime : {stats['uptime']}")

    report_text = "\n".join(report_lines)

    return render_template_string(
        HTML_TEMPLATE,
        now_str=now_wib().strftime("%Y-%m-%d %H:%M:%S") + " WIB",
        today_date=today_str,
        current_time=now_wib().strftime("%H:%M"),
        stats=stats,
        units=UNITS,
        tasks=tasks,
        todos=todos,
        journals=journals_sorted,
        monitored_hosts=monitored_hosts,
        pending_todos_count=len(pending_todos),
        done_todos_count=len(done_todos),
        mutabaah_logs=mutabaah_logs,
        kebersihan_logs=kebersihan_logs,
        mutabaah_count=len(today_mutabaah),
        kebersihan_count=len(today_kebersihan),
        chart_data=chart_data,
        report_text=report_text,
        user_id=user_id,
        user_nama=user_nama,
        user_role=user_role,
        user_role_name=user_role_name,
        user_unit=user_unit,
        user_sub_scope=user_sub_scope,
        user_permissions=user_permissions,
        procurements=procurements,
        proc_stats=proc_stats,
        analytics=analytics,
        tab_pemeliharaan_html=templates_pm.TAB_PEMELIHARAAN_HTML,
        pm_client_script=templates_pm.PM_CLIENT_SCRIPT,
        tab_evaluasi_html=templates_evaluasi.TAB_EVALUASI_HTML,
        evaluasi_client_script=templates_evaluasi.EVALUASI_CLIENT_SCRIPT
    )

@app.route("/add_host", methods=["POST"])
@login_required
def add_host():
    data = load_data()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "Server").strip()
    host_val = request.form.get("host", "").strip()
    type_val = request.form.get("type", "ping").strip()
    port_val = request.form.get("port", "").strip()

    if name and host_val:
        data.setdefault("monitored_hosts", []).append({
            "id": "h_" + str(uuid.uuid4())[:8],
            "name": name,
            "category": category,
            "host": host_val,
            "type": type_val,
            "port": port_val,
            "last_status": "ONLINE",
            "latency_ms": 0,
            "error_msg": "",
            "down_count": 0,
            "up_count": 0,
            "alerted_down": False
        })
        save_data(data)
    return "<script>window.location.href='/?tab=tab-kuma';</script>"

@app.route("/delete_host", methods=["POST"])
@login_required
def delete_host():
    data = load_data()
    host_id = request.form.get("host_id", "").strip()
    hosts = data.get("monitored_hosts", [])
    data["monitored_hosts"] = [h for h in hosts if h.get("id") != host_id]
    save_data(data)
    return "<script>window.location.href='/?tab=tab-kuma';</script>"

@app.route("/edit_host", methods=["POST"])
@login_required
def edit_host():
    data = load_data()
    host_id = request.form.get("host_id", "").strip()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "Server").strip()
    host_val = request.form.get("host", "").strip()
    type_val = request.form.get("type", "ping").strip()
    port_val = request.form.get("port", "").strip()

    if name and host_val:
        for h in data.get("monitored_hosts", []):
            if h.get("id") == host_id:
                h["name"] = name
                h["category"] = category
                h["host"] = host_val
                h["type"] = type_val
                h["port"] = port_val
                break
        save_data(data)
    return "<script>window.location.href='/?tab=tab-kuma';</script>"

@app.route("/add_journal", methods=["POST"])
@login_required
def add_journal():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Operasional").strip()
    date_val = request.form.get("date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    description = request.form.get("description", "").strip()
    output = request.form.get("output", "").strip()

    user_role = session.get('ops_role_code', 'manager')
    user_unit = session.get('ops_unit_code', 'ALL')
    user_nama = session.get('ops_nama', 'Mr Slam')
    user_username = session.get('ops_username', 'admin')

    unit_code = request.form.get("unit_code", user_unit) if user_role == 'manager' else user_unit

    if title and description:
        import sqlite3
        con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
        cur = con.cursor()
        j_id = "j_" + str(uuid.uuid4())[:8]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute('''
            INSERT INTO ops_journals (id, unit_code, author_username, author_nama, category, date, time, title, description, output, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (j_id, unit_code, user_username, user_nama, category, date_val, datetime.now().strftime("%H:%M"), title, description, output, now_str))
        con.commit()
        con.close()
        from ops_core import sync_db_to_json
        sync_db_to_json()

    return "<script>window.location.href='/?tab=tab-journal';</script>"

@app.route("/delete_journal", methods=["POST"])
@login_required
def delete_journal():
    journal_id = request.form.get("journal_id", "").strip()
    user_role = session.get('ops_role_code', 'manager')
    user_username = session.get('ops_username', 'admin')

    import sqlite3
    con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
    cur = con.cursor()
    if user_role == 'manager':
        cur.execute("DELETE FROM ops_journals WHERE id = ?", (journal_id,))
    else:
        cur.execute("DELETE FROM ops_journals WHERE id = ? AND author_username = ?", (journal_id, user_username))
    con.commit()
    con.close()
    from ops_core import sync_db_to_json
    sync_db_to_json()
    return "<script>window.location.href='/?tab=tab-journal';</script>"

@app.route("/add_todo", methods=["POST"])
@login_required
def add_todo():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Umum").strip() or "Umum"
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "Sedang")
    user_role = session.get('ops_role_code', 'manager')
    user_unit = session.get('ops_unit_code', 'ALL')
    user_nama = session.get('ops_nama', 'Mr Slam')

    # Koordinator otomatis membuat to-do untuk unitnya sendiri
    unit_code = user_unit if user_role != 'manager' else (request.form.get("unit_code") or category)

    if title:
        import sqlite3
        con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
        cur = con.cursor()
        td_id = "td_" + str(uuid.uuid4())[:8]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute('''
            INSERT INTO ops_todos (id, unit_code, title, category, due_date, priority, completed, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
        ''', (td_id, unit_code, title, category, due_date, priority, user_nama, now_str))
        con.commit()
        con.close()
        from ops_core import sync_db_to_json
        sync_db_to_json()

    return "<script>window.location.href='/?tab=tab-todo';</script>"

@app.route("/toggle_todo", methods=["POST"])
@login_required
def toggle_todo():
    todo_id = request.form.get("todo_id", "").strip()
    import sqlite3
    con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT completed FROM ops_todos WHERE id = ?", (todo_id,))
    row = cur.fetchone()
    if row:
        new_val = 0 if row["completed"] else 1
        comp_at = datetime.now().strftime("%Y-%m-%d %H:%M") if new_val == 1 else None
        cur.execute("UPDATE ops_todos SET completed = ?, completed_at = ? WHERE id = ?", (new_val, comp_at, todo_id))
        con.commit()
    con.close()
    from ops_core import sync_db_to_json
    sync_db_to_json()
    return "<script>window.location.href='/?tab=tab-todo';</script>"

@app.route("/delete_todo", methods=["POST"])
@login_required
def delete_todo():
    todo_id = request.form.get("todo_id", "").strip()
    user_role = session.get('ops_role_code', '')
    user_nama = session.get('ops_nama', '')
    user_username = session.get('ops_username', '')

    import sqlite3
    con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT created_by, unit_code FROM ops_todos WHERE id = ?", (todo_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return "<script>window.location.href='/?tab=tab-todo';</script>"

    # Koordinator tidak boleh menghapus to-do yang dibuat oleh pimpinan / pihak lain
    if user_role != 'manager' and row["created_by"] not in [user_username, user_nama]:
        con.close()
        return "<script>alert('Anda tidak memiliki izin menghapus to-do yang dibuat oleh pimpinan.'); window.location.href='/?tab=tab-todo';</script>"

    cur.execute("DELETE FROM ops_todos WHERE id = ?", (todo_id,))
    con.commit()
    con.close()
    from ops_core import sync_db_to_json
    sync_db_to_json()
    return "<script>window.location.href='/?tab=tab-todo';</script>"

@app.route("/add_task", methods=["POST"])
@login_required
def add_task():
    unit = request.form.get("unit", "Umum")
    category = request.form.get("category", "Operasional")
    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "Sedang")
    due_date = request.form.get("due_date", "")
    description = request.form.get("description", "")

    if title:
        import sqlite3
        con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
        cur = con.cursor()
        date_part = datetime.now().strftime("%Y%m%d")
        task_id = f"TK-{date_part}-{str(uuid.uuid4())[:4].upper()}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        created_by = session.get('ops_nama', 'Mr Slam')

        from ops_core import get_coordinator_info, send_ops_wa_alert
        coord = get_coordinator_info(unit)
        assigned_to = coord["username"] if coord else ""
        assigned_name = coord["nama_lengkap"] if coord else ""

        cur.execute('''
            INSERT INTO ops_tasks (id, unit_code, category, title, description, priority, status, assigned_to, assigned_name, due_date, source, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, 'manual', ?, ?)
        ''', (task_id, unit, category, title, description, priority, assigned_to, assigned_name, due_date, created_by, now_str))
        con.commit()
        con.close()

        from ops_core import sync_db_to_json
        sync_db_to_json()

    return "<script>window.location.href='/?tab=tab-tasks';</script>"

@app.route("/update_task", methods=["POST"])
@login_required
def update_task():
    task_id = request.form.get("task_id", "").strip()
    new_status = request.form.get("new_status", "Selesai")

    import sqlite3
    con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
    cur = con.cursor()
    comp_at = datetime.now().strftime("%Y-%m-%d %H:%M") if new_status == "Selesai" else None
    cur.execute("UPDATE ops_tasks SET status = ?, completed_at = COALESCE(?, completed_at) WHERE id = ?", (new_status, comp_at, task_id))
    con.commit()
    con.close()
    from ops_core import sync_db_to_json
    sync_db_to_json()
    return "<script>window.location.href='/?tab=tab-tasks';</script>"

def create_excel_response(sheet_name, headers, rows, file_prefix):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Header
    ws.append(headers)
    emerald_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.fill = emerald_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Data rows
    for row in rows:
        ws.append(row)

    # Auto-filter
    ws.auto_filter.ref = ws.dimensions

    # Auto-fit column widths (max length + 2)
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or '')) for cell in col), default=0)
        ws.column_dimensions[col_letter].width = max_len + 2

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"{file_prefix}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/export/mutabaah")
@login_required
def export_mutabaah():
    logs = [l for l in load_logs(MUTABAAH_LOGS_PATH) if l.get('type') not in ['mutubaah_personal', 'mutabaah_personal']]
    headers = ["Tanggal WIB", "Nama", "Unit", "Sholat", "Tilawah", "Dzikir"]
    rows = []
    for log in logs:
        tgl = log.get("wibDate") or (log.get("timestamp") or "")[:10]
        nama = log.get("nama", "")
        unit = log.get("unit", "")
        sholat = log.get("sholat", "")
        tilawah = log.get("tilawah", "")
        dzikir = log.get("dzikir", "")
        rows.append([tgl, nama, unit, sholat, tilawah, dzikir])
    return create_excel_response("Mutabaah", headers, rows, "Mutabaah_AnNahl")

@app.route("/export/kebersihan")
@login_required
def export_kebersihan():
    logs = load_logs(KEBERSIHAN_LOGS_PATH)
    headers = ["Tanggal WIB", "Nama", "Unit", "Area", "Keterangan", "Ada Foto", "Link Foto Drive"]
    rows = []
    for log in logs:
        tgl = log.get("wibDate") or (log.get("timestamp") or "")[:10]
        nama = log.get("nama", "")
        unit = log.get("unit", "")
        area = log.get("area", "")
        keterangan = log.get("keterangan", "")
        p_link = log.get("photoUrl") or log.get("photo_url") or log.get("driveUrl") or log.get("drive_url") or log.get("foto_url") or log.get("local_photo_url") or ""
        ada_foto = "Ya" if (p_link or log.get("hasImage") or log.get("imageBase64")) else "Tidak"
        rows.append([tgl, nama, unit, area, keterangan, ada_foto, p_link or "-"])
    return create_excel_response("Kebersihan", headers, rows, "Kebersihan_AnNahl")

@app.route("/api/kebersihan/laporan", methods=["POST"])
def api_kebersihan_laporan():
    """
    Endpoint ingestion laporan kebersihan dari WhatsApp bot atau integrasi lokal.
    Menyimpan secara persisten ke KEBERSIHAN_LOGS_PATH.
    """
    try:
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            return jsonify({"success": False, "error": "Payload data kosong"}), 400

        nama = data.get("nama", "Petugas").strip()
        unit = data.get("unit", "OB").strip()
        area = data.get("area", "-").strip()
        keterangan = data.get("keterangan", "-").strip()
        timestamp = data.get("timestamp") or datetime.now(timezone.utc).isoformat()
        wib_date = data.get("wibDate") or now_wib().strftime("%Y-%m-%d")

        log_entry = {
            "type": "kebersihan",
            "sender": data.get("sender", ""),
            "pushName": data.get("pushName", ""),
            "nama": nama,
            "unit": unit,
            "area": area,
            "keterangan": keterangan,
            "rawText": data.get("rawText", ""),
            "timestamp": timestamp,
            "wibDate": wib_date,
            "imageMime": data.get("imageMime", "image/jpeg"),
            "hasImage": bool(data.get("hasImage") or data.get("photoUrl") or data.get("local_photo_url")),
            "hasVideo": bool(data.get("hasVideo") or (data.get("local_photo_url") and data.get("local_photo_url").endswith(".mp4")) or (data.get("mediaType") == "video")),
            "mediaType": data.get("mediaType", "video" if (str(data.get("local_photo_url", "")).endswith(".mp4") or data.get("hasVideo")) else "image"),
            "local_photo_url": data.get("local_photo_url", ""),
            "photoUrl": data.get("photoUrl", ""),
            "photo_url": data.get("photo_url", "") or data.get("photoUrl", ""),
            "driveUrl": data.get("driveUrl", "") or data.get("photoUrl", "")
        }

        logs = load_logs(KEBERSIHAN_LOGS_PATH)
        existing = False
        for l in logs:
            if l.get("timestamp") == timestamp and l.get("nama") == nama:
                if log_entry.get("photoUrl") and not l.get("photoUrl"):
                    l["photoUrl"] = log_entry["photoUrl"]
                    l["photo_url"] = log_entry["photo_url"]
                    l["driveUrl"] = log_entry["driveUrl"]
                if log_entry.get("local_photo_url") and not l.get("local_photo_url"):
                    l["local_photo_url"] = log_entry["local_photo_url"]
                existing = True
                break

        if not existing:
            logs.append(log_entry)

        with open(KEBERSIHAN_LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

        return jsonify({
            "success": True,
            "message": "Laporan kebersihan berhasil dicatat ke Dashboard An Nahl Ops",
            "entry": log_entry
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/kebersihan/update_photo", methods=["POST"])
@login_required
def api_update_kebersihan_photo():
    payload = request.get_json() or {}
    timestamp = payload.get("timestamp", "").strip()
    photo_url = payload.get("photo_url", "").strip()

    if not timestamp or not photo_url:
        return jsonify({"status": "error", "message": "Timestamp dan URL foto wajib diisi"}), 400

    logs = load_logs(KEBERSIHAN_LOGS_PATH)
    updated = False
    for l in logs:
        if l.get("timestamp") == timestamp:
            l["photoUrl"] = photo_url
            l["photo_url"] = photo_url
            l["driveUrl"] = photo_url
            l["hasImage"] = True
            updated = True
            break

    if updated:
        try:
            with open(KEBERSIHAN_LOGS_PATH, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "ok", "message": "Berhasil memperbarui tautan foto Google Drive"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Gagal menyimpan ke file: {str(e)}"}), 500
    else:
        return jsonify({"status": "error", "message": "Log kebersihan tidak ditemukan"}), 404

@app.route("/api/kebersihan/sync_drive", methods=["POST", "GET"])
@login_required
def api_sync_kebersihan_drive():
    gas_url = "https://script.google.com/macros/s/AKfycbwV-RKgFsR-GEgWQ0yWxvGz4Ct3Yag5xzhg-zayoE3BoHPqdJWjbLYW_bl9o1gWoZDmIg/exec"
    try:
        import urllib.request
        req = urllib.request.Request(f"{gas_url}?action=kebersihan", headers={"User-Agent": "AnNahl-Ops/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            try:
                gas_data = json.loads(content)
            except Exception:
                return jsonify({
                    "status": "info",
                    "message": "Google Apps Script belum mendukung respons JSON action=kebersihan. Silakan update script di GAS sesuai panduan."
                })

            if gas_data.get("result") != "success" or "rows" not in gas_data:
                return jsonify({"status": "info", "message": gas_data.get("message", "Tidak ada data foto dari Google Sheet")})

            gas_rows = gas_data.get("rows", [])
            logs = load_logs(KEBERSIHAN_LOGS_PATH)
            updated_count = 0

            for grow in gas_rows:
                g_photo = (grow.get("photoUrl") or "").strip()
                if not g_photo or g_photo == "-" or g_photo.startswith("Error"):
                    continue
                g_nama = (grow.get("nama") or "").lower().strip()
                g_tgl = (grow.get("tanggal") or "").strip()
                g_area = (grow.get("area") or "").lower().strip()

                for l in logs:
                    l_tgl = l.get("wibDate") or (l.get("timestamp") or "")[:10]
                    l_nama = (l.get("nama") or "").lower().strip()
                    l_area = (l.get("area") or "").lower().strip()
                    if l_tgl == g_tgl and (l_nama in g_nama or g_nama in l_nama) and (l_area in g_area or g_area in l_area or l_area == "-"):
                        if not l.get("photoUrl") or l.get("photoUrl") == "-":
                            l["photoUrl"] = g_photo
                            l["photo_url"] = g_photo
                            l["driveUrl"] = g_photo
                            l["hasImage"] = True
                            updated_count += 1
                            break

            if updated_count > 0:
                with open(KEBERSIHAN_LOGS_PATH, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)

            return jsonify({
                "status": "ok",
                "message": f"Berhasil menyinkronkan {updated_count} foto dari Google Sheet!",
                "updated_count": updated_count
            })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal menghubungi Google Apps Script: {str(e)}"}), 500

@app.route("/export/journal")
@login_required
def export_journal():
    user_role = session.get('ops_role_code', '')
    user_unit = session.get('ops_unit_code', '')
    user_username = session.get('ops_username', '')

    import sqlite3
    con = sqlite3.connect("/home/ametriyadhi/sas-annahl/database.sqlite")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    if user_role == 'manager':
        cur.execute("SELECT * FROM ops_journals ORDER BY date DESC, time DESC, created_at DESC")
    else:
        cur.execute("""
            SELECT * FROM ops_journals 
            WHERE (unit_code = ? OR author_username = ?)
              AND unit_code != 'ALL'
              AND (author_username IS NULL OR author_username != 'admin')
            ORDER BY date DESC, time DESC, created_at DESC
        """, (user_unit, user_username))
    journals = [dict(r) for r in cur.fetchall()]
    con.close()

    headers = ["Tanggal", "Jam", "Unit", "Penulis", "Kategori", "Judul", "Deskripsi", "Output", "Catatan Supervisi"]
    rows = []
    for j in journals:
        tgl = j.get("date", "")
        jam = j.get("time", "")
        unit = j.get("unit_code", "")
        penulis = j.get("author_nama", "")
        kategori = j.get("category", "")
        judul = j.get("title", "")
        deskripsi = j.get("description", "")
        output_val = j.get("output", "")
        supervisi = j.get("supervisor_feedback", "") or ""
        rows.append([tgl, jam, unit, penulis, kategori, judul, deskripsi, output_val, supervisi])
    return create_excel_response("Jurnal", headers, rows, f"Jurnal_AnNahl_{user_unit or 'Manager'}")

def format_excel_sheet(ws, headers, rows):
    ws.append(headers)
    emerald_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.fill = emerald_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in rows:
        ws.append(row)

    ws.auto_filter.ref = ws.dimensions

    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or '')) for cell in col), default=0)
        ws.column_dimensions[col_letter].width = max(max_len + 2, 10)

@app.route("/api/report/mutabaah")
def api_report_mutabaah():
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    unit = request.args.get("unit", "").strip()

    logs = [l for l in load_logs(MUTABAAH_LOGS_PATH) if l.get('type') not in ['mutubaah_personal', 'mutabaah_personal']]
    filtered = []
    per_unit = {}

    for log in logs:
        tgl = log.get("wibDate") or (log.get("timestamp") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        l_unit = log.get("unit", "")
        if unit and unit.lower() != "semua" and unit.lower() not in l_unit.lower():
            continue

        row = {
            "tanggal": tgl,
            "nama": log.get("nama", ""),
            "unit": l_unit,
            "sholat": log.get("sholat", ""),
            "tilawah": log.get("tilawah", ""),
            "dzikir": log.get("dzikir", "")
        }
        filtered.append(row)
        if l_unit:
            per_unit[l_unit] = per_unit.get(l_unit, 0) + 1

    return jsonify({
        "count": len(filtered),
        "rows": filtered,
        "per_unit": per_unit
    })

@app.route("/api/report/kebersihan")
def api_report_kebersihan():
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    unit = request.args.get("unit", "").strip()

    logs = load_logs(KEBERSIHAN_LOGS_PATH)
    filtered = []
    per_unit = {}

    for log in logs:
        tgl = log.get("wibDate") or (log.get("timestamp") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        l_unit = log.get("unit", "")
        if unit and unit.lower() != "semua" and unit.lower() not in l_unit.lower():
            continue

        p_link = log.get("photoUrl") or log.get("photo_url") or log.get("driveUrl") or log.get("drive_url") or log.get("foto_url") or log.get("local_photo_url") or ""
        row = {
            "tanggal": tgl,
            "nama": log.get("nama", ""),
            "unit": l_unit,
            "area": log.get("area", ""),
            "keterangan": log.get("keterangan", ""),
            "ada_foto": bool(p_link or log.get("hasImage") or log.get("imageBase64")),
            "photo_url": p_link
        }
        filtered.append(row)
        if l_unit:
            per_unit[l_unit] = per_unit.get(l_unit, 0) + 1

    return jsonify({
        "count": len(filtered),
        "rows": filtered,
        "per_unit": per_unit
    })

@app.route("/api/report/journal")
def api_report_journal():
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()

    data = load_data()
    journals = data.get("journals", [])
    filtered = []

    for j in journals:
        tgl = j.get("date") or (j.get("created_at") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue

        row = {
            "tanggal": tgl,
            "jam": j.get("time", ""),
            "kategori": j.get("category", ""),
            "judul": j.get("title", ""),
            "deskripsi": j.get("description", ""),
            "output": j.get("output", "")
        }
        filtered.append(row)

    return jsonify({
        "count": len(filtered),
        "rows": filtered
    })

@app.route("/api/report/tasks")
def api_report_tasks():
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    unit = request.args.get("unit", "").strip()

    data = load_data()
    tasks = data.get("tasks", [])
    filtered = []

    for t in tasks:
        tgl = (t.get("created_at") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        t_unit = t.get("unit", "")
        if unit and unit.lower() != "semua" and unit.lower() not in t_unit.lower():
            continue

        row = {
            "created_at": t.get("created_at", ""),
            "unit": t_unit,
            "category": t.get("category", ""),
            "title": t.get("title", ""),
            "priority": t.get("priority", ""),
            "status": t.get("status", "")
        }
        filtered.append(row)

    return jsonify({
        "count": len(filtered),
        "rows": filtered
    })


@app.route("/api/server/stats")
def api_server_stats():
    """API endpoint for detailed server stats (memory, disk, CPU, processes, network)"""
    stats = get_detailed_server_stats()
    return jsonify(stats)

@app.route("/api/server/stats/<host_id>")
def api_server_stats_remote(host_id):
    """API endpoint for detailed server stats of a specific monitored host via SSH"""
    data = load_data()
    hosts = data.get("monitored_hosts", [])
    host = next((h for h in hosts if h.get("id") == host_id), None)

    if not host:
        return jsonify({"error": "Host not found"}), 404

    # If local host (127.0.0.1 or localhost), return local stats
    if host.get("host") in ("127.0.0.1", "localhost", "::1"):
        return jsonify(get_detailed_server_stats())

    # For remote hosts, try SSH
    remote_host = host.get("host")
    ssh_user = "ametriyadhi"  # Default SSH user

    try:
        import subprocess
        import json as json_lib

        # SSH command to get system stats
        ssh_cmd = (
            "ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=no "
            f"{ssh_user}@{remote_host} "
            "'"
            "echo '===CPU_CORES===' && nproc; "
            "echo '===LOADAVG===' && cat /proc/loadavg; "
            "echo '===MEMINFO===' && cat /proc/meminfo; "
            "echo '===DISK===' && df -k / | tail -1; "
            "echo '===UPTIME===' && cat /proc/uptime; "
            "echo '===PROCS===' && ps aux --sort=-%cpu | head -11; "
            "echo '===NET===' && ip -br addr show | grep -v '^lo'"
            "'"
        )

        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            return jsonify({
                "error": "SSH failed",
                "details": result.stderr[:500],
                "host": host.get("name"),
                "ip": remote_host
            }), 500

        # Parse output
        output = result.stdout
        stats = {"host": host.get("name"), "ip": remote_host}

        # Parse CPU cores
        try:
            stats["cpu_cores"] = int(output.split("===CPU_CORES===")[1].split("===")[0].strip())
        except:
            stats["cpu_cores"] = 0

        # Parse loadavg
        try:
            load_line = output.split("===LOADAVG===")[1].split("===")[0].strip()
            stats["load_avg"] = list(map(float, load_line.split()[:3]))
        except:
            stats["load_avg"] = [0.0, 0.0, 0.0]

        # Parse meminfo
        try:
            meminfo_text = output.split("===MEMINFO===")[1].split("===")[0]
            mem_info = {}
            for line in meminfo_text.strip().split("\n"):
                parts = line.split(":")
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = int(parts[1].split()[0])
            total_mem = mem_info.get("MemTotal", 1) / (1024 * 1024)
            avail_mem = mem_info.get("MemAvailable", 0) / (1024 * 1024)
            used_mem = total_mem - avail_mem
            stats["mem_pct"] = round((used_mem / total_mem) * 100, 1)
            stats["mem_str"] = f"{used_mem:.1f} GB / {total_mem:.1f} GB ({stats['mem_pct']}%)"
            stats["mem_total_gb"] = round(total_mem, 1)
            stats["mem_used_gb"] = round(used_mem, 1)
        except:
            stats["mem_pct"] = 0
            stats["mem_str"] = "N/A"
            stats["mem_total_gb"] = 0
            stats["mem_used_gb"] = 0

        # Parse disk
        try:
            disk_line = output.split("===DISK===")[1].split("===")[0].strip()
            parts = disk_line.split()
            if len(parts) >= 4:
                total_k = int(parts[1])
                used_k = int(parts[2])
                free_k = int(parts[3])
                total_gb = total_k / (1024 * 1024)
                used_gb = used_k / (1024 * 1024)
                free_gb = free_k / (1024 * 1024)
                stats["disk_pct"] = round((used_gb / total_gb) * 100, 1) if total_gb > 0 else 0
                stats["disk_str"] = f"{used_gb:.1f} GB / {total_gb:.1f} GB ({stats['disk_pct']}%)"
                stats["disk_total_gb"] = round(total_gb, 1)
                stats["disk_used_gb"] = round(used_gb, 1)
        except:
            stats["disk_pct"] = 0
            stats["disk_str"] = "N/A"
            stats["disk_total_gb"] = 0
            stats["disk_used_gb"] = 0

        # Parse uptime
        try:
            uptime_seconds = float(output.split("===UPTIME===")[1].split("===")[0].strip().split()[0])
            hours = int(uptime_seconds // 3600)
            mins = int((uptime_seconds % 3600) // 60)
            days = hours // 24
            hours = hours % 24
            if days > 0:
                stats["uptime"] = f"{days}j {hours}j {mins}m"
            else:
                stats["uptime"] = f"{hours}j {mins}m"
        except:
            stats["uptime"] = "N/A"

        # Parse processes
        try:
            proc_text = output.split("===PROCS===")[1].split("===")[0]
            lines = proc_text.strip().split("\n")
            top_processes = []
            if len(lines) > 1:
                for line in lines[1:11]:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        top_processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": float(parts[2]),
                            "mem": float(parts[3]),
                            "vsz": parts[4],
                            "rss": parts[5],
                            "tty": parts[6],
                            "stat": parts[7],
                            "start": parts[8],
                            "time": parts[9],
                            "command": parts[10][:80]
                        })
            stats["top_processes"] = top_processes
        except:
            stats["top_processes"] = []

        # Parse network
        try:
            net_text = output.split("===NET===")[1].split("===")[0]
            net_interfaces = []
            for line in net_text.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 3 and parts[1] in ("UP", "DOWN"):
                    net_interfaces.append({
                        "name": parts[0],
                        "status": parts[1],
                        "ip": parts[2] if len(parts) > 2 else ""
                    })
            stats["net_interfaces"] = net_interfaces
        except:
            stats["net_interfaces"] = []

        # CPU usage - approximate from load avg / cores
        if stats["cpu_cores"] > 0 and stats["load_avg"]:
            stats["cpu_pct"] = round(min((stats["load_avg"][0] / stats["cpu_cores"]) * 100, 100), 1)
        else:
            stats["cpu_pct"] = 0.0

        return jsonify(stats)

    except subprocess.TimeoutExpired:
        return jsonify({"error": "SSH timeout", "host": host.get("name"), "ip": remote_host}), 504
    except Exception as e:
        return jsonify({"error": str(e), "host": host.get("name"), "ip": remote_host}), 500
@app.route("/export/report")
@login_required
def export_combined_report():
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    unit = request.args.get("unit", "").strip()

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # 1. Sheet Mutabaah
    mutabaah_logs = [l for l in load_logs(MUTABAAH_LOGS_PATH) if l.get('type') not in ['mutubaah_personal', 'mutabaah_personal']]
    mutabaah_rows = []
    for l in mutabaah_logs:
        tgl = l.get("wibDate") or (l.get("timestamp") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        l_unit = l.get("unit", "")
        if unit and unit.lower() != "semua" and unit.lower() not in l_unit.lower():
            continue
        mutabaah_rows.append([tgl, l.get("nama", ""), l_unit, l.get("sholat", ""), l.get("tilawah", ""), l.get("dzikir", "")])

    if mutabaah_rows:
        ws = wb.create_sheet(title="Mutabaah")
        format_excel_sheet(ws, ["Tanggal WIB", "Nama", "Unit", "Sholat", "Tilawah", "Dzikir"], mutabaah_rows)

    # 2. Sheet Kebersihan
    kebersihan_logs = load_logs(KEBERSIHAN_LOGS_PATH)
    kebersihan_rows = []
    for l in kebersihan_logs:
        tgl = l.get("wibDate") or (l.get("timestamp") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        l_unit = l.get("unit", "")
        if unit and unit.lower() != "semua" and unit.lower() not in l_unit.lower():
            continue
        p_link = l.get("photoUrl") or l.get("photo_url") or l.get("driveUrl") or l.get("drive_url") or l.get("foto_url") or l.get("local_photo_url") or ""
        ada_foto = "Ya" if (p_link or l.get("hasImage") or l.get("imageBase64")) else "Tidak"
        kebersihan_rows.append([tgl, l.get("nama", ""), l_unit, l.get("area", ""), l.get("keterangan", ""), ada_foto, p_link or "-"])

    if kebersihan_rows:
        ws = wb.create_sheet(title="Kebersihan")
        format_excel_sheet(ws, ["Tanggal WIB", "Nama", "Unit", "Area", "Keterangan", "Ada Foto", "Link Foto Drive"], kebersihan_rows)

    # 3. Sheet Jurnal
    data = load_data()
    journal_rows = []
    for j in data.get("journals", []):
        tgl = j.get("date") or (j.get("created_at") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        journal_rows.append([tgl, j.get("time", ""), j.get("category", ""), j.get("title", ""), j.get("description", ""), j.get("output", "")])

    if journal_rows:
        ws = wb.create_sheet(title="Jurnal")
        format_excel_sheet(ws, ["Tanggal", "Jam", "Kategori", "Judul", "Deskripsi", "Output"], journal_rows)

    # 4. Sheet Tiket
    task_rows = []
    for t in data.get("tasks", []):
        tgl = (t.get("created_at") or "")[:10]
        if start and tgl and tgl < start:
            continue
        if end and tgl and tgl > end:
            continue
        t_unit = t.get("unit", "")
        if unit and unit.lower() != "semua" and unit.lower() not in t_unit.lower():
            continue
        task_rows.append([t.get("created_at", ""), t_unit, t.get("category", ""), t.get("title", ""), t.get("priority", ""), t.get("status", "")])

    if task_rows:
        ws = wb.create_sheet(title="Tiket")
        format_excel_sheet(ws, ["Waktu Dibuat", "Unit", "Kategori", "Judul Pekerjaan", "Prioritas", "Status"], task_rows)

    # If all empty, create "Ringkasan" sheet
    if not wb.sheetnames:
        ws = wb.create_sheet(title="Ringkasan")
        format_excel_sheet(ws, ["Informasi", "Keterangan"], [
            ["Periode", f"{start or 'Semua'} s/d {end or 'Semua'}"],
            ["Unit", unit or "Semua"],
            ["Status Data", "Tidak ada data pada periode ini"]
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Laporan_AnNahl_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============ Sapa Ais Dashboard (JSON API for tab) ============
@app.route("/api/sapaais/data")
@login_required
def sapaais_data():
    """JSON API untuk tab Sapa Ais di dashboard note-umum."""
    import sqlite3
    import datetime as _dt
    
    DB_PATH = os.path.expanduser("~/sas-annahl/database.sqlite")
    
    def get_db():
        con = sqlite3.connect(DB_PATH, timeout=60)
        con.row_factory = sqlite3.Row
        return con
    
    # Get filter params
    filters = {}
    for key in ["status", "kategori", "pelapor_unit", "date_from", "date_to"]:
        if request.args.get(key):
            filters[key] = request.args.get(key)
    
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    
    where_clauses = []
    params = []
    
    if filters:
        if filters.get("status"):
            where_clauses.append("status=?")
            params.append(filters["status"])
        if filters.get("kategori"):
            where_clauses.append("kategori=?")
            params.append(filters["kategori"])
        if filters.get("pelapor_unit"):
            where_clauses.append("pelapor_unit=?")
            params.append(filters["pelapor_unit"])
        if filters.get("date_from"):
            where_clauses.append("date(created_at) >= date(?)")
            params.append(filters["date_from"])
        if filters.get("date_to"):
            where_clauses.append("date(created_at) <= date(?)")
            params.append(filters["date_to"])
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    con = get_db()
    
    # Get data
    query = f"SELECT * FROM laporan {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = con.execute(query, params).fetchall()
    data = [dict(r) for r in rows]
    
    # Total count
    count_query = f"SELECT COUNT(*) FROM laporan {where_sql}"
    count_params = params[:-2]  # remove limit, offset
    total = con.execute(count_query, count_params).fetchone()[0]
    
    # Stats cards
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status='BARU' THEN 1 ELSE 0 END) as baru,
            SUM(CASE WHEN status='DITERIMA' THEN 1 ELSE 0 END) as diterima,
            SUM(CASE WHEN status='SELESAI' THEN 1 ELSE 0 END) as selesai
        FROM laporan
    """).fetchone()
    
    # Per kategori
    cat_stats = con.execute("""
        SELECT kategori, COUNT(*) as jml
        FROM laporan
        GROUP BY kategori
        ORDER BY jml DESC
    """).fetchall()
    
    # SLA overdue
    now = _dt.datetime.now().isoformat()
    overdue = con.execute("""
        SELECT COUNT(*) as jml FROM laporan
        WHERE status IN ('BARU','DITERIMA') AND sla_deadline < ?
    """, (now,)).fetchone()
    
    con.close()
    
    # Build status badge
    def status_badge(status):
        colors = {
            'BARU': 'bg-rose-100 text-rose-700',
            'DITERIMA': 'bg-amber-100 text-amber-700',
            'SELESAI': 'bg-emerald-100 text-emerald-700',
        }
        return f'<span class="text-[10px] px-2 py-0.5 rounded {colors.get(status, "bg-slate-100 text-slate-700")}">{status}</span>'
    
    def sla_badge(sla_deadline):
        if not sla_deadline:
            return '<span class="text-[10px] text-slate-400">-</span>'
        try:
            deadline = _dt.datetime.fromisoformat(sla_deadline.replace('Z', '+00:00'))
            remaining = (deadline - _dt.datetime.now()).total_seconds() / 3600
            if remaining <= 0:
                return '<span class="text-[10px] px-2 py-0.5 rounded bg-rose-100 text-rose-700 font-semibold">⚠ LEWAT</span>'
            elif remaining <= 24:
                return f'<span class="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-700">{remaining:.1f} jam</span>'
            else:
                return f'<span class="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-700">{remaining/24:.1f} hr</span>'
        except:
            return '<span class="text-[10px] text-slate-400">-</span>'
    
    # Table rows
    rows_html = ""
    for r in data:
        foto_link = f'<a href="{r["foto_url"]}" target="_blank" class="text-emerald-600 hover:underline text-[11px]">📸 Foto</a>' if r.get("foto_url") else '<span class="text-slate-400 text-[11px]">-</span>'
        deskripsi_short = r["deskripsi"][:80] + ("..." if len(r.get("deskripsi","")) > 80 else "")
        created_fmt = r["created_at"][:16].replace("T", " ")
        rows_html += f"""<tr class="border-b hover:bg-slate-50">
            <td class="p-2 text-[11px] font-mono">{r["id"]}</td>
            <td class="p-2 text-[11px]">{r["kategori"]}</td>
            <td class="p-2 text-[11px] truncate max-w-xs">{r["lokasi"] or "-"}</td>
            <td class="p-2 text-[11px] truncate max-w-xs">{deskripsi_short}</td>
            <td class="p-2">{status_badge(r["status"])}</td>
            <td class="p-2 text-[11px]">{r["pic_nama"] or "-"}</td>
            <td class="p-2">{sla_badge(r["sla_deadline"])}</td>
            <td class="p-2">{foto_link}</td>
            <td class="p-2 text-[11px]">{created_fmt}</td>
            <td class="p-2">
                <button onclick="editLaporan('{r["id"]}')" class="text-emerald-600 hover:underline text-[11px]">Edit</button>
            </td>
        </tr>"""
    
    if not rows_html:
        rows_html = '<tr><td colspan="10" class="p-4 text-center text-slate-400">Tidak ada laporan</td></tr>'
    
    # Filter form
    status_options = ['BARU', 'DITERIMA', 'SELESAI']
    kategori_options = ['IT', 'FASILITAS', 'KEBERSIHAN', 'BELAJAR', 'LAINNYA']
    
    status_opts_html = "".join(f'<option value="{s}" {"selected" if filters.get("status")==s else ""}>{s}</option>' for s in status_options)
    kategori_opts_html = "".join(f'<option value="{k}" {"selected" if filters.get("kategori")==k else ""}>{k}</option>' for k in kategori_options)
    
    filter_form = f"""
    <form method="GET" class="flex flex-wrap gap-3 mb-4 p-4 bg-white rounded-xl border">
        <select name="status" class="border rounded px-2 py-1 text-sm">
            <option value="">Semua Status</option>
            {status_opts_html}
        </select>
        <select name="kategori" class="border rounded px-2 py-1 text-sm">
            <option value="">Semua Kategori</option>
            {kategori_opts_html}
        </select>
        <input type="date" name="date_from" value="{filters.get("date_from", "")}" class="border rounded px-2 py-1 text-sm">
        <input type="date" name="date_to" value="{filters.get("date_to", "")}" class="border rounded px-2 py-1 text-sm">
        <button type="submit" class="bg-emerald-600 text-white px-3 py-1 rounded text-sm">Filter</button>
        <a href="/sapaais" class="text-slate-500 hover:underline text-sm">Reset</a>
    </form>
    """
    
    # Stats cards
    stats_html = f"""
    <div class="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <div class="bg-white rounded-xl border p-4"><p class="text-2xl font-bold text-rose-600">{stats["baru"] or 0}</p><p class="text-xs text-slate-400">BARU</p></div>
        <div class="bg-white rounded-xl border p-4"><p class="text-2xl font-bold text-amber-600">{stats["diterima"] or 0}</p><p class="text-xs text-slate-400">DITERIMA</p></div>
        <div class="bg-white rounded-xl border p-4"><p class="text-2xl font-bold text-emerald-600">{stats["selesai"] or 0}</p><p class="text-xs text-slate-400">SELESAI</p></div>
        <div class="bg-white rounded-xl border p-4"><p class="text-2xl font-bold text-slate-600">{stats["total"] or 0}</p><p class="text-xs text-slate-400">TOTAL</p></div>
        <div class="bg-white rounded-xl border p-4"><p class="text-2xl font-bold text-rose-600">{overdue["jml"] or 0}</p><p class="text-xs text-slate-400">SLA LEWAT</p></div>
    </div>
    """
    
    # Kategori chart
    cat_html = ""
    for c in cat_stats:
        cat_html += f'<div class="flex items-center justify-between py-1 border-b"><span class="text-sm">{c["kategori"]}</span><span class="font-semibold">{c["jml"]}</span></div>'
    
    # Pagination
    page_num = offset // limit + 1
    total_pages = (total + limit - 1) // limit or 1
    
    prev_link = ""
    if offset > 0:
        prev_link = f'<a href="?status={filters.get("status","")}&kategori={filters.get("kategori","")}&date_from={filters.get("date_from","")}&date_to={filters.get("date_to","")}&limit={limit}&offset={max(0, offset-limit)}" class="px-3 py-1 border rounded text-sm">Sebelumnya</a>'
    else:
        prev_link = '<span class="px-3 py-1 border rounded text-sm opacity-50">Sebelumnya</span>'
    
    next_link = ""
    if offset + limit < total:
        next_link = f'<a href="?status={filters.get("status","")}&kategori={filters.get("kategori","")}&date_from={filters.get("date_from","")}&date_to={filters.get("date_to","")}&limit={limit}&offset={offset+limit}" class="px-3 py-1 border rounded text-sm">Selanjutnya</a>'
    else:
        next_link = '<span class="px-3 py-1 border rounded text-sm opacity-50">Selanjutnya</span>'
    
    # Use the same BASE_LAYOUT pattern as main app
    content = f"""
    <div class="bg-white rounded-xl border p-4 mb-6">
        <h3 class="font-bold text-lg mb-2">📊 Statistik LaporPak</h3>
        {stats_html}
    </div>
    
    <div class="bg-white rounded-xl border p-4 mb-6">
        <h3 class="font-bold text-lg mb-2">📂 Per Kategori</h3>
        <div class="border rounded-lg overflow-hidden">
            {cat_html or '<p class="p-4 text-slate-400 text-sm">Belum ada data</p>'}
        </div>
    </div>
    
    <div class="bg-white rounded-xl border overflow-hidden">
        <div class="p-4 border-b flex items-center justify-between">
            <h3 class="font-bold text-lg">📋 Daftar Laporan</h3>
            <span class="text-sm text-slate-500">Total: {total} | Menampilkan: {len(data)}</span>
        </div>
        {filter_form}
        <div class="overflow-x-auto">
            <table class="w-full text-left">
                <thead class="bg-slate-50">
                    <tr class="border-b text-xs text-slate-500 uppercase">
                        <th class="p-2">ID</th>
                        <th class="p-2">Kategori</th>
                        <th class="p-2">Lokasi</th>
                        <th class="p-2">Deskripsi</th>
                        <th class="p-2">Status</th>
                        <th class="p-2">PIC</th>
                        <th class="p-2">SLA</th>
                        <th class="p-2">Foto</th>
                        <th class="p-2">Dibuat</th>
                        <th class="p-2">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        <div class="p-4 border-t flex items-center justify-between">
            <span class="text-sm text-slate-500">Halaman {page_num} dari {total_pages}</span>
            <div class="flex gap-2">
                {prev_link}
                {next_link}
            </div>
        </div>
    </div>
    
    <script>
    function editLaporan(id) {{
        alert('Edit laporan ' + id + ' - implement modal nanti');
    }}
    </script>
    """
    
    return jsonify({
        "success": True,
        "data": data,
        "total": total,
        "page": page_num,
        "total_pages": total_pages,
        "stats": {
            "baru": stats["baru"] or 0,
            "diterima": stats["diterima"] or 0,
            "selesai": stats["selesai"] or 0,
            "total": stats["total"] or 0,
            "overdue": overdue["jml"] or 0
        },
        "cat_stats": [dict(c) for c in cat_stats]
    })


@app.route("/bot-qr")
def page_bot_qr():
    """Halaman perantara untuk melihat status dan memindai QR Code WhatsApp Bot"""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:3005/qr", timeout=4) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>WhatsApp Bot Offline</title><meta charset="utf-8"><meta http-equiv="refresh" content="5"></head>
        <body style="font-family:sans-serif;text-align:center;padding:50px;background:#0f172a;color:#f8fafc;">
            <h2 style="color:#ef4444;">⚠️ WhatsApp Bot Engine Belum Aktif</h2>
            <p style="color:#94a3b8;">Tidak dapat menghubungi engine bot di port 3005 ({e}).</p>
            <p style="color:#64748b;">Halaman akan mencoba kembali setiap 5 detik...</p>
            <p><a href="/" style="color:#38bdf8;text-decoration:none;">← Kembali ke Dashboard Ops</a></p>
        </body>
        </html>
        """, 502

@app.route("/api/bot/status")
def api_bot_status():
    """Proxy status WhatsApp bot dari loopback port 3005"""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:3005/status", timeout=3) as resp:
            return jsonify(json.loads(resp.read().decode("utf-8")))
    except Exception as e:
        return jsonify({"status": "Offline", "error": str(e), "hasQR": False}), 503

# =========================================================================
# MODUL PEMELIHARAAN SARPRAS (ISO FM-UMUM-AIS-03-02) API & EXPORT ROUTES
# =========================================================================

@app.route("/api/ops/pm/summary", methods=["GET"])
@login_required
def api_ops_pm_summary():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    res = ops_pm.get_pm_dashboard_summary(year=year, month=month)
    return jsonify(res)

@app.route("/api/ops/pm/execute", methods=["POST"])
@login_required
def api_ops_pm_execute():
    data = request.get_json() or {}
    try:
        master_id = int(data.get("master_id"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "master_id harus valid"}), 400

    res = ops_pm.record_pm_execution(
        schedule_id=data.get("schedule_id") or "",
        master_id=master_id,
        execution_date=data.get("execution_date") or datetime.now().strftime("%Y-%m-%d"),
        executor_name=data.get("executor_name") or session.get("ops_nama", "Petugas"),
        executor_type=data.get("executor_type") or "OB",
        condition_rating=data.get("condition_rating") or "BAIK",
        finding_notes=data.get("finding_notes") or "",
        action_taken=data.get("action_taken") or "",
        photo_before_url=data.get("photo_before_url") or "",
        photo_after_url=data.get("photo_after_url") or "",
        create_ticket=bool(data.get("create_ticket")),
        verified_by=session.get("ops_nama", "Mr Slam")
    )
    return jsonify(res)

@app.route("/api/ops/pm/execute_wa", methods=["POST"])
def api_ops_pm_execute_wa():
    """Endpoint publik untuk integrasi pemeliharaan dari WhatsApp Bot"""
    data = request.get_json() or {}
    nama = data.get("nama", "Petugas").strip()
    unit = data.get("unit", "OB").strip()
    sarpras_query = data.get("sarpras", "").strip() or data.get("keterangan", "").strip()
    kondisi = data.get("kondisi", "BAIK").strip()
    keterangan = data.get("keterangan", "").strip()
    photo_url = data.get("photo_url", "").strip()
    sender_phone = data.get("sender_phone", "").strip()

    if not sarpras_query and not keterangan:
        return jsonify({"success": False, "error": "Sarpras atau keterangan wajib diisi"}), 400

    res = ops_pm.execute_from_wa(
        nama=nama,
        unit=unit,
        sarpras_query=sarpras_query,
        kondisi=kondisi,
        keterangan=keterangan,
        photo_url=photo_url,
        sender_phone=sender_phone
    )
    return jsonify(res)

@app.route("/export/pm")
@login_required
def export_pm():
    import csv, io
    conn = ops_pm.get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, m.scope, m.category, m.sub_category, m.item_name, m.indicator_standard,
               m.frequency, m.executor_type, m.pj_role, s.status, s.due_date, s.completed_at, s.completed_by
        FROM ops_pm_master m
        LEFT JOIN ops_pm_schedules s ON m.id = s.master_id AND s.period_year = 2026 AND s.period_month = 10
        ORDER BY m.scope DESC, m.category ASC
    """)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["No", "Lingkup", "Kategori", "Sub-Kategori", "Butir Sarpras", "Standar Mutu", "Frekuensi", "Pelaksana", "Penanggung Jawab", "Status Bulan Ini", "Jatuh Tempo", "Tanggal Selesai", "Petugas"])
    for idx, r in enumerate(rows, 1):
        writer.writerow([idx, r["scope"], r["category"], r["sub_category"] or "-", r["item_name"], r["indicator_standard"], r["frequency"], r["executor_type"], r["pj_role"], r["status"] or "PENDING", r["due_date"] or "-", r["completed_at"] or "-", r["completed_by"] or "-"])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=rekap_pemeliharaan_iso_2026.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

# =========================================================================
# MODUL EVALUASI & RAPOR KINERJA PERSONIL (OB & GARDENER)
# =========================================================================

@app.route("/api/ops/evaluasi/summary", methods=["GET"])
@login_required
def api_ops_evaluasi_summary():
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    unit_filter = request.args.get("unit", "ALL").strip()
    data = ops_evaluasi.get_evaluasi_analytics(
        start_date=start_date,
        end_date=end_date,
        unit_filter=unit_filter
    )
    return jsonify(data)

@app.route("/api/ops/evaluasi/notes", methods=["POST"])
@login_required
def api_ops_evaluasi_notes():
    data = request.get_json() or {}
    petugas_name = data.get("petugas_name", "").strip()
    unit_code = data.get("unit_code", "OB").strip()
    notes = data.get("notes", "").strip()

    if not petugas_name:
        return jsonify({"success": False, "error": "Nama petugas wajib diisi"}), 400

    now = datetime.now()
    res = ops_evaluasi.save_supervisor_notes(
        petugas_name=petugas_name,
        unit_code=unit_code,
        period_year=now.year,
        period_month=now.month,
        notes=notes,
        supervisor_name=session.get("ops_nama", "Mr Slam")
    )
    return jsonify(res)

@app.route("/export/evaluasi")
@login_required
def export_evaluasi():
    import csv, io
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    unit_filter = request.args.get("unit", "ALL").strip()

    data = ops_evaluasi.get_evaluasi_analytics(
        start_date=start_date,
        end_date=end_date,
        unit_filter=unit_filter
    )
    leaderboard = data.get("leaderboard", [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Peringkat", "Nama Personil", "Unit", "Kewajiban Sesi Pos", "Realisasi Hadir (Checkin)",
        "Mangkir Pos (Alpha)", "Tingkat Kehadiran (%)", "Hari Aktif",
        "Tepat Waktu", "Tepat Waktu (%)", "Terlambat", "Terlambat (%)",
        "Luar Radius", "Luar Radius (%)", "Rata-rata Telat (Mnt)", "Paling Telat (Mnt)",
        "Skor Disiplin (0-100)", "Status Rapor", "Rekomendasi Tindak Lanjut", "Catatan Supervisi Mr Slam"
    ])

    for idx, p in enumerate(leaderboard, 1):
        writer.writerow([
            idx, p["nama"], p["unit"], p["target_sessions"], p["total_checkin"],
            p["missed_checkin"], f"{p['attendance_rate']}%", p["days_active"],
            p["tepat_waktu"], f"{p['on_time_pct']}%", p["terlambat"], f"{p['late_pct']}%",
            p["diluar_radius"], f"{p['out_radius_pct']}%", p["avg_late_min"], p["max_late_min"],
            p["discipline_score"], p["eval_badge"], p["recommendation"], p["supervisor_notes"]
        ])

    filename = f"rapor_evaluasi_{data.get('start_date')}_sd_{data.get('end_date')}.csv"
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

app.register_blueprint(mutubaah_bp)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

