#!/usr/bin/env python3

import pathlib
import plistlib
import subprocess
import re


def main():
    for mail_app in [
        pathlib.Path(path_str)
        for path_str in (
            "/Applications/Mail.app",
            "/System/Applications/Mail.app",
        )
    ]:
        if mail_app.is_dir():
            break
    else:
        raise Exception("Can't find Mail.app")
    with open(mail_app / "Contents/Info.plist", "rb") as info_plist_stream:
        mail_app_info_plist = plistlib.load(info_plist_stream)
    try:
        expected_uuid = mail_app_info_plist["PluginCompatibilityUUID"]
    except KeyError:
        raise Exception("No PluginCompatibilityUUID in Mail.app's Info.plist")
    print(f"This Mail.app wants UUID {expected_uuid}")
    full_version = subprocess.check_output(
        ["sw_vers", "-productVersion"], text=True
    ).splitlines()[0]
    major_minor_vers = re.sub(r"^(\d+\.\d+).*", r"\1", full_version)
    if not re.search(r"^\d+\.\d+$", major_minor_vers):
        raise Exception(f"Could not parse macOS version from {full_version!r}")
    print(f"This is macOS {major_minor_vers}")
    bundle_compat_key = f"Supported{major_minor_vers}PluginCompatibilityUUIDs"
    print(f"Bundle compatibility key is {bundle_compat_key}")
    num_updated = 0
    for bundle_dir in (
        pathlib.Path("~/Library/Mail/Bundles").expanduser().iterdir()
    ):
        bundle_info_plist_path = bundle_dir / "Contents/Info.plist"
        if not bundle_info_plist_path.is_file():
            print(f"Skipping {bundle_dir}")
            continue
        print(f"Checking {bundle_info_plist_path}")
        with open(bundle_info_plist_path, "rb") as bundle_info_plist_stream:
            bundle_info_plist = plistlib.load(bundle_info_plist_stream)
        if (
            bundle_compat_key not in bundle_info_plist
            or expected_uuid not in bundle_info_plist[bundle_compat_key]
        ):
            print(f"Updating {bundle_info_plist_path} with current UUID")
            supported_uuids = bundle_info_plist.setdefault(
                bundle_compat_key, []
            )
            supported_uuids.append(expected_uuid)
            with open(bundle_info_plist_path, "wb") as bundle_info_plist_stream:
                plistlib.dump(bundle_info_plist, bundle_info_plist_stream)
            num_updated += 1
    print(f"Updated {num_updated} bundle(s)")


if __name__ == "__main__":
    main()
