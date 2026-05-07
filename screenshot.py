"""
screenshot.py  —  tira screenshot, comprime pra JPEG e salva em D:\ss.jpg
uso: python screenshot.py [qualidade 1-95]  (default 60)
"""
import sys, time
from PIL import ImageGrab, Image

quality = int(sys.argv[1]) if len(sys.argv) > 1 else 60
time.sleep(0.3)  # pequena pausa pro caller sair da frente

img = ImageGrab.grab(all_screens=False)   # monitor principal
w, h = img.size
# reduz pra 50% se resolucao for muito grande (ex: 4K)
if w > 2560:
    img = img.resize((w//2, h//2), Image.LANCZOS)

out = r"D:\ss.jpg"
img.save(out, "JPEG", quality=quality, optimize=True)

import os
size_kb = os.path.getsize(out) // 1024
print(f"Salvo: {out}  ({img.size[0]}x{img.size[1]})  {size_kb} KB  qualidade={quality}")
