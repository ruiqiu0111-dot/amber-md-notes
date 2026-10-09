"""Compatibility entry: run scientific regression checks; old string substitutions retired.

Changing cutoffs, force fields or QM choices by keyword substitution is not a
scientific validation. Review those parameters against the actual system.
"""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    raise SystemExit(subprocess.call([sys.executable, '-m', 'unittest',
                                     'discover', '-s', 'tests', '-v'], cwd=root))
