#!/usr/bin/env python3

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import datetime
import json
import plistlib
import subprocess
import sys


class PlistJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, plistlib.Data):
            return "<Plist data>"
        elif isinstance(obj, bytes):
            return "<bytes>"
        elif isinstance(obj, datetime.datetime):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument("plist_file")
    args = parser.parse_args(argv[1:])
    with open(args.plist_file, "rb") as plist_stream:
        plist = plistlib.load(plist_stream)
    json.dump(
        plist,
        sys.stdout,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
        cls=PlistJSONEncoder,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv)
