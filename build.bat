pyinstaller --log-level=DEBUG ^
            --windowed ^
            --icon=.\images\icon-256.png ^
            --name="NodeMCU-PyFlasher" ^
            --noconfirm ^
            --onefile ^
            nodemcu-pyflasher.py
