# Things Not Automated

* Turning on FileVault
* You need to log into the Mac App Store beforehand


## Applications

* Dash: Turn on sync
* BetterTouchTool: Start at login and set up sync (but sync seems broken as of 2019-07-04, so maybe just export/import), hide with Bartender
* iStat Menus: Start and import settings
* Bartender: License, start at login, position menu items
* Hammerspoon: Start at login, grant accessibility, hide with Bartender
* Textual: Add license, configure Freenode, including nick, auth, auto-reconnect settings, connect commands, +i on connect
* 1Password
* Moom: License, start at login, hide with Bartender


### Textual

Connect commands:

```
/timer 20 1 /quote nickserv ghost dale
/timer 25 1 /nick dale
```


# Notes

* A reboot (or maybe just log out and back in, but reboot to be on the safe side) will be necessary after many of the changes here, particularly the changes in the `macos_system` and `macos_prefs` roles.  I *suspect* that not rebooting **promptly** after some of these changes can cause them to be reverted, especially if you go noodling about in preferences dialogs or System Preferences between Ansible's changes and when you reboot.
