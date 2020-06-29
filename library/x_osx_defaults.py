#!/usr/bin/python

# Copyright: (c) 2018, Dale Sedivec <dale@codefu.org>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: alt_defaults

short_description: Modify macOS preferences

version_added: "2.8"

description:
    - Modify macOS preferences, with some features not available in
      the built-in osx_defaults module.

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

import collections
import copy
import datetime
import re

import CoreFoundation as CF
from PyObjCTools import Conversion
from ansible.module_utils.basic import AnsibleModule

# fmt: on


class ModuleFail(Exception):
    def __init__(self, msg, **kwargs):
        Exception.__init__(self, msg)
        self.result = kwargs


def maybe_convert_key_to_string(key):
    if isinstance(key, bool):
        key = int(key)
    if isinstance(key, (float, int)):
        key = str(key)
    return key


SENTINEL = object()


def merge_dicts(src, dst):
    changed = False
    for key, dst_value in src.iteritems():
        src_value = src.get(key, SENTINEL)
        if isinstance(dst_value, dict) and isinstance(src_value, dict):
            changed = merge_dicts(src_value, dst_value) or changed
        elif src_value != dst_value:
            src[key] = dst_value
            changed = True
    return changed


Operation = collections.namedtuple(
    "Operation",
    "state key_list types new_value check_type add_merge dict_create",
)


def set_value(op, key_idx, container):
    key = op.key_list[key_idx]
    is_last_key = key_idx == (len(op.key_list) - 1)
    if isinstance(container, list) and isinstance(key, str) and key.isdigit():
        op.key_list[key_idx] = key = int(key)
    try:
        cur_value = container[key]
    except (KeyError, TypeError, IndexError):
        container_is_dict = isinstance(container, dict)
        if container_is_dict and not isinstance(key, str):
            # If your key doesn't exist as its current non-string
            # type, but it does exist in its string incarnation, we'll
            # gladly use that.
            str_key = maybe_convert_key_to_string(key)
            if str_key in container:
                op.key_list[key_idx] = str_key
                return set_value(op, key_idx, container)
        if is_last_key:
            cur_value = None
        elif container_is_dict and op.dict_create:
            container[key] = cur_value = {}
        else:
            raise ModuleFail(
                "Cannot find key %r" % (op.key_list[: key_idx + 1],)
            )
    if not is_last_key:
        return set_value(op, key_idx + 1, cur_value)
    else:
        changed = False
        if (
            cur_value is not None
            and op.check_type
            and not isinstance(cur_value, op.types)
        ):
            raise ModuleFail(
                (
                    "Expected one of types (%s) but found %r instead"
                    % (
                        ", ".join(cls.__name__ for cls in op.types),
                        type(cur_value).__name__,
                    )
                )
            )
        if op.state == "absent":
            # You'll never get None out of a plist **as far as I
            # know**.  Instead, if you see None, that means we were
            # requested to delete a top-level preference that doesn't
            # exist.
            if cur_value is None:
                assert len(op.key_list) == 1
            else:
                del container[key]
                changed = True
        else:
            assert op.state == "present", repr(op.state)
            if op.add_merge:
                if isinstance(container, list):
                    if op.new_value not in container:
                        container.append(op.new_value)
                        changed = True
                elif isinstance(container, dict):
                    if not isinstance(op.new_value, dict):
                        raise ModuleFail("Cannot merge provided non-dict value")
                    changed = merge_dicts(op.new_value, container)
            elif cur_value != op.new_value:
                container[key] = op.new_value
                changed = True
        return changed


PREF_VALUE_TYPES = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "bool": bool,
    "boolean": bool,
    "date": datetime.datetime,
    "array": list,
    "dict": dict,
}


# From datetime docs.

ZERO = datetime.timedelta(0)


class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


class FixedOffset(datetime.tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO


def parse_time_stamp(time_stamp_str):
    # Based on YAML spec, but also my experience with time stamps seen
    # in the wild.  Mostly YAML spec though.  See
    # https://yaml.org/type/timestamp.html.
    match = re.search(
        r"""(?x)
        ^\s*
        (?P<date>\d{4}-\d{1,2}-\d{1,2})
        (?:
            (?:[Tt]|\s+)
            (?P<time>
                \d{1,2}:\d{2}
                (?: \d{2}(?: \.\d*)?)?
            )
            \s*
            (?P<zone>
                  Z
                | [-+]\d{1,2}(?: :\d{2})?
            )
        )?
        \s*$
        """,
        time_stamp_str,
    )
    if match:
        date = match.group("date").split("-")
        args = [int(field) for field in date]
        time = match.group("time")
        if time:
            time = re.split("r[:.]", time)
            assert len(time) in (3, 4), (time_stamp_str, time)
            args.extend(int(field) for field in time[:3])
            if len(time) == 4:
                args.append(int(time[3][:6]))
            else:
                args.append(0)
        zone = match.group("zone")
        if zone == "Z":
            args.append(UTC())
        elif zone:
            zone_fields = zone.split(":")
            assert len(zone_fields) in (1, 2), (time_stamp_str, zone_fields)
            minutes = int(zone_fields[0]) * 60
            if len(zone_fields) == 2:
                minutes += int(zone_fields[0][0] + zone_fields[1])
            args.append(FixedOffset(minutes, zone))
        return datetime.datetime(*args)
    else:
        raise Exception("Cannot parse %r as time stamp" % (time_stamp_str,))


def coerce_to_type(value, cls):
    if isinstance(value, cls):
        return value
    if cls == bool:
        if isinstance(value, (int, float)):
            return bool(value)
        elif isinstance(value, str):
            value = value.lower()
            if value in ("y", "yes", "t", "true", "on"):
                return True
            elif value in ("n", "no", "f", "false", "off"):
                return False
    elif cls in (int, float):
        try:
            return cls(value)
        except (TypeError, ValueError):
            pass
    elif cls == datetime.datetime:
        try:
            return parse_time_stamp(value)
        except Exception:
            pass
    elif cls == str:
        # Converting lists or dicts to strings doesn't make sense in
        # the context of this module.
        if not isinstance(value, (list, dict)):
            try:
                return str(value)
            except Exception:
                pass
    raise ModuleFail("Cannot convert %r to %s" % (value, cls.__name__))


def run_module():
    module_args = dict(
        state=dict(
            type="str",
            choices=("present", "absent"),
            required=False,
            default="present",
        ),
        host=dict(type="str", required=False, default=CF.kCFPreferencesAnyHost),
        user=dict(
            type="str", required=False, default=CF.kCFPreferencesCurrentUser
        ),
        domain=dict(type="str", required=False, default="NSGlobalDomain"),
        key=dict(type="raw", required=True),
        value=dict(type="raw", required=False, default=None),
        add_merge=dict(type="bool", required=False, default=False),
        dict_create=dict(type="bool", required=False, default=False),
        type=dict(type="str", required=False, default=None),
        check_type=dict(type="bool", required=False, default=None),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    result = dict(changed=False)
    params = module.params.copy()
    if params["host"].strip() == "currentHost":
        params["host"] = CF.kCFPreferencesCurrentHost
    elif not params["host"].strip() or params["host"] == "anyHost":
        params["host"] = CF.kCFPreferencesAnyHost
    if not params["user"].strip() or params["user"] == "currentUser":
        params["user"] = CF.kCFPreferencesCurrentUser
    if params["domain"] == "NSGlobalDomain":
        params["domain"] = CF.kCFPreferencesAnyApplication
    key_list = params["key"]
    if type(key_list) != list:
        key_list = [key_list]
    elif len(key_list) < 1:
        module.fail_json(msg="key cannot be an empty list", **result)
    # Copying these into the result to ease debugging.  Note that
    # these may be different than some of the info Ansible prints/puts
    # into the result for you, since it'll be filling in the module's
    # parameters, but the below gives you a bit more information about
    # how this module *parsed* your args.
    for params_key in ("host", "user", "domain"):
        result[params_key] = params[params_key]
    result["key_list"] = key_list

    new_value = params["value"]
    desired_type = params["type"] or None
    if desired_type is not None and desired_type not in PREF_VALUE_TYPES.keys():
        module.fail_json(
            msg=(
                "Type %r invalid, must be one of: %s"
                % (desired_type, ", ".join(PREF_VALUE_TYPES))
            )
        )
    check_type = params["check_type"]
    if desired_type is None:
        if check_type:
            module.fail_json(
                msg="Cannot give check_type=true without providing a type",
                **result
            )
    else:
        desired_type = PREF_VALUE_TYPES[desired_type]
        if check_type is None:
            check_type = True
    if params["state"] == "present":
        if new_value is None:
            module.fail_json(msg="Must give value with state=present", **result)
        if desired_type:
            try:
                new_value = coerce_to_type(new_value, desired_type)
            except ModuleFail as ex:
                result.update(ex.result)
                module.fail_json(msg=ex.message, **result)
    else:
        assert params["state"] == "absent"
        if new_value == "":
            new_value = None
        if new_value is not None:
            module.fail_json(
                msg="Cannot provide value with state=absent", **result
            )

    top_key = str(key_list[0])
    top_value = CF.CFPreferencesCopyValue(
        top_key, params["domain"], params["user"], params["host"]
    )
    top_value = Conversion.pythonCollectionFromPropertyList(top_value)
    result["old_value"] = copy.deepcopy(top_value)

    container = {top_key: top_value}
    op = Operation(
        state=params["state"],
        key_list=key_list,
        types=(desired_type,),
        new_value=new_value,
        check_type=check_type,
        add_merge=params["add_merge"],
        dict_create=params["dict_create"],
    )
    try:
        result["changed"] = set_value(op, 0, container)
    except ModuleFail as ex:
        result.update(ex.result)
        module.fail_json(msg=ex.message, **result)
    if len(container) == 0:
        top_value = None
    elif len(container) > 1 or top_key not in container:
        module.fail_json(
            msg="Invalid attempt to change %r" % (top_key,), **result
        )
    else:
        top_value = container[top_key]

    result["new_value"] = top_value
    if result["changed"] and not module.check_mode:
        CF.CFPreferencesSetValue(
            top_key, top_value, params["domain"], params["user"], params["host"]
        )
        CF.CFPreferencesSynchronize(
            params["domain"], params["user"], params["host"]
        )

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
