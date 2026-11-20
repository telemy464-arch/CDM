; ═══════════════════════════════════════════════════════════════════════
; VnA Download Manager v2.0 - Inno Setup Installer Script
; IDM-er Dada, Goriber Bondhu
; Compile with: Inno Setup 6.x  https://jrsoftware.org/isinfo.php
; ═══════════════════════════════════════════════════════════════════════

#define AppName      "VnA Download Manager"
#define AppVersion   "2.0.0"
#define AppPublisher "VnA Software"
#define AppURL       "https://github.com/vna-software/vna-download-manager"
#define AppExeName   "VnA_Download_Manager.exe"
#define ExtPort      "19876"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\VnA Download Manager
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
SourceDir=..
OutputDir=installer\output
OutputBaseFilename=VnA_Download_Manager_v2.0_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
DisableWelcomePage=no
DisableProgramGroupPage=auto
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
ChangesEnvironment=no
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "Create Desktop shortcut";           GroupDescription: "Additional icons:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create Quick Launch shortcut";      GroupDescription: "Additional icons:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startupicon";     Description: "Start with Windows (tray mode)";    GroupDescription: "Startup:"; Flags: unchecked
Name: "chrome_ext";      Description: "Register Chrome Extension (manual load after install)"; GroupDescription: "Browser Integration:";
Name: "firefox_ext";     Description: "Register Firefox Extension (manual load after install)"; GroupDescription: "Browser Integration:";
Name: "assoc_torrent";   Description: "Associate .torrent files with VnA"; GroupDescription: "File Associations:";

[Files]
; Main executable
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

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
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VnADownloadManager"; ValueData: """{app}\{#AppExeName}"" --minimized"; Flags: uninsdeletevalue; Tasks: startupicon

; .torrent file association
Root: HKCU; Subkey: "Software\Classes\.torrent"; ValueType: string; ValueName: ""; ValueData: "VnADownloadManager.torrent"; Flags: uninsdeletekey; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\VnADownloadManager.torrent"; ValueType: string; ValueName: ""; ValueData: "BitTorrent File"; Flags: uninsdeletekey; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\VnADownloadManager.torrent\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\VnADownloadManager.torrent\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_torrent

; magnet: protocol handler
Root: HKCU; Subkey: "Software\Classes\magnet"; ValueType: string; ValueName: ""; ValueData: "URL:Magnet Protocol"; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\magnet"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Tasks: assoc_torrent
Root: HKCU; Subkey: "Software\Classes\magnet\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_torrent

; Product Key & License Registry
Root: HKCU; Subkey: "Software\VnA Download Manager"; Flags: uninsdeletekey

; NativeMessaging host for Chrome (browser extension communication)
Root: HKCU; Subkey: "Software\Google\Chrome\NativeMessagingHosts\com.vna.downloadmanager"; ValueType: string; ValueName: ""; ValueData: "{app}\browser_extension\chrome\native_host.json"; Flags: uninsdeletekey; Tasks: chrome_ext

[Run]
; Launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

; Show extension install instructions
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Browser Extension Setup:`n`nChrome/Edge: 1) Open chrome://extensions  2) Enable Developer Mode  3) Click ""Load unpacked""  4) Select: {app}\browser_extension\chrome`n`nFirefox: 1) Open about:debugging  2) Click ""Load Temporary Add-on""  3) Select manifest.json in {app}\browser_extension\firefox', 'VnA Browser Extension', 0, 64)"""; Flags: nowait postinstall skipifsilent; Description: "Show browser extension setup guide"; Tasks: chrome_ext firefox_ext

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\VnA Download Manager"
Type: filesandordirs; Name: "{app}\*.json"
Type: filesandordirs; Name: "{app}\.trial"
Type: filesandordirs; Name: "{app}\*.key"
Type: filesandordirs; Name: "{app}\*.dat"
Type: filesandordirs; Name: "{app}\*.log"

[Code]
// ═══════════════════════════════════════════════════
// Custom installer code
// ═══════════════════════════════════════════════════

procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Welcome to VnA Download Manager v2.0!'#13#10 +
    '"IDM-er Dada, Goriber Bondhu"'#13#10#13#10 +
    '✅ Multi-connection Super Fast Download'#13#10 +
    '✅ Pause, Resume, Stop anytime'#13#10 +
    '✅ Playlist & YouTube download'#13#10 +
    '✅ Browser Extension (Chrome/Firefox/Edge)'#13#10 +
    '✅ Site Grabber, Torrent, Proxy'#13#10 +
    '✅ Dark / Light / Glass Theme'#13#10 +
    '✅ English / বাংলা / हिंदी UI'#13#10 +
    '✅ 3-Day Free Trial'#13#10#13#10 +
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

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
      UnInstallOldVersion();
  end;
end;
