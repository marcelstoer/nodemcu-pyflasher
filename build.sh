#!/usr/bin/env bash
#rm -fr build dist
pyinstaller --log-level=DEBUG \
            --noconfirm \
            build-on-mac.spec
