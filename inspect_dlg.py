import win32gui

def cb(h, _):
    if not win32gui.IsWindowVisible(h): return
    t = win32gui.GetWindowText(h)
    if 'Export' in t or 'Ableton' in t:
        r = win32gui.GetWindowRect(h)
        print(f'hwnd={h} title="{t}" rect={r}')
        children = []
        def cb2(ch, _):
            ct = win32gui.GetWindowText(ch)
            cc = win32gui.GetClassName(ch)
            children.append((ch, cc, ct))
        try: win32gui.EnumChildWindows(h, cb2, None)
        except: pass
        for ch, cc, ct in children:
            print(f'  child class={cc} text="{ct}"')

win32gui.EnumWindows(cb, None)
