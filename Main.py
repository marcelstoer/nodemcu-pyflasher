#!/usr/bin/env python

import wx
import wx.lib.inspection
import wx.lib.mixins.inspection
import sys
import esptool
import threading
from serial.tools import list_ports
from esptool import ESPROM
from argparse import Namespace

# stuff for debugging
print "Python version:", sys.version
print "wxPython version:", wx.version()
print "esptool.py version:", esptool.version(None)

__version__ = "0.1.0"

# ---------------------------------------------------------------------------


# See discussion at http://stackoverflow.com/q/41101897/131929
class RedirectText:
    def __init__(self, text_ctrl):
        self.__out = text_ctrl
        self.__pending_backspaces = 0

    def write(self, string):
        new_string = ""
        number_of_backspaces = 0
        for c in string:
            if c == "\b":
                number_of_backspaces += 1
            else:
                new_string += c

        if self.__pending_backspaces > 0:
            # current value minus pending backspaces plus new string
            new_value = self.__out.GetValue()[:-1 * self.__pending_backspaces] + new_string
            wx.CallAfter(self.__out.SetValue, new_value)
        else:
            wx.CallAfter(self.__out.AppendText, new_string)

        self.__pending_backspaces = number_of_backspaces

    def flush(self):
        None

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class FlashingThread(threading.Thread):
    def __init__(self, parent, config):
        threading.Thread.__init__(self)
        self.daemon = True
        self.__parent = parent
        self.__config = config

    def run(self):
        esp = ESPROM(port=self.__config.port)
        args = Namespace()
        args.flash_size = "detect"
        args.flash_mode = self.__config.mode
        args.flash_freq = "40m"
        args.no_progress = False
        args.verify = True
        args.baud = self.__config.baud
        args.addr_filename = [[int("0x00000", 0), open(self.__config.file, 'rb')]]
        # needs connect() before each operation, see  https://github.com/espressif/esptool/issues/157
        if self.__config.erase_before_flash:
            esp.connect()
            esptool.erase_flash(esp, args)
        esp.connect()
        esptool.write_flash(esp, args)

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DTO between GUI and flashing thread
class FlashConfig:
    def __init__(self):
        self.baud = 115200
        self.erase_before_flash = False
        self.mode = "qio"
        self.file = None
        self.port = None

    def is_complete(self):
        return self.file is not None and self.port is not None

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class NodeMcuFlasher(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(700, 650),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.__config = FlashConfig()

        self.__build_status_bar()
        self.__set_icons()
        self.__build_menu_bar()
        self.__init_ui()

        sys.stdout = RedirectText(self.console_ctrl)

        self.SetMinSize((640, 480))
        self.Centre(wx.BOTH)
        self.Show(True)

    def __init_ui(self):
        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(7, 2, 10, 10)

        port_label = wx.StaticText(panel, label="Serial port")
        file_label = wx.StaticText(panel, label="NodeMCU firmware")
        baud_label = wx.StaticText(panel, label="Baud rate")
        flashmode_label = wx.StaticText(panel, label="Flash mode")
        erase_label = wx.StaticText(panel, label="Erase flash")
        console_label = wx.StaticText(panel, label="Console")

        self.choice = wx.Choice(panel, choices=self.__get_serial_ports())
        self.choice.Bind(wx.EVT_CHOICE, self.__on_select_port)
        bmp = images.Reload.GetBitmap()
        reload_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp,
                                        size=(bmp.GetWidth() + 7, bmp.GetHeight() + 7))
        reload_button.Bind(wx.EVT_BUTTON, self.__on_reload)

        file_picker = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.__on_pick_file)

        button = wx.Button(panel, -1, "Flash NodeMCU")
        button.Bind(wx.EVT_BUTTON, self.__on_clicked)

        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.console_ctrl.SetFont(wx.Font(13, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.BLACK)
        self.console_ctrl.SetForegroundColour(wx.RED)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.RED))

        serial_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        serial_boxsizer.Add(self.choice, 1,  wx.EXPAND)
        serial_boxsizer.AddStretchSpacer(0)
        serial_boxsizer.Add(reload_button, 0, wx.ALIGN_RIGHT, 20)

        baud_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        baud_boxsizer.Add(wx.RadioButton(panel, name="baud-9600", label="9600", style=wx.RB_GROUP))
        baud_boxsizer.AddSpacer(10)
        baud_boxsizer.Add(wx.RadioButton(panel, name="baud-57600", label="57600"))
        baud_boxsizer.AddSpacer(10)
        baud_boxsizer.Add(wx.RadioButton(panel, name="baud-74880", label="74880"))
        baud_boxsizer.AddSpacer(10)
        radio_button_115200 = wx.RadioButton(panel, name="baud-115200", label="115200")
        radio_button_115200.SetValue(True)  # checks/selects the control
        baud_boxsizer.Add(radio_button_115200)
        baud_boxsizer.AddSpacer(10)
        baud_boxsizer.Add(wx.RadioButton(panel, name="baud-230400", label="230400"))
        baud_boxsizer.AddSpacer(10)
        baud_boxsizer.Add(wx.RadioButton(panel, name="baud-460800", label="460800"))
        baud_boxsizer.AddSpacer(10)
        baud_boxsizer.Add(wx.RadioButton(panel, name="baud-921600", label="921600"))

        flashmode_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        qio_button = wx.RadioButton(panel, name="mode-qio", label="Quad Flash I/O (qio)", style=wx.RB_GROUP)
        qio_button.SetValue(True)
        flashmode_boxsizer.Add(qio_button)
        flashmode_boxsizer.AddSpacer(10)
        flashmode_boxsizer.Add(wx.RadioButton(panel, name="mode-dio", label="Dual Flash I/O (dio), usually for >=4MB flash chips"))

        erase_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        qio_button = wx.RadioButton(panel, name="erase-no", label="no", style=wx.RB_GROUP)
        qio_button.SetValue(True)
        erase_boxsizer.Add(qio_button)
        erase_boxsizer.AddSpacer(10)
        erase_boxsizer.Add(wx.RadioButton(panel, name="erase-yes", label="yes, wipes all data"))

        # handler for all radio button groups as these "light weight" groups can't accept dedicated handlers
        self.Bind(wx.EVT_RADIOBUTTON, self.__on_radio_group)

        fgs.AddMany([
                    port_label, (serial_boxsizer, 1, wx.EXPAND),
                    file_label, (file_picker, 1, wx.EXPAND),
                    baud_label, baud_boxsizer,
                    flashmode_label, flashmode_boxsizer,
                    erase_label, erase_boxsizer,
                    (wx.StaticText(panel, label="")), (button, 1, wx.EXPAND),
                    (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND)])
        fgs.AddGrowableRow(6, 1)
        fgs.AddGrowableCol(1, 1)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def __get_serial_ports(self):
        ports = [""]
        for port, desc, hwid in sorted(list_ports.comports()):
            ports.append(port)
        return ports

    def __on_reload(self, event):
        self.choice.SetItems(self.__get_serial_ports())

    def __on_radio_group(self, event):
        rb = event.GetEventObject()
        name = rb.GetName()
        if name.startswith("baud-"):
            self.__config.baud = int(name[5:])
        elif name.startswith("mode-"):
            self.__config.mode = name[5:]
        elif name.startswith("erase-"):
            self.__config.erase_before_flash = name == "erase-yes"

    def __on_clicked(self, event):
        self.console_ctrl.SetValue("")
        worker = FlashingThread(self, self.__config)
        worker.start()

    def __on_select_port(self, event):
        choice = event.GetEventObject()
        self.__config.port = choice.GetString(choice.GetSelection())

    def __on_pick_file(self, event):
        self.__config.file = event.GetPath().replace("'", "")

    def __set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    def __build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = "Welcome to NodeMCU PyFlasher %s" % __version__
        self.statusBar.SetStatusText(status_text, 0)

    def __build_menu_bar(self):

        # File menu
        self.menuBar = wx.MenuBar()
        menu = wx.Menu()
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit NodeMCU PyFlasher")
        exit_item.SetBitmap(images.Exit.GetBitmap())
        self.Bind(wx.EVT_MENU, self.__on_exit_app, exit_item)
        self.menuBar.Append(menu, "&File")

        # Help menu
        menu = wx.Menu()
        help_item = menu.Append(wx.ID_ABOUT, '&About NodeMCU PyFlasher', 'About')
        self.Bind(wx.EVT_MENU, self.__on_help_about, help_item)
        self.menuBar.Append(menu, '&Help')

        self.SetMenuBar(self.menuBar)

    # Menu methods
    def __on_exit_app(self, event):
        self.Close(True)

    def __on_help_about(self, event):
        from About import MyAboutBox
        about = MyAboutBox(self)
        about.ShowModal()
        about.Destroy()

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class MySplashScreen(wx.SplashScreen):
    def __init__(self):
        wx.SplashScreen.__init__(self, images.Splash.GetBitmap(),
                                 wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                 2500, None, -1)
        self.Bind(wx.EVT_CLOSE, self.__on_close)
        self.__fc = wx.FutureCall(2000, self.__show_main)

    def __on_close(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()

        # if the timer is still running then go ahead and show the
        # main frame now
        if self.__fc.IsRunning():
            self.__fc.Stop()
            self.__show_main()

    def __show_main(self):
        frame = NodeMcuFlasher(None, "NodeMCU PyFlasher")
        frame.Show()
        if self.__fc.IsRunning():
            self.Raise()

# ---------------------------------------------------------------------------


# ----------------------------------------------------------------------------
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):

        import images as i
        global images
        images = i

        wx.SystemOptions.SetOptionInt("mac.window-plain-transition", 1)
        self.SetAppName("NodeMCU PyFlasher")

        # Create and show the splash screen.  It will then create and
        # show the main frame when it is time to do so.  Normally when
        # using a SplashScreen you would create it, show it and then
        # continue on with the application's initialization, finally
        # creating and showing the main application window(s).  In
        # this case we have nothing else to do so we'll delay showing
        # the main frame until later (see ShowMain above) so the users
        # can see the SplashScreen effect.
        splash = MySplashScreen()
        splash.Show()

        return True


# ---------------------------------------------------------------------------
def main():
    app = App(False)
    app.MainLoop()
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    __name__ = 'Main'
    main()
