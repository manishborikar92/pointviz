[Setup]
AppId=PCDVisualizer
AppName=PCD Visualizer
AppVersion=1.0
UninstallDisplayName=PCD Visualizer
UninstallDisplayIcon={app}\PCDVisualizer.exe
AppPublisher=Quantnueral Pvt. Ltd.
DefaultDirName={autopf}\PCDVisualizer
DefaultGroupName=PCD Visualizer
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=PCDVisualizer_Setup_v1.0
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
Source: "..\dist\PCDVisualizer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\PCD Visualizer"; Filename: "{app}\PCDVisualizer.exe"; IconFilename: "{app}\PCDVisualizer.exe"
Name: "{group}\{cm:UninstallProgram,PCD Visualizer}"; Filename: "{uninstallexe}"

; Desktop shortcuts
Name: "{autodesktop}\PCD Visualizer"; Filename: "{app}\PCDVisualizer.exe"; Tasks: desktopicon; IconFilename: "{app}\PCDVisualizer.exe"

[Registry]
; File associations for .pcd files
Root: HKCR; Subkey: ".pcd"; ValueType: string; ValueName: ""; ValueData: "PCDFileVisualizer"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "PCDFileVisualizer"; ValueType: string; ValueName: ""; ValueData: "Point Cloud Data File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "PCDFileVisualizer\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\PCDVisualizer.exe,0"
Root: HKCR; Subkey: "PCDFileVisualizer\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PCDVisualizer.exe"" ""%1"""

; File associations for .ply files
Root: HKCR; Subkey: ".ply"; ValueType: string; ValueName: ""; ValueData: "PLYFileVisualizer"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "PLYFileVisualizer"; ValueType: string; ValueName: ""; ValueData: "Polygon File Format"; Flags: uninsdeletekey
Root: HKCR; Subkey: "PLYFileVisualizer\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\PCDVisualizer.exe,0"
Root: HKCR; Subkey: "PLYFileVisualizer\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PCDVisualizer.exe"" ""%1"""

[Run]
Filename: "{app}\PCDVisualizer.exe"; Description: "{cm:LaunchProgram,PCD Visualizer}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then begin
    MsgBox('PCD Visualizer requires a 64-bit version of Windows.', mbError, MB_OK);
    Result := False;
  end;
end;