# Things Not Automated

* Set up accounts: admin at install, then regular user after
* Allow regular user account to sudo with file in `/etc/sudoers.d`
* Set firmware password
* Initial virtualenv and Ansible install
* Give Terminal and/or iTerm 2 "Full Disk Access" to allow it to read things like Mail.app's preferences file (solution courtesy https://github.com/mathiasbynens/dotfiles/issues/849)
* Turning on FileVault
* You need to log into the Mac App Store beforehand
* Text replacements
* iCloud, Google accounts
* DHCP client ID on wireless and other network interfaces
* Go into Accessibility → Speech → System Voice → Customize and download the high quality voices
* Double tap fn and enable dictation once to download the Enhanced Dictionary
* Set up printer


## Applications

* 1Password
* Alfred: Turn on auto-expand snippets (not synced)
* Amphetamine: Set to run at login
* Bartender: License, start at login, position menu items
* BetterTouchTool: Start at login and set up sync (but sync seems broken as of 2019-07-04, so maybe just export/import), hide with Bartender
* Chrome: Sign in, disable consistency flag, set sync preferences, unlock, import extension settings (Auto Delete Cookies, Privacy Badger, uBlock, ViolentMonkey, SessionBuddy, etc.)
* Dash: Turn on sync
* Dropbox: Start at login, login, turn off photo/video syncing
* Firefox: Sync, Little Snitch private rule, extensions
* GPGMail (mail plug-in): License, set preferences
* Hammerspoon: Start at login, grant accessibility, hide with Bartender
* iStat Menus: Start and import settings
* iTunes: Turn on wifi sync, pair with phone, turn off automatic syncing, manually sync music
  * **Warning!** When I did this, I got a warning saying that my phone can only sync with one library.  (I don't have a library.)  Then all my audiobooks got deleted.  Should find a better way to do this.
* Little Snitch: Not even installed, do it all yourself---**installer will force reboot**
* Mail.app: Enable mail bundles (can't find any plist where these are enabled)
* Moom: License, start at login, hide with Bartender
* OneNote: Sign in
* Parallels: Grant various permissions at first run, install license, copy over VMs
* QuoteFix (mail plug-in): Set preferences
* Safari: Install extensions (AdGuard and sVim currently)
* Signal: Link to phone
* Textual: Add license, configure Freenode, including nick, auth, auto-reconnect settings, connect commands, +i on connect
* Tunnelblick: All configuration
* Witch: Enable, license


### Textual

Connect commands:

```
/timer 20 1 /quote nickserv ghost dale
/timer 25 1 /nick dale
```


# Notes

* A reboot (or maybe just log out and back in, but reboot to be on the safe side) will be necessary after many of the changes here, particularly the changes in the `macos_system` and `macos_prefs` roles.  I *suspect* that not rebooting **promptly** after some of these changes can cause them to be reverted, especially if you go noodling about in preferences dialogs or System Preferences between Ansible's changes and when you reboot.
