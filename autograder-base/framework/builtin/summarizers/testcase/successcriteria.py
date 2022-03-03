#!/usr/sup/bin/python
#
#                          successcriteria.py
#
#         Implements the predicate language for determining whether a test
#         succeeded. 
#
#
#           E.g.:
#
#          "criteria" : {
#	        "exitcode" : 0,
#		"stdout" : "matchcanonical",
#                "OR" : {
#                  "signal": "SIGABRT",
#                  "signal": "SIGSEGV",
#                 }
#          }      
#
#         Each of the handlers that implements a success criterion
#         returns a (success, msg) pair. The msg describes 
#         the condition that led to the success (true) or failure (false).
#

from collections import OrderedDict

import testcase_exceptions
import unixsignals
from testcase_exceptions import TCAssert
from testcase_exceptions import BadFile
from builtin.summarizers.testcase import logproperties
import os, sys
import re
import filecmp                     # standard Python file comparison lib

CLEANEDFILESUFFIX = ".CLEANED"
CANONICALMATCHFAILMESSAGE = "%s is not correct"
CANONICALMATCHFAILRE = re.compile(r"([^ ]+) is not correct")

class NoSuccessReport(Exception):
    def __init__(self, testcase):
        self.msg = "Could not create success report for %s" % testcase.name
    def __str__(self):
         return self.msg



#*****************************************************************
#                       successReport
#
#        Returns True, Msg, False if the program test was passed, 
#                None, Msg, False if the test was abandoned
#                False,Msg, True  if test failed but almost succeeded
#                False,Msg, False if failed completely
#
#
#    Note: successReport does its work by calling conjunctionCriteria
#          on the supplied criteria from the testcase. This in turn
#          recursively invokes the handlers for the specified criteria,
#          which may optionally include further conjunctions or 
#          disjunctions, which are handled recursively. 
# 
#          The individual handlers all return (True/False, msg).
#           -  True is returned if the condition was met, in which
#              case the message explains the success
#           -  False is returned if the condition was not met, in which
#              case the message explains the failure
#
#    The supplied criteria should be a dictionary containg tests
#    ALL of which must be passed (conjunction)
#
#    If the testcase was abandoned, we failed.
#    NEEDSWORK: Do all test cases need to explicitly test timeout?
#    
#
#    However we assume a timeout is a failure
#
#*****************************************************************

def successReport(testcase, criteria):
    #
    # If tests were abandoned or criteria aren't there just return
    #
    if testcaseAbandonedCriterion(testcase, criteria)[0]:
        return (None, False)
    if len(criteria) < 1:
        return (False, "NO SUCCESS CRITERIA PROVIDED IN TEST SPECIFICATION")
    #
    # compute [success, msg]
    #
    # ...where success is True iff test criteria were met
    #
    results =  list(conjunctionCriterion(testcase, criteria))
    
    #
    # See whether a tested failed almost succeeded
    #
    # NEEDSWORK: this is a very fragile way of computing this.
    #
    # Basically, if the test failed, and the message suggests
    # a failure to match the canonical form of a file like
    # stdout or stderr, we look whether the canonicalizer
    # stored a cleaned up form of that file. If so, we try to match that
    #
    
    almostSucceededRetval = False
    msg = results[1]

    #
    # Only do almost succeeded checking if we failed so far
    #
    if not results[0]:
        # see if failure is due to mistmatch on canonical file
        msgmatch = CANONICALMATCHFAILRE.match(msg)
        if msgmatch:
            filename = msgmatch.group(1)      
            almostSucceeded = almostPassed(testcase, filename)
            almostSucceededRetval = almostSucceeded[0]
        else:
            pass

    results.append(almostSucceededRetval) #(bool) tells caller whether almost succeeded
    return results

#
#                       almostPassed
#
# See whether cleaned up user canonical file
# matches correct canonical (same one used for
# matching non-clean files
#
# Returns (True, msg) if almost succeeded
# Returns (False, msg) otherwise
#
def almostPassed(testcase, fname):
    testsetdir = testcase.property("testsetdir")
    resultsdir = testcase.resultsDirectory()
    canonicalName = testcase.canonicalFilename(testcase.name + '.' + fname)
    cleanedName = canonicalName + CLEANEDFILESUFFIX

    cleanedResultsFile = os.path.join(resultsdir, cleanedName)
    if not (os.path.isfile(cleanedResultsFile) and \
                os.access(cleanedResultsFile, os.R_OK)):
        return (False, "almostPassed: results file not found")
    correctCleanedFile = os.path.join(testsetdir, canonicalName)
    if not (os.path.isfile(correctCleanedFile) and \
                os.access(correctCleanedFile, os.R_OK)):
        return (False, "almostPassed: required correct cleaned file %s not found" % correctCleanedFile)
#            raise testcase_exceptions.BadTestcaseSpecification(testcase.name, 
#                    "almostPassed: required correct cleaned file %s not found" % correctCleanedFile)
    
    try:

        if not filecmp.cmp(cleanedResultsFile, correctCleanedFile):
            return (False, "Cleaned %s does not match correct file" % fname)
    except OSError as e:
        print("UNEXPECTED ERROR: in successcriteria.almostPassed: {}".format(repr(e)))
        raise testcase_exceptions.AbandonTestcase(testcase.name, \
                                                      "UNEXPECTED ERROR: in successcriteria.almostPassed: %s" % \
                                                      repr(e))

    return (True, "%s is almost correct" % fname)

# ***********************************************************
#           Handlers for Predicate Language Primitives
#
#      e.g. exitcode, signal_name, etc
#
#      These are called when the corresponding key is found int
#      the testcase successreport criteria
#
#      These return true if the test succeeded, else false.
#      They can also throw KeyError if a bad keyword is used.
#
#      Note that these can be called recursively, in which case
#      the criteria changes during the recursion.
#      
# ***********************************************************


def exitcodeCriterion(testcase, criteria):
    exitCodeDict = logproperties.exitCodeDictionary(testcase)

    if "exitCode" in exitCodeDict and \
            criteria == exitCodeDict["exitCode"]:
        return (True, "exitCode == %d" % exitCodeDict["exitCode"])
    else:
        missingEx, m = missingExecutableCriterion(testcase, True)
        msg = " (missing executable)" if missingEx else ""
        if not missingEx:
            timedout, m = timedoutCriterion(testcase, True)
            if timedout:
                msg = " (timed out)"
            elif ("signal_name" in exitCodeDict) or \
                    ("signal_value" in exitCodeDict):
                msg = " (stopped by signal or illegally high exit code)"
                    
        return (False, "exitCode != %s%s" % (str(criteria), msg))


#
#     NEEDSWORK: Missing executable should honor a true/false test (not sure
#                what I meant here)
#
def missingExecutableCriterion(testcase, criteria):
    criteria = criteria in [True, "true", "True"]
    TCAssert((criteria == True) or (criteria == False), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria \"missingExecutableCriterion\" must be either true or false but is %s" % \
        (testcase.name, criteria)))
    exitCodeDict = logproperties.exitCodeDictionary(testcase)

    if "executablenotfound" in exitCodeDict:
        return (criteria, "Executable program was %sfound" % \
            ("not " if (not criteria) else ""))
    else:
        return (not criteria, "Executable program was %sfound" % \
            ("not " if (criteria) else ""))


def signal_nameCriterion(testcase, criteria):
    # Updated Oct 14, 2021: now takes either a single signal name
    # or a list of signal names
    if isinstance(criteria, str):
        list_of_signals = [criteria]
    else:
        list_of_signals = criteria

    TCAssert(len(list_of_signals) >= 1, 
             testcase_exceptions.BadTestsetSpecification(\
      "Testcase %s signal name success criteria must include at least one signal name" % \
        testcase.name))

    exitCodeDict = logproperties.exitCodeDictionary(testcase)
    for signal_name_to_check in list_of_signals:
        if "signal_name" in exitCodeDict and \
            signal_name_to_check == exitCodeDict["signal_name"]:
            signame = exitCodeDict["signal_name"]
            return (True, "signal_name=%s [%s]" % \
                    (signame, unixsignals.signalsByName[signame]["description"]))
    if len(list_of_signals) == 1:
        return (False, "signal_name!=%s [%s]" % \
                    (list_of_signals[0], unixsignals.signalsByName[criteria]["description"]))
    else:
        return (False, "signal_name not one of [%s]" % \
                    (', '.join(list_of_signals)))



def signal_valueCriterion(testcase, criteria):
    exitCodeDict = logproperties.exitCodeDictionary(testcase)
    if "signal_value" in exitCodeDict and \
            criteria == exitCodeDict["signal_value"]:
        return (True, "signal_value=%d" % exitCodeDict["signal_value"])
    else:
        return (False, "signal_value!=%d" % criteria)

#
#      NEEDSWORK: This duplicates logic found in the summarizer
#                 that also knows that signal 24 is likely a timeout
#      Note: this is recorded for any SIGXCPU(24) regardless of whether
#      our test framework set the limit
#
#      Note that the criterion must be a true or false. If true, then
#      success is that there WAS a timeout, otherwise success is NO timeout.
#
def timedoutCriterion(testcase, criteria):
    criteria = criteria in [True, "true", "True"]
    TCAssert((criteria == True) or (criteria == False), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria \"timedout\" must be either true or false but is %s" % \
        (testcase.name, criteria)))
    shouldTimeout = criteria == True
    exitCodeDict = logproperties.exitCodeDictionary(testcase)
    if "signal_value" in exitCodeDict and \
            exitCodeDict["signal_value"] == 24:  # Misdocument as SIGSTSP actually
                                                 # SIGXCPU
        return (shouldTimeout, "Execution %s" % \
                            "timed out")
    else:
        return (not shouldTimeout, "Execution  %s" % \
                            "did not time out" )

#
#                  testcaseAbandonedCriterion
#
#     This is always checked first, as if we couldnt' complet running the testcase
#     then nothing else can be trusted.
#
#     NOTE: this returns True if testcase abandoned due to exception, but
#           this will later result in an overall success of false.
#
def testcaseAbandonedCriterion(testcase, criteria):
    exitCodeDict = logproperties.exitCodeDictionary(testcase)
    if "abandtontestcaseexception" in exitCodeDict:
        return (True, "Testcase abandoned before completion")
    return (False, "Testcase ran to completion")

#
#                 canonicalMatchCriteria
#
#      The criteria is either a filename or an array of non-canonical filenames
#      For each, a canonical filename is computed, and then the
#      results file is compared to the same named file in the 
#      test set directory
#      
def canonicalMatchCriteria(testcase, criteria):
    # Make sure we have in iterable array of criteria (handle case where
    # user supplied a single filename)
    if isinstance(criteria, str):
        crit = [criteria]
    else:
        crit = criteria

    namesChecked = []
    #
    # Check each file. If bad, immediately return false
    #
    for fname in crit:
        namesChecked.append(fname)
        testsetdir = testcase.property("testsetdir")
        resultsdir = testcase.resultsDirectory()
        canonicalName = testcase.canonicalFilename(testcase.name + '.' + fname)

        #
        # If a failure marker file was left, then there is no canonical file
        # and the test fails  
        #
        failedFullFilename =  os.path.join(resultsdir, \
                                           testcase.failedFilename(canonicalName))
        if (os.path.isfile(failedFullFilename) and \
                os.access(failedFullFilename, os.R_OK)):
            return (False, CANONICALMATCHFAILMESSAGE % fname)
        #
        # The marker for canonicalization failure isn't found, so if the
        # canonicalized file doesn't exist there was some unexpected failure
        # in canonicalizing.
        #
        canonicalResultsFile = os.path.join(resultsdir, canonicalName)
        if not (os.path.isfile(canonicalResultsFile) and \
                os.access(canonicalResultsFile, os.R_OK)):
            print("canonicalMatchCriteria: results file not found")
            raise testcase_exceptions.BadFile(canonicalResultsFile, "Error testing canonical results of testcase %s filename %s...file not found and no failure marker file" % \
                        (testcase.name, canonicalResultsFile))
        correctCanonicalFile = os.path.join(testsetdir, canonicalName)
        if not (os.path.isfile(correctCanonicalFile) and \
                os.access(correctCanonicalFile, os.R_OK)):
            print("canonicalMatchCriteria: required correct canonical file {} not found".format(correctCanonicalFile))
            return (False, "Canonical form of %s could not be checked; test case file %s is missing" % (fname, correctCanonicalFile))
#            raise testcase_exceptions.BadTestcaseSpecification(testcase.name, 
#                    "canonicalMatchCriteria: required correct canonical file %s not found" % correctCanonicalFile)
            
        try:
            if not filecmp.cmp(canonicalResultsFile, correctCanonicalFile):
                return (False, CANONICALMATCHFAILMESSAGE %fname)
        except OSError as e:
            print("UNEXPECTED ERROR: in successcriteria.canonicalMatchCriteria: {}".format(repr(e)))
            raise testcase_exceptions.AbandonTestcase(testcase.name, \
                 "UNEXPECTED ERROR: in successcriteria.canonicalMatchCriteria: %s" % \
                 repr(e))


    #
    # Fall through if no checks failed
    #
    return (True, "File(s) %s is/are correct" % namesChecked)


#
#                 fileMatchCriteria
#
#      The criteria is either a filename (e.g. "stdout") 
#      or an array of filenames.
#
#      For each, the results file is compared to the same named file in the 
#      test set directory
#      
def fileMatchCriteria(testcase, criteria):
    # Make sure we have in iterable array of criteria (handle case where
    # user supplied a single filename)
    if isinstance(criteria, str):
        crit = [criteria]
    else:
        crit = criteria

    #
    # Check each file. If bad, immediately return false
    # fname is short form of name, such as stderr
    # fileName is as it appears in results and testsets:  test1.stderr
    #
    namesChecked = []
    for fname in crit:
        namesChecked.append(fname)
        fileName = testcase.name + '.' + fname
        testsetdir = testcase.property("testsetdir")
        resultsdir = testcase.resultsDirectory()
        resultsFile = os.path.join(resultsdir, fileName)
        if not (os.path.isfile(resultsFile) and \
                os.access(resultsFile, os.R_OK)):
            return (False, "Results file {} not found".format(fname))
        correctFile = os.path.join(testsetdir, fileName)
        if not (os.path.isfile(correctFile) and \
                os.access(correctFile, os.R_OK)):
            print("fileMatchCriteria: required correct file file {} not found".format(correctFile))
            return (False, "File match of %s could not be checked; test case file %s is missing" % (fname, correctFile))
#            raise testcase_exceptions.AbandonTestset("fileMatchCriteria: required correct file file %s not found" % correctFile)
            
        try:
            if not filecmp.cmp(resultsFile, correctFile):
                return (False, "Contents of results file %s are incorrect" % fname)
        except OSError as e:
            print("UNEXPECTED ERROR: in successcriteria.fileMatchCriteria: {}".format(repr(e)))
            raise testcase_exceptions.AbandonTestset( \
              "UNEXPECTED ERROR: in successcriteria.fileMatchCriteria: %s" % \
                  repr(e))

    #
    # Fall through if no checks failed
    #
    return (True, "File(s) %s matched testcase criteria" % namesChecked)
#
#                 emptyFileCriteria
#
#      The criteria is either a filename (e.g. "stdout") 
#      or an array of filenames.
#
#      For each, the results file is compared to the same named file in the 
#      test set directory
#      
def emptyFileCriteria(testcase, criteria):
    # Make sure we have in iterable array of criteria (handle case where
    # user supplied a single filename)
    if isinstance(criteria, str):
        crit = [criteria]
    else:
        crit = criteria

    #
    # Check each file. If not empty, immediately return false
    # fname is short form of name, such as stderr
    # fileName is as it appears in results and testsets:  test1.stderr
    #
    namesChecked = []
    for fname in crit:
        namesChecked.append(fname)
        fileName = testcase.name + '.' + fname
        resultsdir = testcase.resultsDirectory()
        resultsFile = os.path.join(resultsdir, fileName)
        if not (os.path.isfile(resultsFile) and \
                os.access(resultsFile, os.R_OK)):
            return (False, "Results file {} not found".format(fname))
        try:
            if os.path.getsize(resultsFile) > 0:
                return (False, "File %s is not empty" % fname)
        except OSError as e:
            print("UNEXPECTED ERROR: in successcriteria.emptyFileCriteria: {}".format(repr(e)))
            raise testcase_exceptions.AbandonTestset( \
              "UNEXPECTED ERROR: in successcriteria.emptyFileCriteria: %s" % \
                  repr(e))

    #
    # Fall through if no checks failed
    #
    return (True, "File(s) %s is (are) empty" % namesChecked)

#
#                 noValgrindErrorsCriteron
#
#      The criteria is either the string "Default" or "default"  or ""
#      or a message to be used as the reason if there are valgrind errors
#      
#      
NO_VALGRIND_FAILURE_MSG="Valgrind did not run, assuming no valgrind errors"
DEFAULT_VALGRIND_FAILURE_MSG="Valgrind reported errors"
VALGRIND_SUCCESS_MSG="No Valgrind errors reported"

def noValgrindErrorsCriterion(testcase, failure_msg):
    # Make sure we have in iterable array of criteria (handle case where
    # user supplied a single filename)
    if ((failure_msg == "") or
        (failure_msg.lower() == "default")):
        failure_msg = DEFAULT_VALGRIND_FAILURE_MESSAGE
        

    #
    #  Get the dict that matches the valgrind log in the test_results dir
    #
    #  (Too bad we don't have the partially built targetDict from our
    #  caller here, as that tends to have the same information already
    #  available).
    #
    valgrindDict = logproperties.valgrindDictionary(testcase)
    if not valgrindDict:
        return(True, NO_VALGRIND_FAILURE_MSG)

    #
    # Make sure theres a valgrind error count recorded, and get it
    #
    valgrind_error_count = valgrindDict.get("Errors", None)
    if valgrind_error_count == None:
            raise testcase_exceptions.AbandonTestset( \
              "UNEXPECTED ERROR: in successcriteria.noValgrindErrorsCriteria: valgrind was run but log does not include a valgrind \"Errors\" entry.")

    #
    #  Test fails if error_count > 0
    #
    if int(valgrind_error_count) > 0:
        return(False, failure_msg)
    else:
        return(True, VALGRIND_SUCCESS_MSG)

#
#           hansonExceptionCriterion
#
#    If criteria is True then this test passes if there was an exception
#    otherwise the test passes if there was not an exception
#

HansonExceptionRE0 = re.compile(r"Uncaught exception")
HansonExceptionRE1 = re.compile(r"aborting")

def hansonExceptionFound(testcase):
    result = True
    resultsdir = testcase.resultsDirectory()
    fileName = os.path.join(resultsdir, testcase.name + '.' + "stderr")
    if not (os.path.isfile(fileName) and \
                os.access(fileName, os.R_OK)):
        result = False
    else:
        try:
            with open (fileName, "r") as errfile:
                lastTwoLines = errfile.readlines()[-2:]
        except Exception as e:
            print("Hanson exception reading {}".format(filename), file=sys.stderr)
        if len(lastTwoLines) == 2:
            result = HansonExceptionRE0.match(lastTwoLines[0]) and \
                HansonExceptionRE1.match(lastTwoLines[1]) 
        else:
            result = False

    return result

def hansonExceptionCriterion(testcase, criteria):
    exceptionFound = hansonExceptionFound(testcase)
    # crude approximation to result = exceptionFound xor result
    result = exceptionFound if criteria else not exceptionFound
    msgText = "terminated with" if exceptionFound else "did not terminate with"    
    return (result, "Program %s Hanson exception" % msgText)



def conjunctionCriterion(testcase, criteria):
    TCAssert(isinstance(criteria, dict), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria used in conjunction must be Python dict" % \
        testcase.name))
    successfulMsgs = []
    for criterion, value in criteria.items():
        result, msg = HANDLERS[criterion](testcase, value) 
        successfulMsgs.append(msg)
        if not result:
            return (False, "%s" % msg)
        
    # All tests passed
    if len(successfulMsgs) > 1:
        successfulMsgs = "(%s)" % " AND ".join(successfulMsgs)
    elif len(successfulMsgs) ==1:
        successfulMsgs = successfulMsgs[0]
    else:
        successfulMsgs = ""
    return (True, successfulMsgs)

        
def disjunctionCriterion(testcase, criteria):
    TCAssert(isinstance(criteria, dict), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria used in disjunction must be Python dict" % \
        testcase.name))
    failedMsgs = []
    for criterion, value in criteria.items():
        result, msg = HANDLERS[criterion](testcase, value)
        failedMsgs.append(msg)
        if result:
            return (True, msg)
    # All tests failed
    if len(failedMsgs) > 1:
        failedMsgs = "(%s)" % " AND ".join(failedMsgs)
    elif len(failedMsgs) == 1:
        failedMsgs = "%s" % failedMsgs[0]
    else:
        failedMsgs = ""
        
    return (False, failedMsgs)


def negationCriterion(testcase, criteria):
    TCAssert(isinstance(criteria, dict), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria used in negation must be Python dict" % \
        testcase.name))
    TCAssert(len(criteria) == 1, testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria used in negation must contain ONE criterion" % \
        testcase.name))
    # The following will loop only once, but it's a convenient way to
    # get the one key, which could be anything
    for criterion, value in criteria.items():
        result, msg = HANDLERS[criterion](testcase, value)
        if result:
            return False, "%s" % msg
        else:
            return True, "%s" % msg
    assert True, "Internal error: negationCriterion looped more than once for testcase %s" % testcase.name

#
#                        failureMessageCriterion
#
#       * criterion is list of length two
#       * criterion[0] is name of file with the message, such as stderr
#       * criterion[1] is criterion to test. Failure causes message to print
#

def failureMessageCriterion(testcase, criteria):
    TCAssert(isinstance(criteria, list), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria used in failureMessageCriterion must be Python list" % \
        testcase.name))
    TCAssert(len(criteria) == 2, testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criteria used in failureMessageCriterion must contain ONE criterion (an array of 2 elements)" % \
        testcase.name))

    criterion = criteria[1]

    TCAssert(isinstance(criterion, dict), testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criterion used in messageCriterion must be Python dict" % \
        testcase.name))
    TCAssert(len(criterion) == 1, testcase_exceptions.BadTestsetSpecification(\
        "Testcase %s success criterion used in messageCriterion must contain ONE criterion" % \
        testcase.name))
    # The following will loop only once, but it's a convenient way to
    # get the one key, which could be anything
    for criterionName, value in criterion.items():
        result, msg = HANDLERS[criterionName](testcase, value)
        if result:
            return True, "%s" % msg
        else:
            #
            #  Get name of the file with the message and read last line as the msg
            #
            file = criteria[0]
            resultsdir = testcase.resultsDirectory()
            msgFileName = os.path.join(resultsdir, testcase.name + '.' + file)
            if not (os.path.isfile(msgFileName) and \
                        os.access(msgFileName, os.R_OK)):
                return (False, "INTERNAL TESTING ERROR: messageCriterion message file %s is not readable" % file)
            else:
                try:
                    with open (msgFileName, "r") as errfile:
                        failureMsg = errfile.readlines()[-1:]
                except Exception as e:
                    return (False, "INTERNAL TESTING ERROR: messageCriterion exception reading message file %s" % msgFileName)

            #
            # If we got something, use it
            #
            if len(failureMsg) == 1 and failureMsg[0]:
                failureMsg = failureMsg[0].rstrip()
            else:
                failureMsg = "INTERNAL TESTING ERROR: messageCriterion no mess in file %s testcase=%s" % (msgFileName,testcase.name)
            return False, "%s" % failureMsg

    assert True, "Internal error: messageCriterionCriterion looped more than once for testcase %s" % testcase.name


#
#                Map of handlers for criteria keywords
#
#      NOTE: this must be at the end of this source file so all
#      referenced methods are defined.
#

HANDLERS = { 
    "exitcode" : exitcodeCriterion,
    "signal_name" : signal_nameCriterion,
    "signal_value" : signal_valueCriterion,
    "hansonException" : hansonExceptionCriterion,
    "timedout" : timedoutCriterion,
    "canonicalMatch" : canonicalMatchCriteria,
    "fileMatch" : fileMatchCriteria,
    "emptyFile" : emptyFileCriteria,
    "missingexecutable" : missingExecutableCriterion,
    "AND" : conjunctionCriterion,
    "OR" : disjunctionCriterion,
    "NOT" : negationCriterion,
    "and" : conjunctionCriterion,
    "or" : disjunctionCriterion,
    "not" : negationCriterion,
    "failureMessage" : failureMessageCriterion,
    "noValgrindErrors" : noValgrindErrorsCriterion
}
