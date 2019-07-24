# Inspired by MacPorts.
import os.path
import sys

my_dir = os.path.abspath(os.path.dirname(__file__))
gnureadline = None
with open(os.path.join(my_dir, "easy-install.pth")) as easy_install:
    for line in easy_install:
        if line.startswith("./gnureadline"):
            gnureadline = os.path.normpath(os.path.join(my_dir, line.strip()))
            break
if gnureadline:
    version = "%s.%s" % sys.version_info[:2]
    site_packages = os.path.join(
        sys.base_prefix, "lib/python%s/site-packages" % (version,)
    )
    lib_dynload = os.path.join(
        sys.base_exec_prefix, "lib/python%s/lib-dynload" % (version,)
    )
    for idx, path in enumerate(sys.path):
        if path in (site_packages, lib_dynload):
            sys.path.insert(idx, gnureadline)
            break
