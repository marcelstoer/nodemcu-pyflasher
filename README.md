# NodeMCU PyFlasher
[![License](https://marcelstoer.github.io/nodemcu-pyflasher/images/mit-license-badge.svg)](https://github.com/marcelstoer/nodemcu-pyflasher/blob/master/LICENSE)
[![Github Releases](https://img.shields.io/github/downloads/marcelstoer/nodemcu-pyflasher/total.svg?style=flat)](https://github.com/marcelstoer/nodemcu-pyflasher/releases)
[![PayPal Donation](https://marcelstoer.github.io/nodemcu-pyflasher/images/donate-paypal-badge.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=HFN4ZMET5XS2Q)
[![Twitter URL](https://marcelstoer.github.io/nodemcu-pyflasher/images/twitter-badge.svg)](https://twitter.com/intent/tweet?text=Wow:&url=https%3A%2F%2Fgithub.com%2Fmarcelstoer%2Fnodemcu-pyflasher)
[![Facebook URL](https://marcelstoer.github.io/nodemcu-pyflasher/images/facebook-badge.svg)](https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fgithub.com%2Fmarcelstoer%2Fnodemcu-pyflasher)

Self-contained [NodeMCU](https://github.com/nodemcu/nodemcu-firmware) flasher with GUI based on [esptool.py](https://github.com/espressif/esptool) and [wxPython](https://www.wxpython.org/).

![Image of NodeMCU PyFlasher GUI](images/gui.png)

## Installation
NodeMCU PyFlasher doesn't have to be installed, just double-click it and it'll start. Check the [releases section](https://github.com/marcelstoer/nodemcu-pyflasher/releases) for downloads for your platform. For every release there's at least a .exe file for Windows. Starting from 3.0 there's also a .dmg for macOS.

## Status
Scan the [list of open issues](https://github.com/marcelstoer/nodemcu-pyflasher/issues) for bugs and pending features.

**Note** 

This is my first Python project. If you have constructive feedback as for how to improve the code please do reach out to me.

## Getting help
In the unlikely event that you're stuck with this simple tool the best way to get help is to turn to the ["Tools and IDE" subforum on esp8266.com](http://www.esp8266.com/viewforum.php?f=22).

## Donationware
All open-source development by the author is donationware. Show your love and support for open-source development by donating to the good cause through PayPal.

[![PayPal Donations](./images/paypal-256.png)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=HFN4ZMET5XS2Q)

## Build it yourself
If you want to build this application yourself you need to:

- Install Python 3.x
- Install [wxPython 4.x](https://wxpython.org/) manually or run `pip install wxpython`
- Install [esptool.py](https://github.com/espressif/esptool#easy-installation)  and its dependencies manually or run `pip install esptool`

## Why this project exists

### Motivation
This addresses an issue the NodeMCU community touched on several times in the past, most recently at
 [#1500 (comment)](https://github.com/nodemcu/nodemcu-firmware/pull/1500#issuecomment-247884981).

I stated that based on my experience doing NodeMCU user support it should be a lot simpler to flash NodeMCU for Windows users.

- A number of flashing tools are available but only two are actively maintained: esptool-ck and esptool.py. Only one is endorsed by Espressif: [esptool.py](https://github.com/espressif/esptool) (they hired the developer(s)).
- 70% of the users of my [nodemcu-build.com](https://nodemcu-build.com) service are on Windows.
- BUT Windows doesn't come with Python installed - which is required for esptool.py.
- BUT Windows users in general are more reluctant to use the CLI than Linux/Mac users - which is required for esptool.py.

To conclude: this is not a comfortable situation for NodeMCU's largest user group.

### The plan
For quite a while I planned to write a self-contained GUI tool which would use esptool.py in the background. It should primarily target Windows users but since I'm on Mac it should be cross-platform. Even though I had never used Python before I felt confident to pull this off.

### Implementation
- Uses the cross-platform wxPython GUI framework. I also tried PyForms/PyQt4 but settled for wxPython.
- Requires absolutely minimal user input.
- The esptool.py "console" output is redirected to text control on the GUI.
- Uses [PyInstaller](https://github.com/pyinstaller/pyinstaller) to create self-contained executable for Windows and Mac. The packaged app can run standalone i.e. without installing itself, a Python interpreter or any modules.

## License
[MIT](http://opensource.org/licenses/MIT) © Marcel Stör
