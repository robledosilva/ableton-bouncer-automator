"""
Utilitario: captura janela especifica e salva como JPEG pequeno.
Uso: python screenshot_helper.py "Export Audio"
     python screenshot_helper.py "Ableton"
"""
import sys, win32gui
from PIL import ImageGrab

def capture_window(title_part, out="D:/dlg_preview.jpg", quality=55):
    found = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and title_part.lower() in t.lower():
            found.append((h, t))
    win32gui.EnumWindows(cb, None)

    if not found:
        print(f"Nenhuma janela com '{title_part}'")
        return None

    hwnd, title = found[0]
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    print(f"Capturando: '{title}' [{l},{t},{r},{b}]")

    img = ImageGrab.grab(bbox=(l, t, r, b))
    # Reduz para 60% do tamanho original
    w, h = img.size
    img = img.resize((int(w*0.6), int(h*0.6)))
    img.save(out, "JPEG", quality=quality)

    import os
    size_kb = os.path.getsize(out) // 1024
    print(f"Salvo: {out} ({size_kb} KB)")
    return out

if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else "Ableton"
    capture_window(title)
