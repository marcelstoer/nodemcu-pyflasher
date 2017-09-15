
"""
This is a way to save the startup time when running img2py on lots of
files...
"""

from wx.tools import img2py

command_lines = [
    "-F -n Exit images/exit.png images.py",
    "-a -F -n Reload images/reload.png images.py",
    "-a -F -n Splash images/splash.png images.py",
    "-a -F -n Info images/info.png images.py",
    "-a -F -i -n Icon images/icon-256.png images.py",
    ]

if __name__ == "__main__":
    for line in command_lines:
        args = line.split()
        img2py.main(args)

