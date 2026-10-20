Set fso = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.Run "pythonw.exe """ & folder & "\whistle.py""", 0, False