#!/bin/env python
#
#                  testpy.py
#
#        For fooling around

import importlib

mod = importlib.import_module("default.summarizers.testcase")
print type(mod).__name__

mod = importlib.import_module("default.summarizers.testcase.default")
print repr(mod)





