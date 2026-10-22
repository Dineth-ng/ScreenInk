#ifndef AppVersion
  #error AppVersion must be supplied by tools/build_installer.py
#endif
[Setup]
AppId={{940AC59A-791E-4D6C-94E9-76303DB5D734}
AppName=ScreenInk
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\ScreenInk
DefaultGroupName=ScreenInk
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
OutputDir=..\release
OutputBaseFilename=ScreenInk-Setup-{#AppVersion}
SetupIconFile=..\screenink\assets\screenink.ico
UninstallDisplayIcon={app}\ScreenInk.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
AppMutex=Local\ScreenInk.Desktop.Running
CloseApplications=no
RestartApplications=no
LicenseFile=..\LICENSE
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "..\dist\ScreenInk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\ScreenInk"; Filename: "{app}\ScreenInk.exe"
Name: "{userdesktop}\ScreenInk"; Filename: "{app}\ScreenInk.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\ScreenInk.exe"; Description: "Launch ScreenInk"; Flags: nowait postinstall skipifsilent
[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var Command: String;
begin
  if CurUninstallStep = usUninstall then begin
    if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'ScreenInk', Command) then
      if Pos(ExpandConstant('{app}\ScreenInk.exe'), Command) > 0 then
        RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'ScreenInk');
  end;
end;
