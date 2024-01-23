---
title: Ansible Automated Setup of macOS
---

# Introduction

This is my somewhat untested, haphazard, but hopefully useful automated setup of some of my macOS software and settings.

I have broken down and am now using Homebrew by default.

Documentation here is very far from complete.


# Use of Roles

The division of what action(s) go into which role(s) is probably not super-consistent.  I have tried to make some logical and/or useful divisions.

Role `other_software` tends to be for software that I want to use as a "normal user" rather than a developer, per se.  Lots of my GUI packages get stuffed in here.  Truth be told, it may have become somewhat of a dumping group after realizing that I dread making lots and lots of fine-grained roles for software installation.  At least I've broken the things to be installed out into some variables.  This may all get refined later.

`software_dev_*` roles tend to be for "development" in particular languages/activities.

Other `software_*` roles tend to be for specific software that other role(s) will need to depend on.  For example, lots of stuff needs Homebrew installed first, so Homebrew gets it own `homebrew` role that others can depend on.

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
* Save off `brew list` and `mas list`
* Save off `ls /Applications ~/Applications` (particularly since `mas list` doesn't seem to be complete as of this writing)
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
6. `ssh-keygen -t ed25519 -C ...` and follow the prompts.
7. `ssh-add`
8. Upload new key to GitHub.
9. Clone this repo (`macos_ansible`).
10. Run `/usr/bin/python3 -V` and let Xcode command line tools install.
11. Run `/usr/bin/python3 -m venv ~/.vpy/system-ansible` to install a virtual environment.
12. Activate that virtual environment
13. `pip install --upgrade pip`
14. `pip install ansible`
15. Make sure you're logged in to the Mac App Store.  You probably are, if you enabled iCloud during first login.
16. Run this repo, e.g.:

        ansible-playbook site.yaml -l dale -K


# After Install

* Give iTerm2 full disk access
* Get 1Password set up (if you have an old machine, follow their instructions for setting up on the new machine because it's easier)
* At work you probably want OneDrive right away
* You may want to fire up Ubuntu in Docker (don't forget `--privileged`) to use FUSE to mount up the Restic repo
* Probably prioritize getting Firefox up and running (e.g. so you can log into sites like GitHub and set up your new host key)
* Alfred before you go nuts
* AltTab for similar reasons, maybe restore prefs from backup?


# Things Not Automated

* Set firmware password
* Screen saver lock timeout: You can set this with `sysadminctl`, but it requires the user's password on stdin, which seems a bit problematic, so I haven't bothered to automate it
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
* Hammerspoon: Start at login, grant accessibility, hide with Bartender
* iStat Menus: Start and import settings
* Little Snitch: Not even installed, do it all yourself---**installer will force reboot**
* Loopback: Add license
* Mail.app: Enable accounts, enable mail bundles (can't find any plist where these are enabled), set up junk mail (done by rules, mostly), enable mail rules (they come with if you imported a Mail.app directory from another machine), copy any mail over
* OneNote: Sign in
* Safari: Install extensions (AdGuard and sVim currently)
* Signal: Link to phone
* Steam: Log in, set not to start at login
* Tunnelblick: All configuration

Special shout out to the Mozilla Firefox team who make a great browser but who don't give me any sane way to figure out what the default user profile directory is, if any.  *Super* frustrating day, that was.


# Notes

* A reboot (or maybe just log out and back in, but reboot to be on the safe side) will be necessary after many of the changes here, particularly the changes in the `macos_system` and `macos_prefs` roles.  I *suspect* that not rebooting **promptly** after some of these changes are made will result in said changes being reverted, especially if you go noodling about in preferences dialogs or System Preferences between Ansible's changes and when you reboot.


# Hardening Guides I Liked

* https://github.com/ernw/hardening/blob/master/operating_system/osx/10.14/ERNW_Hardening_OS_X_Mojave.md
* https://github.com/drduh/macOS-Security-and-Privacy-Guide
* https://blog.bejarano.io/hardening-macos.html
* http://docs.hardentheworld.org/OS/MacOS_10.12_Sierra/index.html

There are also some interesting utilities available at <https://eclecticlight.co/downloads/> and <https://objective-see.com/>.
