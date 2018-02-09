
# coding=utf-8

import wx
import wx.html
import webbrowser


class HtmlPopupTransientWindow(wx.PopupTransientWindow):
    def __init__(self, parent, style, html_body_content, bgcolor, size):
        wx.PopupTransientWindow.__init__(self, parent, style)
        panel = wx.Panel(self)
        panel.SetBackgroundColour(bgcolor)

        html_window = self.HtmlWindow(panel, wx.ID_ANY, size=size)
        html_window.SetPage('<body bgcolor="' + bgcolor + '">' + html_body_content + '</body>')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html_window, 0, wx.ALL, 5)
        panel.SetSizer(sizer)

        sizer.Fit(panel)
        sizer.Fit(self)
        self.Layout()

    class HtmlWindow(wx.html.HtmlWindow):
        def OnLinkClicked(self, link):
            # get a hold of the PopupTransientWindow to close it
            self.GetParent().GetParent().Dismiss()
            webbrowser.open(link.GetHref())
