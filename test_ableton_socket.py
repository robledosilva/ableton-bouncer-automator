import socket, json

def send_raw(payload):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("localhost", 9877))
    s.sendall(payload.encode())
    data = b""
    while True:
        chunk = s.recv(4096)
        if not chunk: break
        data += chunk
        try: json.loads(data.decode()); break
        except: continue
    s.close()
    return data.decode()

# Testa formatos diferentes
tests = [
    '{"command": "get_session_info"}\n',
    '{"type": "get_session_info"}\n',
    '{"action": "get_session_info"}\n',
    '{"method": "get_session_info"}\n',
    '{"name": "get_session_info"}\n',
]

for t in tests:
    try:
        r = send_raw(t)
        print(f"FORMAT: {t.strip()}")
        print(f"RESP:   {r[:200]}")
        print()
    except Exception as e:
        print(f"FORMAT: {t.strip()} -> ERRO: {e}")
