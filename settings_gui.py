import json
import os
import time
from datetime import date, timedelta
import customtkinter as ctk

CONFIG_FILE = "settings.json"
DAYS_TR = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

THEME_STYLES = {
    "Pink Blossom": {
        "primary": "#FF4081",
        "primary_hover": "#E0356E",
        "accent": "#FF758C",
        "card_bg": "#2B1E28",
        "subcard_bg": "#1F1B24",
        "border": "#3D1D28"
    },
    "Pastel Matcha Green": {
        "primary": "#6B9080",
        "primary_hover": "#5B7C6E",
        "accent": "#A4C3B2",
        "card_bg": "#1E2B22",
        "subcard_bg": "#17231B",
        "border": "#2D3F33"
    },
    "Ocean Blue": {
        "primary": "#0077B6",
        "primary_hover": "#005F92",
        "accent": "#90E0EF",
        "card_bg": "#182838",
        "subcard_bg": "#12202E",
        "border": "#21384E"
    },
    "Dark Slate": {
        "primary": "#5C5C6E",
        "primary_hover": "#4B4B5A",
        "accent": "#A0A0B2",
        "card_bg": "#202025",
        "subcard_bg": "#18181C",
        "border": "#2C2C35"
    }
}


def get_today_str():
    return str(date.today())


def load_config():
    default_config = {
        "daily_goal_liters": 2.0,
        "glass_size_ml": 250,
        "water_interval_mins": 45,
        "break_interval_mins": 60,
        "break_enabled": True,
        "mute_until": 0,
        "active_theme": "Pink Blossom",
        "is_running": True,
        "drunk_today_ml": 0,
        "last_active_date": get_today_str(),
        "streak_count": 0,
        "last_streak_completed_date": "",
        "daily_history": {}  # Format: {"2026-08-15": 2.5}
    }

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = default_config

    for key, val in default_config.items():
        if key not in data:
            data[key] = val


    if "weekly_history" in data:
        del data["weekly_history"]

    today_str = get_today_str()
    last_active = data.get("last_active_date", today_str)


    if last_active != today_str:
        try:
            today_date = date.today()
            yesterday_str = str(today_date - timedelta(days=1))

            if data.get("last_streak_completed_date") != yesterday_str:
                data["streak_count"] = 0
        except Exception:
            pass

        data["drunk_today_ml"] = 0
        data["last_active_date"] = today_str
        save_config(data)

    return data


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class SettingsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = load_config()

        self.title("Hydration & Health Studio ✨")
        self.geometry("440x730")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        self.setup_ui()
        self.apply_theme_colors()
        self.update_display()

    def setup_ui(self):
        # 1. Üst Başlık & Streak
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=(15, 5))

        self.lbl_title = ctk.CTkLabel(self.top_frame, text="Health Assistant ✨", font=("Segoe UI", 18, "bold"))
        self.lbl_title.pack(side="left")

        self.lbl_streak = ctk.CTkLabel(
            self.top_frame, text=f"🔥 {self.config.get('streak_count', 0)} Gün Seri",
            font=("Segoe UI", 11, "bold"), corner_radius=10, padx=10, pady=3
        )
        self.lbl_streak.pack(side="right")

        # 2. İlerleme Kartı
        self.progress_card = ctk.CTkFrame(self, corner_radius=15)
        self.progress_card.pack(fill="x", padx=20, pady=6)

        self.lbl_progress = ctk.CTkLabel(self.progress_card, text="", font=("Segoe UI", 14, "bold"),
                                         text_color="#FFFFFF")
        self.lbl_progress.pack(pady=(8, 2))

        self.progress_bar = ctk.CTkProgressBar(self.progress_card, height=10)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))

        # 3. Butonlar & 1 Saat Sustur
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=2)

        self.btn_drink = ctk.CTkButton(
            btn_frame, text="+1 Bardak Su İçtim (250 ml) 💧",
            font=("Segoe UI", 12, "bold"), corner_radius=10, height=36, command=self.add_glass
        )
        self.btn_drink.pack(fill="x", pady=(0, 4))

        sub_btn_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        sub_btn_frame.pack(fill="x")

        self.btn_reset = ctk.CTkButton(
            sub_btn_frame, text="Bugünü Sıfırla 🔄", font=("Segoe UI", 10),
            fg_color="#24242C", hover_color="#33333E", text_color="#A0A0AA",
            corner_radius=8, height=26, command=self.reset_counter
        )
        self.btn_reset.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_mute = ctk.CTkButton(
            sub_btn_frame, text="1 Saat Sustur 🔕", font=("Segoe UI", 10, "bold"),
            fg_color="#382E24", hover_color="#4F3F2F", text_color="#F4A261",
            corner_radius=8, height=26, command=self.toggle_mute_one_hour
        )
        self.btn_mute.pack(side="right", fill="x", expand=True, padx=(3, 0))

        # 4. Son 7 Gün Grafik Kartı
        self.chart_card = ctk.CTkFrame(self, corner_radius=15)
        self.chart_card.pack(fill="x", padx=20, pady=6)

        self.lbl_chart_title = ctk.CTkLabel(
            self.chart_card, text="Son 7 Günlük Su Tüketimi (Litre) 📊",
            font=("Segoe UI", 11, "bold"), text_color="#E0D0D8"
        )
        self.lbl_chart_title.pack(anchor="w", padx=15, pady=(6, 2))

        self.chart_bars_frame = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.chart_bars_frame.pack(fill="x", padx=10, pady=(0, 6))

        # 5. Ayar Kartı
        self.settings_frame = ctk.CTkFrame(self, corner_radius=15)
        self.settings_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.settings_frame, text="Günlük Hedef (L):", font=("Segoe UI", 11)).grid(row=0, column=0,
                                                                                                padx=10, pady=3,
                                                                                                sticky="w")
        self.entry_goal = ctk.CTkEntry(self.settings_frame, width=75, height=24)
        self.entry_goal.insert(0, str(self.config['daily_goal_liters']))
        self.entry_goal.grid(row=0, column=1, padx=10, pady=3)

        ctk.CTkLabel(self.settings_frame, text="Su Aralığı (dk):", font=("Segoe UI", 11)).grid(row=1, column=0, padx=10,
                                                                                               pady=3, sticky="w")
        self.entry_water_int = ctk.CTkEntry(self.settings_frame, width=75, height=24)
        self.entry_water_int.insert(0, str(self.config['water_interval_mins']))
        self.entry_water_int.grid(row=1, column=1, padx=10, pady=3)

        self.switch_break_var = ctk.BooleanVar(value=self.config.get("break_enabled", True))
        self.switch_break = ctk.CTkSwitch(
            self.settings_frame, text="Göz / Duruş Molası", font=("Segoe UI", 11),
            variable=self.switch_break_var, command=self.toggle_break_entry
        )
        self.switch_break.grid(row=2, column=0, padx=10, pady=3, sticky="w")

        self.entry_break_int = ctk.CTkEntry(self.settings_frame, width=75, height=24)
        self.entry_break_int.insert(0, str(self.config['break_interval_mins']))
        self.entry_break_int.grid(row=2, column=1, padx=10, pady=3)

        ctk.CTkLabel(self.settings_frame, text="Uygulama Teması:", font=("Segoe UI", 11)).grid(row=3, column=0, padx=10,
                                                                                               pady=3, sticky="w")
        self.opt_theme = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Pink Blossom", "Pastel Matcha Green", "Ocean Blue", "Dark Slate"],
            height=24,
            command=self.change_theme
        )
        self.opt_theme.set(self.config.get("active_theme", "Pink Blossom"))
        self.opt_theme.grid(row=3, column=1, padx=10, pady=3)

        self.toggle_break_entry()

        # 6. Alt Eylem Butonları
        bottom_action_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_action_frame.pack(fill="x", padx=20, pady=(6, 12))

        self.btn_save = ctk.CTkButton(
            bottom_action_frame, text="Ayarları Kaydet 💾", font=("Segoe UI", 11, "bold"),
            corner_radius=10, height=32, command=self.save_settings
        )
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_exit = ctk.CTkButton(
            bottom_action_frame, text="Uygulamayı Kapat ❌", font=("Segoe UI", 11, "bold"),
            fg_color="#7A1D2E", hover_color="#9E253B", corner_radius=10, height=32, command=self.exit_full_application
        )
        self.btn_exit.pack(side="right", fill="x", expand=True, padx=(4, 0))

    def apply_theme_colors(self):
        theme_name = self.config.get("active_theme", "Pink Blossom")
        style = THEME_STYLES.get(theme_name, THEME_STYLES["Pink Blossom"])

        self.lbl_title.configure(text_color=style["accent"])
        self.lbl_streak.configure(fg_color=style["border"], text_color=style["accent"])
        self.progress_card.configure(fg_color=style["card_bg"])
        self.chart_card.configure(fg_color=style["subcard_bg"])
        self.settings_frame.configure(fg_color=style["subcard_bg"])
        self.btn_drink.configure(fg_color=style["primary"], hover_color=style["primary_hover"])
        self.progress_bar.configure(progress_color=style["accent"])
        self.switch_break.configure(progress_color=style["primary"])
        self.opt_theme.configure(fg_color=style["primary"], button_color=style["primary_hover"])
        self.btn_save.configure(fg_color=style["border"], hover_color=style["primary"])

    def change_theme(self, choice):
        self.config["active_theme"] = choice
        save_config(self.config)
        self.apply_theme_colors()
        self.render_weekly_chart()

    def toggle_mute_one_hour(self):
        current = time.time()
        mute_until = self.config.get("mute_until", 0)

        if current < mute_until:
            self.config["mute_until"] = 0
            self.btn_mute.configure(text="1 Saat Sustur 🔕", fg_color="#382E24", text_color="#F4A261")
        else:
            self.config["mute_until"] = current + 3600
            self.btn_mute.configure(text="Susturuldu (Aç 🔔)", fg_color="#4CAF50", text_color="#FFFFFF")

        save_config(self.config)

    def toggle_break_entry(self):
        if self.switch_break_var.get():
            self.entry_break_int.configure(state="normal")
        else:
            self.entry_break_int.configure(state="disabled")

    def render_weekly_chart(self):
        for widget in self.chart_bars_frame.winfo_children():
            widget.destroy()

        daily_history = self.config.get("daily_history", {})
        goal_l = max(0.5, self.config.get("daily_goal_liters", 2.0))
        today_date = date.today()
        theme_name = self.config.get("active_theme", "Pink Blossom")
        style = THEME_STYLES.get(theme_name, THEME_STYLES["Pink Blossom"])


        last_7_days = [today_date - timedelta(days=i) for i in range(6, -1, -1)]

        for col_idx, day_d in enumerate(last_7_days):
            day_str = str(day_d)
            day_name = DAYS_TR[day_d.weekday()]
            is_today = (day_d == today_date)

            val_l = daily_history.get(day_str, 0.0)
            ratio = min(1.0, val_l / goal_l)

            col_frame = ctk.CTkFrame(self.chart_bars_frame, fg_color="transparent")
            col_frame.grid(row=0, column=col_idx, padx=4, pady=2, sticky="nsew")
            self.chart_bars_frame.grid_columnconfigure(col_idx, weight=1)

            bar_color = style["primary"] if is_today else style["border"]
            if ratio >= 1.0:
                bar_color = "#4CAF50"

            p_bar = ctk.CTkProgressBar(col_frame, orientation="vertical", width=10, height=38, progress_color=bar_color)
            p_bar.set(ratio)
            p_bar.pack(pady=(2, 2))

            lbl_day = ctk.CTkLabel(
                col_frame, text=day_name,
                font=("Segoe UI", 9, "bold" if is_today else "normal"),
                text_color=style["accent"] if is_today else "#9E9EAA"
            )
            lbl_day.pack()

    def add_glass(self):
        goal_ml = self.config['daily_goal_liters'] * 1000
        current_ml = self.config.get("drunk_today_ml", 0)
        glass_size = self.config.get("glass_size_ml", 250)

        new_total = min(goal_ml, current_ml + glass_size)
        self.config["drunk_today_ml"] = int(new_total)

        # Tarih bazlı kaydet (YYYY-MM-DD)
        today_str = get_today_str()
        if "daily_history" not in self.config:
            self.config["daily_history"] = {}
        self.config["daily_history"][today_str] = round(new_total / 1000, 2)

        # Streak Kontrolü
        if new_total >= goal_ml and self.config.get("last_streak_completed_date") != today_str:
            self.config["streak_count"] = self.config.get("streak_count", 0) + 1
            self.config["last_streak_completed_date"] = today_str

        save_config(self.config)
        self.update_display()

    def reset_counter(self):
        today_str = get_today_str()


        if self.config.get("last_streak_completed_date") == today_str:
            self.config["streak_count"] = max(0, self.config.get("streak_count", 1) - 1)
            self.config["last_streak_completed_date"] = ""

        self.config["drunk_today_ml"] = 0
        if "daily_history" in self.config:
            self.config["daily_history"][today_str] = 0.0

        save_config(self.config)
        self.update_display()

    def save_settings(self):
        try:
            old_goal_ml = self.config["daily_goal_liters"] * 1000
            new_goal_l = float(self.entry_goal.get())
            new_goal_ml = new_goal_l * 1000
            current_ml = self.config.get("drunk_today_ml", 0)
            today_str = get_today_str()

            self.config["daily_goal_liters"] = new_goal_l
            self.config["water_interval_mins"] = int(self.entry_water_int.get())
            self.config["break_interval_mins"] = int(self.entry_break_int.get())
            self.config["break_enabled"] = self.switch_break_var.get()

            # Eğer hedef yükseltildiyse ve mevcut su artık hedefin altında kaldıysa streak geri alınır
            if current_ml < new_goal_ml and self.config.get("last_streak_completed_date") == today_str:
                self.config["streak_count"] = max(0, self.config.get("streak_count", 1) - 1)
                self.config["last_streak_completed_date"] = ""
            elif current_ml >= new_goal_ml and self.config.get("last_streak_completed_date") != today_str:
                self.config["streak_count"] = self.config.get("streak_count", 0) + 1
                self.config["last_streak_completed_date"] = today_str

            save_config(self.config)
            self.update_display()
        except ValueError:
            pass

    def exit_full_application(self):
        self.config["is_running"] = False
        save_config(self.config)
        self.destroy()
        os._exit(0)

    def update_display(self):
        goal_ml = self.config['daily_goal_liters'] * 1000
        drunk_ml = self.config.get('drunk_today_ml', 0)
        drunk_l = drunk_ml / 1000
        goal_l = self.config['daily_goal_liters']

        streak = self.config.get("streak_count", 0)
        self.lbl_streak.configure(text=f"🔥 {streak} Gün Seri")

        if time.time() < self.config.get("mute_until", 0):
            self.btn_mute.configure(text="Susturuldu (Aç 🔔)", fg_color="#4CAF50", text_color="#FFFFFF")
        else:
            self.btn_mute.configure(text="1 Saat Sustur 🔕", fg_color="#382E24", text_color="#F4A261")

        if drunk_ml >= goal_ml and goal_ml > 0:
            self.progress_bar.set(1.0)
            self.progress_bar.configure(progress_color="#4CAF50")
            self.lbl_progress.configure(text=f"{drunk_l:.2f} / {goal_l:.1f} L 🎉 Hedef Tamamlandı!",
                                        text_color="#4CAF50")
            self.btn_drink.configure(text="Tebrikler! Bugünlük Hedefe Ulaştın 🏆", state="disabled", fg_color="#334233")
        else:
            progress_val = (drunk_ml / goal_ml) if goal_ml > 0 else 0
            self.progress_bar.set(progress_val)
            theme_name = self.config.get("active_theme", "Pink Blossom")
            self.progress_bar.configure(progress_color=THEME_STYLES[theme_name]["accent"])
            self.lbl_progress.configure(text=f"{drunk_l:.2f} / {goal_l:.1f} Litre", text_color="#FFFFFF")
            self.btn_drink.configure(
                text="+1 Bardak Su İçtim (250 ml) 💧", state="normal",
                fg_color=THEME_STYLES[theme_name]["primary"]
            )

        self.render_weekly_chart()


if __name__ == "__main__":
    app = SettingsApp()
    app.mainloop()