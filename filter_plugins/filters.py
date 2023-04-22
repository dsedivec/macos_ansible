from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import re
import urllib.parse


def dict_product(a_dict):
    """Returns pairs (k, v_n) for every key and each of that key's values."""
    for k, vs in a_dict.items():
        for v in vs:
            yield (k, v)


def extract_url_param(url, param):
    query = urllib.parse.urlsplit(url).query
    params = urllib.parse.parse_qs(query)
    value = params.get(param)
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value


def filter_casks_by_os_version(cask_list, mac_os_version):
    """cask_list can be \"cask\" or [\"cask\", min_os_version].

    mac_os_version is currently major version number only.

    """
    mac_os_version = int(mac_os_version)
    for cask in cask_list:
        if not isinstance(cask, list):
            yield cask
        else:
            cask, min_version = cask
            if mac_os_version >= int(min_version):
                yield cask


def make_dropbox_url_dl(url):
    parts = urllib.parse.urlsplit(url)
    if re.search(r"^(?:www\.)?dropbox.com", parts.hostname, re.I):
        params = urllib.parse.parse_qs(parts.query)
        params["dl"] = 1
        url = urllib.parse.urlunsplit(
            parts._replace(query=urllib.parse.urlencode(params))
        )
    return url


def named_list(the_lists, index_names):
    """Make each list into a dict with elements named from the given names."""
    for a_list in the_lists:
        yield dict(zip(index_names, a_list))


class FilterModule(object):
    def filters(self):
        return {
            "dict_product": dict_product,
            "extract_url_param": extract_url_param,
            "filter_casks_by_os_version": filter_casks_by_os_version,
            "make_dropbox_url_dl": make_dropbox_url_dl,
            "named_list": named_list,
        }
