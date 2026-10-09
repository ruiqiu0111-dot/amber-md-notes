from pathlib import Path
import json
p=Path('tests/test_ligamd_analysis.py')
s=p.read_text(encoding='utf-8-sig').replace('np.ones(10)]','np.full(10,1.5)]').replace("self.assertAlmostEqual(stats['k_off_biased_s_inv'], 1/(.04e-9))", "np.testing.assert_allclose(stats['k_off_biased_s_inv'], 1/(.04e-9), rtol=1e-12)")
p.write_text(s,encoding='utf-8')
p=Path('index.html'); s=p.read_text(encoding='utf-8')
for name in ['gromacs_vmd']:
    changes=json.loads(Path(f'review_patches/{name}.json').read_text(encoding='utf-8-sig'))
    for i,x in enumerate(changes):
        old=x['old'].replace('\r\n','\n').replace('\r','')
        new=x['new'].replace('\r\r\n','\n').replace('\r\n','\n').replace('\r','')
        if s.count(old)!=1:
            raise ValueError(f'{name}[{i}] matching {s.count(old)}')
        s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('Applied 19 reviewed GROMACS/VMD corrections.')
