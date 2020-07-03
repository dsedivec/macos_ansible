#!/usr/bin/env python


import argparse
import json
import logging as _logging
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ARCHIVE_REGEXP = r"(?i)\.(zip|tar(\.(gz|bz2))?|t(gz|bz2))$"


logger = _logging.getLogger(__name__)


def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--download-regexp", "--dre", default=ARCHIVE_REGEXP)
    parser.add_argument(
        "--font-regexp", "--fre", default=r"(?i)\.(tt[cf]|otf)$"
    )
    parser.add_argument(
        "--dest-dir", "-d", default=os.path.expanduser("~/Library/Fonts")
    )
    parser.add_argument("repo")
    args = parser.parse_args(argv[1:])
    if args.debug:
        logger.setLevel(_logging.DEBUG)
    logger.info("Fetching %s release information from GitHub", args.repo)
    release_info = json.load(
        urllib.request.urlopen(
            "https://api.github.com/repos/%s/releases/latest" % (args.repo,)
        )
    )
    logger.info("Scanning releases")
    for asset in release_info.get("assets", ()):
        if re.search(args.download_regexp, asset.get("name", "")) and asset.get(
            "browser_download_url"
        ):
            break
    else:
        raise Exception(
            "%s has no assets matching %r" % (args.repo, args.download_regexp)
        )
    logger.info("Found release %r", asset["name"])
    local_file_name = re.sub(r"[^\w.-]", "_", asset["name"])
    remote_file = urllib.request.urlopen(asset["browser_download_url"])
    download_dir = tempfile.mkdtemp()
    try:
        local_file_path = os.path.join(download_dir, local_file_name)
        with open(local_file_path, "wb") as local_file:
            shutil.copyfileobj(remote_file, local_file)
        remote_file.close()
        logger.info("Downloaded to %s", local_file_path)
        match = re.search(ARCHIVE_REGEXP, asset["name"])
        if not match:
            raise Exception(
                "Cannot determine archive type for %r" % (asset["name"],)
            )
        extract_dir = os.path.join(download_dir, "extract")
        os.mkdir(extract_dir)
        ext = match.group(1).lower()
        if ext.startswith("z"):
            subprocess.check_call(["unzip", "-d", extract_dir, local_file_path])
        elif ext.startswith("t"):
            subprocess.check_call(
                ["tar", "-C", extract_dir, "-xf", local_file_path]
            )
        else:
            raise Exception("No extract command for extension %r" % (ext,))
        installed = False
        for dir_path, _, file_names in os.walk(extract_dir):
            for file_name in file_names:
                file_path = os.path.join(dir_path, file_name)
                logger.debug("Considering %r against font RE", file_path)
                if re.search(args.font_regexp, file_path):
                    logger.info("Installing %s", file_name)
                    shutil.copy(file_path, args.dest_dir)
                    installed = True
        if not installed:
            raise Exception("No fonts found matching %r" % (args.font_regexp,))
    finally:
        shutil.rmtree(download_dir, ignore_errors=True)


if __name__ == "__main__":
    _logging.basicConfig(level=_logging.INFO)
    main(sys.argv)
