#!/bin/env python3
#
#                              gradeit.py
#                   Author: Noah Mendelsohn
#
#    A control panel application to manage the process of grading student
#    submissions using the grading framework.
#
#    usage: gradeit.py [-h] [--explain] [--hwdir HWDIR]
#                  [--output_stream OUTPUT_STREAM] [--student STUDENT]
#                  [--nproc NPROC]
#                  <subcommand>
#
#    Most subcommands are implemented as one more command line
#    commands. If called with the --explain switch, this program will
#    write the commands to stdout instead of executing them, allowing 
#    you to be sure that what's about to happen is what you intend.
#
#    Subcommands:
#    ------------
#
#    validate            Validate the testing configuration
#    clone_all           Clone all student submissions for testing
#    clean_clones        Remove all cloned student submissions
#    run_tests           Run tests (default is all students)
#    clean_results       Remove test_summaries and test_results in
#                        student_clones
#    report              Run full report on all test results to output_stream
#                        or stdout
#    report4zip          Put all reports and grades in individual files for
#                        zipping
#    clean_TO_ZIP        Remove all reports and grades in TO_ZIP
#    zip_grade_files     Make a zip file with all grades and reports
#    remove_zipfile      Remove the zip file that's prepared for Gradescope
#
#    optional arguments:
#    -------------------
#    
#    -h, --help            show this help message and exit
#    --explain             Echo commands to stdout instead of running them
#    --hwdir HWDIR         Directory where hw_conf.json lives
#    --output_stream OUTPUT_STREAM
#                          Write output here (default is stdout)
#    --student STUDENT     Test only this student
#    --nproc NPROC         Number of parallel forks for run_tests
#
#    NEEDSWORK: arguments that aren't used by a subcommand are silently ignored
#    
#    NEEDSWORK: zip_grade_files should copy master copy of grade_reports.py
#               from $TFB to TO_ZIP, so fixes to the master get picked up.
#



import grade_reports           # used for getting filenames in TO_ZIP/GradeReports
import sys, os, os.path, argparse, glob
import tempfile
import json
import backtick         # Like shell `cmd` runs commands and captures output


#---------------------------------------------------------------
#                    CONFIGURATION CONSTANTS
#
#     NEEDSWORK: Make sure all of these are actually used
#---------------------------------------------------------------
MAX_UNTESTED_TO_LIST = 6  # when validating tests run, max to list explicitly
CLONE_FILE_GLOB_PATTERN = "*.[1-9]"
RESULTS_GLOB_PATTERN = "*.test_*"
STUDENT_CLONES_KEY = "student_clones"
BIN_KEY = "bin_dir"
HW_CONFIG_FILENAME = 'hw_conf.json'

TESTSET_DIR_KEY = "testset_dir"  # in assignment parts
TESTSET_CLEAN_KEY = "testset_clean_command"  # in assignment parts
TESTSET_BUILD_KEY = "testset_build_command"  # in assignment parts

ZIP_DIR_KEY = "zip_dir"
GRADE_REPORTS_FOR_ZIPPING_DIR = "./TO_ZIP/GradeReports"
CLEAN_ZIP_REPORTS_COMMAND_KEY = "clean_zip_reports_command"
CREATE_ZIP_COMMAND_KEY = "create_zip_command"
REMOVE_ZIP_COMMAND_KEY = "remove_zip_command"
GRADE_REPORTS_DIR_KEY = "grade_reports_dir"

#************************************************************************
#                     parseargs
#
#       Use python standard argument parser to parse command line
#       arguments and provide help.
#
#       NEEDSWORK: To allow format where switches are ahead of subcommand
#                  all switches are given as args to main command.
#                  Thus, we are not warning when we should if a supplied
#                  switch is not used by the subcommand (e.g. specifying 
#                  --student for "validate", which does not check that
#                  switch.
#
#************************************************************************
SUBCOMMANDS = [("validate", "Validate the testing configuration"),
               
               ("make_testsets", "Clean and rebuild testsets"),
               ("clone_all", "Clone all student submissions for testing"),
               ("clean_clones", "Remove all cloned student submissions"),
               ("run_tests", "Run tests (default is all students)"), 
               ("clean_results", 
                    "Remove test_summaries and test_results in student_clones"),
              
               ("report", "Run full report on all test results to output_stream or stdout"),
               ("report4zip", "Put all reports and grades in individual files for zipping"),
               ("clean_TO_ZIP", "Remove all reports and grades in TO_ZIP"),
               ("zip_grade_files", "Make a zip file with all grades and reports"),
               ("remove_zipfile", "Remove the zip file that's prepared for Gradescope")
           ]


#
#     Subclass the standard argument parser to provide full help
#     whenever there is a command line error.
#
#     See: https://stackoverflow.com/questions/4042452/display-help-message-with-python-argparse-when-script-is-called-without-any-argu
#
class GradeitArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def parseargs(): 

    parser = GradeitArgParser("gradeit.py",
                                     description="Run commands to configure or perform grading",
                                     epilog="For subcommand help do:\ngradeit.py <subcommand> --help")
#    parser.add_argument('subcommand', help="Identify the function to be performed")
    parser.add_argument("--explain", help="Echo commands to stdout instead of running them", action="store_true")
    parser.add_argument("--hwdir", nargs=1, required=False, default=["."],
                        help="Directory where hw_conf.json lives")
    parser.add_argument("--output_stream", nargs=1, required=False, default=[sys.stdout],
                        help="Write output here (default is stdout)")
    parser.add_argument("--student", 
                                                nargs=1, required=False, 
                                                help="Test only this student",
                                                default=[None])

    parser.add_argument("--nproc", 
                                   help="Number of parallel forks for run_tests",  \
                                   default="0")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
#    parser.add_argument("subcmdargs", nargs="*")
    subparser_objects = {}        # not sure this is needed
    for subcommand, helpstr in SUBCOMMANDS:
        subparser = subparsers.add_parser(subcommand,
                                          description=helpstr, 
                                          help=helpstr)
#        subparser.add_argument("--explain", help="Echo commands to stdout instead of running them", action="store_true")
#        subparser.add_argument("--hwdir", nargs=1, required=False, default=["."])
#        subparser.add_argument("--output_stream", nargs=1, required=False, default=[sys.stdout])
        
        subparser_objects[subcommand] = subparser
                                             
    #
    # Parse all the arguments
    #
    return parser.parse_args()

#************************************************************************
#                Utility functions
#************************************************************************

#
#                     students_from_files_in_dir
#
#      Given directory and a pattern, where the pattern
#      matches filenames like <student>.whatever
#
#      return a set the students who are named
#


def students_from_files_in_dir(dir, pattern):
    cwd = os.getcwd()
    os.chdir(dir)
    set_of_students = set()
    for f in glob.iglob(pattern):
        student_name = f.split('.')[0]
        set_of_students.add(student_name)
    os.chdir(cwd)
    return set_of_students

#
#                     error_print
#
#      Write an error message. 
#      NOTE: for subcommands like "report" we want to be able to 
#      use shell redirection and get clearn results, e.g.
#          gradeit.py --student somestud.1 report > somestud_report.txt
#
#      Therefore, any output that we do not want redirected with
#      stdout should be written using error_print. 
#
        
def error_print(s):
    print(s, file=sys.stderr)


#
#    Local version of os.chdir with explain logging
#
def chdir(d):
    global args
    if args.explain:
        print("cd " + d, file=output_stream)
    os.chdir(d)

#
#                    has_required_keys
#
#       Make sure all required keys are in the config
#
def has_required_keys(hw_config, keys):
    retval = True
    for k in keys:
        if not k in hw_config:
            print("ERROR: {} is missing required key {}".
                  format(HW_CONFIG_FILENAME, k))
            retval = False
    return retval

#---------------------------------------------------------------
#                    get_hw_config
#
#     hw_config is a json file that tells us where to find everything
#     relating to this homework, including testsets, student submissions, etc.
#     and it also has information about which commands to run to, e.g.
#     rebuild testsets.
#
#---------------------------------------------------------------

def get_hw_config():
    try:
        with open(HW_CONFIG_FILENAME) as json_file:
            return json.load(json_file)
    except IOError as e:
        print(("Could not open homework configuration file {}\nMake sure it is in your current directory or use the --hwdir switch to supply the directory".
               format(os.path.abspath(HW_CONFIG_FILENAME))), file=sys.stderr)
        sys.exit(4)

#******************************************************************
#
#                         SUBCOMMAND HANDLERS
#
#     This is where the actual work is done for handling command
#     line requests
#
#******************************************************************

#---------------------------------------------------------------
#                    validate
#
#     Check to make sure all necessary environment variables are
#     set, that testset dirs are reachable and in good shape, etc.
#
#     Returns: True iff all validity conditions met
#
#     NEEDSWORK: add more validations
#
#---------------------------------------------------------------

ENVIRONMENT_VARS_CONF_KEY = "required_environment_vars"

#
#  Helper function to print some status reports when validating
#
def validate_test_summaries(hw_config, quiet):
    #
    # Get list of students who have submitted
    #
        # Make sure the keys we need are there
    if not has_required_keys(hw_config, 
                             [CLEAN_CLONES_COMMAND_KEY]):
        return
    student_clones_dir = hw_config[STUDENT_CLONES_KEY]
    submitting_students = students_from_files_in_dir(student_clones_dir,
                                                     CLONE_FILE_GLOB_PATTERN)
#    error_print("Submitting students: " + repr(list(submitting_students)))

    #
    #  See whether tests have been run for each assignment part
    #
    assignment_parts = hw_config.get(ASSIGNMENT_PARTS_KEY, [])
    if assignment_parts:
        part_names = [ap["name"] for ap in assignment_parts]
#        error_print("Part names: " + repr(part_names))
        #
        # For each assignment part in hw_config, get lists of students for which
        # tests appear to have been run vs not.
        #
        if not quiet:
            error_print("Report on processed submissions (prior to attempting command)")
        for pn in part_names:
            tested_students = []
            untested_students = []
            olddir = os.getcwd()
            chdir(student_clones_dir)
            for student in submitting_students:
                # look for a file like student1.3.test_summaries/pgm1
#               error_print("IN DIRECTORY {} ABOUT TO GLOB {}".format(os.getcwd(), "{}.*.test_summaries/{}".
#                                              format(student,pn)))
                test_summaries_for_student = glob.glob("{}.*.test_summaries/{}".
                                              format(student,pn))
#                error_print("TEST SUMMARIES LIST FOR STUDENT: " + repr(list(test_summaries_for_student)))
                if (len(test_summaries_for_student) == 1 and 
                    (os.path.isdir(test_summaries_for_student[0]))):
                    tested_students.append(student)
                else:
                    untested_students.append(student)

            os.chdir(olddir)

            #
            #  Report on testing for this part
            # 
            num_submitting = len(submitting_students)
            num_untested = len(untested_students)
            if num_submitting:
                #
                # There were some submitting students we should have tried to test
                #
                if len(tested_students) == num_submitting:
                    error_print("{}: tests run for all {} submitting students".format(pn, num_submitting))
                elif num_untested == num_submitting:
                    error_print("{}: NO tests run for any of the {} submitting students".format(pn, num_submitting))
                else:
                    # Some were tested, some not
                    if num_untested <= MAX_UNTESTED_TO_LIST:
                        msg=""
                        num_to_error_print = num_untested
                    else:
                        msg="(partial list)"
                        num_to_error_print = MAX_UNTESTED_TO_LIST
                    error_print(("{} tests run on {} of {} submitting students:\n"
                           .format(pn, len(tested_students), num_submitting)) +
                          ("...UNTESTED STUDENTS{}: {}"
                           .format(msg, ", ".join(list(sorted(untested_students))[:num_to_error_print]))))
            else:
                error_print("{}: no submitting students".format(pn))
                
    else:
        error_error("ERROR: {} is missing required key {}".
                    format(HW_CONFIG_FILENAME, ASSIGNMENT_PARTS_KEY))





def validate_environs(hw_config):
    retval = True
    # required_environment_vars is list of vars like $TFB. Make a list without
    # the $ (and tolerate those that already don't have it)
    required_vars = map(lambda s: s.lstrip('$'), hw_config.get(ENVIRONMENT_VARS_CONF_KEY,
                                                               []))
    for v in required_vars:
        if not v in os.environ:
            error_print("ERROR: Required environment variable ${} not defined\n".
                        format(v))
            retval = False
    return retval
    
ASSIGNMENT_PARTS_KEY = "assignment_parts"
TESTSET_DIR_KEY = "testset_dir"
    
def validate_testsets(hw_config):
    retval = True
    assignment_parts = hw_config.get(ASSIGNMENT_PARTS_KEY, [])
    if assignment_parts:
        for ap in assignment_parts:
            testset_dir = ap.get(TESTSET_DIR_KEY, None)
            if testset_dir:
                if not os.path.isdir(testset_dir):
                    testset_name = ap.get("name", "")
                    error_print("ERROR: testset {} directory {} does not exist".
                                format(testset_name, os.path.abspath(testset_dir)))
                    retval = False
    else:
        error_print("ERROR: {} is missing required key {}".
                    format(HW_CONFIG_FILENAME, ASSIGNMENT_PARTS_KEY))
        retval = False
    return retval
    
def validate(hw_config, quiet):
    retval = True
    retval = retval and validate_environs(hw_config)
    retval = retval and validate_testsets(hw_config)
    if not ((STUDENT_CLONES_KEY in hw_config) and os.path.isdir(hw_config[STUDENT_CLONES_KEY])):
        error_print("ERROR: {} not in {} or supplied directory not available".
                    format(STUDENT_CLONES_KEY, HW_CONFIG_FILENAME))
        retval = False
    if not ((BIN_KEY in hw_config) and os.path.isdir(hw_config[BIN_KEY])):
        error_print("ERROR: {} not in {} or hw/bin directory does not exist".
                    format(BIN_KEY, HW_CONFIG_FILENAME))
        retval = False

    if not ((ZIP_DIR_KEY in hw_config) and os.path.isdir(hw_config[ZIP_DIR_KEY])):
        error_print("ERROR: {} not in {} or supplied directory does not exist".
                    format(ZIP_DIR_KEY, HW_CONFIG_FILENAME))
        retval = False

    if not ((GRADE_REPORTS_DIR_KEY in hw_config) and os.path.isdir(hw_config[GRADE_REPORTS_DIR_KEY])):
        error_print("ERROR: {} not in {} or supplied directory does not exist".
                    format(GRADE_REPORTS_DIR_KEY, HW_CONFIG_FILENAME))
        retval = False


    zip_command = hw_config.get(CREATE_ZIP_COMMAND_KEY, None)
    if not ((CREATE_ZIP_COMMAND_KEY in hw_config) and (os.path.isfile(zip_command) and os.access(zip_command, os.X_OK))):
        error_print("ERROR: {} not in {} or supplied file {} is not executable".
                    format(CREATE_ZIP_COMMAND_KEY, HW_CONFIG_FILENAME, zip_command) )
        retval = False


    remove_zip_command = hw_config.get(REMOVE_ZIP_COMMAND_KEY, None)
    if not ((REMOVE_ZIP_COMMAND_KEY in hw_config) and (os.path.isfile(zip_command) and os.access(zip_command, os.X_OK))):
        error_print("ERROR: {} not in {} or supplied file {} is not executable".
                    format(REMOVE_ZIP_COMMAND_KEY, HW_CONFIG_FILENAME, remove_zip_command) )
        retval = False

    validate_test_summaries(hw_config, quiet)

    return retval
    
#---------------------------------------------------------------
#                     clean_clones
#
#      Remove all student submissions, test results and test summaries
#      from student_clones
#---------------------------------------------------------------

CLEAN_CLONES_COMMAND_KEY = "clean_clones_command"

def clean_clones(hw_config):
    # Make sure the keys we need are there
    if not has_required_keys(hw_config, 
                             [CLEAN_CLONES_COMMAND_KEY]):
        return
        
    # Change into student clones directory
    old_dir = os.getcwd()
    chdir(hw_config[STUDENT_CLONES_KEY])

    # Do the remove
    RUN(hw_config[CLEAN_CLONES_COMMAND_KEY])

    # change back to homework config dir
    chdir(old_dir)
    
#---------------------------------------------------------------
#                     clone_all
#
#      NEEDSWORK: $TFB/clone_any_assignment tends to 
#                 create the hw dir, which is included in
#                 the student_clones path, so for now we cd ..
#                 from there. Wouldn't catch case where it's 
#                 a different hw
#---------------------------------------------------------------

CLONE_ALL_COMMAND_KEY = "clone_all_command"

def clone_all(hw_config):
    # Make sure the keys we need are there
    if not has_required_keys(hw_config, 
                             [CLONE_ALL_COMMAND_KEY]):
        return
    
    # Change into student clones directory
    old_dir = os.getcwd()
    chdir(os.path.join(hw_config[STUDENT_CLONES_KEY],'..'))

    # Do the remove
    RUN(hw_config[CLONE_ALL_COMMAND_KEY])

    # change back to homework config dir
    chdir(old_dir)

    
#---------------------------------------------------------------
#                     run_tests
#---------------------------------------------------------------

RUN_TESTS_COMMAND_KEY = "run_tests_command"

RUN_TESTS_COMMAND = "$TFB/run_tests.py -nproc {} {} {}"

def run_one_testset(hw_config, assignment_part, nproc, student):
    # Must resolve testsetdir before changing to clones dir 
    # as testset dirs are often ./relative to hw dir
    testsetdir = os.path.abspath(assignment_part[TESTSET_DIR_KEY])
    old_dir = os.getcwd()
    chdir(hw_config[STUDENT_CLONES_KEY])
    RUN(RUN_TESTS_COMMAND.format(nproc, testsetdir, (CLONE_FILE_GLOB_PATTERN if (not student) else (student + ".[1-9]"))))  
    chdir(old_dir)
    
def run_tests(hw_config, nproc, student):
    # Change into student clones directory

    for ap in hw_config[ASSIGNMENT_PARTS_KEY]:
        run_one_testset(hw_config, ap, nproc, student)

    
#---------------------------------------------------------------
#                     clean_results
#---------------------------------------------------------------
    
def clean_results(hw_config):
    old_dir = os.getcwd()
    chdir(hw_config[STUDENT_CLONES_KEY])
    RUN("rm -rf " + RESULTS_GLOB_PATTERN)
    chdir(old_dir)

    
    
#---------------------------------------------------------------
#                     clean_to_zip
#
#      Remove all student submissions, test results and test summaries
#      Remove all student submissions, test results and test summaries
#      from student_clones
#---------------------------------------------------------------

def clean_TO_ZIP(hw_config):
    #Remove the zip file itself, if any
    remove_zipfile(hw_config)

    # Make sure the keys we need are there
    if not has_required_keys(hw_config, 
                             [GRADE_REPORTS_DIR_KEY,CLEAN_ZIP_REPORTS_COMMAND_KEY]):
        return
        
    # Change into student clones directory
    old_dir = os.getcwd()
    chdir(hw_config[GRADE_REPORTS_DIR_KEY])

    # Do the remove
    RUN(hw_config[CLEAN_ZIP_REPORTS_COMMAND_KEY])

    # change back to homework config dir
    chdir(old_dir)
    

#---------------------------------------------------------------
#                     make_one_testset
#
#---------------------------------------------------------------

def make_one_testset(hw_config, ap):  
    testsetdir = os.path.abspath(ap[TESTSET_DIR_KEY])
    assert TESTSET_BUILD_KEY in ap, f"No {TESTSET_BUILD_KEY} entry in {HW_CONFIG_FILENAME} for testset {ap['name']}: required for making testsets."
    # get the build key and the clean key
    testset_build_command = ap[TESTSET_BUILD_KEY]
    testset_clean_command = ap.get(TESTSET_CLEAN_KEY, None)
    
    #change to testsetdir and do the work
    old_dir = os.getcwd()
    chdir(testsetdir)
        
    if testset_clean_command:
        print(f"Cleaning testset {ap['name']}. ", file=sys.stderr)
        RUN(testset_clean_command)
    else:
        print(f"No testset clean command for testset name {ap['name']}. Will try building without cleaning first.", file=sys.stderr)

    print(f"Building testset {ap['name']}. ", file=sys.stderr)
    RUN(testset_build_command)

    # change back to homework config dir
    chdir(old_dir)

#---------------------------------------------------------------
#                     make_testsets
#
#---------------------------------------------------------------

def make_testsets(hw_config):
    for ap in hw_config[ASSIGNMENT_PARTS_KEY]:
        make_one_testset(hw_config, ap)
    



#---------------------------------------------------------------
#                     zip_grade_files
#
#      Remove all student submissions, test results and test summaries
#      Remove all student submissions, test results and test summaries
#      from student_clones
#---------------------------------------------------------------


def zip_grade_files(hw_config):
    # 
    # NEEDSWORK: WE WANT TO ALLOW THE ZIP COMMAND TO LIVE IN OR NEAR THE ZIP
    # DIR AND FOR IT TO HAVE .-RELATIVE STUFF, BUT MOST OF OUR OTHER COMMANDS
    # ARE TO BE RUN RELATIVE TO THE HW DIR. SO, THE NAME OF THE COMMAND IS
    # RELATIVE TO THE HW DIR, BUT WE ASSUME WE CD TO THE ZIP DIR BEFORE RUNNING
    # IT. THIS MEANS THE COMMAND IN THE HW_CONF SHOULDN'T INCLUDE DIRS, AS THE 
    # OTHERS DO.

    # Name of command is relative to . so get it right before we cd
    zipcmd = os.path.abspath(hw_config[CREATE_ZIP_COMMAND_KEY])

    # Change into directory where zip is to be done
    old_dir = os.getcwd()
    chdir(hw_config[ZIP_DIR_KEY])
     
    # Do the zip
    RUN(zipcmd)

    # change back to homework config dir
    chdir(old_dir)
    
#---------------------------------------------------------------
#                     remove_zipfile
#
#      Remove all student submissions, test results and test summaries
#      Remove all student submissions, test results and test summaries
#      from student_clones
#---------------------------------------------------------------


def remove_zipfile(hw_config):
    # Make sure the keys we need are there
        
    # Do the remove
    RUN(hw_config[REMOVE_ZIP_COMMAND_KEY])
    
#---------------------------------------------------------------
#                     report
#
#      NEEDSWORK: $TFB/clone_any_assignment tends to 
#                 create the hw dir, which is included in
#                 the student_clones path, so for now we cd ..
#                 from there. Wouldn't catch case where it's 
#                 a different hw
#---------------------------------------------------------------

MASTER_REPORT_WRITER_COMMAND_KEY = "master_report_writer_command"
GRADE_OVERRIDE_FILE_KEY="grade_overrides"

def report(hw_config, student, tozip = False):
    # Make sure the keys we need are there
    if not has_required_keys(hw_config, 
                             [MASTER_REPORT_WRITER_COMMAND_KEY, 
                              GRADE_OVERRIDE_FILE_KEY]):
        return
    
    cmd = os.path.abspath(os.path.join(hw_config[BIN_KEY], hw_config[MASTER_REPORT_WRITER_COMMAND_KEY]))
    assert os.path.isfile(cmd) and os.access(cmd, os.X_OK), \
        ("Report writer {} does not exist or is not executable".
         format(cmd))

    #
    # Get overrides file
    #
    overrides_csv_file = os.path.abspath(hw_config[GRADE_OVERRIDE_FILE_KEY])
    #
    #  If tozip, remember the target directory
    #  and compute switch
    #
    if tozip:
        zip_reports_dir = os.path.abspath(hw_config[GRADE_REPORTS_DIR_KEY])
        zip_switch = " --outputdir {}".format(zip_reports_dir)
    else:
        zip_switch = ""

    # Change into student clones directory
    old_dir = os.getcwd()
    chdir(os.path.join(hw_config[STUDENT_CLONES_KEY]))

    #
    # Find all the summary files, get their absolute paths (since report
    # writer might run with a different cd, and write them in a temp file
    # each on one line. This works with the --stdin option on the
    # report writers, and is needed because otherwise the arglist to the 
    # report writer gets longer than the shell can handle!
    #
    
    if student:
        summary_json_files = "\n".join(os.path.abspath(f) for f in glob.iglob(student +".[1-9]*.test_summaries/*/*.json"))
    else:
        summary_json_files = "\n".join(os.path.abspath(f) for f in glob.iglob("*.test_summaries/*/*.json"))

    assert len(summary_json_files) > 0, "gradeit.py: report subcommand:\n..ERROR: No test_summaries/*/*.json files found from which to generate reports."
    # Use Python service for making a temporary file we can write into
    temp = tempfile.NamedTemporaryFile()
    
    try:
#        print("Created file is:", temp)
#        print("Name of the file is:", temp.name)
        tempFilename = temp.name
        temp.close()  # we could probably just write to this, but I'm not sure of mode

        # write filenames, one per line
        with open(tempFilename, "w") as tf:
            print(summary_json_files, file=tf)
        RUN(cmd + " --overridesCSV "+ overrides_csv_file + zip_switch + " --stdin < " + tempFilename)
    
    finally:
        os.remove(tempFilename)
    
    # change back to homework config dir
    chdir(old_dir)

    

    
#******************************************************************
#                         MAIN
#******************************************************************

if __name__ == "__main__":
    #---------------------------------------------------------------
    #             Parse command line arguments
    #---------------------------------------------------------------

    args = parseargs();
#    print(repr(args))

    # 
    #    The particular action the user requested (e.g. report, validate, etc.)
    #
    subcommand = args.subcommand
    
    #
    #  Get the output stream, which is usually sys.stdout, but which can be overriden
    #
    output_stream = args.output_stream[0]  # could be filename or open sys.stdout
    if output_stream != sys.stdout:
        output_stream = open(output_stream, "w")

    #
    # Get student login
    #
    #   Note, this is the login, not the submission directory
    #
    #   NEEDSWORK: SHOULD VALIDATE THAT STUDENT STUFF EXISTS IN STUDENT
    #              CLONES
    student = getattr(args,"student",[""])[0]  # defaults to empty string


    #---------------------------------------------------------------
    #             --explain switch handling
    #
    #    The --explain switch tells the system to not do anything
    #    (except validate), but rather to list the commands that
    #    >would< be run. This allows you to see what gradeit is 
    #    going to do before you actually let it change anything.
    #---------------------------------------------------------------

    #
    #          Set global variable RUN to function that runs
    #          or logs commands, depending on the --explain switch
    #          This insulates all the rest of the code from whether
    #          --explain is set, or whether (as usual) we are really
    #          running the commands.
    #  
    if args.explain:
        def printit(*args, shell="Ignore", **kwargs):
            print(" ".join(args), file=output_stream)
            return (0,"")
        RUN=printit
    else:
        def run_as_shell(*args, **kwargs):
            quiet = kwargs.get("quiet",True)
            if quiet in kwargs:
                del kwargs["quiet"]
            if not quiet:
                print(" ".join(args), file=output_stream)
            rc, output = backtick.run(*args, shell=True, **kwargs)
            assert not rc, ("ERROR: rc={} from command {}\nOutput=\n{}".
                            format(rc, " ".join(args), output))
            print(output, file=output_stream)
        RUN=run_as_shell        



    #---------------------------------------------------------------
    #             Run the requested subcommand
    #
    #     Note: we always validate first, so if that is the command
    #     then we do nothing else.
    #---------------------------------------------------------------

    #
    #  We run in the homework directory, at least most of the time
    #
    hw_dir = args.hwdir[0]
    original_wd = os.getcwd()
    os.chdir(hw_dir)

    #
    #  Get basic information about this homework, including where all the testsets
    #  are, etc.
    #
    hw_config = get_hw_config()
   
    #
    # Validate that we are set up well enough to run
    # and then run the requested subcommand
    #
    ok = validate(hw_config, subcommand == "validate")

    if not ok:
        error_print("Validation error(s) were found\n")
    elif subcommand == "validate":
        print("Configuration validates", file=output_stream)
    else:
        error_print(f"\nAttempting to run command \"{subcommand}\"")
        if subcommand == "clean_clones":
            clean_clones(hw_config)
        elif subcommand == "clean_TO_ZIP":
            clean_TO_ZIP(hw_config)
        elif subcommand == "clean_results":
            clean_results(hw_config)
        elif subcommand == "remove_zipfile":
            remove_zipfile(hw_config)
        elif subcommand == "make_testsets":
            make_testsets(hw_config)
        elif subcommand == "zip_grade_files":
            zip_grade_files(hw_config)
        elif subcommand == "clone_all":
            clone_all(hw_config)
        elif subcommand == "run_tests":
            run_tests(hw_config, args.nproc, student)
        elif subcommand == "report":
            report(hw_config, student)
        elif subcommand == "report4zip":
            report(hw_config, student, tozip=True)
        else:
            error_print("ERROR: Unsupported command line subcommand \"{}\"".
                        format(subcommand))
    
    #
    # close the output stream
    #
    if output_stream != sys.stdout:
        output_stream.close()
