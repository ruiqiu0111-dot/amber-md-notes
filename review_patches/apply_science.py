from pathlib import Path
import json
p=Path('index.html'); s=p.read_text(encoding='utf-8')
for name in ['qmmm_science']:
    changes=json.loads(Path(f'review_patches/{name}.json').read_text(encoding='utf-8-sig'))
    for i,x in enumerate(changes):
        old=x['old'].replace('\r\n','\n').replace('\r','')
        new=x['new'].replace('\r\r\n','\n').replace('\r\n','\n').replace('\r','')
        if s.count(old)!=1: raise ValueError(f'{name}[{i}]: {s.count(old)} matches')
        s=s.replace(old,new)
s=s.replace('最小化、生产及各窗口必须保持 QM 原子集、总电荷、QM 方法和边界处理一致；改变其中任何一项都会改变势能面，不能将不同 Hamiltonian 的窗口拼成同一个 PMF。', '本例最小化与生产采用同一 QM 定义以简化流程。若先用 MM 或另一 QM 模型准备初态，切换后需要在目标 Hamiltonian 下重新平衡。用于合并同一 PMF 的生产窗口须使用一致的 QM 原子集、总电荷、方法和边界处理；改变它们会改变势能面，须用相应的跨 Hamiltonian 重加权方法，不能直接套用仅去 umbrella 偏置的 WHAM。')
s=s.replace('不能直接接续上文 PM6 的最小化/生产轨迹。若采用此路线，所有初始化、平衡和伞形窗口都必须使用相同的 QM 原子集、', '不能未经目标方法重新平衡就把 PM6 样本当作外部 QM 样本。初态可由另一模型准备，但所有待合并的生产窗口必须使用相同的 QM 原子集、')
p.write_text(s,encoding='utf-8')
print('Applied 12 QM/MM scientific corrections, with explicit re-equilibration conditions.')
