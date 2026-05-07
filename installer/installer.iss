; ============================================================
;  Ableton Bounce Automator — Inno Setup 6 installer script
;  Author : Robledo Silva <robledosilva@gmail.com>
; ============================================================

#define AppName      "Ableton Bounce Automator"
#define AppVersion   "2.0"
#define AppPublisher "Robledo Silva"
#define AppURL       "https://github.com/robledosilva/ableton-bouncer-automator"
#define AppExe       "AbletonBounceAutomator.exe"

; build_installer.bat copies the cx_Freeze output here before running ISCC
#define DistDir      "dist"
#define AssetsDir    "assets"

; ── Setup metadata ────────────────────────────────────────────────────────────
[Setup]
AppId={{F3A7C2D1-88BE-4E9F-B051-1234ABCD5678}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
OutputDir=output
OutputBaseFilename=AbletonBounceAutomator_Setup_v{#AppVersion}
SetupIconFile=..\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
CloseApplications=yes
CloseApplicationsFilter=*.exe

; ── Languages ─────────────────────────────────────────────────────────────────
[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

; ── Optional tasks ───────────────────────────────────────────────────────────
[Tasks]
Name: desktopicon; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional icons:"

; ── Files ─────────────────────────────────────────────────────────────────────
[Files]
; Main app (entire cx_Freeze build output)
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Licenses
Source: "..\LICENSE.txt";                    DestDir: "{app}"; Flags: ignoreversion
Source: "{#AssetsDir}\LICENSE_AbletonMCP.txt"; DestDir: "{app}"; Flags: ignoreversion

; AbletonMCP Remote Script (bundled — MIT license)
Source: "{#AssetsDir}\ableton_mcp_init.py";  DestDir: "{tmp}"; Flags: dontcopy noencryption

; ── Shortcuts ─────────────────────────────────────────────────────────────────
[Icons]
Name: "{group}\{#AppName}";                      Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}";            Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";                Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon

; ── Pascal code ───────────────────────────────────────────────────────────────
[Code]

var
  AbletonRemoteScriptsDir : String;
  MCPAlreadyExists        : Boolean;
  InfoPage                : TOutputMsgWizardPage;

// ── Find Ableton's User Remote Scripts folder ─────────────────────────────
function FindAbletonRemoteScriptsDir(): String;
var
  Base     : String;
  FindRec  : TFindRec;
  Best     : String;
begin
  Result := '';
  Best   := '';
  Base   := ExpandConstant('{%APPDATA}\Ableton\');

  if FindFirst(Base + 'Live *', FindRec) then
  begin
    repeat
      if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) then
        if CompareStr(FindRec.Name, Best) > 0 then
          Best := FindRec.Name;
    until not FindNext(FindRec);
    FindClose(FindRec);
  end;

  if Best <> '' then
    Result := Base + Best + '\Preferences\User Remote Scripts';
end;

// ── Check if Ableton Live is running ─────────────────────────────────────
function AbletonIsRunning(): Boolean;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\cmd.exe'),
       '/c tasklist /FI "IMAGENAME eq Ableton*" 2>nul | find /i "Ableton" >nul',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := (ResultCode = 0);
end;

// ── Install AbletonMCP files ──────────────────────────────────────────────
procedure InstallAbletonMCP();
var
  MCPDir : String;
begin
  MCPDir := AbletonRemoteScriptsDir + '\AbletonMCP';

  if not ForceDirectories(MCPDir) then
  begin
    MsgBox(
      'Could not create folder:' + #13#10 + MCPDir + #13#10#13#10 +
      'AbletonMCP was NOT installed.' + #13#10 +
      'Please install it manually (see README).',
      mbError, MB_OK);
    Exit;
  end;

  ExtractTemporaryFile('ableton_mcp_init.py');
  if not FileCopy(ExpandConstant('{tmp}\ableton_mcp_init.py'),
                  MCPDir + '\__init__.py', False) then
    MsgBox('Warning: could not copy AbletonMCP script to:' + #13#10 + MCPDir,
           mbError, MB_OK);
end;

// ── Remove AbletonMCP on uninstall ────────────────────────────────────────
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  MCPDir : String;
begin
  if CurUninstallStep = usUninstall then
  begin
    MCPDir := FindAbletonRemoteScriptsDir() + '\AbletonMCP';
    if DirExists(MCPDir) then
    begin
      if MsgBox(
        'Remove AbletonMCP from Ableton Live?' + #13#10 +
        '(Recommended unless you use it with other tools)',
        mbConfirmation, MB_YESNO) = IDYES then
          DelTree(MCPDir, True, True, True);
    end;
  end;
end;

// ── Wizard initialisation ─────────────────────────────────────────────────
procedure InitializeWizard();
var
  MCPStatus : String;
begin
  AbletonRemoteScriptsDir := FindAbletonRemoteScriptsDir();
  MCPAlreadyExists := FileExists(AbletonRemoteScriptsDir + '\AbletonMCP\__init__.py');

  if AbletonRemoteScriptsDir = '' then
    MCPStatus :=
      '  Ableton Live not found on this machine.' + #13#10 +
      '  AbletonMCP will NOT be installed automatically.' + #13#10 +
      '  Install it manually after installing Ableton Live.'
  else if MCPAlreadyExists then
    MCPStatus :=
      '  AbletonMCP is already installed — it will be updated.' + #13#10 +
      '  Folder: ' + AbletonRemoteScriptsDir + '\AbletonMCP'
  else
    MCPStatus :=
      '  Will be installed to:' + #13#10 +
      '  ' + AbletonRemoteScriptsDir + '\AbletonMCP';

  InfoPage := CreateOutputMsgPage(
    wpSelectTasks,
    'AbletonMCP Remote Script',
    'Required for communication with Ableton Live',
    'AbletonMCP opens a local socket that lets this app control Ableton.' + #13#10 +
    'It will be installed automatically alongside this app.' + #13#10#13#10 +
    MCPStatus + #13#10#13#10 +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' + #13#10 +
    'After installation, ONE manual step is needed in Ableton:' + #13#10#13#10 +
    '  1. Open Ableton Live' + #13#10 +
    '  2. Settings  →  Link, Tempo & MIDI' + #13#10 +
    '  3. Control Surface  →  select  AbletonMCP' + #13#10 +
    '  4. Input & Output  →  None' + #13#10 +
    '  5. Close Settings — done!' + #13#10#13#10 +
    'This only needs to be done once per Ableton installation.'
  );
end;

// ── Pre-install checks ────────────────────────────────────────────────────
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if AbletonIsRunning() then
  begin
    if MsgBox(
      'Ableton Live appears to be running.' + #13#10#13#10 +
      'Please close it before continuing so AbletonMCP' + #13#10 +
      'can be installed correctly.' + #13#10#13#10 +
      'Click OK once you have closed Ableton Live.',
      mbInformation, MB_OKCANCEL) = IDCANCEL then
        Result := 'Installation cancelled by user.';
  end;
end;

// ── Run AbletonMCP install during main install step ───────────────────────
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    if AbletonRemoteScriptsDir <> '' then
      InstallAbletonMCP();
  end;
end;
