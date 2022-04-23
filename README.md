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



# Notes to Self: Before Reinstall

* Export some browser extension settings, since they're not in the cloud (WTF) and they can be hard to find and/or re-import from the browser profile directory:
  * uBlock Origin
  * Privacy Badger
  * HTTPS Everywhere
  * Cookie Auto-delete
  * CanvasBlocker
  * Dark Reader
  * RES
  * Tree Style Tabs
  * Vimium
  * Temporary Containers
  * Auto Tab Discard
  * GreaseMonkey?  Not sure if this is necessary
* Export your iStat Menus configuration
* Maybe check that you have all your repositories committed up, like dotfiles and dot-emacs-d
* Save off `port echo requested`, `brew list`, and `mas list`
* Make CCC backup


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
8. Activate that virtual environment
9. `pip install --upgrade pip`
10. `pip install ansible`
11. `ssh-keygen -t ed25519 -C ...` and follow the prompts.
12. `ssh-add`
13. Upload new key to GitHub.
14. Clone this repo (`macos_ansible`).
15. Make sure you're logged in to the Mac App Store.  You probably are, if you enabled iCloud during first login.
16. Run this repo, e.g.:

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
* Turn off "Siri Suggestions" in Spotlight preferences, because I don't know where this preference is
* Add Unicode and my Russian input methods (this is in `com.apple.HIToolbox` but I didn't feel confident about setting it due to crazy `KeyboardLayout ID` value that I couldn't identify)
* Audacity: They really don't want you automating downloads, so needs to be installed by hand
* Probably restore a bunch files, documents, desktop, etc.


## Applications

* 1Password: Add vaults
* Adium: Set up account
* Alfred: Turn on auto-expand snippets (not synced)
* AltTab: Start at boot, give permissions
* Amphetamine: Set to run at login
* Audio Hijack: Add license
* Bartender: License, start at login, position menu items
* BetterTouchTool: Start at login and set up sync (but sync seems broken as of 2019-07-04, so maybe just export/import), hide with Bartender
* Brother iPrint&Scan: Add scanner, make workflow (turn off high compression but leave PDF at normal/middle for compression, turn on smart page size detection and searchable PDF)
* Calibre: Point at library
* Chrome: Sign in, disable consistency flag, set sync preferences, unlock, import extension settings (Auto Delete Cookies, Privacy Badger, uBlock, ViolentMonkey, SessionBuddy, etc.)
* Dash: Turn on sync
* Dropbox: Start at login, login, turn off photo/video syncing
* Firefox: Sync, Little Snitch private rule, extensions, `userChrome.css` (checked in here), open up the container extension and tell it to start syncing, tell RES to start syncing/backing up to Dropbox
* Google Play Music: Log in
* Hammerspoon: Start at login, grant accessibility, hide with Bartender
* iStat Menus: Start and import settings
* iTunes: Turn on wifi sync, pair with phone, turn off automatic syncing, manually sync music
  * **Warning!** When I did this, I got a warning saying that my phone can only sync with one library.  (I don't have a library.)  Then all my audiobooks got deleted.  Should find a better way to do this.
* Little Snitch: Not even installed, do it all yourself---**installer will force reboot**
* Loopback: Add license
* Mail.app: Enable accounts, enable mail bundles (can't find any plist where these are enabled), set up junk mail (done by rules, mostly), enable mail rules (they come with if you imported a Mail.app directory from another machine), copy any mail over
* Moom: License, start at login, hide with Bartender
* OneNote: Sign in
* Parallels: Grant various permissions at first run, install license, copy over VMs
* PDFPenPro: License
* Safari: Install extensions (AdGuard and sVim currently)
* ScreenFlow: License
* Sketch: License, install [macOS library][sketch_macos]
* Signal: Link to phone
* Steam: Log in, set not to start at login
* Textual: Add license, configure Freenode, including nick, auth, auto-reconnect settings, connect commands, +i on connect
* Tunnelblick: All configuration

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
