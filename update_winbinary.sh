#!/bin/bash 

wine C:/Python27/python.exe $(winepath -w /home/fizz/pyinstaller-2.0/pyinstaller.py) wanderer.windows.spec && mv wanderer-windows.exe binaries && rm -rf build && rm logdict*
