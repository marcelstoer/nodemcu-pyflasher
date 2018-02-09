#!/usr/bin/env python

import wx
import wx.adv
import wx.lib.inspection
import wx.lib.mixins.inspection

import sys
import os
import esptool
import threading
import json
import images as images
from serial import SerialException
from serial.tools import list_ports
from esptool import ESPLoader
from esptool import NotImplementedInROMError
from argparse import Namespace

__version__ = "3.0"
__flash_help__ = '''
<p>This setting is highly dependent on your device!<p>
<p>
  Details at <a style="color: #004CE5;"
        href="https://www.esp32.com/viewtopic.php?p=5523&sid=08ef44e13610ecf2a2a33bb173b0fd5c#p5523">http://bit.ly/2v5Rd32</a>
  and in the <a style="color: #004CE5;" href="https://github.com/espressif/esptool/#flash-modes">esptool
  documentation</a>
<ul>
  <li>Most ESP32 and ESP8266 ESP-12 use DIO.</li>
  <li>Most ESP8266 ESP-01/07 use QIO.</li>
  <li>ESP8285 requires DOUT.</li>
</ul>
</p>
'''
__supported_baud_rates__ = [9600, 57600, 74880, 115200, 230400, 460800, 921600]

# ---------------------------------------------------------------------------


# See discussion at http://stackoverflow.com/q/41101897/131929
class RedirectText:
    def __init__(self, text_ctrl):
        self.__out = text_ctrl

    def write(self, string):
        if string.startswith("\r"):
            # carriage return -> remove last line i.e. reset position to start of last line
            current_value = self.__out.GetValue()
            last_newline = current_value.rfind("\n")
            new_value = current_value[:last_newline + 1]  # preserve \n
            new_value += string[1:]  # chop off leading \r
            wx.CallAfter(self.__out.SetValue, new_value)
        else:
            wx.CallAfter(self.__out.AppendText, string)

    # noinspection PyMethodMayBeStatic
    def flush(self):
        # noinspection PyStatementEffect
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
        try:
            initial_baud = min(ESPLoader.ESP_ROM_BAUD, self._config.baud)

            esp = ESPLoader.detect_chip(self._config.port, initial_baud)
            print("Chip is %s" % (esp.get_chip_description()))

            esp = esp.run_stub()

            if self._config.baud > initial_baud:
                try:
                    esp.change_baud(self._config.baud)
                except NotImplementedInROMError:
                    print("WARNING: ROM doesn't support changing baud rate. Keeping initial baud rate %d." %
                          initial_baud)

            args = Namespace()
            args.flash_size = "detect"
            args.flash_mode = self._config.mode
            args.flash_freq = "40m"
            args.no_progress = False
            args.no_stub = False
            args.verify = False  # TRUE is deprecated
            args.compress = True
            args.addr_filename = [[int("0x00000", 0), open(self._config.firmware_path, 'rb')]]

            print("Configuring flash size...")
            esptool.detect_flash_size(esp, args)
            esp.flash_set_parameters(esptool.flash_size_bytes(args.flash_size))

            if self._config.erase_before_flash:
                esptool.erase_flash(esp, args)
            esptool.write_flash(esp, args)
            # The last line printed by esptool is "Leaving..." -> some indication that the process is done is needed
            print("\nDone.")
        except SerialException as e:
            self._parent.report_error(e.strerror)
            raise e

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# DTO between GUI and flashing thread
class FlashConfig:
    def __init__(self):
        self.baud = 115200
        self.erase_before_flash = False
        self.mode = "dio"
        self.firmware_path = None
        self.port = None

    @classmethod
    def load(cls, file_path):
        conf = cls()
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            conf.port = data['port']
            conf.baud = data['baud']
            conf.mode = data['mode']
            conf.erase_before_flash = data['erase']
        return conf

    def safe(self, file_path):
        data = {
            'port': self.port,
            'baud': self.baud,
            'mode': self.mode,
            'erase': self.erase_before_flash,
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def is_complete(self):
        return self.firmware_path is not None and self.port is not None

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class NodeMcuFlasher(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(700, 650),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self._config = FlashConfig.load(self._get_config_file_path())

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

        fgs = wx.FlexGridSizer(7, 2, 10, 10)

        self.choice = wx.Choice(panel, choices=self._get_serial_ports())
        self.choice.Bind(wx.EVT_CHOICE, on_select_port)
        self._select_configured_port()
        bmp = images.Reload.GetBitmap()
        reload_button = wx.BitmapButton(panel, id=wx.ID_ANY, bitmap=bmp,
                                        size=(bmp.GetWidth() + 7, bmp.GetHeight() + 7))
        reload_button.Bind(wx.EVT_BUTTON, on_reload)
        reload_button.SetToolTip("Reload serial device list")

        file_picker = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, on_pick_file)

        serial_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        serial_boxsizer.Add(self.choice, 1,  wx.EXPAND)
        serial_boxsizer.AddStretchSpacer(0)
        serial_boxsizer.Add(reload_button, 0, wx.ALIGN_RIGHT, 20)

        baud_boxsizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_baud_radio_button(sizer, index, baud_rate):
            style = wx.RB_GROUP if index == 0 else 0
            radio_button = wx.RadioButton(panel, name="baud-%d" % baud_rate, label="%d" % baud_rate, style=style)
            radio_button.rate = baud_rate
            # sets default value
            radio_button.SetValue(baud_rate == self._config.baud)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_baud_changed)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        for idx, rate in enumerate(__supported_baud_rates__):
            add_baud_radio_button(baud_boxsizer, idx, rate)

        flashmode_boxsizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_flash_mode_radio_button(sizer, index, mode, label):
            style = wx.RB_GROUP if index == 0 else 0
            radio_button = wx.RadioButton(panel, name="mode-%s" % mode, label="%s" % label, style=style)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_mode_changed)
            radio_button.mode = mode
            radio_button.SetValue(mode == self._config.mode)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        add_flash_mode_radio_button(flashmode_boxsizer, 0, "qio", "Quad I/O (QIO)")
        add_flash_mode_radio_button(flashmode_boxsizer, 1, "dio", "Dual I/O (DIO)")
        add_flash_mode_radio_button(flashmode_boxsizer, 2, "dout", "Dual Output (DOUT)")

        erase_boxsizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_erase_radio_button(sizer, index, erase_before_flash, label, value):
            style = wx.RB_GROUP if index == 0 else 0
            radio_button = wx.RadioButton(panel, name="erase-%s" % erase_before_flash, label="%s" % label, style=style)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_erase_changed)
            radio_button.erase = erase_before_flash
            radio_button.SetValue(value)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        erase = self._config.erase_before_flash
        add_erase_radio_button(erase_boxsizer, 0, False, "no", erase is False)
        add_erase_radio_button(erase_boxsizer, 1, True, "yes, wipes all data", erase is True)

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

        def on_info_hover(event):
            from HtmlPopupTransientWindow import HtmlPopupTransientWindow
            win = HtmlPopupTransientWindow(self, wx.SIMPLE_BORDER, __flash_help__, "#FFB6C1", (410, 140))

            image = event.GetEventObject()
            image_position = image.ClientToScreen((0, 0))
            image_size = image.GetSize()
            win.Position(image_position, (0, image_size[1]))

            win.Popup()

        icon = wx.StaticBitmap(panel, wx.ID_ANY, images.Info.GetBitmap())
        icon.Bind(wx.EVT_MOTION, on_info_hover)

        flashmode_label_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        flashmode_label_boxsizer.Add(flashmode_label, 1, wx.EXPAND)
        flashmode_label_boxsizer.AddStretchSpacer(0)
        flashmode_label_boxsizer.Add(icon, 0, wx.ALIGN_RIGHT, 20)

        erase_label = wx.StaticText(panel, label="Erase flash")
        console_label = wx.StaticText(panel, label="Console")

        fgs.AddMany([
                    port_label, (serial_boxsizer, 1, wx.EXPAND),
                    file_label, (file_picker, 1, wx.EXPAND),
                    baud_label, baud_boxsizer,
                    flashmode_label_boxsizer, flashmode_boxsizer,
                    erase_label, erase_boxsizer,
                    (wx.StaticText(panel, label="")), (button, 1, wx.EXPAND),
                    (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND)])
        fgs.AddGrowableRow(6, 1)
        fgs.AddGrowableCol(1, 1)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)

    def _select_configured_port(self):
        count = 0
        for item in self.choice.GetItems():
            if item == self._config.port:
                self.choice.Select(count)
                break
            count += 1

    @staticmethod
    def _get_serial_ports():
        ports = [""]
        for port, desc, hwid in sorted(list_ports.comports()):
            ports.append(port)
        return ports

    def _set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
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

    @staticmethod
    def _get_config_file_path():
        return wx.StandardPaths.Get().GetUserConfigDir() + "/nodemcu-pyflasher.json"

    # Menu methods
    def _on_exit_app(self, event):
        self._config.safe(self._get_config_file_path())
        self.Close(True)

    def _on_help_about(self, event):
        from About import AboutDlg
        about = AboutDlg(self)
        about.ShowModal()
        about.Destroy()

    def report_error(self, message):
        self.console_ctrl.SetValue(message)

    def log_message(self, message):
        self.console_ctrl.AppendText(message)

# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
class MySplashScreen(wx.adv.SplashScreen):
    def __init__(self):
        wx.adv.SplashScreen.__init__(self, images.Splash.GetBitmap(),
                                     wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, 2500, None, -1)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.__fc = wx.CallLater(2000, self._show_main)

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
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
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

