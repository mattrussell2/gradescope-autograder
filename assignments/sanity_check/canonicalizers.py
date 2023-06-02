from pathlib import Path 

def do_nothing(student_unccd_output, reference_unccd_output, testname, streamname, params):
    return student_unccd_output

def sort_lines(student_unccd_output, reference_unccd_output, testname, streamname, params):
    return '\n'.join(sorted(student_unccd_output.splitlines()))

def sort_num_lines(student_unccd_output, reference_unccd_output, testname, streamname, params):
    return '\n'.join([str(x) for x in sorted([int(x) for x in student_unccd_output.splitlines()])])