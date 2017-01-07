
# coding=utf-8

import sys, os, wx
import wx.html
import wx.lib.wxpTag
from Main import __version__

# ---------------------------------------------------------------------------


class MyAboutBox(wx.Dialog):
    text = '''
<html>
<body bgcolor="#DCDCDC" style="font-family: Arial; background-color: #DCDCDC;">
<center>
    <img src="{0}/images/python-256.png" width="64" height="64" alt="Python">
    <img src="{0}/images/icon-256.png" width="64" height="64" alt="NodeMCU">
    <img src="{0}/images/espressif-256.png" width="64" height="64" alt="Espressif, producers of ESP8266 et.al.">
    <img src="{0}/images/wxpython-256.png" width="64" height="43" alt="wxPython, cross-platform GUI framework">

    <h1>NodeMCU PyFlasher</h1>

    <p>Version {1}</p>

    <p>Fork the <a style="color: #004CE5;" href="https://github.com/marcelstoer/nodemcu-pyflasher">project on
    GitHub</a> and help improve it for all!</p>

    <p>&copy; 2016-2017 Marcel St&ouml;r. Licensed under MIT.</p>

    <p>
        <wxp module="wx" class="Button">
            <param name="label" value="Close">
            <param name="id" value="ID_OK">
        </wxp>
    </p>
</center>
</body>
</html>
'''

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "About NodeMCU PyFlasher")
        html = wx.html.HtmlWindow(self, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            html.SetStandardFonts()
        txt = self.text.format(self.__get_bundle_dir(), __version__)
        html.SetPage(txt)
        ir = html.GetInternalRepresentation()
        html.SetSize((ir.GetWidth() + 25, ir.GetHeight() + 25))
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)

    def __get_bundle_dir(self):
        # set by PyInstaller, see http://pyinstaller.readthedocs.io/en/v3.2/runtime-information.html
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
