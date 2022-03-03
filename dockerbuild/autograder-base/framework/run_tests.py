#!/usr/sup/bin/python
# NEEDSWORK: above should be /bin/env python3 (Noah 12/29/2020)

#***********************************************************************************
#
#                               run_tests
#
#        Author: Noah Mendelsohn
#      
#   
#        Runs a set of comp 40 grading tests.
#
#        When running, the current directory must (typically)  be the parent of 
#        the individual compiled assignment directories. This will run
#        the named tests on every directory of the form:
#
#              studentlogin.nnn
#
#        I.e. a directory as named by the Tufts CS Dept "provide" utility.
#        For COMP 40, these directories are typically first copied for 
#        testing using "clone-assignment" and then "compile-assignment", after
#        which "run_tests" (this script) can be used to do the actual testing.
#
#        Arguments: path to directory in which testcase is defined
#
#        Actually, more variations are now supported:
#
#                usage: run_tests.py [-h] [-localdir] [-nproc NPROC]
#                                    testset [studentdirs [studentdirs ...]]
#                
#                positional arguments:
#                  testset       testset directory
#                  studentdirs   student directory(s)
#                
#                optional arguments:
#                  -h, --help    show this help message and exit
#                  -localdir     use the current dir for executable and put results in
#                                ./<testsetname>.testresults
#                  -nproc NPROC  number of parallel forks
#                
#***********************************************************************************

import os, sys, pwd, set_of_tests, errno, re, argparse
import fcntl  # for locking error log when running in parallel

from testcase_exceptions import AbandonStudent, AbandonTestset

from utilities import mkdir

ERROR_LOG="run_tests_errors.txt"

TESTCASEFILE = 'testset.json'
# Each 
TEST_DIR_SYMLINK_NAME = ".tdir"

TESTRESULTSCONTAINERDIR = 'test_results'
SUMMARYCONTAINERDIR = 'test_summaries'

submissionDirPattern= re.compile(r"^([^\.]+)\.([\d]+)$")  # match xxxxx.nnn 


#---------------------------------------------------------------
#                Utility functions
#---------------------------------------------------------------

#
#                     parseargs
#
#       Use python standard argument parser to parse arguments and provide help
#
def parseargs():
    parser = argparse.ArgumentParser("Build a testset file from template(s)")
    parser.add_argument("-localdir", help="use the current dir for executable and put results in ./<testsetname>.testresults", action="store_true")
    parser.add_argument("-nproc", help="number of parallel forks",  \
                            default="0")
    parser.add_argument('testset', help="testset directory")
    parser.add_argument('studentdirs', nargs="*", help="student directory(s)")
    args = parser.parse_args()
    return parser.parse_args()

#
#       Given a student container directory, compute the
#       corresponding test container name
#
def testContainerDir(userdir):
    testContainer = userdir + '.' + TESTRESULTSCONTAINERDIR
    mkdir(testContainer)
    return testContainer

#
#       Given a student container directory, compute the
#       corresponding test container name
#
def summaryContainerDir(userdir):
    summaryContainer = userdir + '.' + SUMMARYCONTAINERDIR
    mkdir(summaryContainer)
    return summaryContainer

#
#                    mkTestdirSymlink
#
#    Often it is necessary to pass into a program being tested
#    an input file in the test directory. The pathnames
#    such directories can be long and inconvenient. To help with this
#    another problems, before running tests we add a symlink from
#    the results directory the test directory. Assuming the link is .tdir
#    then a program can be tested with file AAA by invoking:
#
#             programtotest .tdir/AAA
#
def mkTestdirSymlink(testconfig, env):
    try:
        os.symlink(env["testdir"], \
                   os.path.join(env["resultscontainerdir"],TEST_DIR_SYMLINK_NAME))
    except OSError as e:
        # 
        #  If it's not a file exists error, print (existing file is benign
        #  as it usually comes from repeating the test run. NEEDSWORK: Would be a problem
        #  if the test specification changed what we are linking as old
        #  link will stick. 
        #
        if e.errno != 17:           # check for file already exists error
            print("Error creating simlink for testdir ({}): {}".format(e.errno, e.strerror))
    except Exception as e:
        print("Error creating symink for testdir({})".format(e))
        raise


#---------------------------------------------------------------
#
#                         doASetofTests
#
#    Run each test in set, first making sure it's properly specified 
#
#---------------------------------------------------------------
def doASetofTests(testconfig, env):
    try:
        testconfig.runTests(env)
    except OSError as e:
        print("Error running tests({}): {}".format(e.errno, e.strerror))
    except Exception as e:
        print("Error running tests({})".format(e))
        raise
#---------------------------------------------------------------
#                          Main
#---------------------------------------------------------------

args = parseargs()

workingDir = os.getcwd()                # remember where we're running

#
# Locate the testcase descriptor directory named by the user
#
testDir = args.testset

absTestDir = os.path.abspath(testDir)
assert os.path.isdir(testDir), "Test directory \"%s\" does not exist" % testDir


#
# Env is passed into the individual tests to set parameters
#

env = {
          "testdir" : absTestDir,
          "testeruid" : pwd.getpwuid(os.getuid()).pw_name,
          "testsetname" : os.path.split(absTestDir)[-1]
       }
#
#   Load the details of the testcases from the JSON testcase description file
#   This creates an instance of testcase.SetofTests, which we assign
#   here to testconfig.
#
os.chdir(env["testdir"])

try:
    testconfig = set_of_tests.createTestsfromJSON(TESTCASEFILE)
except Exception as e:
    print("Error loading test configuration: {}".format(str(e)))
    raise

os.chdir(workingDir)

#
#                    Run the Tests
#
#   If -localdir switch is not provided:
#   ------------------------------------
#
#   For each students submission subdirectory, run the tests
#   For a submission directory:
# 
#                 somestudent.3   (their 3rd submission)
#
#   This will create (if necessary) and populate
#
#                somestudent.3.test_results/testsetname
#
#   Within that, the outputfiles from individual tests will
#   typically include the name of the test, e.g.:
#
#                somestudent.3.badchartest.stdout
#
#   To actually run the test, we add to the environment object
#   specific to this student and test (such as the directories just mentioned)
#   and iterate calling the runTest method on each test object, passing in
#   the environment object.
#
#   If -localdir switch is provided:
#   --------------------------------
#  
#   Same as above but the studentdir is assumed to be the current dir
#   and its name is not checked and the results become a subdirectory
#   of the current directory with the name "<testsetname>.testresults"
#

#
#   Remove any error log from previous run
#
try:
    os.remove(ERROR_LOG)
except FileNotFoundError as e:
    pass

explicitDirlist = False
didSomething = False
if args.localdir:
    dirlist = [workingDir]
    print("WARNING(run_tests.py): --local dir option has bugs, leaves some files in parent dir", file=sys.stderr)
elif len(args.studentdirs) > 0:
    dirlist = args.studentdirs
    def stripslash(s):
        return s.rstrip("/")
    dirlist = list(map(stripslash, dirlist))
    explicitDirlist = True
else:
    dirlist = os.listdir(workingDir)

#
#  If nprocs used to request forking, then do it,
#  dividing dirlist into roughly equal pieces for each fork
#


if args.localdir:
    badDirs = []                  # assume any local dir is to be trusted
    # if localdir, dirlist was set above
else:
    badDirs = [x for x in dirlist if not submissionDirPattern.match(os.path.basename(x))]
    dirlist = [x for x in dirlist if submissionDirPattern.match(os.path.basename(x))]


if len(badDirs) > 0:
    print("Skipping non-student directory(s): {}".format(badDirs), file=sys.stderr)

nproc = int(args.nproc)

if nproc > 1:
    print("********NPROC = {} ***********".format(nproc))

# ORIGINAL BLOCKED FORKING CODE
#if nproc > 0:
#    print("Forking {} ways".format(nproc), file=sys.stderr)
#    # number of files per process...be sure not to round down to zero
#    # Bug fix for Python 3: following changed to integer division // (Noah 12/29/2020)
#    chunkSize = (len(dirlist) + nproc -1) // nproc
#    # one sublist per fork
#    splitdir=[dirlist[x:min(x+chunkSize, len(dirlist))] \
#                  for x in range(0, len(dirlist), chunkSize)]
#        
#    procstostart = len(splitdir) - 1
#    inParent = False
#    for i in range(procstostart):
#        dirlist = splitdir[i]
#        childid = os.fork()
#        if childid == 0:            # if child go do work
#            print("********CHILD = {} ***********".format(i))
#            break;
#    if childid !=0:
#        print("********PARENT  ***********")
#        inParent = True
#        dirlist = splitdir[-1] # last chunk to parent
        

    available_procs = nproc
    count_to_grade = len(dirlist)
    num_graded = 0
    
    # We'll be popping off the list, and it's more convenient 
    # if we actually work in alphabetical order, so we pop
    # from a reversed list
    dirs_not_graded = list(reversed(dirlist))

    # 
    # Until we've graded them all
    #
    while num_graded < count_to_grade:
        inParent = False
#        print(f"DEBUG: Loop top num_graded = {num_graded} and count_to_grade={count_to_grade}")
#        print(f"DEBUG: ...dirs_not_graded={repr(dirs_not_graded)}")
        # The old version relied on this being a list. Now it's
        # always a singleton with the new forking logic that does
        # one dir per fork. We leave the logic in case we ever want to
        # go back.
        if available_procs > 0 and len(dirs_not_graded) > 0:
            dirlist = [dirs_not_graded.pop()]  # see comment below for why called dirlist            
            childid = os.fork()
                        # if child go do work
            if childid == 0:
#                print(f"********CHILD PROCESS = {nproc - available_procs} for dir={dirlist[0]} {inParent} ***********")
                break;
            else:
                inParent = True
                available_procs -= 1              # one less proc is available 
        # In parent for sure
        if available_procs == 0 or len(dirs_not_graded) == 0:
            os.wait()
            num_graded += 1
            available_procs += 1
            print(f"Have now graded {num_graded} out of {count_to_grade}")
    #
    #       We're done looping
    #        -- in the child process, we need to go on and do the work
    #        -- in the parent we're all done, so we just exit. 
    #       NEEDSWORK: Later we may find a way to reflect errors in the 
    #                  exit codes, but for now, exit(0)
    if inParent:
            sys.exit(0)



        
#==============================================================================================
#                 THIS CODE RUNS ONLY IN THE CHILD PROCESSES THAT ACTUALLY
#                 DO THE GRADING (or in the only process if nproc>1
#==============================================================================================

# 
#  Note: When --nproc >1 used, len(dirist) will always be 1
#        When nproc is 1 (default), then the dirlist will contain all submissions 
#
#print(f"DEBUG: In child dirlist={dirlist}")
try:
    for studentDir in dirlist:
#        print(f"DEBUG: In child studentDir={studentDir}")
        try:
            absStudentDir = os.path.abspath(studentDir)

            #
            #       If this doesn't seem to actually be a student
            #       submission directory, skip it (don't do this check
            #       if we're working in localdir)
            #
            if (not args.localdir) and ((not os.path.isdir(studentDir)) or \
                                        (not submissionDirPattern.match(studentDir))):
                if explicitDirlist:
                    print("Warning, skipping {}: is not directory or doesn't match pattern studentname.\n".format(studentDir))
                continue
        
            didSomething = True
        
            print("\nStarting: {}".format(studentDir))
        
            # testcontainer contains all the tests for that student
            # Within that we have a subdir to contain the results of this test set
            # Within that, individual test results are coded in the output filenames
            testcontainer = testContainerDir(absStudentDir)
        
            if args.localdir:
                resultscontainerdir = mkdir(os.path.join(workingDir, \
                                                         env["testsetname"] + \
                                                         ".testresults"))
            else:
                resultscontainerdir = mkdir(os.path.join(testcontainer, \
                                                         env['testsetname']))

            summarycontainerdir = summaryContainerDir(absStudentDir)
    
            #
            # Set student-specific environment vars for test runner code
            #
            env["studentdir"] = studentDir       # local name of dir e.g. studentname.3
            env["studentabsdir"] = os.path.abspath(studentDir)  # full path
            if args.localdir:
                env["studentuid"] = env["testeruid"]
            else:
                env["studentuid"] = studentDir.split('.')[0]
            env["summarycontainerdir"] = summarycontainerdir
            env["resultscontainerdir"] = resultscontainerdir

            #
            # Make a simlink from resultscontainerDir to testdir
            # This gives shorthand name usable in tests and results
            #
            mkTestdirSymlink(testconfig, env)

            #
            # Run the tests
            #
            doASetofTests(testconfig, env)

            os.chdir(workingDir)               # needed so outer for loop iterates properly
        except AbandonStudent as e:
            print("AbandonStudent exception raised (studentDir={}): {}".format(studentDir, e.msg), file=sys.stderr)
            print("Continuing with next student", file=sys.stderr)
   

        if not didSomething:
            print("run_tests: current working directory ({}) does not appear to have student submissions".format(workingDir))

except AbandonTestset as e:
    print("AbandonTestset exception raised: {}".format(e.msg), file=sys.stderr)
    sys.exit(1)

