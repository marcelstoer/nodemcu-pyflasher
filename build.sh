#!/usr/bin/env bash
rm -fr build dist
pyinstaller --log-level=DEBUG \
            --windowed \
            --icon=./images/icon-256.icns \
            --name="NodeMCU-PyFlasher" \
            --noconfirm \
            --onefile \
            --osx-bundle-identifier=com.frightanic.nodemcu-pyflasher \
            nodemcu-pyflasher.py
