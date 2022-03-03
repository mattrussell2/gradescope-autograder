#
#                  grade_reports.py
# 
#   Wrapper class for grade reports in the TO_ZIP
#   directory.
#
#   For use with gradescope autograde_phase2.py framework,
#   but elsewhere as well.
#
#      Routines to gather all information for a particular student.
#
#

import glob, os, os.path, sys
from errno import ENOENT

GRADE_REPORTS_DIR="GradeReports"

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

#
#    This prepares the object that will be serialized as Jason
def get_student_gradescope_results(student_name):
    if (student_name == None) or (student_name.strip() == ""):
        raise IOError(ENOENT,"Gradescope did not provide a student_id for this autograde.\nYour submission might not have been uploaded to gradescope")

    # We will eventually put our answer here
    total_score = 0
    all_reports = ""

    for report, score in reports_and_grades_for_student(student_name):
        total_score += score      # Add to running score for student
        # add an extra <br> as a separator
        # and replace all new lines with <br>
        # which Gradescope seems to want
        all_reports += "<br>" + report.replace("\n","<br>")

        
    # Prepare object that will be used as the JSON value 
    # returned to Gradescope

    all_reports = "<pre>{}</pre>".format(all_reports)

    retval = result = {
       "output" : all_reports,
	"score" : total_score
    }
    
    return retval

    

#--------------------------------------------------
#
#            Test code
#
#--------------------------------------------------

if __name__ == "__main__":
    print(repr(get_student_gradescope_results("oracle")))
    print(repr(get_student_gradescope_results("wrongexit")))
    print(repr(get_student_gradescope_results("dummy")))
