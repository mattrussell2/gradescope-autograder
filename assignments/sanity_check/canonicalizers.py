from pathlib import Path 

def do_nothing(output, *args):
    return output

def sort_lines(student_output, *args):
    return '\n'.join(sorted(student_output.splitlines()))

def sort_num_lines(student_output, *args):
    return '\n'.join([str(x) for x in sorted([int(x) for x in student_output.splitlines()])])