[Setup]
AppId={#ExecutableName}
AppName={#AppName}
AppVersion={#AppVersion}
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#ExecutableName}.exe
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#ExecutableName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename={#InstallerBaseName}_v{#AppVersion}
SetupIconFile=..\assets\visualizer_icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableFinishedPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Desktop shortcuts:"

[Files]
; Main executable
Source: "..\dist\{#ExecutableName}.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExecutableName}.exe"; IconFilename: "{app}\{#ExecutableName}.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop shortcuts
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExecutableName}.exe"; Tasks: desktopicon; IconFilename: "{app}\{#ExecutableName}.exe"

[Registry]
; File associations for .pcd files
Root: HKCR; Subkey: ".pcd"; ValueType: string; ValueName: ""; ValueData: "PCDFileVisualizer"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "PCDFileVisualizer"; ValueType: string; ValueName: ""; ValueData: "Point Cloud Data File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "PCDFileVisualizer\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#ExecutableName}.exe,0"
Root: HKCR; Subkey: "PCDFileVisualizer\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#ExecutableName}.exe"" ""%1"""

; File associations for .ply files
Root: HKCR; Subkey: ".ply"; ValueType: string; ValueName: ""; ValueData: "PLYFileVisualizer"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "PLYFileVisualizer"; ValueType: string; ValueName: ""; ValueData: "Polygon File Format"; Flags: uninsdeletekey
Root: HKCR; Subkey: "PLYFileVisualizer\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#ExecutableName}.exe,0"
Root: HKCR; Subkey: "PLYFileVisualizer\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#ExecutableName}.exe"" ""%1"""

[Run]
Filename: "{app}\{#ExecutableName}.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then begin
    MsgBox('{#AppName} requires a 64-bit version of Windows.', mbError, MB_OK);
    Result := False;
  end;
end;