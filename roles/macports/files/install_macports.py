#!/usr/bin/env python

import json
import logging
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib


def main(argv):
    logging.basicConfig(level=logging.INFO)
    logging.info("Fetching macOS version")
    output = subprocess.check_output(["sw_vers", "-productVersion"], text=True)
    match = re.search(r"^\d+\.\d+", output)
    macos_version = match.group(0)
    logging.info("macOS version is %r", macos_version)
    logging.info("Fetching MacPorts release information from GitHub")
    release_info = json.load(
        urllib.urlopen(
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
    remote_pkg = urllib.urlopen(asset["browser_download_url"])
    download_dir = tempfile.mkdtemp()
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
    shutil.rmtree(download_dir)


if __name__ == "__main__":
    main(sys.argv)
