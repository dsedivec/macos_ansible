# Things Not Automated

* Turning on FileVault
* You need to log into the Mac App Store beforehand

# Notes

* A reboot (or maybe just log out and back in, but reboot to be on the safe side) will be necessary after many of the changes here, particularly the changes in the `macos_system` and `macos_prefs` roles.  I *suspect* that not rebooting **promptly** after some of these changes can cause them to be reverted, especially if you go noodling about in preferences dialogs or System Preferences between Ansible's changes and when you reboot.
