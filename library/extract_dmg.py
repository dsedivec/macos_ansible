#!/usr/bin/python

# Copyright: (c) 2018, Dale Sedivec <dale@codefu.org>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: extract_dmg

short_description: Extract some files from a DMG

version_added: "2.8"

description:
    - "Extract some files from a DMG."

options:
    src:
        description:
            - Path or URL to the DMG file.
        required: true
    dest:
        description:
            - Local path where the file(s) from the DMG should be
              copied to.  If this value ends with a slash, or if
              regexp matches more than one file, this is expected to
              be a directory, and in this case the directory will be
              created if necessary.  If only a single regular file is
              matched by regexp, and the dest path does not currently
              exist, the file will be copied to the path specified by
              dest.
        required: true
    regexp:
        description:
            - Regular expression for files to be copied.  Will be
              matched against the path of each file in the DMG,
              relative to the root of the DMG (so the paths do not
              start with a slash).  If a directory matches this
              pattern, the entire directory will be copied to the
              destination.
        required: true
    creates:
        description:
            - Specifies files created by this task.  May be a single
              string or a list.  Specifications are globs (processed
              by python's glob module).  All specifications in the
              list must match at least one file in order for this task
              to be skipped.
        required: false

author:
    - Dale Sedivec (@dsedivec)
"""

EXAMPLES = """
TBD
"""

RETURN = """
TBD
"""

# fmt: off

import atexit
import glob
import os
import os.path
import plistlib
import re
import shutil

from ansible.module_utils import urls
from ansible.module_utils.basic import AnsibleModule

# fmt: on


def is_url(string):
    return re.search(r"(?i)^[a-z]+://", string)


def register_hdiutil_detach_clean_up(module, mount_point):
    def clean_up():
        module.run_command(["hdiutil", "detach", mount_point])

    atexit.register(clean_up)


def mount_dmg(module, path, agree_eulas=None):
    # "IDME" seems to be something that could happen automatically
    # when mounting a disk image.  I don't think anyone uses it, and
    # it's been disabled by default since forever.  Still, for
    # security reasons, and because Homebrew does it, I explicitly
    # disable it here.
    _, stdout, _ = module.run_command(
        [
            "hdiutil",
            "attach",
            "-plist",
            "-readonly",
            "-noidme",
            "-nobrowse",
            path,
        ],
        check_rc=True,
        data="qy\n" if agree_eulas else "",
    )
    match = re.search(r"^<\?xml", stdout, re.M)
    plist_xml = stdout[match.start() :]
    plist = plistlib.loads(plist_xml.encode("utf-8"))
    any_device = None
    mount_point = None
    for entity in plist["system-entities"]:
        if "mount-point" in entity:
            if mount_point:
                raise Exception(
                    (
                        "I don't know what to do with DMG that has"
                        " multiple mount points"
                    )
                )
            mount_point = entity["mount-point"]
            # Note that, at least on my recent-ish macOS,
            # detaching one mount point detaches the whole DMG, if
            # I'm reading hdiutil(1) correctly.
            register_hdiutil_detach_clean_up(module, mount_point)
        elif not any_device:
            any_device = entity.get("dev-entry")
    if not mount_point:
        if any_device:
            register_hdiutil_detach_clean_up(module, mount_point)
        raise Exception(
            (
                "Attached disk image but found no mount point"
                " (image may still be attached in some form)"
            )
        )
    module.debug("Mounted DMG at %r" % (mount_point,))
    return mount_point


def run_module():
    module_args = dict(
        src=dict(type="str", required=True),
        dest=dict(type="path", required=True),
        regexp=dict(type="str", required=True),
        creates=dict(type="list", required=False, default=[]),
        agree_eulas=dict(type="bool", required=False, default=False),
        force=dict(type="bool", required=False, default=False),
    )
    module_args.update(urls.url_argument_spec())
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False)
    creates = module.params["creates"]
    if not creates or not all(glob.glob(pat) for pat in creates):
        if is_url(module.params["src"]):
            dmg_path = urls.fetch_file(module, module.params["src"])
        else:
            dmg_path = module.params["src"]
        mount_point = mount_dmg(module, dmg_path, module.params["agree_eulas"])
        to_copy = []
        regexp = re.compile(module.params["regexp"])
        regexp_path_group = regexp.groupindex.get("path")
        for dir_path, dir_names, file_names in os.walk(mount_point):
            for coll, is_dir in ((dir_names, True), (file_names, False)):
                for idx in reversed(range(len(coll))):
                    name = coll[idx]
                    abs_path = os.path.join(dir_path, name)
                    rel_path = os.path.relpath(abs_path, mount_point)
                    match = re.search(module.params["regexp"], rel_path)
                    if match:
                        if regexp_path_group is None:
                            match_path = name
                        else:
                            match_path = match.group(regexp_path_group)
                            if os.path.isabs(match_path):
                                module.fail_json(
                                    msg=(
                                        "path group in regexp is an"
                                        " absolute path, not allowed"
                                    ),
                                    **result
                                )
                        dst_path = os.path.join(
                            module.params["dest"], match_path
                        )
                        to_copy.append((rel_path, abs_path, dst_path, is_dir))
                        if is_dir:
                            del coll[idx]
        files_copied = []
        result["files_copied"] = files_copied
        if module.check_mode:
            for rel_path, _, dst_path, _ in to_copy:
                files_copied.append((rel_path, dst_path))
        else:
            for src_rel_path, src_abs_path, dst_path, is_dir in to_copy:
                if os.path.exists(dst_path):
                    if not module.params["force"]:
                        continue
                    if os.path.isdir(dst_path):
                        shutil.rmtree(dst_path)
                    else:
                        os.unlink(dst_path)
                if is_dir:
                    shutil.copytree(src_abs_path, dst_path)
                else:
                    shutil.copy(src_abs_path, dst_path)
                files_copied.append((src_rel_path, dst_path))
            result["changed"] = bool(files_copied)
        if not files_copied:
            module.fail_json(msg="No files found to install", **result)
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
