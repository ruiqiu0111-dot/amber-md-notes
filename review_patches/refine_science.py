from pathlib import Path
import html,re
p=Path('index.html'); s=p.read_text(encoding='utf-8')
a=s.index('      <table>',s.index('8.1 QM 方法选择')); b=s.index('      </table>',a)+len('      </table>')
s=s[:a]+'''      <table>
        <tr><th>方法</th><th>成本与适用性</th><th>需要验证的因素</th></tr>
        <tr><td>PM3 / AM1 / PM6</td><td>较低成本，用于初步结构/路径探索</td><td>反应能、质子转移与势垒可能有体系依赖误差；不能凭方法名确定精度</td></tr>
        <tr><td>SCC-DFTB</td><td>成本较低，需适用的参数集</td><td>元素覆盖、参数化范围及该反应的基准误差</td></tr>
        <tr><td>DFT（B3LYP、M06-2X、ωB97X-D 等）</td><td>成本通常更高，应选合适基组和嵌入</td><td>泛函、基组、色散、电荷分布与 QM 区收敛性；不存在通用五星排序</td></tr>
      </table>''' + s[b:]
a=s.index('      <table>',s.index('8.3 计算资源估算')); b=s.index('      </table>',a)+len('      </table>')
s=s[:a]+'''      <p>不能仅根据 QM 原子数推断 ns 级 QM/MM 耗时。先以相同 QM 方法、基组、SCF 设置、嵌入、软件构建和硬件跑短基准，测量 wall time/MD step，再按窗口数×每窗口步数估算，并单独记录核数、并行效率与失败重启开销。示例工作量不代表采样已经收敛。</p>''' + s[b:]
s=s.replace('检查 PME 设置，确保 <code>qm_ewald=1</code>', '按所用 QM 接口和周期边界核对支持的长程静电方案；不要对所有外部程序盲设 qm_ewald/qm_pme')
s=s.replace('ts_idx = np.argmax(pmf)  # 过渡态','ts_idx = np.nanargmax(pmf)  # 此坐标PMF的极大值候选；需排除低采样端点并验证反应路径/committor')
s=s.replace('过渡态（TS）: ξ ≈ 0.0 Å', '候选中间区域: ξ ≈ 0.0 Å（真实过渡态不能由距离差为零保证）')
s=s.replace('<pre>&amp;cntrl\n  imin=0, irest=1, nstlim=500000', '<pre>QM/MM umbrella template: verify topology and external QM interface\n&amp;cntrl\n  imin=0, irest=1, ntx=5, nstlim=500000')
p.write_text(s,encoding='utf-8')
Path('LiGaMD/tleap.in').write_text('''# Compatibility entry point: use the parameterized-MOL2 copy/translate builder.
# From the project root, first run with real, aligned inputs and pocket coordinates:
# python LiGaMD/setup_multi_T3Q.py protein.pdb SAM.mol2 T3Q.mol2 x,y,z N
# Inspect the resulting tleap_multi_T3Q.in before invoking this wrapper.
# N is the count of initially free T3Q in that workflow, not SAM + T3Q.
# Do not combine the N-free-ligand output with nlig=6 unless six T3Q are present.
source tleap_multi_T3Q.in
''',encoding='utf-8')
Path('fix_md_errors.py').write_text('''"""Compatibility entry: run scientific regression checks; old string substitutions retired.

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
''',encoding='utf-8')
print('Replaced unsupported method rankings/resource estimates and obsolete helper behavior.')
