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

import copy
import datetime
import re

import CoreFoundation as CF
from PyObjCTools import Conversion
from ansible.module_utils.basic import AnsibleModule

# fmt: on


def ensure_key_is_str(key):
    if isinstance(key, bool):
        key = int(key)
    if isinstance(key, (float, int)):
        key = str(key)
    if not isinstance(key, str):
        raise Exception(f"Cannot convert key {key!r} to string")
    return key


SENTINEL = object()


def merge_dicts(src, dst):
    changed = False
    for key, src_value in src.items():
        key = ensure_key_is_str(key)
        dst_value = dst.get(key, SENTINEL)
        if isinstance(src_value, dict) and isinstance(dst_value, dict):
            changed = merge_dicts(src_value, dst_value) or changed
        elif src_value != dst_value:
            dst[key] = src_value
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


class ModuleFail(Exception):
    def __init__(self, message, **kwargs):
        Exception.__init__(self, message)
        self.message = message
        self.result = kwargs


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
        # container_types is necessary if you want to be able to
        # create entirely missing keys (past the top-level key).
        container_types=dict(type="raw", required=False, default=None),
        value=dict(type="raw", required=False, default=None),
        value_type=dict(type="str", required=False, default=None),
        merge_value=dict(type="bool", required=False, default=False),
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

    def fail(msg):
        module.fail_json(msg=msg, **result)

    key_list = params["key"]
    if not key_list:
        fail("key cannot be empty")
    elif type(key_list) != list:
        key_list = [key_list]
    elif len(key_list) < 1:
        fail("key cannot be an empty list")

    # The first container type is always a dict (AFAIK that's how
    # preferences work), so you don't need to include that.
    num_container_types_needed = len(key_list) - 1
    container_types = params["container_types"]
    if container_types is None:
        container_types = [None] * num_container_types_needed
    else:
        if not isinstance(container_types, list):
            container_types = [container_types]
        CONTAINER_TYPE_STR_TO_CLS = {"list": list, "dict": dict, "array": list}
        # Ansible doesn't like it if you put things that can't be serialized
        # into JSON into the data structures that it owns, and which it will
        # eventually try to put into the response.  Make a copy.
        container_types = container_types[:]
        for idx, container_type in enumerate(container_types):
            try:
                container_types[idx] = CONTAINER_TYPE_STR_TO_CLS[container_type]
            except KeyError:
                fail(f"Unknown container type {container_type}")
        if len(container_types) == (num_container_types_needed + 1):
            # Allow user to tell us that the first container is a
            # dict, which it always is in preferences, AFAIK.  (See
            # also my comment above where I introduce
            # num_container_types_needed.)
            if container_types[0] != dict:
                fail(
                    f"If you want to pass {num_container_types_needed + 1}"
                    f" value(s) in container_types (rather than"
                    f" {num_container_types_needed} value(s), which is/are"
                    f' all that are required), the first element must be "dict"'
                )
            del container_types[0]
        elif len(container_types) != num_container_types_needed:
            fail(
                f"container_types must have {num_container_types_needed}"
                " element(s)"
            )

    # Copying these into the result to ease debugging.  Note that
    # these may be different than some of the info Ansible prints/puts
    # into the result for you, since it'll be filling in the module's
    # parameters, but the below gives you a bit more information about
    # how this module *parsed* your args.
    for params_key in ("host", "user", "domain"):
        result[params_key] = params[params_key]
    result["key_list"] = key_list

    new_value = params["value"]
    if new_value is None:
        fail("Cannot handle new value of None")
    value_type = params["value_type"] or None
    if value_type is not None:
        try:
            value_type = PREF_VALUE_TYPES[value_type]
        except KeyError:
            fail(
                "Type %r invalid, must be one of: %s"
                % (value_type, ", ".join(PREF_VALUE_TYPES))
            )
    merge_value = params["merge_value"]
    if merge_value:
        if params["state"] == "absent":
            fail("Cannot use merge_value with state=absent")
        if not isinstance(new_value, (dict, list)):
            fail("merge_value can only be used with dict or list values")

    if params["state"] == "present":
        if new_value is None:
            fail("Must give value with state=present")
        if value_type:
            try:
                new_value = coerce_to_type(new_value, value_type)
            except ModuleFail as ex:
                result.update(ex.result)
                fail(ex.message)
    else:
        assert params["state"] == "absent"
        if new_value == "":
            new_value = None
        if new_value is not None:
            fail("Cannot provide value with state=absent")

    top_key = ensure_key_is_str(key_list[0])
    top_value = CF.CFPreferencesCopyValue(
        top_key, params["domain"], params["user"], params["host"]
    )
    top_value = Conversion.pythonCollectionFromPropertyList(top_value)
    result["old_value"] = copy.deepcopy(top_value)

    # Drill down to the container we need to modify.
    top_container = container = {top_key: top_value}
    for key_idx, key in enumerate(key_list[:-1]):
        next_container_type = container_types[key_idx]
        if type(container) == dict:
            key = ensure_key_is_str(key)
            if key not in container or container[key] is None:
                if next_container_type:
                    container[key] = next_container_type()
                else:
                    fail(f"No container at {key_list[key_idx:]!r}")
        elif type(container) == list:
            key = int(key)
            if key == len(container):
                container.append(None)
            elif key > len(container):
                fail(
                    f"Index {key} is longer"
                    f" than the list at key(s)) {key_list[:key_idx]}"
                )
            elif next_container_type and container[key] is None:
                container.append(next_container_type())
        else:
            raise Exception("Should never get here")
        container = container[key]
        if next_container_type and type(container) != next_container_type:
            fail(
                f"Expected container type {next_container_type.__name__}"
                f" (key_idx={key_idx}) at {key_list[: key_idx + 1]!r}"
                f" but found type {type(container).__name__} instead"
            )
        if key_idx == 0 and container is not top_value:
            top_value = container

    # Do the modification on the leaf container.
    changed = False
    last_key = key_list[-1]
    if type(container) == dict:
        last_key = ensure_key_is_str(last_key)
    elif type(container) == list:
        last_key = int(key)
    if params["state"] == "absent":
        if type(container) == dict:
            if last_key in container:
                del container[last_key]
                changed = True
        elif type(container) == list:
            if last_key < len(container):
                del container[last_key]
                changed = True
    else:
        assert params["state"] == "present", repr(params["state"])
        if type(container) == dict:
            old_value = container.get(last_key)
        elif type(container) == list:
            last_key = int(last_key)
            if last_key < len(container):
                old_value = container[last_key]
            elif last_key == len(container):
                assert new_value is not None
                old_value = None
                container.append(old_value)
            else:
                fail(
                    f"Key index {last_key} is longer"
                    " than the list at {key_list}"
                )
        if old_value is None:
            container[last_key] = new_value
            changed = True
        elif merge_value:
            if type(old_value) != type(new_value):
                module.fail_json(
                    msg="Cannot merge {} and {}".format(
                        type(old_value).__name__, type(new_value).__name__
                    )
                )
            elif type(old_value) == list:
                for elem in new_value:
                    if elem not in old_value:
                        old_value.append(elem)
                        changed = True
            elif type(old_value) == dict:
                changed = merge_dicts(new_value, old_value)
            else:
                raise Exception("Should never get here")
        elif old_value != new_value:
            container[last_key] = new_value
            changed = True

    # Note that setting a preference to None (NULL) is the same as
    # deleting the preference, so getting None here just means we
    # deleted the preference entirely (state=absent).
    new_value = top_container.get(top_key)
    result["new_value"] = new_value
    if changed and not module.check_mode:
        CF.CFPreferencesSetValue(
            top_key,
            new_value,
            params["domain"],
            params["user"],
            params["host"],
        )
        CF.CFPreferencesSynchronize(
            params["domain"], params["user"], params["host"]
        )
        result["changed"] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
