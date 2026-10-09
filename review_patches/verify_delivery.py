from pathlib import Path
import html,re,ast
import numpy as np
source=Path('index.html').read_text(encoding='utf-8')
for filename,heading in [('smd/md_smd.in','md_smd.in — SMD 输入文件'),('smd/cv.in','cv.in — 质心距离限制文件'),('LiGaMD/job1.in','job1.in — conventional MD + GaMD Equilibration'),('LiGaMD/job2.in','job2.in — GaMD Production')]:
    start=source.index(heading); match=re.search(r'<pre>(.*?)</pre>',source[start:],re.S)
    assert Path(filename).read_text(encoding='utf-8').strip()==html.unescape(match.group(1)).strip(), filename
setup=Path('LiGaMD/setup_multi_T3Q.py').read_text(encoding='utf-8-sig')
start=source.index('Python — setup_multi_T3Q.py'); match=re.search(r'<pre>(.*?)</pre>',source[start:],re.S)
assert html.unescape(match.group(1)).strip()==setup.strip()
for f in ['analysis/ligamd_analysis.py','LiGaMD/setup_multi_T3Q.py','fix_md_errors.py','pack.py']:
    ast.parse(Path(f).read_text(encoding='utf-8-sig'))
print('Embedded scripts/input pairs match their files; maintained Python files parse.')
# Synthetic integration data verify the CLI pipeline and frame spacing, not real simulation physics.
rng=np.random.default_rng(123)
distance=np.r_[rng.normal(4,.1,90),rng.normal(12,.1,10)]
rows=np.column_stack([np.arange(1,101)*10000,distance,np.full(100,7.)])
Path('review_patches/cli_smoke').mkdir(exist_ok=True)
np.savetxt('review_patches/cli_smoke/production.csv',rows,delimiter=',',header='step,distance_A,boost_kcal_mol',comments='')
