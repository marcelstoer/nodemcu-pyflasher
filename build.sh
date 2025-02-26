#!/usr/bin/env bash
# rm -fr build dist
VERSION=5.1.0
NAME="NodeMCU PyFlasher"
DIST_NAME="NodeMCU-PyFlasher"

pyinstaller --log-level=DEBUG \
            --noconfirm \
            build-on-mac.spec

# https://github.com/sindresorhus/create-dmg
create-dmg "dist/$NAME.app"
mv "$NAME $VERSION.dmg" "dist/$DIST_NAME.dmg"
