#!/usr/bin/env python3
"""Ableton Bounce Automator v2.0"""

import sys, os, subprocess, time, gzip, threading, socket, json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

try:
    import win32gui, win32con
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0.05
except ImportError as e:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Missing dependency", f"{e}\npip install pywin32 pyautogui")
    sys.exit(1)

MAX_RENDER_SEC = 180

# ── ALS ──────────────────────────────────────────────────────────────────────
def als_tempo(path):
    try:
        with gzip.open(path, "rb") as f:
            root = ET.fromstring(f.read())
        for t in root.iter("Tempo"):
            m = t.find("Manual")
            if m is not None: return float(m.get("Value", 120))
    except: pass
    return 120.0

def als_last_clip_sec(path):
    try:
        with gzip.open(path, "rb") as f:
            root = ET.fromstring(f.read())
        bps = als_tempo(path) / 60.0
        max_end = 0.0
        for clip in root.iter():
            if clip.tag in ("AudioClip", "MidiClip"):
                for ce in clip.findall(".//CurrentEnd"):
                    v = float(ce.get("Value", 0))
                    if v > max_end: max_end = v
        return (max_end / bps) if max_end > 0 else None
    except: return None

def bars_for_seconds(seconds, tempo, beats_per_bar=4):
    bars = int(seconds * tempo / 60.0 / beats_per_bar) + 1
    return f"{bars}. 0. 0"

# ── Window helpers ────────────────────────────────────────────────────────────
def find_ableton():
    found = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "Ableton Live" in win32gui.GetWindowText(h):
            found.append(h)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

def splash_is_open():
    found = []
    def cb(h, _):
        if not win32gui.IsWindowVisible(h): return
        if win32gui.GetWindowText(h) != "": return
        try:
            if win32gui.GetClassName(h) == "Ableton Live Window Class":
                r = win32gui.GetWindowRect(h)
                if 100 < r[2]-r[0] < 800 and 100 < r[3]-r[1] < 800:
                    found.append(h)
        except: pass
    win32gui.EnumWindows(cb, None)
    return bool(found)

def _get_ableton_popup():
    hwnd = find_ableton()
    if not hwnd: return None
    try:
        popup = win32gui.GetWindow(hwnd, win32con.GW_ENABLEDPOPUP)
        if not popup or popup == hwnd: return None
        if not win32gui.IsWindowVisible(popup): return None
        return popup
    except: return None

def dismiss_save_dialog():
    popup = _get_ableton_popup()
    if not popup: return False
    try: win32gui.SetForegroundWindow(popup)
    except: pass
    time.sleep(0.3)
    pyautogui.press("tab"); time.sleep(0.1)
    pyautogui.press("enter"); time.sleep(0.5)
    return True

def dismiss_ok_dialog():
    popup = _get_ableton_popup()
    if not popup: return False
    try: win32gui.SetForegroundWindow(popup)
    except: pass
    time.sleep(0.3)
    pyautogui.press("enter"); time.sleep(0.5)
    return True

# ── AbletonMCP socket ─────────────────────────────────────────────────────────
def ableton_command(command, timeout=5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(("localhost", 9877))
        s.sendall((json.dumps({"type": command}) + "\n").encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            data += chunk
            try: json.loads(data.decode()); break
            except json.JSONDecodeError: continue
        s.close()
        return json.loads(data.decode())
    except: return None

# ── wait_ableton (4 fases) ────────────────────────────────────────────────────
def wait_ableton(timeout=180, expected_stem=None):
    start = time.time()
    # Fase 0: splash fechar
    while time.time() - start < timeout:
        if not splash_is_open(): break
        time.sleep(0.4)
    # Fase 1: sem dialogs pendentes
    for _ in range(40):
        if time.time() - start >= timeout: return False
        if _get_ableton_popup() is None: break
        dismiss_save_dialog(); time.sleep(0.3)
    # Fase 2: titulo correto
    while time.time() - start < timeout:
        dismiss_save_dialog()
        hwnd = find_ableton()
        if hwnd:
            title = win32gui.GetWindowText(hwnd)
            if not expected_stem or expected_stem.lower() in title.lower(): break
        time.sleep(0.5)
    else:
        hwnd = find_ableton()
        if hwnd and "untitled" in win32gui.GetWindowText(hwnd).lower():
            return "corrupted"
        return False
    # Fase 3: socket estavel por 5s
    check_start = time.time()
    while time.time() - start < timeout:
        dismiss_save_dialog()
        resp = ableton_command("get_session_info")
        if resp and resp.get("status") == "success":
            if time.time() - check_start >= 5.0: return True
        else:
            check_start = time.time()
        time.sleep(0.5)
    return False

# ── Export helpers ────────────────────────────────────────────────────────────
def open_export_dialog():
    hwnd = find_ableton()
    if not hwnd: return None
    try:
        if win32gui.IsIconic(hwnd): win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except: pass
    time.sleep(0.3)
    rect = win32gui.GetWindowRect(hwnd)
    pyautogui.click((rect[0]+rect[2])//2, rect[1]+15)
    time.sleep(0.4)
    dismiss_ok_dialog(); time.sleep(0.2)
    pyautogui.hotkey("ctrl", "shift", "r")
    time.sleep(2.5)
    exp = []
    def find_exp(h, _):
        if not win32gui.IsWindowVisible(h): return
        if h == hwnd: return
        if "Export Audio/Video" in win32gui.GetWindowText(h): exp.append(h)
    for _ in range(20):
        win32gui.EnumWindows(find_exp, exp)
        if exp: return exp[0]
        time.sleep(0.3)
    return None


def is_orange(r, g, b):
    """Pixel laranja do botao ON do Ableton: RGB aprox (250,165,70)."""
    return r > 200 and 100 < g < 185 and b < 100

def grab_dialog(hwnd):
    from PIL import ImageGrab
    rect = win32gui.GetWindowRect(hwnd)
    img  = ImageGrab.grab(bbox=rect, all_screens=True)
    return img, img.size[0], img.size[1]

def find_orange_rows(hwnd):
    """Retorna lista de y_frac onde ha pixels laranjas (botoes ON)."""
    img, w, h = grab_dialog(hwnd)
    found = []
    for y in range(h):
        for xf in [0.72, 0.75, 0.78, 0.81, 0.84, 0.87, 0.90]:
            r, g, b = img.getpixel((int(w * xf), y))
            if is_orange(r, g, b):
                found.append(round(y / h, 3))
                break
    return found

def check_toggles(hwnd):
    """Tira UM screenshot e retorna (wav_on, mp3_on) de uma vez.
    WAV (Encode PCM) esta em y_frac ~0.390, MP3 em y_frac ~0.730-0.742.
    """
    rows = find_orange_rows(hwnd)
    wav_on = any(0.350 < r < 0.440 for r in rows)
    mp3_on = any(0.700 < r < 0.780 for r in rows)
    return wav_on, mp3_on

def is_toggle_on(hwnd, y_frac):
    """Wrapper: usa check_toggles para evitar screenshots multiplos."""
    wav_on, mp3_on = check_toggles(hwnd)
    if 0.350 < y_frac < 0.440:
        return wav_on
    if 0.700 < y_frac < 0.780:
        return mp3_on
    # fallback: scan direto
    img, w, h = grab_dialog(hwnd)
    yc = int(h * y_frac)
    for dy in range(-15, 16):
        y = yc + dy
        if y < 0 or y >= h: continue
        for xf in [0.70, 0.73, 0.76, 0.79, 0.82, 0.85, 0.88, 0.91]:
            r, g, b = img.getpixel((int(w * xf), y))
            if is_orange(r, g, b): return True
    return False

def navigate_export_dialog(export_hwnd, project_folder, als_stem, end_sec, log=None):
    """
    Tab x3  -> Render Start  (leave as-is)
    Tab x1  -> Render Length -> digita barras -> Enter
    Tab x7  -> WAV toggle    -> desliga se ON
    Tab x4  -> MP3 toggle    -> liga se OFF
    Tab x4  -> Export button -> Enter -> Save As
    """
    win32gui.SetForegroundWindow(export_hwnd)
    time.sleep(0.7)
    for _ in range(3): pyautogui.press("tab"); time.sleep(0.08)
    pyautogui.press("tab"); time.sleep(0.15)
    als_path = Path(project_folder) / (als_stem + ".als")
    tempo    = als_tempo(als_path) if als_path.exists() else 120.0
    pyautogui.hotkey("ctrl", "a"); time.sleep(0.1)
    pyautogui.write(bars_for_seconds(end_sec, tempo), interval=0.05)
    pyautogui.press("enter"); time.sleep(0.2)
    for _ in range(7): pyautogui.press("tab"); time.sleep(0.08)
    time.sleep(0.5)
    wav_on, mp3_on = check_toggles(export_hwnd)
    log("  [toggle] current state — WAV=" + ("ON" if wav_on else "OFF") + " MP3=" + ("ON" if mp3_on else "OFF"))
    if wav_on:
        log("  [toggle] WAV ON -> turning off")
        pyautogui.press("enter"); time.sleep(0.5)

    # Tab x4 -> MP3
    for _ in range(4): pyautogui.press("tab"); time.sleep(0.08)
    time.sleep(0.5)
    if not mp3_on:
        log("  [toggle] MP3 OFF -> turning on")
        pyautogui.press("enter"); time.sleep(0.5)

    # Verificacao final com novo screenshot
    wav_final, mp3_final = check_toggles(export_hwnd)
    log("  [toggle] FINAL — WAV=" + ("ON" if wav_final else "OFF") + " MP3=" + ("ON" if mp3_final else "OFF"))
    if wav_final or not mp3_final:
        log("  [toggle] WARNING incorrect state!", warn=True)

    # Tab x4 -> Export button -> Enter
    for _ in range(4): pyautogui.press("tab"); time.sleep(0.08)
    pyautogui.press("enter"); time.sleep(2.0)
    ableton_hwnd = find_ableton()
    IGNORE = {"Ableton Bounce Automator","Program Manager","claude","Arc","WhatsApp",
              "Configuracoes","Experiencia de Entrada","Transport Time",
              "RaycastUIAccessHelperWindow","RaycastNodeGracefulShutdownWindow","PowerToys"}
    save_dlg = []
    def find_save(h, _):
        if not win32gui.IsWindowVisible(h): return
        if h in (ableton_hwnd, export_hwnd): return
        t = win32gui.GetWindowText(h)
        if not t or any(ig in t for ig in IGNORE): return
        r = win32gui.GetWindowRect(h)
        if r[2]-r[0] > 200 and r[3]-r[1] > 80: save_dlg.append(h)
    for _ in range(30):
        win32gui.EnumWindows(find_save, None)
        if save_dlg: break
        time.sleep(0.3)
    if not save_dlg: return False, "Save As dialog did not open"
    win32gui.SetForegroundWindow(save_dlg[0]); time.sleep(0.5)
    mp3_name = f"{Path(project_folder).name} - {als_stem}.mp3"
    mp3_full = str(Path(project_folder) / mp3_name)
    subprocess.run(["clip"], input=mp3_full.encode("utf-16-le"), check=True)
    pyautogui.hotkey("ctrl", "a"); time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v"); time.sleep(0.3)
    pyautogui.press("enter"); time.sleep(1.0)
    return True, mp3_full

def find_export_audio_window():
    found = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h)
            if "Export Audio" in t and "Video" not in t: found.append(h)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

def wait_export_progress():
    for _ in range(60):
        if find_export_audio_window(): break
        time.sleep(0.25)
    else:
        return False, "'Export Audio...' window did not appear"
    while find_export_audio_window(): time.sleep(0.4)
    time.sleep(2.0)
    if find_export_audio_window():
        while find_export_audio_window(): time.sleep(0.4)
        time.sleep(2.0)
    return True, "Export complete"

def clear_popups(n=15, delay=0.3):
    """Dismisses all pending Ableton dialogs until none remain."""
    for _ in range(n):
        if not _get_ableton_popup(): break
        dismiss_ok_dialog()
        time.sleep(delay)

# ── Watchdog helpers ─────────────────────────────────────────────────────────
def is_ableton_frozen():
    hwnd = find_ableton()
    if not hwnd: return False
    title = win32gui.GetWindowText(hwnd)
    return "(Not Responding)" in title or "(Não está respondendo)" in title

def kill_ableton():
    subprocess.run(["taskkill", "/F", "/FI", "IMAGENAME eq Ableton*"],
                   capture_output=True)
    for _ in range(30):
        if not find_ableton(): break
        time.sleep(0.5)
    time.sleep(2.0)

# ── GUI ───────────────────────────────────────────────────────────────────────
class BounceApp:
    C = dict(bg="#0f0f1a",panel="#1a1a2e",header="#1e3a5f",green="#00c853",
             orange="#ff6d00",red="#d50000",text="#e8eaf6",dim="#546e7a",
             info="#69f0ae",warn="#ffd740",err="#ff5252",step="#40c4ff",done="#ea80fc")

    def __init__(self, root):
        self.root = root
        self.root.title("Ableton Bounce Automator")
        self.root.geometry("740x600")
        self.root.minsize(620, 480)
        self.root.configure(bg=self.C["bg"])
        self._running = self._paused = self._stop = False
        self._ableton_frozen = False
        self._thread  = None
        self._build_ui()
        self._log("Ready. Select a folder and click Start.", "dim")

    def _build_ui(self):
        C = self.C
        hdr = tk.Frame(self.root, bg=C["header"], pady=10); hdr.pack(fill="x")
        tk.Label(hdr, text="  Ableton Bounce Automator", bg=C["header"], fg="white",
                 font=("Segoe UI",15,"bold")).pack(side="left", padx=16)
        tk.Label(hdr, text="v2.0", bg=C["header"], fg=C["dim"],
                 font=("Segoe UI",9)).pack(side="right", padx=12)
        fr = tk.Frame(self.root, bg=C["bg"], padx=14, pady=10); fr.pack(fill="x")
        tk.Label(fr, text="Projects folder:", bg=C["bg"], fg=C["text"],
                 font=("Segoe UI",10)).pack(anchor="w")
        row = tk.Frame(fr, bg=C["bg"]); row.pack(fill="x", pady=(4,0))
        self.folder_var = tk.StringVar()
        tk.Entry(row, textvariable=self.folder_var, bg=C["panel"], fg=C["text"],
                 relief="flat", insertbackground=C["text"],
                 font=("Consolas",10), bd=8).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Browse", command=self._browse, bg=C["header"], fg="white",
                  relief="flat", cursor="hand2", padx=12,
                  font=("Segoe UI",9)).pack(side="left", padx=(6,0))
        sb = tk.Frame(self.root, bg=C["panel"], padx=14, pady=6); sb.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(sb, textvariable=self.status_var, bg=C["panel"], fg=C["orange"],
                 font=("Segoe UI",10,"bold"), anchor="w").pack(side="left")
        self.prog_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self.prog_var, bg=C["panel"], fg=C["dim"],
                 font=("Segoe UI",9), anchor="e").pack(side="right")
        lf = tk.Frame(self.root, bg=C["bg"], padx=14, pady=6); lf.pack(fill="both", expand=True)
        tk.Label(lf, text="Execution log:", bg=C["bg"], fg=C["dim"],
                 font=("Segoe UI",8)).pack(anchor="w")
        self.log_box = scrolledtext.ScrolledText(lf, bg="#050510", fg=C["info"],
                 font=("Consolas",9), relief="flat", state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True, pady=(2,0))
        for tag, color in [("info",C["info"]),("warn",C["warn"]),("err",C["err"]),
                           ("step",C["step"]),("done",C["done"]),("dim",C["dim"]),("head","white")]:
            self.log_box.tag_config(tag, foreground=color)
        bf = tk.Frame(self.root, bg=C["bg"], pady=12); bf.pack()
        self.btn_play = tk.Button(bf, text="  Start", command=self._toggle_play,
            bg=C["green"], fg="#080808", font=("Segoe UI",13,"bold"),
            width=15, relief="flat", cursor="hand2", pady=7)
        self.btn_play.grid(row=0, column=0, padx=10)
        self.btn_stop = tk.Button(bf, text="  Stop", command=self._do_stop,
            bg=C["red"], fg="white", font=("Segoe UI",13,"bold"),
            width=15, relief="flat", cursor="hand2", pady=7, state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=10)
        self.btn_list_failed = tk.Button(bf, text="List Failures", command=self._list_failed,
            bg=C["warn"], fg="#080808", font=("Segoe UI",10,"bold"),
            width=15, relief="flat", cursor="hand2", pady=5)
        self.btn_list_failed.grid(row=1, column=0, padx=10, pady=(8,0))
        self.btn_clear_failed = tk.Button(bf, text="Clear Failures", command=self._clear_failed,
            bg=C["dim"], fg="white", font=("Segoe UI",10,"bold"),
            width=15, relief="flat", cursor="hand2", pady=5)
        self.btn_clear_failed.grid(row=1, column=1, padx=10, pady=(8,0))

    def _browse(self):
        p = filedialog.askdirectory(title="Select your Ableton projects folder")
        if p: self.folder_var.set(p.replace("/","\\"))

    def _log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] ", "dim")
        self.log_box.insert("end", f"{msg}\n", tag)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _toggle_play(self):
        if not self._running:
            folder = self.folder_var.get().strip()
            if not folder or not os.path.isdir(folder):
                messagebox.showerror("Error","Please select a valid folder."); return
            self._running = True; self._paused = self._stop = False
            self.btn_play.config(text="  Pause", bg=self.C["orange"])
            self.btn_stop.config(state="normal")
            self._thread = threading.Thread(target=self._worker, args=(folder,), daemon=True)
            self._thread.start()
        elif self._paused:
            self._paused = False
            self.btn_play.config(text="  Pause", bg=self.C["orange"])
            self.status_var.set("Resuming..."); self._log("Resumed.", "step")
        else:
            self._paused = True
            self.btn_play.config(text="  Resume", bg=self.C["green"])
            self.status_var.set("Paused"); self._log("Paused.", "warn")

    def _do_stop(self):
        self._stop = True; self._paused = False
        self._log("Stop requested.", "err"); self.status_var.set("Stopping...")
        self.btn_stop.config(state="disabled"); self.btn_play.config(state="disabled")

    def _reset(self):
        self._running = False
        self.btn_play.config(text="  Start", bg=self.C["green"], state="normal")
        self.btn_stop.config(state="disabled")

    def _list_failed(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first."); return
        failed = self._load_failed(folder)
        if not failed:
            self._log("Failure list is empty.", "info"); return
        self._log(f"── Failed projects ({len(failed)}) ─────────────────────────", "warn")
        for p in sorted(failed):
            self._log(f"  ✗  {Path(p).parent.name} / {Path(p).name}", "err")
        self._log("──────────────────────────────────────────────────────", "warn")

    def _clear_failed(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first."); return
        p = self._failed_path(folder)
        if not p.exists():
            self._log("Failure list is already empty.", "info"); return
        if messagebox.askyesno("Clear Failures", "Remove all projects from the failure list?"):
            p.unlink()
            self._log("Failure list cleared.", "step")

    def _watchdog_loop(self):
        while self._running and not self._stop:
            time.sleep(5)
            if not self._running or self._stop: break
            if is_ableton_frozen():
                self._log("[WATCHDOG] Ableton not responding! Flagging crash...", "err")
                self._ableton_frozen = True
                break

    def _ok(self):
        if self._stop or self._ableton_frozen: return False
        while self._paused:
            time.sleep(0.2)
            if self._stop or self._ableton_frozen: return False
        return True

    def _sleep(self, s):
        end = time.time() + s
        while time.time() < end:
            if not self._ok(): return False
            time.sleep(0.1)
        return True

    @staticmethod
    def mp3_exists(als_path):
        return (als_path.parent / f"{als_path.parent.name} - {als_path.stem}.mp3").exists()

    def _failed_path(self, folder):
        return Path(folder) / "_bouncer_failed.json"

    def _load_failed(self, folder):
        p = self._failed_path(folder)
        if p.exists():
            try: return set(json.loads(p.read_text(encoding="utf-8")))
            except: pass
        return set()

    def _save_failed(self, folder, path_str):
        p = self._failed_path(folder)
        data = self._load_failed(folder)
        data.add(path_str)
        p.write_text(json.dumps(sorted(data), indent=2, ensure_ascii=False), encoding="utf-8")

    def _scan(self, folder):
        results = []; skipped = []; failed_list = []; base = Path(folder)
        failed = self._load_failed(folder)
        def newest(d):
            files = [f for f in d.glob("*.als") if "backup" not in f.parent.name.lower()]
            return max(files, key=lambda p: p.stat().st_mtime) if files else None
        seen = set()
        for d in [base] + sorted([d for d in base.rglob("*")
                                   if d.is_dir() and "backup" not in d.name.lower()]):
            if d in seen: continue
            seen.add(d)
            f = newest(d)
            if not f: continue
            if str(f) in failed:
                failed_list.append(f)
            elif self.mp3_exists(f):
                skipped.append(f)
            else:
                results.append(f)
        return results, skipped, failed_list

    def _worker(self, folder):
        try:
            self._log(f"Folder: {folder}", "head")
            projects, skipped, failed_list = self._scan(folder)
            if failed_list:
                self._log(f"{len(failed_list)} failed project(s) (skipped):", "err")
                for p in failed_list: self._log(f"  ✗  {p.parent.name} / {p.name}", "err")
                self._log("", "dim")
            if skipped:
                self._log(f"{len(skipped)} already have MP3:", "dim")
                for p in skipped: self._log(f"  ok  {p.parent.name} - {p.stem}.mp3", "dim")
                self._log("", "dim")
            if not projects:
                self._log("No new projects found.", "warn"); self.root.after(0, self._reset); return
            self._log(f"{len(projects)} project(s) to process:", "done")
            for i, p in enumerate(projects, 1):
                self._log(f"  {i:3}. [{p.parent.name}]  {p.name}", "dim")
            self._log("", "dim")

            threading.Thread(target=self._watchdog_loop, daemon=True).start()

            for idx, als in enumerate(projects, 1):
                if self._stop: break
                crash_retries = 0
                while True:
                    # If watchdog flagged a freeze: kill, wait, restart
                    if self._ableton_frozen:
                        if crash_retries >= 1:
                            self._log("  [WATCHDOG] Repeated crash. Skipping project.", "err")
                            kill_ableton()
                            self._sleep(4)
                            self._ableton_frozen = False
                            threading.Thread(target=self._watchdog_loop, daemon=True).start()
                            break
                        crash_retries += 1
                        self._log(f"  [WATCHDOG] Killing frozen Ableton...", "err")
                        kill_ableton()
                        self._log(f"  [WATCHDOG] Restarting watchdog and reopening project ({als.name})...", "step")
                        self._ableton_frozen = False
                        threading.Thread(target=self._watchdog_loop, daemon=True).start()

                    if self._stop: break

                    self.root.after(0, lambda i=idx, t=len(projects): self.prog_var.set(f"{i} / {t}"))
                    name = als.parent.name; self.status_var.set(f"  {name}")
                    self._log("─"*54, "dim")
                    self._log(f"[{idx}/{len(projects)}]  {name}", "done")
                    self._log(f"  file     : {als.name}", "dim")
                    dur = als_last_clip_sec(als)
                    end_sec = min(dur, MAX_RENDER_SEC) if dur else MAX_RENDER_SEC
                    if dur: self._log(f"  duration : {dur:.1f}s  ->  {end_sec:.1f}s", "info")
                    else:   self._log(f"  duration not detected  ->  {end_sec}s", "warn")
                    if not self._ok(): break

                    clear_popups()
                    self._log("  -> Opening project...", "step")
                    os.startfile(str(als))
                    self._log("  -> Waiting for Ableton to load...", "step")
                    loaded = wait_ableton(timeout=180, expected_stem=als.stem)
                    if loaded == "corrupted":
                        self._log("  ERROR: Corrupted project — Ableton reverted to Untitled. Marking as failed.", "err")
                        self._save_failed(folder, str(als))
                        break
                    if not loaded:
                        if self._ableton_frozen:
                            continue  # volta ao topo do while para tratar o crash
                        self._log("  ERROR: Timeout. Skipping.", "err"); break
                    self._log("  Project ready.", "info")
                    if not self._ok():
                        if self._ableton_frozen: continue
                        break

                    self.status_var.set(f"Exporting: {name}")
                    MAX_EXPORT_ATTEMPTS = 15
                    exp_hwnd = None
                    for attempt in range(1, MAX_EXPORT_ATTEMPTS + 1):
                        if not self._ok(): break
                        self._log(f"  -> Export Audio/Video (attempt {attempt}/{MAX_EXPORT_ATTEMPTS})...", "step")
                        exp_hwnd = open_export_dialog()
                        if exp_hwnd: break
                        popup = _get_ableton_popup()
                        if popup:
                            popup_title = win32gui.GetWindowText(popup)
                            self._log(f"  Unexpected dialog: '{popup_title or '(no title)'}' — dismissing...", "warn")
                            dismiss_ok_dialog()
                            time.sleep(0.8)
                        else:
                            self._log(f"  Export did not open. Waiting 3s...", "warn")
                            self._sleep(3)
                    if not exp_hwnd:
                        if self._ableton_frozen: continue
                        if _get_ableton_popup():
                            dismiss_ok_dialog(); time.sleep(0.5)
                        self._log(f"  {MAX_EXPORT_ATTEMPTS} attempts failed. Skipping (not saved).", "err")
                        break

                    self._log("  Dialog open. Configuring...", "info")
                    ok, result = navigate_export_dialog(exp_hwnd, str(als.parent), als.stem, end_sec, log=lambda msg, warn=False: self._log(msg, 'warn' if warn else 'dim'))
                    if not ok:
                        self._log(f"  ERROR: {result}", "err")
                    else:
                        mp3_name = f"{als.parent.name} - {als.stem}.mp3"
                        mp3_path = als.parent / mp3_name
                        self._log(f"  Rendering: {mp3_name}", "info")
                        exp_ok, exp_msg = wait_export_progress()
                        clear_popups()
                        if exp_ok:
                            size_kb = mp3_path.stat().st_size // 1024 if mp3_path.exists() else 0
                            self._log(f"  Done: {mp3_name} ({size_kb} KB)", "done")
                        else:
                            self._log(f"  WARNING: {exp_msg}", "warn")
                    if self._ableton_frozen: continue
                    if not self._ok(): break
                    self._sleep(1.0)
                    break  # project completed successfully

            if self._stop: self._log("\nStopped.", "err"); self.status_var.set("Stopped.")
            else:          self._log("\nAll done!", "done"); self.status_var.set("Done!")

        except Exception as e:
            import traceback
            self._log(f"Error: {e}", "err"); self._log(traceback.format_exc(), "err")
        finally:
            self.root.after(0, self._reset)

if __name__ == "__main__":
    from license import is_activated, ActivationWindow
    root = tk.Tk()
    root.withdraw()                          # hide main window during activation check
    if not is_activated():
        aw = ActivationWindow(root)
        root.wait_window(aw.win)             # block until dialog closes
        if not aw.activated:                 # user closed without activating
            root.destroy()
            sys.exit(0)
    root.deiconify()                         # show main window
    BounceApp(root)
    root.mainloop()











