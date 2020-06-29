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
module: pmset

short_description: Modify power settings on macOS

version_added: "2.8"

description:
    - "Modify power settings on macOS via the pmset command."

options: TBD

author:
    - Dale Sedivec (@dsedivec)
"""

EXAMPLES = """
"""

RETURN = """
"""

# fmt: off

import subprocess

from ansible.module_utils.basic import AnsibleModule

# fmt: on


def run_module():
    module_args = dict(
        # I can't seem to get UPS output from "pmset -g custom" so I'm
        # not supporting it for now.  I need a way to get the current
        # UPS settings.  (Maybe I could trawl a plist somewhere...)
        #
        # Lack of UPS is also why I'm not supporting "all".
        type=dict(
            type="str",
            choices=("battery", "charger", "both"),
            required=False,
            default="all",
        ),
        name=dict(type="str", required=True),
        value=dict(type="str", required=True),
    )
    result = dict(changed=False, messages=[])
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    current_settings = {"battery": {}, "charger": {}}
    reading_type = None
    for line in subprocess.check_output(
        ["pmset", "-g", "custom"], text=True
    ).splitlines():
        line = line.strip()
        if line == "Battery Power:":
            reading_type = "battery"
        elif line == "AC Power:":
            reading_type = "charger"
        elif reading_type is None:
            module.fail_json(
                msg=f"Got line={line!r} before reading power source line",
                **result,
            )
        else:
            setting, value = line.split(None, 1)
            current_settings[reading_type][setting] = value
    types_to_check = []
    if module.params["type"] in ("battery", "both"):
        types_to_check.append("battery")
    if module.params["type"] in ("charger", "both"):
        types_to_check.append("charger")
    setting_name = module.params["name"]
    desired_value = module.params["value"]
    if module.check_mode:
        verb_phrase = "Would change"
    else:
        verb_phrase = "Changed"
    for setting_type in types_to_check:
        current_value = current_settings[setting_type].get(setting_name)
        if current_value != desired_value:
            if not module.check_mode:
                subprocess.check_call(
                    [
                        "pmset",
                        "-%s" % (setting_type[0],),
                        setting_name,
                        desired_value,
                    ]
                )
            result["messages"].append(
                (
                    "%s %r for %r from %r to %r."
                    % (
                        verb_phrase,
                        setting_name,
                        setting_type,
                        current_value,
                        desired_value,
                    )
                )
            )
            result["changed"] = True
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
