#!/usr/sup/bin/python
#
#                  testcase.py
#
#        Author: Noah Mendelsohn
#      
#   
#        Classes:
#
#             Test:     A single test that can be run to yield a result
#


# NEEDSWORK: some of these imports not needed after latest code refactor

import os, sys, subprocess, asciijson, re, errno, unixsignals, valgrind, pwd
import json, importlib, traceback

import testcase_exceptions
from testcase_exceptions import TCAssert
from collections import OrderedDict

import hook                                 # local support for dynamic import
import resource                             # set CPU limits, etc.
import signal

from utilities import mkdir, forceRemoveFile  # local wrappers for directory
                                            # creation and file removal

#**********************************************************************
#
#                     Class Test
#
#     Represents an individual test to be run. 
#
#     Required properties
#     -------------------
#
#     name - A short string name for the test, suitable for use
#            as part of filenames, etc.
#
# 
#     description - a brief description useful for
#            describing the test to people
#
#     programdir - A directory in which the test program can be found,
#            May be relative (e.g. .)
#
#     program - the filename of the program executable within programdir
#
#
#     args() - a method returning the arguments to be supplied on the
#            test as a Python list (note that a default implementation)
#            is supplied that returns arglist, so if that member is 
#            set this method can be used.
#
#     Optional properties
#     -------------------
#
#     shell  "True" or "False". Only if true, the args are joined
#            with a space and then the resulting command line
#            is sent with Shell=True to subprocess call. This is useful, e.g.
#            for making test commands with pipes.
#
# 
#
#
#     Public Methods:
#
#          Constructor: takes a dictionary which in which the keys
#          are the properties listed above (and others if you like),
#          and creates the corresponding test descriptor
#
#          validateProperties: ensures required properties provided
#
#**********************************************************************

class Test(object):

    requiredProperties = ("name", "description", "program", "arglist")

    # The boolean properties will be converted from string values ("True") to
    # true booleans (True) when stored

    booleanProperties = ("shell")

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #               __init__
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, properties):
        for item, value in properties.items():
            # convert boolean properties to actual True/False
            if item in Test.booleanProperties:
                name = properties.get("name", "NAMENOTYETKNOWN")
                TCAssert((value == "True" or value == "False"), \
                     testcase_exceptions.BadTestcaseSpecification(name, \
                 "Test constructor: property %s must be boolean True or False" % \
                                                                      (item)))
                if value == "True":
                    value = True
                else:
                    value = False
            setattr(self, item, value)

            
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #     Methods to ensure required properties present
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def validateProperty(self, prop):
        TCAssert(hasattr(self, prop), \
                     testcase_exceptions.BadTestcaseSpecification(self.name, \
                     "Test.validate(): property %s is missing" % prop))

    def validateProperties(self):
        for prop in Test.requiredProperties:
            self.validateProperty(prop)
        


#**********************************************************************
#              TEST CODE FOR THESE CLASSES
#**********************************************************************
     
if __name__ == "__main__":
    assert False, "NEEDSWORK: self-testing for testcase.py is broken due to changes in directory structures and new rules for passing environemnts to runtests"
    env = {
        "testdir" : ".",
        "studentdir" : ".",
        "studentuid" : "dummystudent",
        "testeruid" : pwd.getpwuid(os.getuid()).pw_name,
        "testsetname" : "DummyTest"
       }
    env["studentdir"] = "dummystudent.3"       # local name of dir e.g. studentname.3
    env["studentabsdir"] = os.path.abspath(env["studentdir"])  # full path
    env["resultscontainerdir"] = "."


    print("Running testcase.py test code")

    testTest = Test({"name" : "test1andtest2",
                     "description" : "Duplines on sample files test1 and test2",
                     "programdir" : ".",
                     "program" : "duplines",
                     "arglist" : ["test1.data", "test2.data#{name}"],
                     "resultscontainerdir" : "."
                     });
    testTest.validateProperties()


    testTest2 = Test({"name" : "Anothertest",
                     "description" : "Yet Another Test",
                     "programdir" : ".",
                     "program" : "duplines",
                     "arglist" : ["test1.data", "test2.data", "test3.data"],
                     "resultscontainerdir" : "."
                     });
    testTest2.validateProperties()




