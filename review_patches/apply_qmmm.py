from pathlib import Path
import json
p=Path('index.html'); s=p.read_text(encoding='utf-8')
a=json.loads(Path('review_patches/qmmm.json').read_text(encoding='utf-8-sig'))
for i,x in enumerate(a):
    old=x['old'].replace('\r\n','\n').replace('\r','')
    new=x['new'].replace('\r\r\n','\n').replace('\r\n','\n').replace('\r','')
    if s.count(old)!=1:
        raise ValueError(f'qmmm[{i}]: {s.count(old)} matches; {old[:100]}')
    s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('Applied 7 QM/MM corrections')
print('\n\n'.join(x['new'] for x in a if 'FES' in x['new']))
