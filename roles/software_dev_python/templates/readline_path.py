# Inspired by MacPorts.
import os.path
import sys

gnureadline_install_dir = "{{ software_dev_python_py3_gnureadline_dir }}"
version = "%s.%s" % sys.version_info[:2]
site_packages = os.path.join(
    sys.base_prefix, "lib/python%s/site-packages" % (version,)
)
lib_dynload = os.path.join(
    sys.base_exec_prefix, "lib/python%s/lib-dynload" % (version,)
)
for idx, path in enumerate(sys.path):
    if path in (site_packages, lib_dynload):
        sys.path.insert(idx, gnureadline_install_dir)
        break
