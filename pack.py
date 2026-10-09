"""Package the current website and its reproducible analysis examples."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
files = ['index.html', 'style.css', 'main.js', 'README.md',
         'SCIENTIFIC_CORRECTIONS.md', 'requirements-analysis.txt',
         'analysis/ligamd_analysis.py', 'tests/test_ligamd_analysis.py',
         'LiGaMD/setup_multi_T3Q.py', 'LiGaMD/job1.in', 'LiGaMD/job2.in',
         'LiGaMD/tleap.in', 'smd/cv.in', 'smd/md_smd.in']
if __name__ == '__main__':
    with ZipFile(ROOT / 'website.zip', 'w', ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(ROOT / name, name)
    print(f'website.zip created: {len(files)} files')
