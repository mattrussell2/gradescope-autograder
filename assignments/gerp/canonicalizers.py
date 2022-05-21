from pathlib import Path 

def sort_lines(fname):
    return '\n'.join(sorted(Path(fname).read_text().splitlines()))