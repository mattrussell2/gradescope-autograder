#!/usr/sup/bin/python
#
#                          asciijson.py
#
#         Wrapper around some of the standard json methods to work
#         in ascii instead of unicode

import json, sys, numbers
from collections import OrderedDict

def ascii_encode_dict(data):
    # When we're asked to deal with a string, encode it, otherwise
    # it's likely something like a number, in which case we leave it alone
    ascii_encode = lambda x: x.encode('ascii') if isinstance(x, bytes) else x
    return dict(map(ascii_encode, pair) for pair in data.items())

#
#  Wrap json.loads
# 
#  NEEDSWORK: should provide an object hook parameter here.
#
def loads(data):
    return json.loads(data, object_pairs_hook=OrderedDict, object_hook=ascii_encode_dict)
    


