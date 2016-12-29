#!/usr/bin/env bash
pyinstaller --noconfirm --log-level=INFO \
    --onefile --windowed \
    --name="NodeMCU PyFlasher" \
    --icon=./images/icon-256.icns \
    --osx-bundle-identifier=com.frightanic.nodemcu-pyflasher \
    --upx-dir=/usr/local/share/ \
    nodemcu-pyflasher.spec
