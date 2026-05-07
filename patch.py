
lines = open('D:/ableton_bouncer.py', encoding='utf-8').readlines()

# Linhas 249-253 (indices 248-252):
# 249: '    # Tab x7 -> WAV (Encode PCM) -> garante OFF\n',
# 250: '    for _ in range(7): pyautogui.press("tab"); time.sleep(0.08)\n',  <- DUPLICADO
# 251: '    # Verifica WAV e MP3 com UM screenshot antes dos tabs\n',
# 252: '    # Tab x7 -> WAV (Encode PCM)\n',
# 253: '    for _ in range(7): pyautogui.press("tab"); time.sleep(0.08)\n',  <- o correto

# Remove linhas 249-252 (indices 248-251), mantendo apenas a linha 253
for i, l in enumerate(lines):
    print(f'{i+1}: {l.rstrip()}') if 247 <= i <= 254 else None

print()
# Remove o bloco duplicado: linhas 249-252 (indices 248-251)
del lines[248:252]

open('D:/ableton_bouncer.py', 'w', encoding='utf-8').writelines(lines)
print(f'OK - {len(lines)} linhas')

import ast
try:
    ast.parse(open('D:/ableton_bouncer.py', encoding='utf-8').read())
    print('Sintaxe OK')
except SyntaxError as e:
    print(f'ERRO linha {e.lineno}: {e.msg}')
