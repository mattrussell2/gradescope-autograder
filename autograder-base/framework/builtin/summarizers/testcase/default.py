#!/usr/sup/bin/python
#
#                          default.py
#
#         Default summarizer for individual test cases.
#
#      This is also intended to be useful (though not required) as a base
#      function for more specialized summarizers, as returned dictionary
#      values can be overridden.
#
#      NEEDSWORK: this should probably be turned into a class
#                 so subclassing can be used for specialization
#
#      Note that the results are collected in an OrderedDict so that
#      the JSON will be written in a sensible order.
#

from collections import OrderedDict
from testcase_exceptions import TestcasePropertyError
import traceback
import re
# extracts information from execution results files
from builtin.summarizers.testcase import logproperties
# implements the predicate language for testing whether test was successful
from builtin.summarizers.testcase import successcriteria




# TopLevelProperties are included at the top level of the summary file
TopLevelProperties = ["name", "description", "category", "categories", "data"]
DetailsProperties = ["programdir", "program", "arglist", "studentuid", "testsetdir","resultscontainerdir"]

#
#                        summarize
#
#  In general, this should be all the information that any report writer or
#  grading program will need for this test case.
#
#  Prepare the data that will go into the
#  login.n.test_summaries/testset/xxx.summary.json file
#
#
def summarize(testcase, resultsDir):
    summary = OrderedDict()
    #
    # We put TopLevelProperties at the top level so name and description are easy 
    # to spot in the JSON
    #
    gatherProperties(testcase, TopLevelProperties, summary)

    #
    #   Get and put out valgrind results, if any
    #   (Moved this ahead of "success" so that success criteria
    #   can depend on valgrind errors) Noah M. (4/17/2021)
    #
    valgrindResults(testcase, summary)
    
    #
    #   Compute and record whether the test passed or failed
    #
    success(testcase, summary)
    
    #
    #   Get and put out main execution summary 
    #
    executionResults(testcase, summary)
    
    #
    # Now collect all the other properties. The ones we currently
    # report are the "DetailsProperties" listed above unioned
    # with all the ones in the environment. The business
    # with tempdetails is just to sort them in the json
    #
    detailedProperties(testcase, summary)
    return summary

#
#      Put named testcase properties into the supplied target dictionary
#
#      propsToGather is an array of property names
#      target is a dictionary
#

def gatherProperties(testcase, propsToGather, target):
    for propName in propsToGather:
        try:
            target[propName] = testcase.property(propName)
        except TestcasePropertyError as e:
            pass                       # if testcase doesn't have it, don't add it


#
#                      success
#
#      Override these to (respectively) hook the location and parsing of
#      exitcode information and/or the representation of results in the summary
#

def success(testcase, targetDict):
    #
    #                     Find the criteria we are to check
    #
    # In the following, we raise TestcasePropertyError or KeyError
    # if the testset configuration file doesn't specify test criteria
    #
    try:
        successProp = testcase.property("successreport")
        criteria = successProp["criteria"]
    except TestcasePropertyError as e:
        criteria = {}
    except KeyError as e:
        criteria = {}

    #
    #    Evaluate the success criteria
    #
    try:
         results, msg, almostSucceeded = \
             successcriteria.successReport(testcase, criteria)
    # NEEDSWORK: Following exceptions tend to happen when success criteria
    #            are not properly specified. Need better messages and handling
    except KeyError as e:
        targetDict["success"] = "INTERNAL ERROR RUNNING SUCCESS REPORT - " + \
            "successreport TESTSET SPECIFICATION MAY NOT BE CONSISTENT " + \
            "WITH EXECUTION RESULTS KeyError...PROBABLE CAUSE IS BAD KEY" + \
            " IN SUCCESS CRITERION. Keyname = %s" % e
        targetDict["traceback"] = traceback.format_exc()
    except TestcasePropertyError as e:
        targetDict["success"] = "INTERNAL ERROR RUNNING SUCCESS REPORT - " + \
            "successreport TESTSET SPECIFICATION MAY NOT BE CONSISTENT " + \
            "WITH EXECUTION RESULTS TestcasePropertyError"
        targetDict["traceback"] = traceback.format_exc()
    except AttributeError as e:
        targetDict["success"] = "INTERNAL ERROR RUNNING SUCCESS REPORT - " + \
            "successreport TESTSET SPECIFICATION MAY NOT BE CONSISTENT " + \
            "WITH EXECUTION RESULTS AttributeError"
        targetDict["traceback"] = traceback.format_exc()
    except successcriteria.NoSuccessReport as e:
        targetDict["success"] = "INTERNAL ERROR RUNNING SUCCESS REPORT - " + \
            "successreport TESTSET SPECIFICATION MAY NOT BE CONSISTENT " + \
            "WITH EXECUTION RESULTS NoSuccessReport"
        targetDict["traceback"] = traceback.format_exc()
    #
    # Successfully evaluated success - recored results in targetDict
    #
    else:
        if results == None:
            targetDict["success"] = "COULDNOTRUNTESTS"
        else:
            targetDict["success"] = "PASSED" if results else "FAILED"
        #
        # record almostSucceeded
        #
        targetDict["almostsucceeded"] = almostSucceeded
        #
        # record reason
        #
        targetDict["reason"] = msg
        
    return


#
#                      checkedRuntimeError
#
#       Called when a signal 6 (SIGABRT) was recorded to check stderr
#       for evidence of an uncaught Hanson-style exception. If found
#       return a dictionary entry with the message.
#

CRE_RE = re.compile(r"^Uncaught exception (.*)")

def checkedRuntimeError(testcase):
    try:
        for line in open(testcase.sterrname()).readlines():
            result = CRE_RE.match(line)
            if result:
                return {"message" : line}
    except IOError as e:
        return None
    return None   


#
#                      exectutionResults
#
#      Override these to (respectively) hook the location and parsing of
#      exitcode information and/or the representation of results in the summary
#

def executionResults(testcase, targetDict):
    signalValue = None
    exitcodeDict = logproperties.exitCodeDictionary(testcase)
    results = OrderedDict()
    if "exitCode" in exitcodeDict:
        results["exitcode"] = exitcodeDict["exitCode"]
    elif "signal_value" in exitcodeDict:
        results["signal"] = exitcodeDict
        signalValue = exitcodeDict["signal_value"]
    elif "executablenotfound" in exitcodeDict or "executablelauncherror" in exitcodeDict:
        results["execution_failed"] = exitcodeDict
    elif "abandontestcaseexception" in exitcodeDict:
        results["abandontestcaseexception"] = exitcodeDict["abandontestcaseexception"]
    else:
        results["testprocessingerror"] = "Unknown failure retrieving execution status"

    #
    # In the case where signal_value = 6 (SIGABRT) then
    # we may have a Hanson-style Checked Runtime Error.
    # Look in the stderr log to see if it's there and record it
    #
    if signalValue == 6:
        cre = checkedRuntimeError(testcase)
        if cre:
            results["cre"] = cre        

    #
    # In the case where signal_value = 9 (SIGKILL) then
    # if we also were cpulimited then we assume the 
    # program timed out.
    #
    if signalValue == 24:
        if testcase.hasProperty("cpulimit"):
            results["timedout"] = testcase.property("cpulimit")        

    targetDict["executionsummary"] = results


#
#                      valgrindResults
#
#      Only if valgrind testing results are recorded in valgrind JSON
#      file, include those in the results summary
#

def valgrindResults(testcase, targetDict):
    valgrindDict = logproperties.valgrindDictionary(testcase)
    if valgrindDict:
        targetDict["valgrind"] = valgrindDict
#        print "FOUND VALGRIND DICT"
    else:
#        print "NO VALGRIND DICT"
        pass

#
#                      detailedProperties
#
#      Put into the supplied target dictionary under the key "details":
#
#      1) The properties named in array DetailsProperties, in order
#      2) Any other properties supplied in env (I.e. including properties
#         the tester supplied that the core framework might not knwo about)
#
#      NEEDSWORK: almost everyplace else we iterate the 
#

def detailedProperties(testcase, target):
    tempDetails = {}
    prop_names = testcase.invocation_property_names
    gatherProperties(testcase, DetailsProperties, tempDetails)
    for envItem in prop_names:                      # add the ones from env
        if not envItem in tempDetails:
            tempDetails[envItem] = getattr(testcase, envItem)
    details = OrderedDict()                # now sort them
    for detail in sorted(tempDetails):
        details[detail] = tempDetails[detail]
    target["details"] = details


