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
import urllib.request
import argparse


def main(argv):
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument("repo")
    parser.add_argument("--regexp", "--regex", "-r", default=r"(?i)\.pkg$")
    args = parser.parse_args(argv[1:])
    logging.info("Fetching %s release information from GitHub", args.repo)
    release_info = json.load(
        urllib.request.urlopen(
            "https://api.github.com/repos/%s/releases/latest" % (args.repo,)
        )
    )
    logging.info("Scanning releases")
    for asset in release_info.get("assets", ()):
        if re.search(args.regexp, asset.get("name", "")) and asset.get(
            "browser_download_url"
        ):
            break
    else:
        raise Exception(
            "%s has no assets matching %r" % (args.repo, args.regexp)
        )
    logging.info("Found release %r", asset["name"])
    pkg_file_name = re.sub(r"[^\w.-]", "_", asset["name"])
    remote_pkg = urllib.request.urlopen(asset["browser_download_url"])
    download_dir = tempfile.mkdtemp()
    try:
        local_pkg_path = os.path.join(download_dir, pkg_file_name)
        with open(local_pkg_path, "wb") as local_pkg:
            shutil.copyfileobj(remote_pkg, local_pkg)
        remote_pkg.close()
        logging.info("Downloaded to %s", local_pkg_path)
        cmd = ["installer", "-pkg", local_pkg_path, "-target", "/"]
        if os.getuid() != 0:
            cmd.insert(0, "sudo")
        logging.info("Running: %r" % (cmd,))
        subprocess.check_call(cmd)
    finally:
        shutil.rmtree(download_dir, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv)
