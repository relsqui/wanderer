#!/bin/bash 

wine C:/Python27/python.exe -O $(winepath -w /home/fizz/pyinstaller-2.0/pyinstaller.py) --noupx wanderer.windows.spec && mv wanderer-windows.exe binaries
