#!/usr/sup/bin/python
# NEEDSWORK: above should be /bin/env python3 (Noah 12/29/2020)
#
#                        grading.py
#
#      The classes in this module are intended to help with the development
#      of grading framework report writers, including the assignment of
#      numeric grades. This class works closely with the Results class in 
#      results.py (currently at V3 so named Results3 as of 1/29/2021) to
#      create subsets of grading results, each of which contributes a section
#      to a grading report.
#      

import sys

#
#            GradeReport    
#
#    This is the enclosing class for a grade report. Typically it will be
#    instantiated once per student, though in principle it could be used in 
#    other ways, e.g. if one wishes to make a summary report across students.
#


GR_NONE = 1
GR_PROPORTIONAL = 2
GR_ANY = 3
GR_ALL = 4

class GradeReport:
    # grade_type is typically int or float to determine whether 
    # fractional grades should be carried and reported
    # Note that the total_grade and addGradeGroup methods both provide for
    # overrides
    def __init__(self, resultsData, grade_type=int):
        # The Results3 object containg test results array, byXXX groupings, etc.        
        self.resultsData = resultsData
        self.gradeGroups = []
        self.grade_type=int

    def addGradeGroup(self, subset=None, description=None, grading=GR_PROPORTIONAL,
                      points=None, total_points=None,
                      remove=False, parent=None, report_success_counts=False,
                      grade_type=None):
        # Turns out you can't reference self in the initializers in the parm list
        if grade_type == None: 
            grade_type = self.grade_type
        newGroup = GradeGroup(self, subset=subset, 
                              description=description, grading=grading, 
                              points=points, total_points=total_points,
                              grade_type = grade_type,    # typically int or float
                              parent=parent, remove=remove,
                              report_success_counts=report_success_counts)
        self.gradeGroups.append(newGroup)
        return newGroup
    
    #
    #     total_grade
    #
    #     Returns a pair of (actual_grade, max_possible) counting only
    #     gradegroups for which grading !=GR_NONE
    def total_grade(self, grade_type = None):
        if grade_type == None:
            grade_type = self.grade_type
        # NEEDSWORK: assuming float is most general here?
        gather_actual = grade_type(0.0)
        gather_max = grade_type(0.0)
        for gg in self.gradeGroups:
            if gg.grading != GR_NONE:
                actual, max = gg.grades()
                gather_actual += actual
                gather_max += max
        return grade_type(gather_actual), grade_type(gather_max)

    def __iter__(self):
        return iter(self.gradeGroups)

    def __getitem__(self, i):
        return self.gradeGroups[i]

#
#            GradeGroup
#
#    Represents a subgroup of tests that will be reported and graded together.
#    For example, perhaps the abillity to handle complex input values is
#    is tested using a 5 test cases, and the student can get 
#    a score of 0-10 on those tests combined, by defining a grade group
#    for all of them, a per_item_score of 2, this class will automatically
#    compute the score and the max score (the letter extrapolated from the 
#    number of tests).
#
#    Options:
#
#         grading=proportional, total_points=n (each tests counts n/all_test_count)
#                      Note:proportional always adds up fractional points
#                      and truncates to int at the end if grade_type is int.
#                      NEEDSWORK: rounding not supported
#         grading=any, points=n  (The points given if at least one test passed,
#                       otherwise zero. Maxscore is implicitly points)
#         grading=all, points=n  (The points given if all tests in group passed,
#                       otherwise zero. Maxscore is implicitly points)
#         grade_type    Grades are cast to this type, which is normally passed
#                       in from add_grade_group but which otherwise defaults to int
#
#         ...Note: in the case of a group with one test, all and any do the same thing.
#
#            The grade_report object builds a tree (typically a list
#            of the groups. Each inherits a list of successful tests,
#            failed tests, etc.  from it's predecesoor in the list
#            (parent in the general case). By default, the grade_report
#            class adds groups in order, so that they form a simple list.
#            Sometimes, one wants to remove a set of tests from further consideration.
#            E.g. the first test might be to see if a program compiles. Even if
#            it does, one might not wish to include that in further reports
#            of how many tests passed and failed, etc. The remove switch indicates
#            that the tests in the current group should not be included in the
#            list of tests for any descendents.
#
#            Using the specific example, assume there are four tests:
#                  1 test to build the executable program
#                  3 tests on specific inputs. 
#
#            Let's say you want a reporting group that gives extra credit for
#            passing all tests and you want the message to say:
#                 Congratulations on passing all 3 tests.
#            By having the build test remove itself, then when the number of
#            tests and successful tests is queried in the next group, it will be
#            3 and 3 rather than 4 and 4.
#                                     
#         remove=True (default False)  
#
#         One of the following must be specified:
#            subset= <set of indices of items included in this group>
#            subset= None...group has same members as parent but after subsetting
#                       
#

class GradeGroup:
    def __init__(self, grade_report, subset=None, 
                 description=None,
                 report_success_counts=False,
                 points=None,
                 total_points = None,
                 grading=GR_PROPORTIONAL, grade_type = int,
                 remove=False, parent=None):
        assert description, "grading.Gradegroup: description argument missing on constructor"
        assert parent or subset != None, "grading.Gradegroup: {} constructor must have at least one of parent and subset".format(description)

        # The Results3 object containg test results array, byXXX groupings, etc.        
        self.grade_report = grade_report

        #
        # Record other arguments
        #
        self.parent = parent
        self.grading = grading
        self.remove = remove
        self.grade_type = grade_type
        self.description = description
        self.report_success_counts = report_success_counts
        if (grading == GR_ANY) or (grading == GR_ALL):
            assert points, "grading.Gradegroup: {}: \"points\" required for GR_ANY or GR_ALL"\
                .format(description)
        elif grading == GR_PROPORTIONAL:
            assert total_points, "grading.Gradegroup: {}: \"total_points\" required for GR_PROPORTIONAL"\
                .format(description)

        self.points = grade_type(points) if points != None else None
        self.total_points = grade_type(total_points) if total_points != None else None
        
        # resultsData
        self.resultsData = grade_report.resultsData
        r = self.resultsData               # short name for results data

        self.supplied_subset = subset
        s = subset                         # short name for subset
        
        #
        #    self.all_tests is the set of tests that are part of this group
        #
        #    If this group has a parent, then we intersect with its subset,
        #    as each child must be contained within parent. Note that by
        #    calling activeTests() rather than getting parent.subset
        #    we allow a parent to remove it's own tests from what children
        #    see.
        #
        #    If there is no parent (e.g. we are starting for a new student)
        #    then we take the supplied subset as is.
        #
        #    If subset=None then there is surely a parent, this creates 
        #    a all_tests just to get parent after removals processed. E.g.
        #    parent might remove the test for compiling from source. A null
        #    subset after that would set a universe of tests not including that.
        #

        # - - - - - - - - - - - - - - - - - - - - - - - - - 
        #    Collect various related subsets of this one
        # - - - - - - - - - - - - - - - - - - - - - - - - -

        #
        # All tests (intersects with parent if any)
        #
        if subset != None:
            self.all_tests = (subset & parent.activeTests()) if parent else (subset)
        else:
            self.all_tests = parent.activeTests()
        
        all = self.all_tests              # we'll use this a lot so give a short name

        self.all_test_count = len(all)

        #
        # TIMED OUT
        #
        self.successful_tests = r.successful & all 
        self.successful_test_count = len(self.successful_tests)
        
        #
        # ALLFAILED (includes timed out but not valgrind_definitely_lost)
        #
        self.all_failed_tests =  r.failed & all
        self.all_failed_test_count = len(self.all_failed_tests)

        #
        # TIMED OUT
        #
        self.timedout_tests =  r.timedout & all
        self.timedout_test_count = len(self.timedout_tests)

        #
        # VALGRIND DEFINITELY LOST
        #
        self.valgrind_definitely_lost_tests =  r.valgrinddefinitelylost & all
        self.valgrind_definitely_lost_test_count = \
                    len(self.valgrind_definitely_lost_tests)

        #
        # VALGRIND DEFINITELY LOST
        #
        self.valgrind_errors_tests =  r.valgrinderrors & all
        self.valgrind_errors_test_count = \
                    len(self.valgrind_errors_tests)

        #
        # FAILED (but not timed out..see ALLFAILED above))
        #
        self.failed_tests = self.all_failed_tests - self.timedout_tests # set difference 
                                                         # not subtraction!
        self.failed_test_count = len(self.failed_tests)

    #
    #    activeTests
    #
    #    The universe of all tests generally is passed from parent to child,
    #    but the parent can request removal, in which case not.
    def activeTests(self):
        if self.parent:
            parentActive = self.parent.activeTests()
        else:
            parentActive = self.all_tests
        if self.remove:
            return parentActive - self.all_tests  # set difference
        else:
            return parentActive
        
    def __iter__(self):
        return iter(self.all_tests)

    def __getitem__(self, i):
        return self.all_tests[i]

    def __len__(self):
        return len(self.all_tests)
        
        
    def __repr__(self):
        result = ""
        result+= "\n[[GradeGroup[Desc: {}] ".format(self.description)
        result+="\n  All Tests:\n---------\n"
        for r in self.all_results():
            result+="\n  {} {} {}".format(r["student"], r["testname"], r["description"])
        result+="\n  Successful Tests:\n---------------\n"
        for r in self.successful_results():
            result+="\n  {} {} {}".format(r["student"], r["testname"], r["description"])
        result+="\n  Failed Tests:\n------------\n"
        for r in self.failed_results():
            result+="\n  {} {} {}".format(r["student"], r["testname"], r["description"])
        result+="\nEnd Gradegroup ]]\n"
        return result
        
        

    #
    #  Returns all the results items in this subset, regardless of whether passed 
    #  or failed.
    #
    def all_results(self):
        return (self.grade_report.resultsData[i] for i in self.all_tests)

    def successful_results(self):
        return (self.grade_report.resultsData[i] for i in self.successful_tests)

    def timedout_results(self):
        return (self.grade_report.resultsData[i] for i in self.timedout_tests)

    def failed_results(self):
        return (self.grade_report.resultsData[i] for i in self.failed_tests)

    def all_failed_results(self):
        return (self.grade_report.resultsData[i] for i in self.all_failed_tests)

    #
    #  Returns set of failure reasons not including timeouts
    #
    
    def failure_reasons(self):
        return {fr["failurereason"] for fr in self.failed_results() 
                if fr["failurereason"]}
    

    #
    #  Returns set of failure reasons not including timeouts
    #
    
    def all_failure_reasons(self):
        return {fr["failurereason"] for fr in self.all_failed_results()
                if fr["failurereason"]}

    #
    #               grades
    #
    #      This method assigns the actual grades (which is to say, it 
    #      computes and returns them when asked).
    #       
    #      Returns a tuple of (points_awarded, max_points)
    #      Note, for GR_PROPORTIONAL, floating dividsion is done
    #      so grade my have a fractional part, regardless of grade_type.
    #      If the grade_type is int, then the grade is rounded before
    #      being returned.x
    #
    def grades(self):
        # GR_PROPORTIONAL, GR_ALL, GR_ANY, GR_NONE
        grading = self.grading
        if grading == GR_NONE:
            return (self.grade_type(0), self.grade_type(0))

        # Max points
        # Note that self.total_points and self.max_points are already of grade_type
        if grading==GR_PROPORTIONAL:
            max_points = self.total_points
            if self.all_test_count:
                points_per_item = (max_points / self.all_test_count)
                                      # floating division!
            else:
                points_per_item = 0
            # We have been adding up fractional points regardless of grade_type
            # Now truncate to integer if necessary, I.e. use whatever grade_type is.
            # NEEDSWORK: should have more general facilities for rounding
            # The following is a little redundant since it's not quite clear that
            # there are other sensible types beyond float and int, but the following
            # at least sort of tries to allow for the possibility, with the caveat
            # that int is the only type that gets rounding here.
            grade = (points_per_item * self.successful_test_count)
            if self.grade_type == int:
                grade = round(grade)        # in Python3 this returns an int (Not on p2!)
            grade = self.grade_type(grade)  # redundant in the case of int or float
                                            # ...who knows, maybe there's something 
                                            # ...else? Would be great if types had a
                                            # ...round as a class method, then we
                                            # ...could generalize this!
        elif grading==GR_ANY:
            max_points = self.points
            # Any gives credit if any test was passed
            grade = self.points if self.successful_test_count else 0
        elif grading==GR_ALL:
            max_points = self.points
            # Any gives credit if all tests were passed
            # Noah change Feb 20, 2021: added test to make sure all_test_count > 0
            # Otherwise has the weird behavior that if we wound up with no tests
            # at all in this group (when can happen when there's missing summary
            # data, for example), students can get credit for 0 out of 0. Fixed.
            #
            grade = (self.points 
                     if (self.all_test_count and 
                         (self.successful_test_count == self.all_test_count)) 
                     else 0)
        return (grade, max_points)

    
    
