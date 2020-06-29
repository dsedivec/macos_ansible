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
module: osx_auth_policy_db

short_description: Update the authorization policy database on macOS

version_added: "2.8"

description:
    - "Update the authorization policy database on macOS."

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

import plistlib
import subprocess

from ansible.module_utils.basic import AnsibleModule

# fmt: on


def run_module():
    module_args = dict(
        right=dict(type="str", default="system.preferences"),
        key=dict(type="str", required=True),
        type=dict(
            type="str",
            choices=(
                "string",
                "str",
                "boolean",
                "bool",
                "float",
                "real",
                "integer",
                "int",
            ),
        ),
        value=dict(type="raw", required=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    desired_value = module.params["value"]
    desired_value_type = module.params.get("type")
    if desired_value_type in ("string", "str"):
        if not isinstance(desired_value, str):
            desired_value = str(desired_value)
    elif desired_value_type in ("boolean", "bool"):
        desired_value = module.boolean(desired_value)
    elif desired_value_type in ("float", "real"):
        desired_value = float(desired_value)
    elif desired_value_type in ("integer", "int"):
        desired_value = int(desired_value)
    plist_xml = subprocess.check_output(
        ["security", "authorizationdb", "read", module.params["right"]]
    )
    plist = plistlib.loads(plist_xml)
    key = module.params["key"]
    try:
        current_value = plist[key]
    except KeyError:
        module.fail_json(
            msg=("Key %r not in plist for %r" % (key, module.params["right"]))
        )
    result = {
        "old_value": current_value,
        "new_value": desired_value,
        "changed": (current_value != desired_value),
    }
    if result["changed"] and not module.check_mode:
        plist[key] = desired_value
        security = subprocess.Popen(
            ["security", "authorizationdb", "write", module.params["right"]],
            stdin=subprocess.PIPE,
        )
        security.communicate(plistlib.dumps(plist))
        if security.returncode != 0:
            module.fail_json(
                msg=(
                    "security authorizationdb write returned %r"
                    % (security.returncode,)
                )
            )
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
