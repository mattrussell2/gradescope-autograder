#!/usr/sup/bin/python
# NEEDSWORK: above should be /bin/env python3 (Noah 12/29/2020)
#
#                        comp11_report_override_grade.py
#
#       Prepares a report on the override grade, if any. 
#       If there is no override, then no output is produced
#      

import sys, argparse, textwrap, os, os.path
import csv

from comp11_grade_report_helper import INDENT, INDENT_STRING, WRAP_WIDTH
from comp11_grade_report_helper import printWrapped, printList
from comp11_grade_report_helper import print_box

REPORT_FILE_TEMPLATE = "{}.ADJUST.report"
GRADE_FILE_TEMPLATE = "{}.ADJUST.grade"
ADJUSTMENT_LINE_TEMPLATE = "{reason} (Adjustment: {adjustment} points)"


#---------------------------------------------------------------
#                     parseargs
#
#    Use Python standard argument parser to parse arguments and provide help
#---------------------------------------------------------------

def parseargs():
    parser = argparse.ArgumentParser()
    # Formats not supported right now
#    parser.add_argument("-format", nargs=1, help="output format", \
#                            choices=[DIGITSFORMATKEY, JSONFORMATKEY, CSVFORMATKEY], \
#                            default=[DIGITSFORMATKEY])
    parser.add_argument("--outputdir", nargs=1, 
                        help="Name the directory where report and grade files will be written. Default is sys.stderr for reports and os.devnull for grades")
    parser.add_argument("--overridesCSV", nargs=1, required=True,
                        help="Name of a CSV file with override information")
    parser.add_argument('student', help="student login", nargs=1)
    return parser.parse_args()

#*****************************************************************************
#                          Write override report for this student
#*****************************************************************************


def writeReportforStudent(student, csv_filename, 
                          report_file=sys.stdout,
                          grade_file=None):
    
    #
    #  Warn if no CSV Filename
    #
    if not csv_filename:
        print("comp11_report_override_grade.py: writeReport for student called with no csv_filename.\nSKIPPING REPORTING OF OVERRIDE GRADES\n", file=sys.stderr)
        return
    with open(csv_filename, "r", newline='') as csvfile:
        dr = csv.DictReader(csvfile)
#        overrides_for_student = [ovr for ovr in dr ]
        overrides_for_student = [ovr for ovr in dr if (ovr["Login"] == student)]

    #
    # if no overrides, return
    #
    if len(overrides_for_student) == 0:
        return

    #
    # Write report header
    #
    print_box("Grade Adjustments for Student {}".format(student), file=report_file)

    #
    # Write individual adjustments
    #
#    printList((ADJUSTMENT_LIST_HEADER,), file=report_file)

    net_adjustment = 0          # net adjustment

    for ovr in overrides_for_student:
        adjustment = ovr["Adjustment"]
        
        assert adjustment, ("In file {} entry for student {}: Adjustment is missing or 0"
                            .format(os.path.abspath(csv_filename), student))
        assert int(adjustment)==float(adjustment), ("In file {} entry for student {}: Adjustment is not an integer)"
                                                    .format(os.path.abspath(csv_filename), student), adjustment)
        adjustment = int(adjustment)       # convert from number to string
        printWrapped(ADJUSTMENT_LINE_TEMPLATE.format(adjustment = adjustment,
                                                     reason = ovr["Reason"]), 
                     file = report_file)
        net_adjustment += adjustment       # keep the running tally

    # - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - -
    # If we have been asked to, write the grade into the grade file
    # - - - - - - - - - - - - - -- - - - - - - - - - - - - - - - - - -
    
    if (grade_file):
        # Get the actual total score on all  successful tests
        assert net_adjustment == int(net_adjustment),\
            ("In file {} entry for student {}: net adjustment {}  is not an integer".
             format(os.path.abspath(csv_filename), student, net_adjustment))
        print(int(net_adjustment), file=grade_file)


#*****************************************************************************
#                          Main for Testing
#
#         Normally this module is imported by other report writers
#         that load the results data and invoke writeReportforStudent
#
#*****************************************************************************

if __name__ == "__main__":

    # - - - - - - - - - - - - - - - - - - - - - - - - 
    #    Parse args and make sure all files are readable before starting
    # - - - - - - - - - - - - - - - - - - - - - - - - 

    args = parseargs()

    output_dir = args.outputdir
    student = args.student[0]
    
    report_file_name = REPORT_FILE_TEMPLATE.format(student)
    grade_file_name = GRADE_FILE_TEMPLATE.format(student)
    
    if output_dir: 
        report_file = open(os.path.join(output_dir, report_file_name, "w"))
        grade_file = open(os.path.join(output_dir, grade_file_name, "w"))
    else:
        report_file = sys.stdout
        grade_file = open(os.devnull, "w")


    writeReportforStudent(student, args.overridesCSV[0], report_file, grade_file)

                                   


