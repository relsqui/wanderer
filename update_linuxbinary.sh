#!/bin/bash 

python -O /home/fizz/pyinstaller-2.0/pyinstaller.py wanderer.linuxmac.spec && mv wanderer-linux binaries && rm -rf build && rm logdict* 2>/dev/null
