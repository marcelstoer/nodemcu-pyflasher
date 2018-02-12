#!/usr/bin/env bash
#rm -fr build dist
pyinstaller --log-level=DEBUG \
            --noconfirm \
            build-on-mac.spec

#https://github.com/sindresorhus/create-dmg
#
#create-dmg NodeMCU-PyFlasher-3.0.app
