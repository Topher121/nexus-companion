#ifndef AppVersion
  #define AppVersion "0.8.0"
#endif
[Setup]
AppId={{CF671286-84ED-4974-B7B4-C10E768F739A}
AppName=Nexus Companion
AppVersion={#AppVersion}
AppPublisher=Nexus Companion
AppPublisherURL=https://github.com/Topher121/nexus-companion
DefaultDirName={localappdata}\Programs\Nexus Companion
DefaultGroupName=Nexus Companion
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.18362
DisableProgramGroupPage=yes
#ifdef TestBuild
OutputDir=..\work\installer-validation
OutputBaseFilename=NexusCompanion-Validation-Setup
#else
OutputDir=releases
OutputBaseFilename=NexusCompanion-Setup-{#AppVersion}
#endif
SetupIconFile=assets\ui\nexus.ico
UninstallDisplayIcon={app}\NexusCompanion.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
AppMutex=NexusCompanionApp
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\NexusCompanion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Nexus Companion"; Filename: "{app}\NexusCompanion.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Nexus Companion"; Filename: "{app}\NexusCompanion.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\NexusCompanion.exe"; Description: "Launch Nexus Companion"; Flags: nowait postinstall skipifsilent unchecked

; Personal data lives in a separate folder and is deliberately preserved on uninstall.
