from pathlib import Path 

def sort_lines(student_output):
    return '\n'.join(sorted(student_output.splitlines()))