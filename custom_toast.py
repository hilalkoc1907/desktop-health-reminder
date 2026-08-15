import os
import platform
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageTk

IS_WINDOWS = platform.system() == "Windows"

CARD_W, CARD_H = 340, 96
RADIUS = 20
PADDING = 10
SUPERSAMPLE = 3
MARGIN_SCREEN = 20
GAP_BETWEEN_TOASTS = 12
DEFAULT_DURATION_MS = 5000
DEFAULT_POSITION = "bottom-right"
FADE_STEPS = 12
FADE_DELAY_MS = 15
QUEUE_POLL_MS = 100
SOUND_ENABLED_DEFAULT = True

TRANSPARENT_KEY = "#ff00fe"
SHADOW_COLOR = (0, 0, 0, 130)


THEMES = {
    "Pink Blossom": {
        "bg": (38, 25, 32),
        "title": (255, 255, 255),
        "msg": (230, 200, 215),
        "accent": (255, 117, 140)
    },
    "Pastel Matcha Green": {
        "bg": (24, 36, 26),
        "title": (255, 255, 255),
        "msg": (205, 230, 210),
        "accent": (144, 190, 109)
    },
    "Ocean Blue": {
        "bg": (18, 30, 45),
        "title": (255, 255, 255),
        "msg": (195, 220, 245),
        "accent": (77, 150, 223)
    },
    "Dark Slate": {
        "bg": (25, 25, 28),
        "title": (255, 255, 255),
        "msg": (180, 180, 190),
        "accent": (130, 130, 145)
    }
}

ICONS = {
    "water": "\U0001F4A7",
    "break": "\U0001F9D8",
    "pomodoro": "\U0001F345",
    "default": "\U0001F514"
}

import ctypes


def _open_settings():
    try:
        if IS_WINDOWS:
            user32 = ctypes.windll.user32
            window_title = "Hydration & Health Studio ✨"
            hwnd = user32.FindWindowW(None, window_title)

            if hwnd != 0:
                SW_RESTORE = 9
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
                return

        script_dir = os.path.dirname(os.path.abspath(__file__))


        exe_target = os.path.join(script_dir, "settings_gui.exe")
        py_target = os.path.join(script_dir, "settings_gui.py")

        if os.path.exists(exe_target):
            subprocess.Popen([exe_target])
        elif os.path.exists(py_target):
            subprocess.Popen([sys.executable, py_target])

    except Exception as e:
        print(f"Ayarlar penceresi açılamadı: {e}", file=sys.stderr)


def _play_pop():
    def _worker():
        try:
            if IS_WINDOWS:
                import winsound
                try:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    winsound.Beep(800, 40)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()


def _load_font(candidates, size):
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return "\n".join(lines[:3])


def _draw_card_rgba(title, message, kind, theme_name, scale):
    palette = THEMES.get(theme_name, THEMES["Pink Blossom"])
    bg_color = (*palette["bg"], 255)
    title_color = palette["title"]
    msg_color = palette["msg"]
    accent = palette["accent"]

    full_w, full_h = (CARD_W + PADDING * 2) * scale, (CARD_H + PADDING * 2) * scale
    canvas = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    card_w, card_h = CARD_W * scale, CARD_H * scale
    pad = PADDING * scale
    radius = RADIUS * scale

    # Gölge
    draw.rounded_rectangle(
        [pad + int(2 * scale), pad + int(4 * scale), pad + card_w + int(2 * scale), pad + card_h + int(4 * scale)],
        radius=radius, fill=SHADOW_COLOR
    )

    # Gövde
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=radius, fill=bg_color)

    # Sol Şerit
    strip = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    ImageDraw.Draw(strip).rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=radius, fill=(*accent, 255))
    strip_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(strip_mask).rectangle([0, 0, int(5 * scale), card_h], fill=255)
    card.paste(strip, (0, 0), strip_mask)

    # İkon Dairesi
    d = int(46 * scale)
    icon_box = (int(16 * scale), (card_h - d) // 2, int(16 * scale) + d, (card_h + d) // 2)
    cd.ellipse(icon_box, fill=(*accent, 255))
    font_emoji = _load_font(["seguiemj.ttf", "NotoColorEmoji.ttf"], int(20 * scale))
    cd.text((icon_box[0] + d / 2, icon_box[1] + d / 2), ICONS.get(kind, ICONS["default"]), font=font_emoji, fill="white", anchor="mm")

    # Başlık & Mesaj
    text_x = int(16 * scale) + d + int(14 * scale)
    font_title = _load_font(["segoeuib.ttf", "Arial Bold.ttf"], int(14 * scale))
    font_msg = _load_font(["segoeui.ttf", "Arial.ttf"], int(11 * scale))

    cd.text((text_x, int(18 * scale)), title, font=font_title, fill=title_color)
    wrapped = _wrap(message, font_msg, card_w - text_x - int(14 * scale))
    cd.multiline_text((text_x, int(42 * scale)), wrapped, font=font_msg, fill=msg_color, spacing=int(4 * scale))

    canvas.alpha_composite(card, (pad, pad))
    return canvas


def _build_toast_image(title, message, kind="default", theme_name="Pink Blossom"):
    hi_res = _draw_card_rgba(title, message, kind, theme_name, SUPERSAMPLE)
    target_size = (CARD_W + PADDING * 2, CARD_H + PADDING * 2)
    lo_res = hi_res.resize(target_size, Image.LANCZOS)

    if not IS_WINDOWS:
        return lo_res, False

    r, g, b, a = lo_res.split()
    a = a.point(lambda p: 255 if p > 110 else 0)
    lo_res = Image.merge("RGBA", (r, g, b, a))

    chroma_bg = Image.new("RGB", lo_res.size, ImageColor.getrgb(TRANSPARENT_KEY))
    chroma_bg.paste(lo_res, (0, 0), lo_res)
    return chroma_bg, True


class _ToastWindow:
    def __init__(self, root, image, is_chroma_keyed, duration_ms, position, stack_index, on_close, sound):
        self.root = root
        self.duration_ms = duration_ms
        self.position = position
        self.on_close = on_close
        self.w, self.h = image.size

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)

        if is_chroma_keyed:
            self.win.configure(bg=TRANSPARENT_KEY)
            try:
                self.win.attributes("-transparentcolor", TRANSPARENT_KEY)
            except tk.TclError:
                pass

        try:
            self.win.attributes("-alpha", 0.0)
        except tk.TclError:
            pass

        self._tk_img = ImageTk.PhotoImage(image)

        x, y = self._position_for(stack_index)
        self.win.geometry(f"{self.w}x{self.h}+{x}+{y}")

        label_bg = TRANSPARENT_KEY if is_chroma_keyed else None
        label = tk.Label(self.win, image=self._tk_img, bd=0, highlightthickness=0, cursor="hand2")
        if label_bg:
            label.configure(bg=label_bg)
        label.pack()

        def _on_click(event):
            self.close()
            _open_settings()

        label.bind("<Button-1>", _on_click)
        self.win.bind("<Button-1>", _on_click)

        if sound:
            _play_pop()

        self._fade_in()

    def _position_for(self, stack_index):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - self.w - MARGIN_SCREEN if "right" in self.position else MARGIN_SCREEN
        offset = stack_index * (CARD_H + GAP_BETWEEN_TOASTS)
        y = screen_h - self.h - MARGIN_SCREEN - offset if "bottom" in self.position else MARGIN_SCREEN + offset
        return x, y

    def reposition(self, stack_index):
        x, y = self._position_for(stack_index)
        try:
            self.win.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def _fade_in(self, step=0):
        if not self._alive():
            return
        self._set_alpha(min(1.0, step / FADE_STEPS))
        if step < FADE_STEPS:
            self.win.after(FADE_DELAY_MS, self._fade_in, step + 1)
        else:
            self.win.after(self.duration_ms, self._fade_out)

    def _fade_out(self, step=0):
        if not self._alive():
            return
        self._set_alpha(max(0.0, 1 - step / FADE_STEPS))
        if step < FADE_STEPS:
            self.win.after(FADE_DELAY_MS, self._fade_out, step + 1)
        else:
            self.close()

    def _set_alpha(self, value):
        try:
            self.win.attributes("-alpha", value)
        except tk.TclError:
            pass

    def _alive(self):
        try:
            return bool(self.win.winfo_exists())
        except tk.TclError:
            return False

    def close(self):
        if self._alive():
            try:
                self.win.destroy()
            except tk.TclError:
                pass
        self.on_close(self)


class ToastManager:
    def __init__(self, position=DEFAULT_POSITION, duration_ms=DEFAULT_DURATION_MS, sound_enabled=SOUND_ENABLED_DEFAULT):
        self.position = position
        self.duration_ms = duration_ms
        self.sound_enabled = sound_enabled
        self._queue = queue.Queue()
        self._active = []
        self._root = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("Toast penceresi başlatılamadı.")

    def _run(self):
        self._root = tk.Tk()
        self._root.withdraw()
        self._ready.set()
        self._poll_queue()
        self._root.mainloop()

    def _poll_queue(self):
        try:
            while True:
                title, message, kind, theme_name, duration_ms, position, sound = self._queue.get_nowait()
                self._spawn(title, message, kind, theme_name, duration_ms, position, sound)
        except queue.Empty:
            pass
        if self._root:
            self._root.after(QUEUE_POLL_MS, self._poll_queue)

    def _spawn(self, title, message, kind, theme_name, duration_ms, position, sound):
        image, is_chroma_keyed = _build_toast_image(title, message, kind, theme_name)
        same_corner = [t for t in self._active if t.position == position]
        toast = _ToastWindow(self._root, image, is_chroma_keyed, duration_ms, position, len(same_corner), self._on_closed, sound)
        self._active.append(toast)

    def _on_closed(self, toast):
        if toast in self._active:
            self._active.remove(toast)
            same_corner = [t for t in self._active if t.position == toast.position]
            for i, t in enumerate(same_corner):
                t.reposition(i)

    def show(self, title, message, kind="default", theme_name="Pink Blossom", duration_ms=None, position=None):
        self._queue.put((
            title,
            message,
            kind,
            theme_name,
            duration_ms if duration_ms is not None else self.duration_ms,
            position if position is not None else self.position,
            self.sound_enabled,
        ))

    def stop(self):
        if self._root:
            try:
                self._root.after(0, self._root.quit)
            except Exception:
                pass