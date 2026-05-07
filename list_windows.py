import win32gui
wins = []
def cb(h, _):
    if win32gui.IsWindowVisible(h):
        t = win32gui.GetWindowText(h)
        if t: wins.append(t)
win32gui.EnumWindows(cb, None)
for t in sorted(wins):
    print(repr(t))
