# 🎛️ Ableton Bounce Automator

Batch bounce automator for **Ableton Live** on Windows.  
Opens each `.als` project from a folder, configures the export dialog and saves the result as **MP3** — no manual intervention required.

---

## ✨ Features

- **Automatic batch export** — processes all `.als` projects in a folder and subfolders
- **Skips already-exported projects** — detects if the MP3 already exists and moves on
- **Automatic duration detection** — reads the actual project length directly from the `.als` file (compressed XML)
- **Dialog configuration via UI automation** — disables WAV, enables MP3, sets the Render Length
- **Smart retry** — if an unexpected dialog appears (e.g. missing samples), dismisses it and retries up to 15 times
- **Crash watchdog** — monitors if Ableton freezes (`Not Responding`) and automatically restarts the process
- **Crash retry** — reopens the project after a crash; if it freezes twice in a row, skips to the next one
- **GUI with real-time log** — follow each step, pause or stop at any time
- **AbletonMCP communication** — validates the project is fully loaded before exporting (socket on port `9877`)

---

## 🖥️ Requirements

- Windows 10 or 11
- **Ableton Live** (any edition) with **AbletonMCP** installed and active
- **Python 3.10+**
- Python dependencies:

```
pywin32
pyautogui
Pillow
```

---

## ⚙️ Installation

**1. Clone the repository**

```bash
git clone https://github.com/robledosilva/ableton-bouncer-automator.git
cd ableton-bouncer-automator
```

**2. Install dependencies**

```bash
pip install pywin32 pyautogui Pillow
```

**3. Make sure AbletonMCP is running**

The script communicates with Ableton via socket on port `9877`.  
AbletonMCP must be installed as a Remote Script in Ableton Live and active in the current session.

---

## 🚀 How to use

**1. Open Ableton Live** (no project needs to be open)

**2. Run the script**

```bash
python ableton_bouncer.py
```

**3. In the interface:**
- Click **Browse** and select the root folder containing your Ableton projects
- Click **Start**
- Follow the real-time log
- Use **Pause / Resume** for manual control
- Use **Stop** to interrupt the process

**4. MP3 files are saved inside each project folder**, named as:
```
FolderName - FileName.als.mp3
```

---

## 📁 Expected folder structure

The script picks the most recently modified `.als` file from each subfolder:

```
Projects/
├── Project Alpha/
│   └── Project Alpha.als       → Projects/Project Alpha/Project Alpha - Project Alpha.mp3
├── Another Beat/
│   └── Another Beat v2.als     → Projects/Another Beat/Another Beat - Another Beat v2.mp3
└── ...
```

Folders containing `backup` in their name are automatically ignored.

---

## 🛠️ Utility files

| File | Description |
|---|---|
| `ableton_bouncer.py` | Main script |
| `claude_control.py` | Mini panel to pause/stop the process externally via flag files |
| `inspect_dlg.py` | Inspects handles and titles of open windows |
| `list_windows.py` | Lists all visible system windows |
| `screenshot_helper.py` | Captures screenshots of specific windows |
| `screenshot.py` / `screenshot_all.py` | Visual debug utilities |
| `test_ableton_socket.py` | Tests the connection with AbletonMCP |
| `patch.py` | Utility for targeted adjustments |

---

## ⚠️ Notes

- The computer must remain **unlocked** during the process (the automation uses mouse and keyboard)
- Do not move the mouse to the corners of the screen during execution
- Maximum render time per project is **180 seconds** (configurable via `MAX_RENDER_SEC`)
- Projects with undetected duration are also exported (using the maximum limit)

---

## 📬 Contact

Created by **Robledo Silva**  
✉️ [robledosilva@gmail.com](mailto:robledosilva@gmail.com)  
🐙 [github.com/robledosilva](https://github.com/robledosilva)

---
---

# 🎛️ Ableton Bounce Automator

Automatizador de bounce em lote para **Ableton Live** no Windows.  
Abre cada projeto `.als` de uma pasta, configura o diálogo de export e salva o resultado como **MP3** — sem intervenção manual.

---

## ✨ Funcionalidades

- **Batch export automático** — processa todos os projetos `.als` de uma pasta e subpastas
- **Pula projetos já exportados** — detecta se o MP3 já existe e ignora
- **Duração automática** — lê o tempo real do projeto direto do arquivo `.als` (XML comprimido)
- **Configuração do diálogo via UI automation** — desliga WAV, liga MP3, define o Render Length
- **Retry inteligente** — se um diálogo inesperado aparecer (ex: amostras não carregadas), fecha e tenta de novo por até 15 vezes
- **Watchdog de crash** — monitora se o Ableton travou (`Not Responding`) e reinicia automaticamente o processo
- **Retry por crash** — reabre o projeto após um crash; se travar duas vezes seguidas, pula para o próximo
- **GUI com log em tempo real** — acompanhe cada etapa, pause ou pare a qualquer momento
- **Comunicação via AbletonMCP** — valida que o projeto está totalmente carregado antes de exportar (socket na porta `9877`)

---

## 🖥️ Requisitos

- Windows 10 ou 11
- **Ableton Live** (qualquer edição) com o **AbletonMCP** instalado e ativo
- **Python 3.10+**
- Dependências Python:

```
pywin32
pyautogui
Pillow
```

---

## ⚙️ Instalação

**1. Clone o repositório**

```bash
git clone https://github.com/robledosilva/ableton-bouncer-automator.git
cd ableton-bouncer-automator
```

**2. Instale as dependências**

```bash
pip install pywin32 pyautogui Pillow
```

**3. Certifique-se de que o AbletonMCP está rodando**

O script se comunica com o Ableton via socket na porta `9877`.  
O AbletonMCP precisa estar instalado como Remote Script no Ableton Live e ativo na sessão.

---

## 🚀 Como usar

**1. Abra o Ableton Live** (não precisa ter nenhum projeto aberto)

**2. Execute o script**

```bash
python ableton_bouncer.py
```

**3. Na interface:**
- Clique em **Browse** e selecione a pasta raiz com seus projetos Ableton
- Clique em **Iniciar**
- Acompanhe o log em tempo real
- Use **Pausar / Retomar** para controle manual
- Use **Parar** para interromper o processo

**4. Os arquivos MP3 são salvos dentro de cada pasta de projeto**, com o nome:
```
NomeDaPasta - NomeDoArquivo.als.mp3
```

---

## 📁 Estrutura de pastas esperada

O script busca o arquivo `.als` mais recente em cada subpasta:

```
Projetos/
├── Projeto Alpha/
│   └── Projeto Alpha.als       → Projetos/Projeto Alpha/Projeto Alpha - Projeto Alpha.mp3
├── Outro Beat/
│   └── Outro Beat v2.als       → Projetos/Outro Beat/Outro Beat - Outro Beat v2.mp3
└── ...
```

Pastas com `backup` no nome são ignoradas automaticamente.

---

## 🛠️ Arquivos utilitários

| Arquivo | Descrição |
|---|---|
| `ableton_bouncer.py` | Script principal |
| `claude_control.py` | Mini painel para pausar/parar o processo externamente via flags |
| `inspect_dlg.py` | Inspeciona handles e títulos de janelas abertas |
| `list_windows.py` | Lista todas as janelas visíveis do sistema |
| `screenshot_helper.py` | Captura screenshots de janelas específicas |
| `screenshot.py` / `screenshot_all.py` | Utilitários de debug visual |
| `test_ableton_socket.py` | Testa a conexão com o AbletonMCP |
| `patch.py` | Utilitário de ajustes pontuais |

---

## ⚠️ Observações

- O computador precisa estar **desbloqueado** durante o processo (a automação usa mouse e teclado)
- Não mova o mouse para os cantos da tela durante a execução
- O tempo máximo de render por projeto é de **180 segundos** (configurável via `MAX_RENDER_SEC`)
- Projetos com duração não detectada também são exportados (usando o limite máximo)

---

## 📬 Contato

Criado por **Robledo Silva**  
✉️ [robledosilva@gmail.com](mailto:robledosilva@gmail.com)  
🐙 [github.com/robledosilva](https://github.com/robledosilva)
