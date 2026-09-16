#define MyAppName "Task Manager"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Dionis6059"
#define MyAppExeName "TaskManager.exe"

[Setup]
AppId={{A3E0CB8E-DF8A-4E2D-A925-6E7D35146C92}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\TaskManager
DefaultGroupName=Task Manager

DisableProgramGroupPage=yes
PrivilegesRequired=lowest

OutputDir=installer
OutputBaseFilename=TaskManager-Setup-1.0.1

Compression=lzma
SolidCompression=yes

WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

UninstallDisplayName={#MyAppName}

[Files]
Source: "dist\TaskManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Task Manager"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Task Manager"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные параметры:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить Task Manager"; Flags: nowait postinstall skipifsilent