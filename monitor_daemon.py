import os
import sys
import json
import time
import socket
import subprocess
import re
import urllib.request
import urllib.error
import requests
from datetime import datetime

DATA_FILE = os.path.expanduser("~/annahl_ops_data.json")
CONFIG_WA_FILE = os.path.expanduser("~/mutabaah-wa-bot/config.json")

# Target alert khusus pribadi Mr Slam (format internasional tanpa +)
SLAM_PRIVATE_JID = "6287809199096@s.whatsapp.net"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"monitored_hosts": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"monitored_hosts": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_bot_port():
    try:
        if os.path.exists(CONFIG_WA_FILE):
            with open(CONFIG_WA_FILE, "r") as f:
                cfg = json.load(f)
                return cfg.get("port", 3005)
    except Exception:
        pass
    return 3005

def get_wa_targets():
    # HANYA kirim alert ke nomor pribadi Mr Slam (bukan group)
    # Group (reminder_jids dari config WA bot) KHUSUS untuk mutabaah/laporan,
    # tidak untuk alert infrastructure monitor.
    return [SLAM_PRIVATE_JID]

def send_wa_message(target_jid, text):
    port = get_bot_port()
    try:
        res = requests.post(f"http://127.0.0.1:{port}/send_alert", json={
            "target": target_jid,
            "text": text
        }, timeout=8)
        return res.status_code == 200
    except Exception as e:
        print(f"[WA Alert Error on port {port}]: {e}")
        return False

def check_target(item):
    host = item.get("host", "").strip()
    htype = item.get("type", "ping").lower()
    port = item.get("port", None)

    start_time = time.time()
    is_up = False
    error_msg = ""
    latency_ms = 0.0

    if htype == "ping":
        try:
            res = subprocess.run(
                ["ping", "-c", "3", "-i", "0.2", "-W", "1", host],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_up = (res.returncode == 0)
            if is_up:
                match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", res.stdout)
                if match:
                    latency_ms = float(match.group(1))
                else:
                    latency_ms = round((time.time() - start_time) * 1000, 1)
            else:
                error_msg = "Ping Unreachable / Timeout"
        except subprocess.TimeoutExpired:
            is_up = False
            error_msg = "Ping Timeout (5s)"
        except Exception as e:
            is_up = False
            error_msg = f"Ping Error: {e}"

    elif htype == "port":
        p = int(port) if port else 80
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect((host, p))
            is_up = True
            latency_ms = round((time.time() - start_time) * 1000, 1)
            s.close()
        except Exception as err:
            is_up = False
            error_msg = f"Port {p} Closed / Unreachable ({err})"

    elif htype in ["http", "https"]:
        url = host if host.startswith("http") else f"{htype}://{host}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AnNahl-Monitor/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                is_up = (response.status == 200)
                latency_ms = round((time.time() - start_time) * 1000, 1)
                if not is_up:
                    error_msg = f"HTTP Status {response.status}"
        except Exception as err:
            is_up = False
            error_msg = f"HTTP Error: {err}"

    return is_up, round(latency_ms, 2), error_msg

def broadcast_alert(host_name, target, category, is_down, details="", latency_ms=0):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    wa_targets = get_wa_targets()

    if is_down:
        msg = f"🚨 *ALERT: {host_name} OFFLINE!*\n"
        msg += f"_An Nahl Uptime Kuma Monitor_\n\n"
        msg += f"🔴 *Perangkat:* {host_name}\n"
        msg += f"📍 *IP/Host:* `{target}`\n"
        msg += f"📁 *Kategori:* {category}\n"
        msg += f"⚠️ *Penyebab Terdeteksi:* {details or 'Tidak diketahui'}\n"
        msg += f"⏰ *Waktu:* {now_str} WIB\n\n"
        msg += f"💡 *Saran Tindakan:* Periksa koneksi jaringan, power/POE switch, atau restart perangkat terkait.\n\n"
        msg += f"🌐 *Dashboard:* https://note-umum.ametriyadhi.com"
    else:
        msg = f"✅ *RECOVERY: {host_name} ONLINE kembali!*\n"
        msg += f"_An Nahl Uptime Kuma Monitor_\n\n"
        msg += f"🟢 *Perangkat:* {host_name}\n"
        msg += f"📍 *IP/Host:* `{target}`\n"
        msg += f"📁 *Kategori:* {category}\n"
        msg += f"⚡ *Latency:* {latency_ms} ms\n"
        msg += f"⏰ *Waktu Pulih:* {now_str} WIB\n\n"
        msg += f"_Sistem telah kembali terhubung & normal._\n"
        msg += f"🌐 *Dashboard:* https://note-umum.ametriyadhi.com"

    print(f"[ALERT BROADCAST] {datetime.now()}: {host_name} -> Down: {is_down}")

    for t in wa_targets:
        ok = send_wa_message(t, msg)
        print(f"[ALERT SEND] to {t}: {'OK' if ok else 'FAILED'}")

def main_loop():
    print("🚀 An Nahl Uptime Kuma Daemon Started (Alert ke WA Pribadi Mr Slam aktif)...")
    last_pm_check_date = ""

    while True:
        try:
            data = load_data()
            hosts = data.get("monitored_hosts", [])
            data_changed = False

            # Daily PM Reminder Check (Pagi hari mulai pukul 07:30 WIB)
            today_str = datetime.now().strftime("%Y-%m-%d")
            if today_str != last_pm_check_date and datetime.now().hour >= 7:
                try:
                    import ops_pm
                    res_pm = ops_pm.check_and_send_pm_reminders()
                    print(f"[PM REMINDER CHECK]: {res_pm}")
                    last_pm_check_date = today_str
                except Exception as e:
                    print(f"[PM REMINDER ERROR]: {e}")

            for idx, item in enumerate(hosts):
                old_status = item.get("last_status", "ONLINE")
                is_up, latency_ms, error_msg = check_target(item)
                new_status = "ONLINE" if is_up else "OFFLINE"

                item["last_status"] = new_status
                item["latency_ms"] = latency_ms
                item["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                item["error_msg"] = error_msg

                down_count = item.get("down_count", 0)
                up_count = item.get("up_count", 0)
                alerted_down = item.get("alerted_down", False)

                if new_status == "OFFLINE":
                    down_count += 1
                    up_count = 0
                    item["down_count"] = down_count
                    item["up_count"] = 0

                    # Kirim alert DOWN setelah 2x berturut-turut OFFLINE (60 detik), dan hanya jika belum dikirim alert DOWN
                    if down_count >= 2 and not alerted_down:
                        item["alerted_down"] = True
                        data_changed = True
                        broadcast_alert(
                            host_name=item.get("name"),
                            target=item.get("host"),
                            category=item.get("category", "Server"),
                            is_down=True,
                            details=error_msg,
                            latency_ms=latency_ms
                        )
                else:
                    up_count += 1
                    down_count = 0
                    item["up_count"] = up_count
                    item["down_count"] = 0

                    # Kirim alert RECOVERY HANYA jika sebelumnya sudah dikirim alert DOWN (alerted_down == True)
                    if alerted_down and up_count >= 1:
                        item["alerted_down"] = False
                        data_changed = True
                        broadcast_alert(
                            host_name=item.get("name"),
                            target=item.get("host"),
                            category=item.get("category", "Server"),
                            is_down=False,
                            details="Perangkat kembali merespons normal",
                            latency_ms=latency_ms
                        )

            data["monitored_hosts"] = hosts
            save_data(data)

        except Exception as e:
            print(f"[Daemon Exception]: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main_loop()
