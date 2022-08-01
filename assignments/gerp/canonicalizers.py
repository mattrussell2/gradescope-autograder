from pathlib import Path 

def sort_lines(student_output, *args):
    return '\n'.join(sorted(student_output.splitlines()))