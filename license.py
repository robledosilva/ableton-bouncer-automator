"""
Ableton Bounce Automator — License module
Validation, activation and activation dialog.
"""

import hmac
import hashlib
import winreg
import tkinter as tk

# ── Secret (XOR-obfuscated, do not modify) ───────────────────────────────────
# Decoded at runtime: bytes(b ^ 0x5A for b in _RAW)
_RAW = bytes([0x08,0x6A,0x38,0x36,0x69,0x3E,0x6A,0x77,
              0x1B,0x18,0x1B,0x77,0x11,0x69,0x23,0x7B])
_S   = bytes(b ^ 0x5A for b in _RAW)

_REG_PATH  = r"Software\AbletonBounceAutomator"
_REG_VALUE = "LicKey"
_MAX_SERIALS = 9999   # max licenses ever generated


# ── Core logic ────────────────────────────────────────────────────────────────
def _clean(key: str) -> str:
    return key.upper().replace("-", "").replace(" ", "")

def _expected(serial: int) -> str:
    seed = str(serial).zfill(4).encode()
    return hmac.new(_S, seed, hashlib.sha256).hexdigest().upper()[:16]

def validate(key: str) -> bool:
    """Returns True if key matches any valid serial (1 – _MAX_SERIALS)."""
    k = _clean(key)
    if len(k) != 16:
        return False
    for i in range(1, _MAX_SERIALS + 1):
        if hmac.compare_digest(k, _expected(i)):
            return True
    return False

def is_activated() -> bool:
    """Returns True if a valid key is already saved in the Windows registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH) as reg:
            val, _ = winreg.QueryValueEx(reg, _REG_VALUE)
            return validate(val)
    except Exception:
        return False

def activate(key: str) -> bool:
    """Validates key and, if valid, saves it to the registry. Returns success."""
    if not validate(key):
        return False
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_PATH) as reg:
            winreg.SetValueEx(reg, _REG_VALUE, 0, winreg.REG_SZ, key.upper())
        return True
    except Exception:
        return False


# ── Activation window ─────────────────────────────────────────────────────────
class ActivationWindow:
    C = dict(bg="#0f0f1a", panel="#1a1a2e", header="#1e3a5f",
             green="#00c853", orange="#ff6d00", red="#d50000",
             text="#e8eaf6", dim="#546e7a", info="#69f0ae", warn="#ffd740")

    def __init__(self, master: tk.Tk):
        self.activated = False
        self.win = tk.Toplevel(master)
        self.win.title("Ableton Bounce Automator — Activation")
        self.win.geometry("500x300")
        self.win.resizable(False, False)
        self.win.configure(bg=self.C["bg"])
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        self.win.lift()
        self.win.focus_force()

    def _build(self):
        C = self.C

        # Header
        hdr = tk.Frame(self.win, bg=C["header"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  Ableton Bounce Automator", bg=C["header"],
                 fg="white", font=("Segoe UI", 14, "bold")).pack(side="left", padx=16)
        tk.Label(hdr, text="v2.0", bg=C["header"], fg=C["dim"],
                 font=("Segoe UI", 9)).pack(side="right", padx=12)

        # Body
        body = tk.Frame(self.win, bg=C["bg"], padx=36, pady=22)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Enter your license key:", bg=C["bg"],
                 fg=C["text"], font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(body, text="Format:  XXXX-XXXX-XXXX-XXXX", bg=C["bg"],
                 fg=C["dim"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 12))

        self.key_var = tk.StringVar()
        self._entry = tk.Entry(
            body, textvariable=self.key_var,
            bg=C["panel"], fg=C["info"],
            font=("Consolas", 15), relief="flat", bd=10,
            insertbackground=C["info"], width=22, justify="center",
        )
        self._entry.pack(fill="x")
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda _: self._on_activate())

        # Auto-format while typing
        self._trace_id = self.key_var.trace_add("write", self._format_key)

        self.status_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.status_var, bg=C["bg"],
                 font=("Segoe UI", 9), fg=C["warn"]).pack(pady=(10, 0))

        # Buttons
        bf = tk.Frame(body, bg=C["bg"])
        bf.pack(pady=(12, 0))
        tk.Button(bf, text="  Activate", command=self._on_activate,
                  bg=C["green"], fg="#080808", font=("Segoe UI", 11, "bold"),
                  width=13, relief="flat", cursor="hand2", pady=6).pack(side="left", padx=6)
        tk.Button(bf, text="  Exit", command=self._on_close,
                  bg=C["red"], fg="white", font=("Segoe UI", 11, "bold"),
                  width=13, relief="flat", cursor="hand2", pady=6).pack(side="left", padx=6)

    def _format_key(self, *_):
        """Auto-formats input as XXXX-XXXX-XXXX-XXXX while typing."""
        raw = "".join(c for c in self.key_var.get().upper() if c.isalnum())[:16]
        parts = [raw[i:i+4] for i in range(0, len(raw), 4)]
        formatted = "-".join(parts)
        # Detach trace to avoid recursion
        self.key_var.trace_remove("write", self._trace_id)
        cursor = self._entry.index(tk.INSERT)
        self.key_var.set(formatted)
        self._entry.icursor(min(cursor, len(formatted)))
        self._trace_id = self.key_var.trace_add("write", self._format_key)

    def _on_activate(self):
        key = self.key_var.get().strip()
        if activate(key):
            self.activated = True
            self.status_var.set("✓  License activated successfully!")
            self.win.after(1200, self.win.destroy)
        else:
            self.status_var.set("✗  Invalid key — please check and try again.")

    def _on_close(self):
        self.win.destroy()
