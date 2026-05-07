import tkinter as tk
import os

PAUSE_FLAG = r"D:\claude_PAUSE.flag"
STOP_FLAG  = r"D:\claude_STOP.flag"

# Limpa flags anteriores ao iniciar
for f in [PAUSE_FLAG, STOP_FLAG]:
    if os.path.exists(f): os.remove(f)

paused = False

def toggle_pause():
    global paused
    paused = not paused
    if paused:
        open(PAUSE_FLAG, "w").close()
        btn_pause.config(text="▶  Retomar", bg="#4CAF50")
        status_var.set("⏸  Pausado — Claude aguardando")
    else:
        if os.path.exists(PAUSE_FLAG): os.remove(PAUSE_FLAG)
        btn_pause.config(text="⏸  Pausar", bg="#FF9800")
        status_var.set("▶  Rodando...")

def stop_process():
    open(STOP_FLAG, "w").close()
    if os.path.exists(PAUSE_FLAG): os.remove(PAUSE_FLAG)
    btn_pause.config(state="disabled")
    btn_stop.config(state="disabled")
    status_var.set("⛔  Processo interrompido")

root = tk.Tk()
root.title("Claude Workflow Control")
root.geometry("320x160")
root.resizable(False, False)
root.configure(bg="#1e1e1e")
root.attributes("-topmost", True)

status_var = tk.StringVar(value="▶  Rodando...")
lbl = tk.Label(root, textvariable=status_var, bg="#1e1e1e", fg="white",
               font=("Segoe UI", 11), pady=10)
lbl.pack()

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=10)

btn_pause = tk.Button(frame, text="⏸  Pausar", command=toggle_pause,
                      bg="#FF9800", fg="white", font=("Segoe UI", 12, "bold"),
                      width=12, relief="flat", cursor="hand2")
btn_pause.grid(row=0, column=0, padx=10)

btn_stop = tk.Button(frame, text="⏹  Parar", command=stop_process,
                     bg="#f44336", fg="white", font=("Segoe UI", 12, "bold"),
                     width=12, relief="flat", cursor="hand2")
btn_stop.grid(row=0, column=1, padx=10)

lbl2 = tk.Label(root, text="flags em D:\\  •  sempre no topo",
                bg="#1e1e1e", fg="#666", font=("Segoe UI", 8))
lbl2.pack(pady=4)

root.mainloop()
