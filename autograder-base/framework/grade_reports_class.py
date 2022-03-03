#!/usr/sup/bin/python3
#
#                  grade_reports_class.py
# 
#   Wrapper class for grade reports in the TO_ZIP
#   directory.
#
#   For eventual use with gradescope autograde_phase2.py framework,
#   but for now this is an overlapping copy of grade_reports.py
#   adapted for more general use and wrapped as a class.
#
#
#

import glob, os, os.path, sys
from errno import ENOENT

GRADE_REPORTS_DIR="GradeReports"

#
#   Does a chdir returning old dir
#
    
class GradeReports:
    # Argument is the grade_reports directory, not the parent TO_ZIP
    
    def __init__(self, grade_reports_dir):
        self.grade_reports_dir = grade_reports_dir
        self.caller_dir = None

    def pushdir(self, d=None):
        assert self.caller_dir == None, "Class GradeReports:  nested call to pushdir"
        if not d:
            d = self.grade_reports_dir
        self.caller_dir = os.getcwd()
        os.chdir(d)

    def popdir(self):
        assert self.caller_dir != None, "Class GradeReports:  popdir called with no dir pushed"
        os.chdir(self.caller_dir)
        self.caller_dir = None
        
    
    
    # Returns a sorted list of students who have at least one result in the 
    # supplied directory. The list is based on existence of either report or 
    # grade file

    def students(self, report_or_grade = "report"):
        self.pushdir()
        set_of_students = set()
        glob_pattern = "*.*.{}".format(report_or_grade)
        for f in glob.iglob(glob_pattern):
            student_name = f.split('.')[0]
            set_of_students.add(student_name)
        self.popdir()
        return sorted(set_of_students)
        
    #
    #    Yields a list of report/grade_fname, report-contents/grade pairs
    #    Depending on whether reports or grades are requested
    #
    def reports_or_grades_for_student(self, s, testset, report_or_grade = "report"):
        self.pushdir()
        report_list = glob.glob("{}.{}.{}".format(s, testset, report_or_grade))
        self.popdir()
            
        for report_fname in report_list:
            self.pushdir()
            with open(report_fname, "r") as f:
                if (report_or_grade == "report"):
                    output = f.read()
                else:
                    output = int(f.readline())
            self.popdir()
            yield (s, output)

    #
    #   Use to ensure there is only one..the pair is returned rather than yielded
    #
    def single_report_or_grade_for_student(self, s, testset, report_or_grade = "report"):
        rgs = list(self.reports_or_grades_for_student(s, testset, report_or_grade="grade"))
        assert len(rgs)==1, ("More than one grade report for student {} testset {}"
                             .format(s, testset))
        filename, grade = rgs[0]
        return s, grade

#--------------------------------------------------
#
#            Test code
#
#--------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("USAGE: {} Grade-Reports-Dir Testsetname".format(sys.argv[0]), file=sys.stderr)
        sys.exit(4)
    dir = sys.argv[1]
    testset = sys.argv[2]

    


    grs = GradeReports(dir)

    students = grs.students()

    grade_students = grs.students(report_or_grade="grade")


    for s in grade_students:
        # Could return a list of pairs, but we only expect 1
        filename, grade = grs.single_report_or_grade_for_student(s, testset, report_or_grade="grade")
        print("{:>5} {}".format(grade, filename))

