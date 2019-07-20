from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals


def dict_product(a_dict):
    """Returns pairs (k, v_n) for every key and each of that key's values."""
    for k, vs in a_dict.iteritems():
        for v in vs:
            yield (k, v)


def named_list(the_lists, index_names):
    """Make each list into a dict with elements named from the given names."""
    for a_list in the_lists:
        yield dict(zip(index_names, a_list))


class FilterModule(object):
    def filters(self):
        return {"dict_product": dict_product, "named_list": named_list}
