; ═══════════════════════════════════════════════════════════════════════
; CDM - Cloud Download Manager v2.0
; Official Inno Setup Installer Script
; ═══════════════════════════════════════════════════════════════════════

#define AppName      "CDM - Cloud Download Manager"
#define AppVersion   "2.3.8"
#define AppPublisher "CDM Technology"
#define AppURL       "https://github.com/telemy464-arch/CDM"
#define AppExeName   "CDM.exe"
#define ExtPort      "19876"

[Setup]
AppId={{C1D2E3F4-A5B6-7890-CDEF-1234567890AB}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\CDM
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
SourceDir=..
OutputDir=installer\output
OutputBaseFilename=CDM_Setup_v2.3.8
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
DisableProgramGroupPage=auto
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
ChangesEnvironment=no
CloseApplications=force
CloseApplicationsFilter=*.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "Create Desktop shortcut";           GroupDescription: "Additional icons:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create Quick Launch shortcut";      GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startupicon";     Description: "Start with Windows (tray mode)";    GroupDescription: "Startup:"; Flags: unchecked
Name: "chrome_ext";      Description: "Register Chrome Extension";         GroupDescription: "Browser Integration:";
Name: "firefox_ext";     Description: "Register Firefox Extension";        GroupDescription: "Browser Integration:";
Name: "assoc_torrent";   Description: "Associate .torrent files with CDM"; GroupDescription: "File Associations:";

[Files]
; Main executable
Source: "dist\CDM_2.3.8.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion

; Browser extension
Source: "browser_extension\chrome\*"; DestDir: "{app}\browser_extension\chrome"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "browser_extension\firefox\*"; DestDir: "{app}\browser_extension\firefox"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets & sounds
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\assets'))
Source: "sounds\*"; DestDir: "{app}\sounds"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\sounds'))

; Default settings
Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Registry]
; Startup
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "CDM"; ValueData: """{app}\{#AppExeName}"" --minimized"; Flags: uninsdeletevalue; Tasks: startupicon

; .torrent file association
Root: HKCU; Subkey: "Software\Classes\.torrent"; ValueType: string; ValueName: ""; ValueData: "CDM.torrent"; Flags: uninsdeletekey; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\CDM.torrent"; ValueType: string; ValueName: ""; ValueData: "BitTorrent File"; Flags: uninsdeletekey; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\CDM.torrent\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\CDM.torrent\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_torrent

; magnet: protocol handler
Root: HKCU; Subkey: "Software\Classes\magnet"; ValueType: string; ValueName: ""; ValueData: "URL:Magnet Protocol"; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\magnet"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\magnet\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_torrent

; cdm: protocol handler for browser extension launch
Root: HKCU; Subkey: "Software\Classes\cdm"; ValueType: string; ValueName: ""; ValueData: "URL:CDM Protocol"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\cdm"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCU; Subkey: "Software\Classes\cdm\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""

; Product Key & License Registry
Root: HKCU; Subkey: "Software\CDM"; Flags: uninsdeletekey

; Auto-start on Windows boot (minimized to background like IDM)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "CDM"; ValueData: """{app}\{#AppExeName}"" --minimized"; Flags: uninsdeletevalue

; Chrome Extension
Root: HKCU; Subkey: "Software\Google\Chrome\Extensions\cdm_download_manager"; ValueType: string; ValueName: "path"; ValueData: "{app}\browser_extension\chrome"; Flags: uninsdeletekey; Tasks: chrome_ext

; Brave Extension
Root: HKCU; Subkey: "Software\BraveSoftware\Brave-Browser\Extensions\cdm_download_manager"; ValueType: string; ValueName: "path"; ValueData: "{app}\browser_extension\chrome"; Flags: uninsdeletekey; Tasks: chrome_ext

; Edge Extension
Root: HKCU; Subkey: "Software\Microsoft\Edge\Extensions\cdm_download_manager"; ValueType: string; ValueName: "path"; ValueData: "{app}\browser_extension\chrome"; Flags: uninsdeletekey; Tasks: chrome_ext

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\CDM"
Type: filesandordirs; Name: "{app}\*.json"
Type: filesandordirs; Name: "{app}\.trial"
Type: filesandordirs; Name: "{app}\*.key"
Type: filesandordirs; Name: "{app}\*.dat"
Type: filesandordirs; Name: "{app}\*.log"

[Code]
function InitializeSetup(): Boolean;
var
  iResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM CDM.exe /T', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  Exec('taskkill.exe', '/F /IM CDM.exe /T', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  Sleep(500);
  Result := True;
end;

procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Welcome to CDM - Cloud Download Manager v2.2!'#13#10 +
    '"Smart Cloud Downloader with Multi-Connection Speed"'#13#10#13#10 +
    '✅ Multi-connection Super Fast Download'#13#10 +
    '✅ Pause, Resume, Stop anytime'#13#10 +
    '✅ Video & Media Grabber'#13#10 +
    '✅ Browser Extension (Chrome/Firefox/Edge)'#13#10 +
    '✅ Site Grabber, Torrent, Proxy'#13#10 +
    '✅ Microsoft-style Product Key activation'#13#10#13#10 +
    'Click Next to continue...';
end;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','',
            SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure KillRunningApp();
var
  iResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM CDM.exe /T', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  Sleep(500);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    KillRunningApp();
  end;
end;
