#!/usr/bin/env python3

import argparse
import os
import os.path
import subprocess
import sys


def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument("dest_dir")
    args = parser.parse_args(argv[1:])
    go_dir = subprocess.check_output("go env GOPATH".split(), text=True).rstrip("\r\n")
    if not go_dir:
        raise Exception("Can't read GOPATH")
    environ = os.environ.copy()
    # Not sure if this is right.  See
    # https://github.com/rfjakob/gocryptfs/issues/553.
    environ["GO111MODULE"] = "auto"
    subprocess.check_call("go get -d github.com/rfjakob/gocryptfs".split(), env=environ)
    gocryptfs_src_dir = os.path.join(go_dir, "src/github.com/rfjakob/gocryptfs")
    subprocess.check_call("git pull --ff-only".split(), cwd=gocryptfs_src_dir)
    subprocess.check_call("./build.bash", cwd=gocryptfs_src_dir)
    gocryptfs_bin = os.path.join(go_dir, "bin/gocryptfs")
    if not os.access(gocryptfs_bin, os.X_OK):
        raise Exception("gocryptfs at %r missing or non-executable" % (gocryptfs_bin,))
    os.symlink(
        os.path.relpath(gocryptfs_bin, args.dest_dir),
        os.path.join(args.dest_dir, "gocryptfs"),
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv) or 0)
