; Inno Setup script. Run build_windows.bat first, then compile this file.
[Setup]
AppName=SmartCorrect
AppVersion=2.0.0
DefaultDirName={autopf}\SmartCorrect
DefaultGroupName=SmartCorrect
OutputBaseFilename=SmartCorrect-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\dist\SmartCorrect\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\SmartCorrect"; Filename: "{app}\SmartCorrect.exe"
Name: "{userstartup}\SmartCorrect"; Filename: "{app}\SmartCorrect.exe"; Tasks: startup

[Tasks]
Name: "startup"; Description: "Start SmartCorrect when Windows starts"
