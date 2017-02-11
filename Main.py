#!/usr/bin/env python

import wx
import wx.lib.inspection
import wx.lib.mixins.inspection
import sys
import esptool
import threading
import images as images
from serial.tools import list_ports
from esptool import ESPLoader
from argparse import Namespace

__version__ = "0.2.0"
__supported_baud_rates__ = [9600, 57600, 74880, 115200, 230400, 460800, 921600]

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
        self._parent = parent
        self._config = config

    def run(self):
        args = Namespace()
        args.flash_size = self._config.flashsize
        args.flash_mode = self._config.mode
        args.flash_freq = "40m"
        args.no_progress = True
        args.verify = False
        args.compress = True
        args.ucIsHspi = True
        args.no_stub = False
        args.baud = self._config.baud
        args.addr_filename = [[int("0x00000", 0), open(self._config.firmware_path, 'rb')]]
        esp = ESPLoader.detect_chip(self._config.port, 115200)
        esp = esp.run_stub()
        esp.change_baud(args.baud)

        # needs connect() before each operation, see  https://github.com/espressif/esptool/issues/157
        if self._config.erase_before_flash:
            #esp.connect()
            esptool.erase_flash(esp, args)



            esptool.write_flash(esp, args)


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DTO between GUI and flashing thread
class FlashConfig:
    def __init__(self):
        self.baud = 115200
        self.erase_before_flash = False
        self.mode = "qio"
        self.flashsize = "detect"
        self.firmware_path = None
        self.port = None

    def is_complete(self):
        return self.firmware_path is not None and self.port is not None

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class NodeMcuFlasher(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(700, 650),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self._config = FlashConfig()

        self._build_status_bar()
        self._set_icons()
        self._build_menu_bar()
        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)

        self.SetMinSize((640, 480))
        self.Centre(wx.BOTH)
        self.Show(True)

    def _init_ui(self):
        def on_reload(event):
            self.choice.SetItems(self._get_serial_ports())

        def on_baud_changed(event):
            radio_button = event.GetEventObject()

            if radio_button.GetValue():
                self._config.baud = radio_button.rate

        def on_mode_changed(event):
            radio_button = event.GetEventObject()

            if radio_button.GetValue():
                self._config.mode = radio_button.mode

        def on_flashsize_changed(event):
            radio_button = event.GetEventObject()

            if radio_button.GetValue():
                self._config.flashsize = radio_button.flashsize

        def on_erase_changed(event):
            radio_button = event.GetEventObject()

            if radio_button.GetValue():
                self._config.erase_before_flash = radio_button.erase

        def on_clicked(event):
            self.console_ctrl.SetValue("")
            worker = FlashingThread(self, self._config)
            worker.start()

        def on_select_port(event):
            choice = event.GetEventObject()
            self._config.port = choice.GetString(choice.GetSelection())

        def on_pick_file(event):
            self._config.firmware_path = event.GetPath().replace("'", "")

        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(8, 2, 10, 10)

        self.choice = wx.Choice(panel, choices=self._get_serial_ports())
        self.choice.Bind(wx.EVT_CHOICE, on_select_port)
        bmp = images.Reload.GetBitmap()
        reload_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp,
                                        size=(bmp.GetWidth() + 7, bmp.GetHeight() + 7))
        reload_button.Bind(wx.EVT_BUTTON, on_reload)

        file_picker = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, on_pick_file)

        serial_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        serial_boxsizer.Add(self.choice, 1,  wx.EXPAND)
        serial_boxsizer.AddStretchSpacer(0)
        serial_boxsizer.Add(reload_button, 0, wx.ALIGN_RIGHT, 20)

        baud_boxsizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_baud_radio_button(sizer, idx, rate):
            style = wx.RB_GROUP if idx == 0 else 0
            radio_button = wx.RadioButton(panel, name="baud-%d" % rate, label="%d" % rate, style=style)
            radio_button.rate = rate
            # sets default value
            radio_button.SetValue(rate == self._config.baud)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_baud_changed)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        for idx, rate in enumerate(__supported_baud_rates__):
            add_baud_radio_button(baud_boxsizer, idx, rate)

        flashmode_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        qio_button = wx.RadioButton(panel, name="mode-qio", label="Quad Flash I/O (qio)", style=wx.RB_GROUP)
        qio_button.Bind(wx.EVT_RADIOBUTTON, on_mode_changed)
        qio_button.mode = "qio"
        qio_button.SetValue(True)
        dio_button = wx.RadioButton(panel, name="mode-dio", label="Dual Flash I/O (dio), usually for >=4MB flash chips")
        dio_button.Bind(wx.EVT_RADIOBUTTON, on_mode_changed)
        dio_button.mode = "dio"
        flashmode_boxsizer.Add(qio_button)
        flashmode_boxsizer.AddSpacer(10)
        flashmode_boxsizer.Add(dio_button)

        flashsize_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        detect_button = wx.RadioButton(panel, name="flashsize-detect", label="Autodetect flash size", style=wx.RB_GROUP)
        detect_button.Bind(wx.EVT_RADIOBUTTON, on_flashsize_changed)
        detect_button.flashsize = "detect"
        detect_button.SetValue(True)
        large_button = wx.RadioButton(panel, name="flashsize-8m", label="Use 8mb flash size (for 16MB module)")
        large_button.Bind(wx.EVT_RADIOBUTTON, on_flashsize_changed)
        large_button.flashsize = "1MB"
        flashsize_boxsizer.Add(detect_button)
        flashsize_boxsizer.AddSpacer(10)
        flashsize_boxsizer.Add(large_button)

        erase_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        erase_no_button = wx.RadioButton(panel, name="erase-no", label="no", style=wx.RB_GROUP)
        erase_no_button.Bind(wx.EVT_RADIOBUTTON, on_erase_changed)
        erase_no_button.erase = False
        erase_no_button.SetValue(True)
        erase_yes_button = wx.RadioButton(panel, name="erase-yes", label="yes, wipes all data")
        erase_yes_button.Bind(wx.EVT_RADIOBUTTON, on_erase_changed)
        erase_yes_button.erase = True
        erase_boxsizer.Add(erase_no_button)
        erase_boxsizer.AddSpacer(10)
        erase_boxsizer.Add(erase_yes_button)

        button = wx.Button(panel, -1, "Flash NodeMCU")
        button.Bind(wx.EVT_BUTTON, on_clicked)

        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.console_ctrl.SetFont(wx.Font(13, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.BLACK)
        self.console_ctrl.SetForegroundColour(wx.RED)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.RED))

        port_label = wx.StaticText(panel, label="Serial port")
        file_label = wx.StaticText(panel, label="NodeMCU firmware")
        baud_label = wx.StaticText(panel, label="Baud rate")
        flashmode_label = wx.StaticText(panel, label="Flash mode")
        flashsize_label = wx.StaticText(panel, label="Flash size")
        erase_label = wx.StaticText(panel, label="Erase flash")
        console_label = wx.StaticText(panel, label="Console")

        fgs.AddMany([
                    port_label, (serial_boxsizer, 1, wx.EXPAND),
                    file_label, (file_picker, 1, wx.EXPAND),
                    baud_label, baud_boxsizer,
                    flashmode_label, flashmode_boxsizer,
                    flashsize_label, flashsize_boxsizer,
                    erase_label, erase_boxsizer,
                    (wx.StaticText(panel, label="")), (button, 1, wx.EXPAND),
                    (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND)])
        fgs.AddGrowableRow(7, 1)
        fgs.AddGrowableCol(1, 1)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def _get_serial_ports(self):
        ports = [""]
        for port, desc, hwid in sorted(list_ports.comports()):
            ports.append(port)
        return ports

    def _set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = "Welcome to NodeMCU PyFlasher %s" % __version__
        self.statusBar.SetStatusText(status_text, 0)

    def _build_menu_bar(self):
        self.menuBar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit NodeMCU PyFlasher")
        exit_item.SetBitmap(images.Exit.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)
        self.menuBar.Append(file_menu, "&File")

        # Help menu
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ABOUT, '&About NodeMCU PyFlasher', 'About')
        self.Bind(wx.EVT_MENU, self._on_help_about, help_item)
        self.menuBar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menuBar)

    # Menu methods
    def _on_exit_app(self, event):
        self.Close(True)

    def _on_help_about(self, event):
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
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.__fc = wx.FutureCall(2000, self._show_main)

    def _on_close(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()

        # if the timer is still running then go ahead and show the
        # main frame now
        if self.__fc.IsRunning():
            self.__fc.Stop()
            self._show_main()

    def _show_main(self):
        frame = NodeMcuFlasher(None, "NodeMCU PyFlasher")
        frame.Show()
        if self.__fc.IsRunning():
            self.Raise()

# ---------------------------------------------------------------------------


# ----------------------------------------------------------------------------
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
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
