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
