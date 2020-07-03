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
module: dl_and_extract

short_description: Download something you can extract some files from

version_added: "2.8"

description:
    - "TBD"

options: TBD

extends_documentation_fragment: TBD

author:
    - Dale Sedivec (@dsedivec)
"""

EXAMPLES = "TBD"

RETURN = "sure let me just get that for y---lol I mean TBD"

# fmt: off

import os
import os.path
import pathlib
import re
import shutil
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_file

# fmt: on


def run_module():
    module_args = dict(
        url=dict(type="str", required="true"),
        dest=dict(type="path", requried="true"),
        regexp=dict(type="str", required=False, default=".*"),
        skip_macos=dict(type="bool", required=False, default=True),
        creates=dict(type="path", required=False, default=None),
    )
    result = dict(changed=False)
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    params = module.params

    if params["creates"] and os.path.exists(params["creates"]):
        module.exit_json(msg="%s already exists", changed=False)

    arch_path = fetch_file(module, params["url"])
    with tempfile.TemporaryDirectory() as temp_dir:
        for cmd in (
            ["unzip", arch_path],
            ["tar", "xf", arch_path],
            ["gtar", "xf", arch_path],
            ["7z", "x", arch_path],
            ["7za", "x", arch_path],
        ):
            rc, *_ = module.run_command(cmd, cwd=temp_dir)
            if rc == 0:
                break
        else:
            module.fail_json(
                msg="Don't know how to extract the archive", **result
            )

        dest_path = pathlib.Path(params["dest"])
        regexp = re.compile(params["regexp"])
        temp_path = pathlib.Path(temp_dir)
        copied = []
        for dir_path, subdir_names, file_names in os.walk(temp_dir):
            rel_dir_path = pathlib.Path(dir_path).relative_to(temp_path)
            for idx in reversed(range(len(subdir_names))):
                subdir_name = subdir_names[idx]
                if (
                    subdir_name == "__MACOSX"
                    and dir_path == temp_dir
                    and params["skip_macos"]
                ):
                    del subdir_names[idx]
                    continue
                subdir_path = rel_dir_path / subdir_names[idx]
                match = regexp.search(str(subdir_path))
                if match:
                    try:
                        match_name = match.group("dest")
                    except IndexError:
                        match_name = match.group(0)
                    if not match_name:
                        module.fail_json(
                            msg=(
                                "regexp match on %s matched the empty string"
                                % (subdir_path,)
                            )
                        )
                    copy_from = temp_path / subdir_path
                    copy_to = dest_path / match_name
                    if not module.check_mode:
                        shutil.copytree(copy_from, copy_to)
                    # Don't need to traverse this directory.
                    del subdir_names[idx]
                    copied.append(
                        {"src": str(subdir_path), "dest": str(copy_to)}
                    )
            for file_name in file_names:
                file_path = rel_dir_path / file_name
                match = regexp.search(str(file_path))
                if match:
                    try:
                        match_name = match.group("dest")
                    except IndexError:
                        match_name = match.group(0)
                    if not match_name:
                        module.fail_json(
                            msg=(
                                "regexp match on %s matched the empty string"
                                % (file_path,)
                            )
                        )
                    copy_from = temp_path / file_path
                    copy_to = dest_path / match_name
                    if not module.check_mode:
                        shutil.copy2(
                            temp_path / file_path, dest_path / file_path
                        )
                    copied.append({"src": str(file_path), "dest": str(copy_to)})
    result.update(copied=copied, changed=bool(copied))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
