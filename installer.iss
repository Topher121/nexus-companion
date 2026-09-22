#ifndef AppVersion
  #define AppVersion "0.9.0"
#endif
[Setup]
AppId={{CF671286-84ED-4974-B7B4-C10E768F739A}
AppName=Nexus Forge
AppVersion={#AppVersion}
AppPublisher=Pocket Forge Studios
AppPublisherURL=https://github.com/Topher121/nexus-companion
DefaultDirName={localappdata}\Programs\Nexus Forge
DefaultGroupName=Nexus Forge
; Keep AppId and the executable name for seamless upgrades from Nexus Companion.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.18362
DisableProgramGroupPage=yes
#ifdef TestBuild
OutputDir=build\installer-validation
OutputBaseFilename=NexusForge-Validation-Setup
#else
OutputDir=releases
OutputBaseFilename=NexusForge-Setup-{#AppVersion}
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
Name: "{group}\Nexus Forge"; Filename: "{app}\NexusCompanion.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Nexus Forge"; Filename: "{app}\NexusCompanion.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\NexusCompanion.exe"; Description: "Launch Nexus Forge"; Flags: nowait postinstall skipifsilent unchecked

; Personal data lives in a separate folder and is deliberately preserved on uninstall.

[Code]
procedure RemoveLegacyShortcut(const Filename: String);
var
  Shell, Link: Variant;
begin
  if not FileExists(Filename) then exit;
  try
    Shell := CreateOleObject('WScript.Shell');
    Link := Shell.CreateShortcut(Filename);
    { Only replace our installed shortcut; leave source/custom launchers alone. }
    if CompareText(Link.TargetPath, ExpandConstant('{app}\NexusCompanion.exe')) = 0 then
      DeleteFile(Filename);
  except
    Log('Could not inspect legacy shortcut; left it unchanged: ' + Filename);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RemoveLegacyShortcut(ExpandConstant('{group}\Nexus Companion.lnk'));
    if WizardIsTaskSelected('desktopicon') then
      RemoveLegacyShortcut(ExpandConstant('{userdesktop}\Nexus Companion.lnk'));
  end;
end;
