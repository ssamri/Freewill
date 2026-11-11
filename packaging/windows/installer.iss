; Inno Setup recipe for the Freewill installer.
; Build with: iscc /DAppVersion=0.1.0 packaging\windows\installer.iss
; after PyInstaller has produced dist\Freewill.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{7B0C3F0E-5F1D-4E7B-9C56-2A9E4D6F1B38}
AppName=Freewill (experimental)
AppVersion={#AppVersion}
AppPublisher=Samri Anass
AppPublisherURL=https://github.com/ssamri/Freewill
DefaultDirName={autopf}\Freewill
DefaultGroupName=Freewill
DisableProgramGroupPage=yes
; Installs for the current user: no administrator rights are asked for.
PrivilegesRequired=lowest
LicenseFile=..\..\LICENSE
SetupIconFile=freewill.ico
UninstallDisplayIcon={app}\Freewill.exe
OutputDir=..\..\dist
OutputBaseFilename=Freewill-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\Freewill\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Freewill"; Filename: "{app}\Freewill.exe"
Name: "{autodesktop}\Freewill"; Filename: "{app}\Freewill.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Freewill.exe"; Description: "{cm:LaunchProgram,Freewill}"; Flags: nowait postinstall skipifsilent

; Life files live in %APPDATA%\Freewill and are deliberately left in place on uninstall.
