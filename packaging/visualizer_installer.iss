[Setup]
AppName=PCD Visualizer
AppVersion=1.0
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
Name: "quicklaunchicon"; Description: "Create Quick Launch shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Main executable
Source: "..\dist\PCDVisualizer.exe"; DestDir: "{app}"; Flags: ignoreversion
; Assets (icon)
Source: "..\assets\visualizer_icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\PCD Visualizer"; Filename: "{app}\PCDVisualizer.exe"; IconFilename: "{app}\assets\visualizer_icon.ico"
Name: "{group}\{cm:UninstallProgram,PCD Visualizer}"; Filename: "{uninstallexe}"
; Desktop shortcuts
Name: "{autodesktop}\PCD Visualizer"; Filename: "{app}\PCDVisualizer.exe"; Tasks: desktopicon; IconFilename: "{app}\assets\visualizer_icon.ico"
; Quick Launch
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\PCD Visualizer"; Filename: "{app}\PCDVisualizer.exe"; Tasks: quicklaunchicon; IconFilename: "{app}\assets\visualizer_icon.ico"
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

; Application registration for proper uninstall
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PCDVisualizer"; ValueType: string; ValueName: "DisplayName"; ValueData: "PCD Visualizer"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PCDVisualizer"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "1.0"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PCDVisualizer"; ValueType: string; ValueName: "Publisher"; ValueData: "Quantnueral Pvt. Ltd."
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PCDVisualizer"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PCDVisualizer"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"

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