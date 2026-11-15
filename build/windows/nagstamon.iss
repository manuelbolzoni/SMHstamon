[Setup]
AppName=SMHstamon
AppVerName=SMHstamon {#version}
DefaultDirName={autopf}\SMHstamon
DefaultGroupName=SMHstamon
AlwaysUsePersonalGroup=false
ShowLanguageDialog=no
SetupIconFile={#resources}\smhstamon.ico
UsePreviousGroup=false
OutputBaseFilename=SMHstamon-{#version}-win{#arch}_setup
UninstallDisplayIcon={app}\resources\smhstamon.ico
UsePreviousAppDir=false
AppID={{44F7CFFB-4776-4DA4-9930-A07178069517}
UninstallRestartComputer=false
VersionInfoVersion={#version_is}
VersionInfoCopyright=Manuel Bolzoni
VersionInfoProductName=SMHstamon
VersionInfoProductVersion={#version_is}
InternalCompressLevel=max
Compression=lzma
SolidCompression=true
SourceDir={#source}
ArchitecturesAllowed={#archs_allowed}
ArchitecturesInstallIn64BitMode=x64
CloseApplications=no
[Icons]
Name: {group}\SMHstamon; Filename: {app}\SMHstamon.exe; WorkingDir: {app}; IconFilename: {app}\resources\smhstamon.ico; IconIndex: 0
Name: {commonstartup}\SMHstamon; Filename: {app}\SMHstamon.exe; WorkingDir: {app}; IconFilename: {app}\resources\smhstamon.ico; IconIndex: 0
[Files]
Source: "*"; DestDir: {app}; Flags: recursesubdirs createallsubdirs ignoreversion; BeforeInstall: KillRunningNagstamon()
[Tasks]
Name: RunAfterInstall; Description: Run SMHstamon after installation
[Run]
Filename: {app}\SMHstamon.exe; Flags: shellexec skipifsilent nowait; Tasks: RunAfterInstall
[Code]
procedure KillRunningNagstamon();
var
  ReturnCode: Integer;
begin
    Exec(ExpandConstant('taskkill.exe'), '/f /t /im SMHstamon.exe', '', SW_HIDE, ewWaitUntilTerminated, ReturnCode);
end;
