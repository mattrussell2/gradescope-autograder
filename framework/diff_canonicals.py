#!/bin/env python3
#
#                              diff_canonicals.py
#                   Author: Noah Mendelsohn
#
#    A class and application to diff the canonicals for a named student
#    and testset 

import grade_reports           # used for getting filenames in TO_ZIP/GradeReports
from results import Results3
import sys, os, os.path, argparse, glob
import tempfile
import json
import backtick         # Like shell `cmd` runs commands and captures output


#---------------------------------------------------------------
#                    CONFIGURATION CONSTANTS
#---------------------------------------------------------------
MAX_UNTESTED_TO_LIST = 6  # when validating tests run, max to list explicitly
CLONE_FILE_GLOB_PATTERN = "*.[1-9]"
STUDENT_CLONES_KEY = "student_clones"
BIN_KEY = "bin_dir"
HW_CONFIG_FILENAME = 'hw_conf.json'
TESTSET_DIR_KEY = "testset_dir"  # in assignment parts
ZIP_DIR_KEY = "zip_dir"
GRADE_REPORTS_FOR_ZIPPING_DIR = "./TO_ZIP/GradeReports"
CLEAN_ZIP_REPORTS_COMMAND_KEY = "clean_zip_reports_command"
CREATE_ZIP_COMMAND_KEY = "create_zip_command"
REMOVE_ZIP_COMMAND_KEY = "remove_zip_command"
GRADE_REPORTS_DIR_KEY = "grade_reports_dir"



#---------------------------------------------------------------
#                Utility functions
#---------------------------------------------------------------

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
#      Write an error message
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
#                     parseargs
#
#       Use python standard argument parser to parse arguments and provide help
#
def parseargs():
    parser = argparse.ArgumentParser("Run commands to configure or perform grading")
    parser.add_argument("--explain", help="Echo commands to stdout instead of running them", action="store_true")
    parser.add_argument("--hwdir", nargs=1, required=False, default=["."])
    parser.add_argument("--output_stream", nargs=1, required=False, default=[sys.stdout])
    parser.add_argument('testsetname', help="Name of the testset")
    parser.add_argument('students', nargs="*", help="students on whom to reprot")
    return parser.parse_args()

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
def validate_test_summaries(hw_config):
    #
    # Get list of students who have submitted
    #
        # Make sure the keys we need are there
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
    
def validate(hw_config):
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

    validate_test_summaries(hw_config)

    return retval


def students_to_test():
    pass


def all_diffs_for_student(hw_config, testsetname, s): 
    zip_reports_dir = os.path.abspath(hw_config[GRADE_REPORTS_DIR_KEY])

    # Change into student clones directory
    old_dir = os.getcwd()
    chdir(os.path.join(hw_config[STUDENT_CLONES_KEY]))

    summary_json_files = list(os.path.abspath(f) for f in glob.iglob("{}.*.test_summaries/{}/*.json".format(s, testsetname)))
    # change back to homework config dir
    chdir(old_dir)

    # Because of the globbing above these are all for the student and testset
    resultsData = Results3(files=summary_json_files)
    
    for r in resultsData:
        if r["success"] == "PASSED":
            continue
        one_diff_for_student(hw_config, testsetname, s, r)


def stdout_filename_from_testname(t):
    return t + ".stdout"

def canonical_filename_from_testname(t):
    return t + ".stdout.canonical"

def canonical_failed_filename_from_testname(t):
    return t + ".stdout.canonical.FAILED"

def one_diff_for_student(hw_config, testsetname, s, r):
    testname = r["testname"]
    testsetdir = r["testsetdir"]
    resultscontainerdir = r["resultscontainerdir"]

    #
    #  If there's a failed canonical, then there's nothing to compare
    #
    student_failed_canonical_filename = os.path.abspath(os.path.join(resultscontainerdir,
                                                     canonical_failed_filename_from_testname(testname)))
    try:
        student_failed_canonical_output = file_as_string(student_failed_canonical_filename)
        print("FAILED CANONICAL: " + student_failed_canonical_output)
        try:
            student_stdout_filename = os.path.abspath(os.path.join(resultscontainerdir,
                                                     stdout_filename_from_testname(testname)))
            student_stdout_text = file_as_string(student_stdout_filename)
            print("STUDENT STDOUT: " + student_stdout_text)
            correct_stdout_filename = os.path.abspath(os.path.join(testsetdir,
                                                     stdout_filename_from_testname(testname)))
            correct_stdout_text = file_as_string(correct_stdout_filename)
            print("CORRECT STDOUT: " + correct_stdout_text)
        except IOError as e:
            print("Could not open student stdout: " + student_stdout_filename, file=sys.stderr)
            return
        return
    except IOError as e:
        # There's no failed canonical, keep going
        pass


    student_canonical_filename = os.path.abspath(os.path.join(resultscontainerdir,
                                                     canonical_filename_from_testname(testname)))
    try:
        student_canonical_output = file_as_string(student_canonical_filename)
    except IOError as e:
        print("Could not open student canonical: " + student_canonical_filename, file=sys.stderr)
        return

    correct_canonical_filename = os.path.abspath(os.path.join(testsetdir,
                                                     canonical_filename_from_testname(testname)))
    try:
        correct_canonical_output = file_as_string(correct_canonical_filename)
    except IOError as e:
        print("Could not open testset canonical: " + student_canonical, file=sys.stderr)
        return
        
    print("-------TESTNAME {} -----------".format(testname))
    report_a_diff(student_canonical_output.replace("\n","|"), correct_canonical_output.replace("\n","|"),
                  "STUDENT: ", "CORRECT: ")
        
    

    
def file_as_string(fname):
    with open(fname, "r", encoding="utf-8") as f:
        return f.read()
    

def report_a_diff(s1, s2, s1_label, s2_label):
    assert(len(s1_label) == len(s2_label)), "report a diff: labels must have same length"
    prefix = ' ' * len(s1_label)
    print(s1_label + s1)
    sys.stdout.write(prefix)
    min_len = min(len(s1), len(s2))
    diffpoint = None
    for i in range(min_len):
        if s1[i] == s2[i]:
            sys.stdout.write(" ")
        else:
            diffpoint = i
            print("^")
            break
    if diffpoint==None:
        print()
        if len(s2) == len(s1):
            print("NO DIFFERENCE")
        else:
            print(s2_label + s2)
            print("LENGTHS DIFFER")
    else:
        print(s2_label + s2)
        print("DIFFERENCE STARTING IN COLUMN: " + str(diffpoint))


            
        

            
    
    

#---------------------------------------------------------------
#                    Main
#---------------------------------------------------------------

if __name__ == "__main__":
    args = parseargs();
#    print(repr(args))

    testsetname = args.testsetname
    students = args.students
    
    #
    #  Note the output stream, which is usually sys.stdout, but which can be overriden
    #
    output_stream = args.output_stream[0]  # could be filename or open sys.stdout
    if output_stream != sys.stdout:
        output_stream = open(output_stream, "w")

    
    #
    #  Get basic information about this homework, including where all the testsets
    #  are, etc.
    #
    hw_config = get_hw_config()

    #
    # Validate that we are set up well enough to run
    # and then run the requested subcommand
    #
    ok = validate(hw_config)
    
    for s in students:
        print("\n============================================\nSTARTING Student: {}\n============================================\n".format(s))
        
        all_diffs_for_student(hw_config, testsetname, s)
        
    sys.exit(0)
    


    #
    #  We run in the homework directory, at least most of the time
    #
    hw_dir = args.hwdir[0]
    original_wd = os.getcwd()
    os.chdir(hw_dir)
    

    if not ok:
        error_print("Validation error(s) were found\n")
    elif subcommand == "validate":
        print("Configuration validates", file=output_stream)
    elif subcommand == "clean_clones":
        clean_clones(hw_config)
    elif subcommand == "clean_TO_ZIP":
        clean_TO_ZIP(hw_config)
    elif subcommand == "remove_zipfile":
        remove_zipfile(hw_config)
    elif subcommand == "zip_grade_files":
        zip_grade_files(hw_config)
    elif subcommand == "clone_all":
        clone_all(hw_config)
    elif subcommand == "run_tests":
        run_tests(hw_config, args.nproc)
    elif subcommand == "report":
        report(hw_config)
    elif subcommand == "report4zip":
        report(hw_config, tozip=True)
    else:
        error_print("ERROR: Unsupported command line subcommand \"{}\"".
                    format(subcommand))

    
    #
    # close the output stream
    #
    if output_stream != sys.stdout:
        output_stream.close()
