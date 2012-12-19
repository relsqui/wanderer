#!/bin/bash 

python /home/fizz/pyinstaller-2.0/pyinstaller.py wanderer.linuxmac.spec && mv wanderer-linux binaries && rm -rf build && rm logdict*
