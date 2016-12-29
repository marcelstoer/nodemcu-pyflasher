
# coding=utf-8

import wx
import wx.html
import wx.lib.wxpTag
from Main import __version__

# ---------------------------------------------------------------------------


class MyAboutBox(wx.Dialog):
    text = '''
<html>
<body bgcolor="#DCDCDC">
<style>
    body {
        font-family: Arial;
        background-color: #DCDCDC;
    }
</style>
<center>
    <img src="images/python-256.png" width="64" height="64" alt="Python">
    <img src="images/icon-256.png" width="64" height="64" alt="NodeMCU">
    <img src="images/espressif-256.png" width="64" height="64" alt="Espressif, producers of ESP8266 et.al.">
    <img src="images/wxpython-256.png" width="64" height="43" alt="wxPython, cross-platform GUI framework">

    <h1>NodeMCU PyFlasher</h1>

    <p>Version %s</p>

    <p>Fork the <a style="color: #004CE5;" href="https://github.com/marcelstoer/nodemcu-pyflasher">project on
    GitHub</a> and help improve it for all!</p>

    <p>© 2016-2017 Marcel Stör. Licensed under MIT.</p>

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
        txt = self.text % __version__
        html.SetPage(txt)
        ir = html.GetInternalRepresentation()
        html.SetSize((ir.GetWidth() + 25, ir.GetHeight() + 25))
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)


# ---------------------------------------------------------------------------
