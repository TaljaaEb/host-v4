#wine /home/user/.wine/drive_c/users/user/AppData/Local/Programs/Python/Python312/Scripts/pyinstaller.exe --onefile proc_service.py
wine /home/user/.wine/drive_c/users/user/AppData/Local/Programs/Python/Python312/Scripts/pyinstaller.exe --onefile --hidden-import=stub --hidden-import=win32timezone --hidden-import=win32service --hidden-import=win32serviceutil --hidden-import=servicemanager proc_service.py

zip -r install.zip dist/