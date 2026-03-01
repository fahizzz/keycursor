#!/usr/bin/env python3

import os
import sys
import subprocess

os.environ['YDOTOOL_SOCKET'] = '/run/ydotool.sock'

from controller import MouseController

if __name__ == '__main__':
    if os.environ.get('GDK_BACKEND') != 'x11':
        print("⚠️  Warning: Run with: GDK_BACKEND=x11 python3 main.py")
    
    if subprocess.run(['pgrep', 'ydotoold'], capture_output=True).returncode != 0:
        print("Error: ydotoold is not running!")
        print("Start with: sudo systemctl start ydotool")
        sys.exit(1)

    controller = MouseController()
    controller.run()