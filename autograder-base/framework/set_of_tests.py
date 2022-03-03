#!/usr/sup/bin/python
#
#                  set_of_tests.py
#
#        Author: Noah Mendelsohn
#      
#   
#        Classes:
#
#             SetofTests: Zero or More tests (designed to be subclassed)
#
#        Note that in principle a set of tests can, in principle, be 
#        represented as a concrete list of Test objects, or can be
#        simulated through iteration using generators.

import os, sys, subprocess, asciijson, re, errno, unixsignals, valgrind, pwd
import json, importlib, traceback

import testcase_exceptions
from testcase_exceptions import TCAssert

from testcase import Test
from test_invocation import Test_Invocation


#**********************************************************************
#
#                Class SetofTests
#
#     NEEDSWORK: we call this a set of tests but it's really a list, as
#            we currently don't catch duplicates
#
#     Subscripting and iteration work through the test objects
#     (Added 1/1/2021 Noah M.)
# 
#**********************************************************************

class SetofTests(object):

    #
    #      __init__
    #
    #      supplied_tests must, if supplied, be a list of Test objects
    #
    #      testsetdir must be the directory in which the SetofTests is defined
    #                 In particular, this is where the canonical directory
    #                 must live if custom canonicalizers are provided for files
    #      
    #
    def __init__(self, supplied_tests = [], testsetdir = "NO TESTSET DIR SUPPLIED TO SetofTestsConstructor",
                 description = "No SetofTests Description Supplied"):
        TCAssert(isinstance(supplied_tests, (list, tuple)) , 
               testcase_exceptions.BadTestsetSpecification(
               "Set of tests must be initialized with a list or tuple of tests)"))
        for t in supplied_tests:
            TCAssert( type(t)==Test,
               testcase_exceptions.BadTestsetSpecification(
               "Argument to SetofTests constructor must be list of Test instances"))

        self.testsetdir = testsetdir
        self.description = description

        # Add all the supplied tests to the set, augmenting them with properties
        # like testsetdir as appropriate
        self.testList = []
        for t in supplied_tests:
            self.addTest(t)


    #
    #     Add to or query the tests in the set
    #
    def addTest(self, test):
        test.testsetdir = self.testsetdir
        self.testList.append(test)

    def tests(self):
        return self.testList

    #
    #                  runTests
    #
    #     Run all the tests in the set and summarize the results
    #

    def runTests(self, env):
        for t in self.tests():
            t.validateProperties()
            try:
                runnable_test = Test_Invocation(t, env);
                runnable_test.runTest(env)
            except testcase_exceptions.AbandonTestcase as e:
                print("SetofTests.runTests: received AbandonTestcase exception running testcase %s, continuing with next testcase".format(t.name))
                # Note, it is intentional that we summarize whether or not we to
                # AbandonTestcase exception, since that leaves an 
                # "abandontestcase" key in the exitcode file, and the summarizer
                # will (should) pick that up.
            try:
                runnable_test.summarize()           # prepare summary JSON file for this test
            except testcase_exceptions.AbandonTestcase as e:
                print("SetofTests.runTests: received AbandonTestcase exception summarizing testcase %s, continuing with next testcase".format(t.name))

    #
    #       Subscript access and iteration (added 1/1/2021 Noah M.)
    #

    def __getitem__(self, x):
        return self.tests()[x]

    def __iter__(self):
        return iter(self.tests())
    



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
#                    createTestsfromJSON
#
#      Factory function for creating SetofTests from JSON
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
def createTestsfromJSON(filename):
    if filename == "STDIN":
        f = sys.stdin
    else:
        try:
            f = open(filename, "r")
        except IOError:
            print("loadTestsfromJSON: Could not open or read file {}".format(filename), file=sys.stderr)
            raise testcase_exceptions.BadTestsetSpecification( \
                     "createTestsfromJSON: Could not open or read file %s" % \
                         (filename))

        jsondata = f.read()
        f.close()

        try:
            data = asciijson.loads(jsondata)
        except ValueError:
            print("{}: Could not parse {} as JSON".format(sys.argv[0], filename), file=sys.stderr)
            raise testcase_exceptions.BadTestsetSpecification(
               "%s: Could not parse %s as JSON" % (sys.argv[0], filename))

        TCAssert("description" in data,
               testcase_exceptions.BadTestsetSpecification(
               "SetofTests.createTestsfromJSON() \"description\" key missing from JSON"))

        TCAssert("tests" in data,
               testcase_exceptions.BadTestsetSpecification(
               "SetofTests.createTestsfromJSON() \"tests\" key missing from JSON"))

        # NEEDSWORK: is this a dir name or a filename?
        newSet = SetofTests(testsetdir = \
                            os.path.dirname(os.path.abspath(filename)),      \
                description = data["description"])
        for t in data["tests"]:
            newSet.addTest(Test(t))
        return newSet




#**********************************************************************
#              TEST CODE FOR THESE CLASSES
#**********************************************************************
     
if __name__ == "__main__":
    assert False, "NEEDSWORK: self-testing for set_of_tests.py is broken due to changes in directory structures and new rules for passing environemnts to runtests"
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

    allTests = SetofTests([testTest, testTest2])
    allTests.runTests(env)
    
    print("\n\nRUNNING JSON TESTS\n_________________\n")

    jsonTests = createTestsfromJSON('testset.json') 
    jsonTests.runTests(env)



