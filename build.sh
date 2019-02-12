#!/usr/bin/env bash
#rm -fr build dist
VERSION=4.0
NAME=NodeMCU-PyFlasher

pyinstaller --log-level=DEBUG \
            --noconfirm \
            build-on-mac.spec

#https://github.com/sindresorhus/create-dmg
create-dmg dist/$NAME-$VERSION.app
mv "$NAME-$VERSION 0.0.0.dmg" dist/$NAME-$VERSION.dmg
