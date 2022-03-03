#!/bin/env python
#
#                           testcase_exceptions
#
#
#        Exceptions for global use in testcase processing
#
#        Most exceptions are named after their semantics and are thrown
#        and caught locally as needed.
#
#        Threespecial exceptions are used to control overall flow, and are
#        often raised with handlers for others.
#
#        AbandonTestcase:       We can continue with other tests, but not this one
#        AbandonStudent:        Something is misconfigured that prevents us from
#                               continuing with this student
#        AbandonTestSet:        The testset or running of it is faulty.
#                               Stop immediately
#


#
#    NEEDSWORK: Looks like BadFile was planned as an exception but is not
#               ever used. 


class BadFile(Exception):
    def __init__(self, fname, reason):
        self.msg = "Results file %s: %s" % (fname, reason)
        self.fname = fname
        self.reason = reason
    def __str__(self):
        return self.msg

class NoFile(Exception):
    def __init__(self, fname):
        self.msg = "Results file %s could not be read " % fname
        self.fname = fname
    def __str__(self):
         return self.msg

class BadTestcaseSpecification(Exception):
    def __init__(self, testcasename, msg):
        self.msg = "Testcase %s: %s" % (testcasename, msg)
    def __str__(self):
         return self.msg

class BadTestsetSpecification(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
         return self.msg

class TestcasePropertyError(Exception):
    def __init__(self, prop):
        self.msg = "Property %s does not exist in Test case attributes or env" % prop
    def __str__(self):
        return self.msg

# --------------------------------------------------------------
#               Control overall flow of testing
# --------------------------------------------------------------

#
#   Give up on this testcase, continue with next in set
#
#   It is assumed that execution status is set before throwing this.
#
class AbandonTestcase(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
         return self.msg

#
#   Give up on this student, continue with next
#

class AbandonStudent(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
         return self.msg

#
#   Whole testset is faulty, give up on all students
#

class AbandonTestset(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
         return self.msg


#
#                TCAssert
#
#     A version of assert that throws an exception we control
#
def TCAssert(condition, excpt):
    if not condition:
        raise excpt
