#!/usr/bin/env python3

import json
import logging
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request


def main(argv):
    logging.basicConfig(level=logging.INFO)
    logging.info("Fetching macOS version")
    output = subprocess.check_output(["sw_vers", "-productVersion"], text=True)
    match = re.search(r"^\d+\.\d+", output)
    macos_version = match.group(0)
    macos_major = int(macos_version.split('.', 1)[0])
    if macos_major >= 11:
        # macOS is just 11, 12, etc. starting with Big Sur.
        # At least, according to MacPorts it is.
        macos_version = str(macos_major)
    logging.info("macOS version is %r", macos_version)
    logging.info("Fetching MacPorts release information from GitHub")
    release_info = json.load(
        urllib.request.urlopen(
            "https://api.github.com/repos/macports/macports-base/releases/latest"
        )
    )
    version_regexp = re.compile(
        r"^MacPorts-.*-%s-\w+.pkg$" % (re.escape(macos_version),)
    )
    logging.info("Scanning MacPorts releases")
    for asset in release_info["assets"]:
        if "name" in asset and version_regexp.search(asset["name"]):
            break
    else:
        raise Exception("Can't find MacPorts release")
    pkg_file_name = asset["name"]
    logging.info("Found MacPorts release %r", pkg_file_name)
    if "/" in pkg_file_name:
        raise Exception("Illegal file name %r" % (pkg_file_name))
    remote_pkg = urllib.request.urlopen(asset["browser_download_url"])
    with tempfile.TemporaryDirectory() as download_dir:
        local_pkg_path = os.path.join(download_dir, pkg_file_name)
        with open(local_pkg_path, "wb") as local_pkg:
            shutil.copyfileobj(remote_pkg, local_pkg)
        remote_pkg.close()
        logging.info("Downloaded MacPorts pkg")
        cmd = ["installer", "-pkg", local_pkg_path, "-target", "/"]
        if os.getuid() != 0:
            cmd.insert(0, "sudo")
        logging.info("Running: %r" % (cmd,))
        subprocess.check_call(cmd)


if __name__ == "__main__":
    main(sys.argv)
