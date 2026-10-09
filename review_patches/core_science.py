from pathlib import Path
import html, re
p=Path('index.html'); s=p.read_text(encoding='utf-8')
# These choices illustrate a staged relaxation protocol, not a uniquely correct protocol.
s=s.replace('第2步：限制溶剂和离子','第2步：约束溶质重原子，松弛溶剂')
s=s.replace('放松溶质原子，仅固定水分子和离子。','继续约束溶质重原子，让水、离子和氢原子松弛；位置约束具有有限力常数，不等于冻结坐标。')
s=s.replace("restraintmask=':Na+,Cl-,WAT'", "restraintmask=':1-239&amp;!@H='")
s=s.replace('固定溶剂/离子，放松溶质（优化蛋白-配体接触）','约束溶质重原子，松弛溶剂/离子和氢')
s=s.replace('放松配体和小分子，仅固定蛋白质残基。','约束蛋白质残基，放松配体、辅因子和溶剂；确认该阶段不会破坏待研究的初始结合构象。')
s=s.replace('固定蛋白质，放松配体和小分子','约束蛋白质，放松配体、辅因子和溶剂')
s=s.replace(' ntc=2, ntb=1,\n  ntf=2,\n  ntpr=100,',' ntc=1, ntb=1,\n  ntf=1,\n  ntpr=100,')
# Consistent LiGaMD source values: don't replace specialized force evaluation
# with conventional MD settings solely on the basis of a SHAKE comment.
a=s.index('id="ligamd"'); b=s.index('  <!-- ===== Gromacs',a) if '  <!-- ===== Gromacs' in s[a:] else len(s)
x=s[a:b]
x=x.replace('ntf=2,         ! Do not calculate forces of bonds containing hydrogen (standard with ntc=2)','ntf=1,         ! Complete force evaluation; check LiGaMD/TI compatibility for this build')
x=x.replace('ntc=2, ntf=2,','ntc=2, ntf=1,')
x=x.replace('ntc = 2, ntf = 1（SHAKE）','ntc = 2（含氢键长约束）, ntf = 1（完整力评估；按实现核对）')
x=x.replace('atom_p=1636,','atom_p=__FILL_PROTEIN_REFERENCE_ATOM__,')
x=x.replace('atom_l=1,  ! 示例：配体内部第1个原子；必须选定与口袋参考点相配的原子','atom_l=__FILL_LIGAND_INTERNAL_ATOM__,')
x=x.replace('需要 <strong>1 个结合在活性位点的配体</strong>和<strong>数个游离在溶剂中的配体</strong>（一般推荐 3-5 个）。','可采用单配体或多配体方案，初态可用于结合或解离研究，并非必须同时有一个结合配体和固定数目的游离配体。多配体数量会改变游离浓度、配体间作用与再结合统计，需要结合盒子体积和目标问题设计。下方放置脚本生成 N 个初始游离 T3Q；SAM 是辅因子，不能计入 T3Q 的 nlig。')
x=x.replace('Job1 总步数：<code>nstlim = ntcmd + nteb</code>','Job1 总步数：<code>nstlim = ntcmd + nteb</code>；ntcmdprep 和 ntebprep 包含在各自阶段内部，不另行相加。输入中 __FILL_...__ 是待核对的最终拓扑编号，替换后才可运行。')
x=x.replace('ntpr=1000,     ! Print energies every 1000 steps','ntpr=1000,     ! Print energies every 1000 steps')
x=x.replace('ntwr=2500,    ! Print a restart file every 10K steps','ntwr=2500,    ! Print a restart file every 2500 steps')
x=x.replace('t = np.arange(len(distance)) * frame_dt_ns', 'frame_dt_ns = 0.02  # Job2示例保存间隔；按实际步号核对\nt = np.arange(len(distance)) * frame_dt_ns')
x=x.replace('def find_transition_state_structures(', 'def find_intermediate_candidates(')
# Embed the corrected authoritative setup script, eliminating an obsolete independent copy.
pos=x.index('Python — setup_multi_T3Q.py'); ca=x.index('<pre>',pos)+5; cb=x.index('</pre>',ca)
setup=Path('LiGaMD/setup_multi_T3Q.py').read_text(encoding='utf-8-sig')
x=x[:ca]+html.escape(setup,quote=False)+x[cb:]
# Single-ligand residue pairs for MDTraj contacts, not zipped atom indices.
pos=x.index('def analyze_contacts_per_state'); ca=x.rfind('<pre>',0,pos)+5; cb=x.index('</pre>',pos)
contacts='''def analyze_contacts_per_state(trajectory, topology, states, ligand_residue='LIG'):
    """Return protein-residue contact frequencies in biased bound frames (not reweighted)."""
    import numpy as np
    import mdtraj as md
    traj = md.load(trajectory, top=topology)
    states = np.asarray(states)
    if states.shape != (traj.n_frames,):
        raise ValueError('states must align with trajectory frames')
    ligand_residues = [r.index for r in traj.topology.residues if r.name == ligand_residue]
    if len(ligand_residues) != 1:
        raise ValueError('Select one physical ligand; split multi-ligand analysis')
    protein_residues = [r.index for r in traj.topology.residues if r.is_protein]
    bound_frames = np.flatnonzero(states == 1)
    if not protein_residues or not bound_frames.size:
        raise ValueError('Protein residues and bound frames required')
    pairs = np.array([(r, ligand_residues[0]) for r in protein_residues], dtype=int)
    distances_nm, pairs = md.compute_contacts(traj.slice(bound_frames),
        contacts=pairs, scheme='closest-heavy', periodic=True)
    frequency = (distances_nm < 0.45).mean(axis=0)
    return pairs[:,0], frequency  # topology residue indices, zero-based
# MDTraj returns nm; 0.45 nm = 4.5 A. Mapping to residue labels needs topology.residue(index).'''
x=x[:ca]+html.escape(contacts,quote=False)+x[cb:]
x=x.replace('hbond out hbond_time.dat :1-300 :LIG dist 3.0 angle 120 series','hbond LigandHB (:1-237|:239) out hbond_time.dat dist 3.0 angle 120 nointramol series\nrun')
x=x.replace('distance com_dist :LIG :45-55,78-85,110-120 out com_distance.dat','distance com_dist :239 :45-55,78-85,110-120 out com_distance.dat\n# 239和口袋mask仅为示例；单个物理配体/PBC处理/身份跟踪须按体系核对。\nrun')
x=x.replace('hbond out hbond.dat :1-300 :LIG dist 3.0 angle 120','hbond LigandHB (:1-237|:239) out hbond.dat dist 3.0 angle 120 nointramol\nrun')
s=s[:a]+x+s[b:]
# Prefer linear constant-speed illustrative SMD path, with correct integer-vector length.
s=s.replace('cv_ni = 10,\n  cv_i = 3592,3591,3590,3593, 0, 3660,3654,3649,3664,3665,3644,','cv_ni = 11,  ! 4 + delimiter 0 + 6 integer entries\n  cv_i = 3592,3591,3590,3593, 0, 3660,3654,3649,3664,3665,3644,')
s=s.replace("npath = 5, path=6,7,8,9,10\n  path_mode = 'SPLINE'", "npath = 2, path=6.0,10.0\n  path_mode = 'LINES'")
s=s.replace("<code>path_mode='SPLINE'</code> — 使用样条插值定义拉伸路径", "<code>path_mode='LINES'</code> — 1 ns 内目标中心由 6 增到 10 Å，本例为 4 Å/ns。反向路径同样可用于结合方向；弹簧参数和路径需验证，不能由章节名称决定。原子列表仅为示例，必须按最终拓扑选择实际口袋与配体原子。")
s=s.replace('<strong>弹簧常数</strong>：通常为 5-10 kcal/mol/Å²，过软会导致信号噪音，过硬会导致瞬时力过大','<strong>弹簧参数</strong>：数值与软件偏置势定义有关，先核对 harm 与物理 k 的因子；依据反应坐标波动、积分稳定性和重构误差选择，不能把 10 或 800 当作普遍标准')
s=s.replace('<strong>收敛性检查</strong>：多条轨迹的结果方差应在可接受范围','<strong>收敛性检查</strong>：检查低功尾部采样、分块与独立重复不确定度、协议端态平衡及速度敏感性；仅方差小不保证收敛')
s=s.replace('完全脱离口袋，弹簧力归零','离开口袋不保证弹簧力归零；仍有粘滞阻力及移动偏置作用')
s=s.replace('# 从 NAMD/Amber SMD 输出日志提取拉伸力','# 仅适用于下述 NAMD SMD 日志格式；AMBER 需按原生输出另写解析器')
p.write_text(s,encoding='utf-8')
# Resynchronize authoritative input blocks after the physical assumptions are made explicit.
for filename,heading in [('smd/md_smd.in','md_smd.in — SMD 输入文件'),('smd/cv.in','cv.in — 质心距离限制文件'),('LiGaMD/job1.in','job1.in — conventional MD + GaMD Equilibration'),('LiGaMD/job2.in','job2.in — GaMD Production')]:
    start=s.index(heading); match=re.search(r'<pre>(.*?)</pre>',s[start:],re.S)
    Path(filename).write_text(html.unescape(match.group(1)).strip()+'\n',encoding='utf-8')
print('Scientific assumptions made explicit; source scripts and inputs synchronized.')
