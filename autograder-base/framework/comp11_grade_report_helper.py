#!/usr/sup/bin/python
# NEEDSWORK: above should be /bin/env python3 (Noah 12/29/2020)
#
#                        grade_report_helper.py
#
#       Utiltity routines to help with the formatting of grading reports
#      

import sys
import textwrap

from grading import GradeReport, GR_NONE, GR_PROPORTIONAL, GR_ANY, GR_ALL

#---------------------------------------------------------------
#                     Text Wrapping Services
#---------------------------------------------------------------


#
#      Text wrapping specifications for long output lines
#
INDENT=11
INDENT_STRING = ' ' * INDENT
GRADE_REPORT_PREFIX = INDENT_STRING + ' '
WRAP_WIDTH = 78
BOX_INDENT = INDENT
BOX_WIDTH=67
BOX_CHAR='*'

FAILURE_REASONS_HEADER=(
INDENT_STRING + "Reasons Your Tests Did Not Succeed\n" + 
INDENT_STRING + "----------------------------------"
)

SUCCESS_VALUES_HEADER = (
INDENT_STRING + "Input values on which your program succeeded\n" + 
INDENT_STRING + "--------------------------------------------"
)

FAILED_VALUES_HEADER = (
INDENT_STRING + "Input values on which your program failed\n" + 
INDENT_STRING + "-----------------------------------------"
)

HINT_HEADER=(
INDENT_STRING + "Hints and Explanations\n" + 
INDENT_STRING + "----------------------"
)

BUILD_EXECUTABLE_TESTCASE_NAME='build_executable'


REPORT_BODY_TEXTWRAPPER = textwrap.TextWrapper(width=WRAP_WIDTH, initial_indent=INDENT_STRING, subsequent_indent=INDENT_STRING)

FAILURE_REASONS_TEXTWRAPPER = textwrap.TextWrapper(width=WRAP_WIDTH, initial_indent=INDENT_STRING, subsequent_indent=INDENT_STRING + "....")

#---------------------------------------------------------------
#                   printWrapped
#
#       Prints supplied output, with default wrapping and training extra \n
#       by default
#
#---------------------------------------------------------------

def printWrapped(s, trailing_newline="\n", preamble="", file=sys.stdout):
    print(REPORT_BODY_TEXTWRAPPER.fill(preamble + s)+trailing_newline, file=file)

#---------------------------------------------------------------
#                   printList
#
#       A list of strings. Each string should be short enough to fit on a line
#
#---------------------------------------------------------------

def printList(lst, trailing_newline="\n", file=sys.stdout):
    
    for i in lst:
        print(FAILURE_REASONS_TEXTWRAPPER.fill(i), 
              file=file)
    file.write(trailing_newline)

#---------------------------------------------------------------
#                formatted_grades_by_group
# 
#      Prints the breakout table of categorized grades that
#      we normally put near the top of each report
#--------------------------------------------------------------

#
#    Return a formatted line for a single graded grade_group.
#
def format_subgrade(g):
    grade, max = g.grades()
    success_string = ""
    if g.report_success_counts:
        success_string = " ({} of {} PASSED)".format(g.successful_test_count,
                                                     g.all_test_count)
    return GRADE_REPORT_PREFIX + "{:>3} / {:>3}   {:<40}".format(int(grade), int(max), g.description + success_string)

#
#    Return the whole table
#
def formatted_grades_by_group(grade_report):
    hdr = (GRADE_REPORT_PREFIX + " PTS / MAX  Test Description\n" + 
           GRADE_REPORT_PREFIX + " ---   ---  --------------------------------\n")
    return hdr + "\n".join(map(format_subgrade, (g for g in grade_report 
                                           if g.grading != GR_NONE)))

#---------------------------------------------------------------
#        printReportHeader
#---------------------------------------------------------------

BOX_INDENT_STRING = ' ' * BOX_INDENT
BOX_TOP_BOTTOM = BOX_INDENT_STRING + (BOX_CHAR * BOX_WIDTH)

def center_in_box(s, box_indent_string=BOX_INDENT_STRING,
                  box_top_bottom=BOX_TOP_BOTTOM,
                  box_width=BOX_WIDTH, 
                  box_side_char=BOX_CHAR):
    prefix = box_indent_string + box_side_char
    remaining_width = box_width - len(prefix)
    in_box_indent_string = ' ' * int((box_width - len(s) - 1) / 2)
    content_so_far = prefix + in_box_indent_string + s
    box_right_filler_len = max(0, len(box_top_bottom) - len(content_so_far) - 1)
    return prefix + in_box_indent_string + s + (' ' * box_right_filler_len) + box_side_char

def print_box(s, box_indent_string=BOX_INDENT_STRING,
              box_top_bottom=BOX_TOP_BOTTOM,
              box_width=BOX_WIDTH, 
              box_char=BOX_CHAR, 
              box_side_char=BOX_CHAR, 
              file=sys.stdout):
    print(box_top_bottom, file=file)
    print(center_in_box(s, box_indent_string, box_top_bottom, 
                        box_width, box_side_char), file=file)
    print(box_top_bottom + "\n", file=file)
    
    
def print_report_header(student, program_name, code_type="program", file=sys.stdout):
    print_box(f"{program_name} {code_type} test results for login {student}",
              file=file)

#---------------------------------------------------------------
#                  print_failure_reasons
#
#     Note: this works only if testcase in testset.json has "data" key 
#     with a short value to be printed.
#
#     Switch: only_if_failure: if True, only print this report
#                              if there was at least one failure
#---------------------------------------------------------------

#
#  Some failure reasons are misleading. Here we can substitute
#  Mappings is a list of tuples: a compiiled regexp and subtitution text
#  If the substitution text is a function, then it is called to rewrite the text
#
def map_failure_reasons(reason, mappings):
    if not mappings:
        return reason.strip()
    for regexp, mapped_output in mappings:
        if regexp.match(reason):
            if callable(mapped_output):
                return mapped_output(reason)
            else:
                return mapped_output.strip()
    return reason.strip()

def print_failure_reasons(grade_group, 
                          failure_reasons_header=FAILURE_REASONS_HEADER,
                          mappings=None,
                          file=sys.stderr):
    if grade_group.all_failed_test_count:
        print(failure_reasons_header, file=file)
        mapped_reasons=(map_failure_reasons(r, mappings) for r in grade_group.all_failure_reasons())
        printList(mapped_reasons, file=file)

#---------------------------------------------------------------
#                  print_success_and_failure_inputs
#
#     Note: this works only if testcase in testset.json has "data" key 
#     with a short value to be printed.
#
#     Switch: only_if_failure: if True, only print this report
#                              if there was at least one failure
#---------------------------------------------------------------

def print_the_values(values, separate_lines=None, quote=False, 
                     cleanup_function=None, join_string=None, file=sys.stderr):
    if cleanup_function:
        values=map(cleanup_function, values)
    if quote:
        values = ("\"{}\"".format(v) for v in values)
    if separate_lines:
        # Experiment to use printList, which uses same text_wrapper as
        # failure reasons
        printList(values, file=file)
        print(file=file)
    else:
        printWrapped(join_string.join(values), file=file)

def remove_missing_data_results(results, msgstring):
    for r in results:
        if r["data"] != None:
            yield r
        else:
            print(msgstring + "testname {} does not have a data key in the testset".format(r["testname"]),
                  file=sys.stderr)

def print_success_and_failure_inputs(grade_group, 
                                     only_if_failure=False,
                                     separate_lines=False,
                                     join_string=", ",
                                     quote=False,
                                     success_values = None,
                                     failed_values = None,
                                     cleanup_function = None,
                                     success_values_header=SUCCESS_VALUES_HEADER,
                                     failed_values_header=FAILED_VALUES_HEADER,
                                     file=sys.stderr):
    if  grade_group.all_failed_test_count or (not only_if_failure):
        #
        #   Print possible success values
        #
        if grade_group.successful_test_count:
            if success_values:
                values = success_values
            else:
                values = [str(r["data"]) 
                          for r in sorted(remove_missing_data_results(grade_group.successful_results(), 
                                                                      "Reporting Successful Test Values: "), 
                                          key=lambda r:r["data"])]
            if len(values)>0:         # Might be false if all were missing r["data"]
                print(success_values_header, file=file)
                print_the_values(values, separate_lines = separate_lines,
                                 join_string = join_string, 
                                 cleanup_function = cleanup_function,
                                 quote=quote,
                                 file=file)
            
        #
        #   Print failed values
        #
        if failed_values:
            values = failed_values
        else:
            values = [str(r["data"]) 
                      for r in sorted(remove_missing_data_results(grade_group.all_failed_results(),
                                                                  "Reporting Failed Test Values: "),
                                      key=lambda r:r["data"])]
            
        if len(values)>0:         # Might be false if all were missing r["data"]
            print(failed_values_header, file=file)
            print_the_values(values, separate_lines = separate_lines,
                             join_string = join_string, 
                             cleanup_function=cleanup_function,
                             quote=quote,
                             file=file)
        print(file=file)

#---------------------------------------------------------------
#
#                hints_and_explanations_helper
#
#          Specifications for hints and explanations section
#
#  This function returns a list of hint strings, if any.
#
#  Argument is a grade report object and a specification of what requires an
#  explanation. The format of that is described below:
#
#  Each entry is a pair:
#
#    1) A function or lambda implementing a predicate. Function is 
#       passed grade_report as a single argument. The return value should be
#       a pair(t/f, tuple), where if the result is true, the tuple will be 
#       be passed as argument to the format string below. If false, None
#       can be returned for the tuple. The first element of the tuple can
#       be anything truthy (e.g. a count that's 0 vs not zero).
#    2) A format string that will be evaluated only if the predicate is true.
# 
#
#              This is a sample
#    
#    HINTS_EXPLANATIONS = [
#        # Write message if source has tabs
#        (lambda gr: (gr.long_source_lines.failed_test_count, None), 
#         "Your source file has at least one line that's longer than 80 characters, 
#         which is not allowed by our style guide. For this first assignment we are 
#        not deducting, but for future assignments we will."),
#    
#        # Write message if source has tabs
#        (lambda gr: (gr.source_has_tabs.failed_test_count, None), 
#         "Your source file contained tab characters (these are somewhat like space 
#          characters and your Atom editor might be misconfigured to use them when 
#          you indent your code.) For this first assignment, we are not deducting 
#          for tabs, but in future assignments we will. If you are confused about
#          this, consult a TA."),
#
#
#    ]
#
#---------------------------------------------------------------
   

def hints_and_explanations_helper(gr, hints_specifications):
    #
    #  Loop gathering hints
    #
    hints_strings = []
    for h in hints_specifications:
        # h[0] is a tuple with a predicate function that returns t/f, and an optional
        #      tuple to use with the format string
        # h[1] is a formattable string to be written if hint is needed.
        #     
        # that returns the tuple for a format string
        test_function = h[0]
        format_string = h[1]
        
        # see if this hint is needed and if so add the hint to the list
        needed, format_args  = test_function(gr)

        if needed:
            if format_args:
                if (type(format_args) is tuple):
                    hint_string = format_string.format(*format_args)
                else:
                    hint_string = format_string.format(format_args)

                
            else:
                hint_string = format_string
            hints_strings.append(hint_string)
            
    return hints_strings

#---------------------------------------------------------------
#                 print_hints_and_explanations
#---------------------------------------------------------------

def print_hints_and_explanations(grade_report, hints_and_explanations, 
                                 header=HINT_HEADER,
                                 file=sys.stdout):
    hints_strings = hints_and_explanations_helper(grade_report, hints_and_explanations)
    if hints_strings:
        print(header, file=file)
        for hs in hints_strings:
            printWrapped(hs, file=file)

#---------------------------------------------------------------
#
#                 comp11GradeReport
#
#         Subclass of standard GradeReport class.
#
#    Automatically adds grade groups for standard comp 11 things like
#    whether build_executable succeeded, etc.
#
#    Individual report writers can either further subclass this or just
#    add GradeGroups if any are needed.
#
#---------------------------------------------------------------


class COMP11GradeReport(GradeReport):
    def __init__(self, resultsData, student, tests_for_student, 
                 code_compiles_grade=None,
                 other_tests_grade=None,
                 long_lines_grade=None,
                 has_tabs_grade=None,
                 long_lines_or_tabs_grade=None,
                 report_other_success_counts=True):
# longsourceortabs
        # Initialize superclass 
        GradeReport.__init__(self, resultsData)
        self.student = student
        self.tests_for_student = tests_for_student
        self.compute_grading_components(code_compiles_grade = code_compiles_grade,
                                        other_tests_grade = other_tests_grade,
                                        long_lines_grade = long_lines_grade,
                                        has_tabs_grade = has_tabs_grade,
                                        long_lines_or_tabs_grade = long_lines_or_tabs_grade,
                                        report_other_success_counts = report_other_success_counts)  # add all the standard grading components
        # Add to the master list of all digits results for all students

    def compute_grading_components(self, 
                                   code_compiles_grade = None,
                                   other_tests_grade = None,
                                   report_other_success_counts = True,
                                   long_lines_or_tabs_grade=None,
                                   long_lines_grade=None,
                                   has_tabs_grade=None):
        # Start with an ungraded (I.e. doesn't directly add points) grading
        # group for this student's tests. Note that this will compute.
        # which succeed, failed, etc. but because of grading GR_NONE won't
        # add grade points at this level.
        self.for_student= self.addGradeGroup(subset=self.tests_for_student, 
                                                description="Tests for student: "
                                                             + self.student,
                                                grading = GR_NONE)
        # - - - - - - - - - - - - - - - - - - - - - - - - - 
        #          Create a grading group for whether code compiles
        # - - - - - - - - - - - - - - - - - - - - - - - - - 

        #  If code_compiles_grade not supplied, we leave it out of the reporting tables
        if code_compiles_grade != None:
            code_compiles_grading = GR_ALL
            code_compiles_points = code_compiles_grade
        else: 
            code_compiles_points = None
            code_compiles_grading = GR_NONE
        
        #
        #  most comp11 testsets have combined category longsourceortabs, but that
        #  wasn't implemented for hw1. So we make it conditional
        #
        self.code_compiles= \
          self.addGradeGroup(subset=self.resultsData.byCategory[BUILD_EXECUTABLE_TESTCASE_NAME],
                             parent=self.for_student,
                             description="Code compiles and links",
                             grading=code_compiles_grading,
                             points=code_compiles_points,
                             remove=True) 

        # The above could in principle return more than one test
        # that was labeled as building the executable
            
#        assert len(self.code_compiles)==1,\
#            "More than one test was in category 'build_executable' for student {}".format(self.student)


        # - - - - - - - - - - - - - - - - - - - - - - - - - 
        #          Create a grading group for combination of
        #          source has long lines and tabs 
        # - - - - - - - - - - - - - - - - - - - - - - - - - 

        #  If long_lines_grade not supplied, we leave it out of the reporting tables
        if long_lines_or_tabs_grade != None:
            long_lines_or_tabs_grading = GR_ALL
            long_lines_or_tabs_points = long_lines_or_tabs_grade
        else: 
            long_lines_or_tabs_points = None
            long_lines_or_tabs_grading = GR_NONE
        
        #
        #  most comp11 testsets have combined category longsourceortabs, but that
        #  wasn't implemented for hw1. So we make it conditional
        #
        active_parent = self.code_compiles
        if "longsourceortabs" in self.resultsData.byCategory:
            self.long_lines_or_tabs= \
                 self.addGradeGroup(subset=self.resultsData.
                                    byCategory["longsourceortabs"],
                                    parent=self.code_compiles,
                                    description=".cpp source has no long lines and no tabs",
                                    grading=long_lines_or_tabs_grading,
                                    points = long_lines_or_tabs_points,
                                    report_success_counts = report_other_success_counts,
                                    remove=False) 

            # The above could in principle return more than one test
            # that was labeled as building the executable
            
 #           if long_lines_or_tabs_grade:
 #               assert len(self.long_lines_or_tabs) == 2,\
 #                   "When grading for long_lines_or_tabs, both tests must be provided for {} but we have {}".format(self.student, len(self.long_lines_or_tabs))
            active_parent = self.long_lines_or_tabs  # next one can link from this


        # - - - - - - - - - - - - - - - - - - - - - - - - - 
        #          Create a grading group for whether source has long lines
        # - - - - - - - - - - - - - - - - - - - - - - - - - 

        #  If long_lines_grade not supplied, we leave it out of the reporting tables
        if long_lines_grade != None:
            long_lines_grading = GR_ALL
            long_lines_points = long_lines_grade
        else: 
            long_lines_points = None
            long_lines_grading = GR_NONE
        self.long_source_lines= \
          self.addGradeGroup(subset=self.resultsData.byCategory["longsourcelines"],
                                     parent=active_parent,
                                     description="No source lines > 80 chars",
                                     grading=long_lines_grading,
                                     points = long_lines_points,
                             report_success_counts = report_other_success_counts,
                                     remove=True) 

        # The above could in principle return more than one test
        # that was labeled as building the executable
            
#        assert len(self.long_source_lines)==1,\
#            "More than one test was in category 'longsourcelines' for student {}".format(self.student)

        # - - - - - - - - - - - - - - - - - - - - - - - - - 
        #   Find sourcehastabs test
        # - - - - - - - - - - - - - - - - - - - - - - - - -
        #  If long_lines_grade not supplied, we leave it out of the reporting tables
        if has_tabs_grade != None:
            has_tabs_grading = GR_ALL
            has_tabs_points = has_tabs_grade
        else: 
            has_tabs_grading = GR_NONE
            has_tabs_points = None
        self.source_has_tabs= \
          self.addGradeGroup(subset=self.resultsData.byCategory["sourcehastabs"],
                                     parent=self.long_source_lines,
                                     description="No tabs in source",
                                     grading=has_tabs_grading,
                                     points=has_tabs_points,
                                     remove=True) 

       
        # The above could in principle return more than one test
        # that was labeled as building the executable
            
#        assert len(self.source_has_tabs)==1, "More than one test was in category 'sourcehastabs' for student {}".format(self.student)
        
        # - - - - - - - - - - - - - - - - - - - - - - - - -
        # Main collector of all tests where we actually ran
        # student code on data.
        # - - - - - - - - - - - - - - - - - - - - - - - - -

        if other_tests_grade != None:
            other_tests_grading = GR_PROPORTIONAL
            other_tests_points = other_tests_grade
        else: 
            other_tests_grading = GR_NONE
            other_tests_points = None
        self.data_tests = self.addGradeGroup(subset=None,
                                                parent=self.source_has_tabs,
                                                description="Tests that give input to student code",
                                                total_points = other_tests_points,
                                                report_success_counts = report_other_success_counts,
                                                grading=other_tests_grading) 

        # - - - - - - - - - - - - - - - - - - - - - - - - -
        #   Make a GradeGroup for tests on which valgrind was
        #   run. Note that this will automatically have:
        #
        #        valgrind_definitely_lost_tests: lists of tests with definitely lost
        #        valgrind_definitely_lost_test_count: count of tests with definitely lost
        #
        #   (April 23, 2021) FIXED: do this conditionally, as testsets that don't 
        #   use valgrind at all will typically not have the category
        # - - - - - - - - - - - - - - - - - - - - - - - - -

        if "valgrind" in self.resultsData.byCategory:
            self.valgrind_tests = \
                                  self.addGradeGroup(subset=self.resultsData.byCategory["valgrind"],
                                                     parent=self.data_tests,
                                                     description="Tests on which valgrind was run",
                                                     report_success_counts = False,
                                                     grading=GR_NONE) 


        
        
