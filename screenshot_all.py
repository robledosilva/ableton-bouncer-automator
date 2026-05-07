"""
screenshot_all.py - captura todos os monitores e salva cada um separado
"""
from PIL import ImageGrab, Image
import sys, os

# Captura area total de todos os monitores
img = ImageGrab.grab(all_screens=True)
w, h = img.size
print(f"Total: {w}x{h}")

# Salva tela inteira comprimida
quality = int(sys.argv[1]) if len(sys.argv) > 1 else 55
# Reduz 50% se muito grande
if w > 3000:
    img2 = img.resize((w//2, h//2), Image.LANCZOS)
else:
    img2 = img
img2.save(r"D:\ss_all.jpg", "JPEG", quality=quality, optimize=True)
sz = os.path.getsize(r"D:\ss_all.jpg")//1024
print(f"Salvo: D:\\ss_all.jpg  ({img2.size[0]}x{img2.size[1]})  {sz} KB")

# Salva segunda tela separada (x >= 1920)
if w > 1920:
    mon2 = img.crop((1920, 0, w, h))
    mon2.save(r"D:\ss_mon2.jpg", "JPEG", quality=quality, optimize=True)
    sz2 = os.path.getsize(r"D:\ss_mon2.jpg")//1024
    print(f"Monitor 2: D:\\ss_mon2.jpg  ({mon2.size[0]}x{mon2.size[1]})  {sz2} KB")
