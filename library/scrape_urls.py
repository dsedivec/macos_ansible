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
module: scrape_urls

short_description: Scrape URLs out of HTML

version_added: "2.9"

description:
    - "TBD""

options: TBD

author:
    - Dale Sedivec (@dsedivec)
"""

EXAMPLES = "TBD"

RETURN = "TBD"

# fmt: off

import html.parser
import io
import re
import urllib.request

from ansible.module_utils.basic import AnsibleModule

# fmt: on


class ModuleFail(Exception):
    pass


class AttributeScraper(html.parser.HTMLParser):
    class _LimitReached(Exception):
        pass

    def __init__(self, tags_to_scrape, attribs_to_scrape, value_regexp):
        super().__init__()
        self._tags_to_scrape = {tag.lower() for tag in tags_to_scrape}
        self._attribs_to_scrape = {
            attrib.lower() for attrib in attribs_to_scrape
        }
        self._value_regexp = re.compile(value_regexp)
        self._max_matches = None
        self.values_found = []

    def feed_from(self, stream):
        while True:
            data = stream.read(4096)
            if not data:
                break
            self.feed(data)

    def handle_starttag(self, tag, attribs):
        if tag.lower() in self._tags_to_scrape:
            for name, value in attribs:
                if name in self._attribs_to_scrape:
                    if self._value_regexp.search(value):
                        self.values_found.append(value)
                        if (
                            self._max_matches
                            and len(self.values_found) >= self._max_matches
                        ):
                            raise self._LimitReached

    @classmethod
    def scrape_url(
        cls,
        url,
        tags_to_scrape,
        attribs_to_scrape,
        value_regexp,
        max_matches=None,
    ):
        with urllib.request.urlopen(url) as url_stream:
            if url_stream.getcode() != 200:
                raise ModuleFail(f"URL returned HTTP {url_stream.getcode()}")
            url_stream = io.TextIOWrapper(url_stream, encoding="utf-8")
            instance = cls(tags_to_scrape, attribs_to_scrape, value_regexp)
            instance._max_matches = max_matches
            try:
                instance.feed_from(url_stream)
                instance.close()
            except cls._LimitReached:
                pass
        return instance.values_found


def run_module():
    module_args = dict(
        url=dict(type="str", required=True),
        tags=dict(type="list", required=False, default=["a"]),
        attributes=dict(type="list", required=False, default=["href"]),
        url_regexp=dict(type="str", required=True),
        max_num_urls=dict(type="int", required=False, default=None),
    )
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)
    params = module.params
    try:
        result["urls"] = AttributeScraper.scrape_url(
            params["url"],
            params["tags"],
            params["attributes"],
            params["url_regexp"],
            max_matches=params.get("max_num_urls"),
        )
    except ModuleFail as ex:
        module.fail_json(msg=str(ex))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
