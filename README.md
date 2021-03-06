---
title: Ansible Automated Setup of macOS
---

# Introduction

This is my somewhat untested, haphazard, but hopefully useful automated setup of some of my macOS software and settings.

As a general principle, I prefer using MacPorts to Homebrew.  I have, however, decided to use Homebrew Cask to install lots of binary/GUI packages, because it is very convenient and none (or almost none) of these packages can be installed via MacPorts.

Documentation here is very far from complete.


# Use of Roles

The division of what action(s) go into which role(s) is probably not super-consistent.  I have tried to make some logical and/or useful divisions.

Role `other_software` tends to be for software that I want to use as a "normal user" rather than a developer, per se.  Lots of my GUI packages get stuffed in here.  Truth be told, it may have become somewhat of a dumping group after realizing that I dread making lots and lots of fine-grained roles for software installation.  At least I've broken the things to be installed out into some variables.  This may all get refined later.

`software_dev_*` roles tend to be for "development" in particular languages/activities.

Other `software_*` roles tend to be for specific software that other role(s) will need to depend on.  For example, lots of stuff needs MacPorts installed first, so MacPorts gets it own `software_macports` role that others can depend on.

Additionally, some software has been broken out into its own roles to get me software that I need to actually work on this Ansible setup first.  For example, Emacs and/or Vim get installed early on so that I have good editors with good configurations to start editing YAML or Python if need be.


# Notes to Self: Bootstrapping

Create admin account at install time.  **Do not set up iCloud.**  In fact, opt out of basically everything during install.


## With the Admin Account

1. Flip modifiers before you go crazy.
2. Change scroll direction and turn on tap to click.
3. Check all software updates, go ahead and reboot if you need to.
4. Change host name, probably needs to match what's in your Ansible inventory.
5. Create regular user account.
6. Give new user account sudo access via `/etc/sudoers.d/dale`.  Make sure to run `visudo -c` afterwards to make sure you didn't botch it.

Now you can log out and log in as your new account.


## With Your User Account

1. Go ahead and sign into iCloud on first login.  You will at least get the chance to tell it not to sync all of your documents, downloads, photos and such.
2. Flip modifiers before you go crazy.
3. Change scroll direction and turn on tap to click.
4. Give Terminal "Full Disk Access".
5. Open Terminal.
6. Run `/usr/bin/python3 -V` and let Xcode command line tools install.
7. Run `/usr/bin/python3 -m venv ~/.vpy/system-ansible` to install a virtual environment.
8. Activate that virtual environment and `pip install ansible`.
9. `ssh-keygen -t ed25519 -C ...` and follow the prompts.
10. `ssh-add`
11. Upload new key to GitHub.
12. Clone this repo (`macos_ansible`).
13. Make sure you're logged in to the Mac App Store.  You probably are, if you enabled iCloud during first login.
14. Run this repo, e.g.:

        ansible-playbook site.yaml -l dale -K


# Things Not Automated

* Set firmware password
* Set up accounts: admin at install, then regular user after
* Allow regular user account to sudo with file in `/etc/sudoers.d`
* Initial virtualenv and Ansible install
* Give Terminal and/or iTerm 2 "Full Disk Access" to allow it to read things like Mail.app's preferences file (solution courtesy https://github.com/mathiasbynens/dotfiles/issues/849)
* Turning on FileVault
* You need to log into the Mac App Store beforehand
* Text replacements
* iCloud, Google accounts
* DHCP client ID on wireless and other network interfaces
* Set up printer
* Turn a bunch of notifications to "show content only when unlocked"
* Turn off "Spotlight Suggestions" and "Allow Spotlight Suggestions in Look Up", because the preference for the former is a big complicated array that I don't want to script, and I'm not at all sure I know what the preference for the second even is
* Add Unicode and my Russian input methods (this is in `com.apple.HIToolbox` but I didn't feel confident about setting it due to crazy `KeyboardLayout ID` value that I couldn't identify)
* Audacity: They really don't want you automating downloads, so needs to be installed by hand


## Applications

* 1Password
* Adium: Set up account
* Alfred: Turn on auto-expand snippets (not synced)
* Amphetamine: Set to run at login
* Audio Hijack: Add license
* Bartender: License, start at login, position menu items
* BetterTouchTool: Start at login and set up sync (but sync seems broken as of 2019-07-04, so maybe just export/import), hide with Bartender
* Brother iPrint&Scan: Add scanner, make workflow (turn off high compression but leave PDF at normal/middle for compression, turn on smart page size detection and searchable PDF)
* Calibre: Point at library
* Chrome: Sign in, disable consistency flag, set sync preferences, unlock, import extension settings (Auto Delete Cookies, Privacy Badger, uBlock, ViolentMonkey, SessionBuddy, etc.)
* Dash: Turn on sync
* Dropbox: Start at login, login, turn off photo/video syncing
* Firefox: Sync, Little Snitch private rule, extensions, `userChrome.css` (checked in here)
* Google Play Music: Log in
* GPGMail (mail plug-in): License, set preferences
* Hammerspoon: Start at login, grant accessibility, hide with Bartender
* iStat Menus: Start and import settings
* iTunes: Turn on wifi sync, pair with phone, turn off automatic syncing, manually sync music
  * **Warning!** When I did this, I got a warning saying that my phone can only sync with one library.  (I don't have a library.)  Then all my audiobooks got deleted.  Should find a better way to do this.
* Little Snitch: Not even installed, do it all yourself---**installer will force reboot**
* Loopback: Add license
* Mail.app: Enable mail bundles (can't find any plist where these are enabled)
* Moom: License, start at login, hide with Bartender
* OneNote: Sign in
* Parallels: Grant various permissions at first run, install license, copy over VMs
* PDFPenPro: License
* QuoteFix (mail plug-in): Set preferences
* Safari: Install extensions (AdGuard and sVim currently)
* ScreenFlow: License
* Signal: Link to phone
* Steam: Log in, set not to start at login
* Textual: Add license, configure Freenode, including nick, auth, auto-reconnect settings, connect commands, +i on connect
* Tunnelblick: All configuration
* Witch: Enable, license

Special shout out to the Mozilla Firefox team who make a great browser but who don't give me any sane way to figure out what the default user profile directory is, if any.  *Super* frustrating day, that was.


### Textual

Connect commands:

```
/timer 20 1 /quote nickserv ghost dale
/timer 25 1 /nick dale
```


# Notes

* A reboot (or maybe just log out and back in, but reboot to be on the safe side) will be necessary after many of the changes here, particularly the changes in the `macos_system` and `macos_prefs` roles.  I *suspect* that not rebooting **promptly** after some of these changes are made will result in said changes being reverted, especially if you go noodling about in preferences dialogs or System Preferences between Ansible's changes and when you reboot.


# Hardening Guides I Liked

* https://github.com/ernw/hardening/blob/master/operating_system/osx/10.14/ERNW_Hardening_OS_X_Mojave.md
* https://github.com/drduh/macOS-Security-and-Privacy-Guide
* https://blog.bejarano.io/hardening-macos.html
* http://docs.hardentheworld.org/OS/MacOS_10.12_Sierra/index.html

There are also some interesting utilities available at <https://eclecticlight.co/downloads/> and <https://objective-see.com/>.
