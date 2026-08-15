import time
import json
import os
from custom_toast import ToastManager
import ctypes

CONFIG_FILE = "settings.json"

def get_settings():
    default_cfg = {
        "water_interval_mins": 45,
        "break_interval_mins": 60,
        "break_enabled": True,
        "mute_until": 0,
        "active_theme": "Pink Blossom",
        "is_running": True,
        "drunk_today_ml": 0,
        "daily_goal_liters": 2.0,
        "daily_history": {}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_cfg
    return default_cfg

def set_running_status(status: bool):
    cfg = get_settings()
    cfg["is_running"] = status
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

set_running_status(True)

toaster = ToastManager(position="bottom-right", duration_ms=6000, sound_enabled=True)

init_theme = get_settings().get("active_theme", "Pink Blossom")
toaster.show(
    title="Health Studio Aktif ",
    message="Hatırlatıcı devrede! Hedef veya tema ayarları için tıkla ",
    kind="default",
    theme_name=init_theme
)

last_water = time.time()
last_break = time.time()

print("Hatırlatıcı devrede... Kapatmak için arayüzden 'Uygulamayı Kapat' butonuna basabilirsin.")

while True:
    cfg = get_settings()

    if not cfg.get("is_running", True):
        print("\nKapatma emri alındı. Durduruluyor...")
        toaster.stop()
        os._exit(0)

    current_time = time.time()
    active_theme = cfg.get("active_theme", "Pink Blossom")
    mute_until = cfg.get("mute_until", 0)
    is_muted = current_time < mute_until

    # 1 Saat Sustur Modu Kontrolü
    if is_muted:
        time.sleep(2)
        continue

    water_interval = cfg.get("water_interval_mins", 45) * 60
    break_interval = cfg.get("break_interval_mins", 60) * 60
    break_enabled = cfg.get("break_enabled", True)

    # 1. Su Kontrolü
    if current_time - last_water >= water_interval:
        drunk_l = cfg.get("drunk_today_ml", 0) / 1000
        goal_l = cfg.get("daily_goal_liters", 2.0)
        toaster.show(
            title="Water Reminder 💧",
            message=f"Güncel: {drunk_l:.2f}/{goal_l:.1f} L. Bir bardak su içmeyi unutma!",
            kind="water",
            theme_name=active_theme
        )
        last_water = current_time

    # 2. Mola Kontrolü (Sade & Sabit Mola Mesajı)
    if break_enabled and (current_time - last_break >= break_interval):
        toaster.show(
            title="Break Reminder 🧘",
            message="Gözlerini ekrandan ayır ve biraz dinlen!",
            kind="break",
            theme_name=active_theme
        )
        last_break = current_time

    time.sleep(1)