#!/bin/env python3
#
#                        grade_summary_csv
#                   Author: Noah Mendelsohn
#
#    Using the grade information in a TO_ZIP/GradeReports, write a csv file
#    with one line for each student, with a column for each testset, grades
#    on each part, and then a column with a total

import grade_reports           # used for getting filenames in TO_ZIP/GradeReports
import csv
import sys, os, os.path, argparse, glob
import json


#---------------------------------------------------------------
#                    CONFIGURATION CONSTANTS
#---------------------------------------------------------------
STUDENT_COL = "Student"       # Column in csv for totlas
TOTAL_COL = "Total"       # Column in csv for totlas
HW_CONFIG_FILENAME = 'hw_conf.json'
ZIP_DIR_KEY = "zip_dir"
GRADE_REPORTS_FOR_ZIPPING_DIR = "./TO_ZIP/GradeReports"
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
    parser = argparse.ArgumentParser("Make a CSV summary file for all students")
    parser.add_argument("--explain", help="Echo commands to stdout instead of running them", action="store_true")
    parser.add_argument("--hwdir", nargs=1, required=False, default=["."])
    parser.add_argument("--output_stream", nargs=1, required=False, default=[sys.stdout])
#    parser.add_argument('testsetname', help="Name of the testset")
#    parser.add_argument('students', nargs="*", help="students on whom to reprot")
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

def testset_and_grades_for_student(s, grade_reports_dir):
    cwd = os.getcwd()
    os.chdir(grade_reports_dir)
    grade_list = glob.glob(s + "*.grade")
    os.chdir(cwd)
    if len(grade_list) == 0:
        raise IOError(ENOENT,"No grade files for student: " + s)
    for grade_fname in grade_list:
        os.chdir(grade_reports_dir)
        with open(grade_fname, "r") as f:
            score = int(f.readline())
        os.chdir(cwd)
        yield grade_fname, score

def all_csvs_for_students(hw_config, output_stream): 
    zip_reports_dir = os.path.abspath(hw_config[GRADE_REPORTS_DIR_KEY])
    students = grade_reports.students(zip_reports_dir)

    results = {}      # key is student, each entry is a dict
    testnames = set()
    #
    #   Gather results dict: key is student, value is dict with keys for each test
    #   Also gather set of testnames
    #
    for s in students:
        for grade_fname, grade in testset_and_grades_for_student(s, zip_reports_dir):
            splitname = grade_fname.split('.')
            assert splitname[0]==s, "Grade name not of form student.testset.grade"
            testset = splitname[1]
            testnames.add(testset)
            student_res = results.get(s, {})
            student_res[testset] = grade
            results[s] = student_res
    #
    #  Add a total column to each
    #
    for s, res in list(results.items()):
        total = 0
        for ts, grade in res.items():
            total += grade
            pre_res = res
        res["Total"] = total

    #
    #  Write a CSV with all the data
    #
    testname_list = [tn for tn in testnames]
    fieldnames = [STUDENT_COL]
    fieldnames.extend(testname_list)
    fieldnames.append(TOTAL_COL)
    dw = csv.DictWriter(output_stream, fieldnames)
    dw.writeheader()          # write column names
    for s, res in list(results.items()):
        r = res
        r[STUDENT_COL] = s         # add student as value for student_col
        dw.writerow(r)


def stdout_filename_from_testname(t):
    return t + ".stdout"

def canonical_filename_from_testname(t):
    return t + ".stdout.canonical"

def canonical_failed_filename_from_testname(t):
    return t + ".stdout.canonical.FAILED"
    
def file_as_string(fname):
    with open(fname, "r", encoding="utf-8") as f:
        return f.read()
    

        

            
    
    

#---------------------------------------------------------------
#                    Main
#---------------------------------------------------------------

if __name__ == "__main__":
    args = parseargs();
#    print(repr(args))

    
    #
    #  Note the output stream, which is usually sys.stdout, but which can be overriden
    #
    output_stream = args.output_stream[0]  # could be filename or open sys.stdout
    if output_stream != sys.stdout:
              output_stream = open(output_stream, "w", newline="")

    
    #
    #  Get basic information about this homework, including where all the testsets
    #  are, etc.
    #
    hw_config = get_hw_config()

    #
    # Validate that we are set up well enough to run
    # and then run the requested subcommand
    #
    all_csvs_for_students(hw_config, output_stream)
    
    output_stream.close()

