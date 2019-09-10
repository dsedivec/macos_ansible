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
module: osx_group_member

short_description: Add or remove users from groups on macOS

version_added: "2.8"

description:
    - "Add or remove users from groups on macOS.""

options: TBD

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

import os
import subprocess

from ansible.module_utils.basic import AnsibleModule

# fmt: on


def run_module():
    module_args = dict(
        group=dict(type="str", required=True),
        user=dict(type="str", required=True),
        state=dict(type="str", choices=("present", "absent")),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    should_be_in_group = module.params["state"] == "present"
    checkmember_rc = subprocess.call(
        [
            "dseditgroup",
            "-o",
            "checkmember",
            "-m",
            module.params["user"],
            module.params["group"],
        ]
    )
    if checkmember_rc == 0:
        is_in_group = True
    elif checkmember_rc == os.EX_NOUSER:
        is_in_group = False
    elif checkmember_rc == os.EX_USAGE:
        module.fail_json(
            msg=(
                "dseditgroup says group %r does not exist (exited %r)"
                % (module.params["group"], checkmember_rc)
            )
        )
    else:
        module.fail_json(
            msg="dseditgroup -o checkmember exited %r" % (checkmember_rc,)
        )
    result = dict(changed=should_be_in_group != is_in_group)
    if result["changed"] and not module.check_mode:
        subprocess.check_call(
            [
                "dseditgroup",
                "-o",
                "edit",
                "-t",
                "user",
                "-a" if should_be_in_group else "-d",
                module.params["user"],
                module.params["group"],
            ]
        )
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
