#!/bin/env python3
#
#                  grade_report_merge.py
# 
#   Given two directories with grade reports, either report
#   the differences, or merge so that the target dir
#   has the union of the results with the highest grade.
#
#      Routines to gather all information for a particular student.
#
#

import glob, os, os.path, sys, argparse, shutil
from errno import ENOENT

#
#                     parseargs
#
#       Use python standard argument parser to parse arguments and provide help
#
def parseargs():
    parser = argparse.ArgumentParser("Merge one grade report dir into another")
    parser.add_argument('--update', dest='update', action='store_true')
    parser.add_argument('--no-update', dest='update', action='store_false')
    parser.set_defaults(update=False)
    parser.add_argument('target_dir', help="Merge into this dir")
    parser.add_argument('other_dir',help="arguments to subcommand")
    return parser.parse_args()


class GradeReports:
    def __init__(self, dir):
        self.dir = dir
        
    def abspath(self, f):
        return os.path.abspath(os.path.join(self.dir, f))

    def pairs(self):
        cwd = os.getcwd()
        os.chdir(self.dir)
        for f in glob.iglob("*.*.report"):
            result = (f,
                      grade_fname_from_report_fname(f))
            os.chdir(cwd)
            yield result
            cwd = os.getcwd()
            os.chdir(self.dir)
        os.chdir(cwd)
        
    def __contains__(self, fname):
        cwd = os.getcwd()        
        os.chdir(self.dir)
        retval = True
        if not os.path.isfile(fname):
            retval = Falsen
        os.chdir(cwd)
        return retval
        
        
    def grade_from_fname(self, fname):
        cwd = os.getcwd()        
        os.chdir(self.dir)
        if not os.path.isfile(fname):
            os.chdir(cwd)
            raise IOError(ENOENT,"No grade file {} "\
                  .format(fname))
        with open(grade_fname, "r") as f:
            score = float(f.readline())
        os.chdir(cwd)
        return score

        
    def __iter__(self):
        return self.pairs()



# Returns a sorted list of students who have at least one result in the 
# supply directory

def students(dir):
    cwd = os.getcwd()
    os.chdir(dir)
    set_of_students = set()
    for f in glob.iglob("*.*.report"):
        student_name = f.split('.')[0]
        set_of_students.add(student_name)
    os.chdir(cwd)
    return sorted(set_of_students)

def grade_fname_from_report_fname(rpt):
    parts = rpt.split('.')
    parts[2] = 'grade'
    return '.'.join(parts)
    

#
#  For a given student, yields contents of all reports and grades as pairs.
#
#  Raises IOError if no reports for this student or if there is a report that 
# lacks a matching grade file
#
def reports_and_grades_for_student(s):
    cwd = os.getcwd()
    os.chdir(GRADE_REPORTS_DIR)
    report_list = glob.glob(s + "*.report")
    os.chdir(cwd)
    if len(report_list) == 0:
        raise IOError(ENOENT,"No reports files for student: " + s)
    for report_fname in report_list:
        grade_fname = grade_fname_from_report_fname(report_fname)
        os.chdir(GRADE_REPORTS_DIR)
        if not os.path.isfile(grade_fname):
            os.chdir(cwd)
            raise IOError(ENOENT,"No grade file {} for report file {}"\
                  .format(grade_fname,report_fname))
        with open(report_fname, "r") as f:
            report = f.read()
        with open(grade_fname, "r") as f:
            score = int(f.readline())
        os.chdir(cwd)
        yield report, score
    

#--------------------------------------------------
#
#            Test code
#
#--------------------------------------------------

if __name__ == "__main__":
    args = parseargs()
    target_dir = args.target_dir
    other_dir = args.other_dir
    update = args.update

    #
    #  Get a class to wrap each set of reports
    #
    target_reports = GradeReports(target_dir)
    other_reports = GradeReports(other_dir)

    copy_list = []
    for report_fname, grade_fname in other_reports:
        target_grade = target_reports.grade_from_fname(grade_fname)
        other_grade = other_reports.grade_from_fname(grade_fname)
        if not report_fname in target_reports:
            print("{} not in target {}".format(report_fname, 
                                               "copying" if update else ""))
            if update:
                copy_list.append( (report_fname, grade_fname) )
        elif (target_grade < other_grade):
            print("for {}: other grade {} > grade {} ()".format(grade_fname, 
                                                                other_grade,
                                                                target_grade,
                                               "copying" if update else ""))
            if update:
                copy_list.append( (report_fname, grade_fname) )


    #
    # We didn't want to change anything until iteration was done, now do the copying
    #
    for (report_fname, grade_fname) in copy_list:
        shutil.copyfile(other_reports.abspath(report_fname), 
                        target_reports.abspath(report_fname))
        shutil.copyfile(other_reports.abspath(grade_fname), 
                        target_reports.abspath(grade_fname))
        
            
        
        
