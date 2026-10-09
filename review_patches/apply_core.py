from pathlib import Path
import html
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8-sig')

def replace(old, new, count=None):
    global s
    actual = s.count(old)
    if not actual or (count is not None and actual != count):
        raise ValueError(f'replacement count {actual}: {old[:90]}')
    s = s.replace(old, new)

def block_after(anchor, new_code):
    global s
    start = s.index(anchor)
    a = s.index('<pre>', start) + len('<pre>')
    b = s.index('</pre>', a)
    s = s[:a] + html.escape(new_code, quote=False) + s[b:]

def subsection(anchor, next_anchor, content):
    global s
    a = s.rfind('    <div class="subsection">', 0, s.index('id="'+anchor+'"'))
    b = s.rfind('    <div class="subsection">', 0, s.index('id="'+next_anchor+'"'))
    s = s[:a] + content + '\n\n' + s[b:]

def code(text, label='Python'):
    return '<div class="code-block"><div class="code-header"><span class="lang">'+label+'</span><button class="copy-btn">复制</button></div><pre>'+html.escape(text, quote=False)+'</pre></div>'

replace('本站记录了使用 <strong>AMBER</strong> 进行蛋白质-配体分子动力学模拟的完整流程，涵盖从 RESP 电荷计算、体系搭建、平衡模拟到正式 MD 运行及结果分析的全部步骤。', '本站整理 AMBER / GROMACS 模拟方法与示例。输入参数需要按体系调整；本仓库进行静态检查和分析算法回归测试，未完成真实体系的模拟验证。常规 AMBER 示例约定蛋白为 :1-237、SAM 为 :238、目标配体为 :239；QM/MM 与其他示例使用各自的编号，不能混用。运行前从最终拓扑核对原子、残基、净电荷、质子化态、盒子与力场。软件版本和依赖说明见 README。')
replace('RESP电荷计算 → 小分子/蛋白质准备', '选择 RESP 或 AM1-BCC 电荷 → 小分子/蛋白质准备')
replace('使用 Multiwfn 计算 RESP 电荷步骤：<code>7 → 18 → 1</code>', '使用 Multiwfn 的 RESP 拟合功能（菜单依版本核对），记录拟合设置、等价原子约束及净电荷；HF/MK 步骤生成 ESP 数据，RESP 是其后的拟合步骤')
replace('将计算得到的每个原子的电荷修改到 <code>GA_ante.mol2</code> 内', '逐原子核对元素、名称、连接和顺序后导出 charge 文件或写入 mol2；必须检查电荷总和等于设定净电荷。不要按行号盲目覆盖，不要在 RESP 后重新运行 BCC 覆盖电荷')
replace('在 Chimera、DS 里面对 ligand 做加 H 加电荷处理（AM1-BCC 电荷），structure editing。', '先确定配体的化学结构、键级、质子化态、互变异构体和净电荷，再加氢。RESP 与 AM1-BCC 是两条替代路线；下面是 AM1-BCC/GAFF2 示例，净电荷必须由使用者设置，不使用默认电荷猜测。SAM 的参数适用性需要单独检查。')
block_after('id="ligand"', '''# 设置实际净电荷后运行，例如 export GA1_CHARGE=...; export SAM_CHARGE=...
: "${GA1_CHARGE:?请设置目标配体整数净电荷}"
: "${SAM_CHARGE:?请设置SAM整数净电荷}"
antechamber -i GA1.mol2 -fi mol2 -o GA1_ante.mol2 -fo mol2 -at gaff2 -c bcc -nc "$GA1_CHARGE"
parmchk2 -i GA1_ante.mol2 -f mol2 -s gaff2 -o GA1.frcmod
antechamber -i SAM.mol2 -fi mol2 -o SAM_ante.mol2 -fo mol2 -at gaff2 -c bcc -nc "$SAM_CHARGE"
parmchk2 -i SAM_ante.mol2 -f mol2 -s gaff2 -o SAM.frcmod
# RESP 路线：使用已验证与输入原子顺序一致的 charge 文件，替代 -c bcc：
# antechamber ... -at gaff2 -c rc -cf resp_charges.txt -nc "$GA1_CHARGE"
# 检查 frcmod 中缺失/低可信度参数、mol2 原子类型和电荷总和。''')
# Scope common examples to the documented residue mapping.
common_end = s.index('  <!-- QMMM + Umbrella Sampling -->')
a, b = s[:common_end], s[common_end:]
a = a.replace('source leaprc.gaff', 'source leaprc.gaff2')
a = a.replace('COM = combine {REC, LIG1, LIG2}', 'COM = combine {REC LIG2 LIG1}')
a = a.replace('LIG = combine {LIG1, LIG2}', 'LIG = combine {LIG1 LIG2}')
a = a.replace("restraintmask='!:1-249'", "restraintmask=':1-237'")
a = a.replace("restraintmask=':Na+,WAT'", "restraintmask=':Na+,Cl-,WAT'")
a = a.replace(':1-357', ':1-239').replace(':1-355', ':1-237')
a = a.replace('receptor 1-355, 357', '蛋白示例范围 1-237；请按最终拓扑核对')
a = a.replace('print_res="1-357"', 'print_res="1-239"')
a = a.replace('heat.mdcrd', 'heat.nc').replace('equil.dcd', 'equil.nc').replace('md.dcd', 'md.nc')
a = a.replace('ntpr=500, ntwx=500,', 'ntpr=500, ntwx=500, ioutfm=1,')
a = a.replace('ntpr=1000, ntwx=1000, ntwr=5000,', 'ntpr=1000, ntwx=1000, ntwr=5000, ioutfm=1,')
a = a.replace('ntpr=5000, ntwx=5000, ntwr=50000,', 'ntpr=5000, ntwx=5000, ntwr=50000, ioutfm=1,')
a = a.replace('其余重原子固定', '其余重原子受到谐振位置约束（并非完全固定）')
a = a.replace('固定重原子，仅放松 H', '约束重原子，优先松弛 H')
a = a.replace('50ps 恒压模拟', '恒压密度松弛（50 ps 示例）')
a = a.replace('使体系密度达到平衡值。', '先运行 50 ps 恒压密度松弛，再依据密度、体积和能量的分块统计决定是否延长；固定时长不能保证平衡。')
a = a.replace('检查 MD 主干重原子 RMSD 是否平衡。', '监测蛋白 Cα RMSD；平台只是一个诊断指标，需要结合热力学量、关键构象、多条独立轨迹和目标可观测量的收敛。')
a = a.replace('检查主干重原子 RMSD', '检查蛋白 Cα RMSD')
a = a.replace('以 amber 的氢命名方式重新添加H原子', '检查质子化态后使用 reduce 加氢，随后核对 AMBER 命名')
a = a.replace('pdb4amber -i SeNMT.pdb -o SeNMT.pdb', 'pdb4amber -i SeNMT.pdb -o SeNMT_checked.pdb')
a = a.replace('source leaprc.water.tip3p                   # 加载水分子力场 tip3p', 'source leaprc.water.tip3p                   # 加载水分子力场 tip3p\nset default PBRadii mbondi2                # 本例 MM/GBSA igb=2；其他模型需匹配半径')
s = a + b
replace('# 将 mdcrd 格式转换为 VMD 可识别的 nc 格式\ncpptraj -p com_solvated.prmtop -y equil.nc -x equil.nc', '# 输入已用 ioutfm=1 生成 NetCDF；文件后缀本身不会决定格式。\n# 如需转换其他轨迹，应使用不同输出文件名，避免覆盖输入。')
replace('startframe=5000, endframe=10000, verbose=2,  ! 取平衡后50%轨迹进行分析', 'startframe=2501, endframe=5000, interval=5, verbose=2,  ! 本例5000帧；需检查实际帧数和相关时间')
# full complex is REC+SAM+GA1; target ligand GA1 and receptor REC+SAM
replace('-rp receptor.prmtop -lp GA1.prmtop', '-rp receptor_SAM.prmtop -lp GA1.prmtop')
replace('COM = combine {REC, LIG2}\nsaveamberparm LIG com.prmtop com.inpcrd', 'REC_SAM = combine {REC LIG2}\nsaveamberparm REC_SAM receptor_SAM.prmtop receptor_SAM.inpcrd\nCOM = combine {REC_SAM LIG1}\nsaveamberparm COM com.prmtop com.inpcrd')
replace('此处的 LIG2（SAM）不是研究重点，将其与 receptor 合并，最后的 ligand 为你所研究的分子。', '本例研究 GA1 在含 SAM 的蛋白受体上的结合：-rp 使用 receptor_SAM.prmtop，-lp 使用 GA1.prmtop，-cp 使用完整 com.prmtop。这是与将两个配体作为一个整体不同的热力学分割；必须保持原子顺序、力场参数和半径一致，建议从同一完整拓扑派生。MM/PBSA、MM/GBSA 是端点近似；本例未计算熵，结果不能作为严格的绝对结合自由能。')
replace("rms first\naverage crdset MyAvg\nrun\nrms ref MyAvg", "autoimage\nrms first :1-237@CA\naverage avg.pdb :1-237 pdb\nrun\nclear actions\nreference avg.pdb\nrms reference :1-237@CA")
replace('atomicfluct out backbone-atoms.agr @C,CA,N</pre>', 'atomicfluct out backbone-atoms.agr :1-237@C,CA,N\nrun</pre>')
# Consistent data format / production-stage parameters
replace('nstlim = ntcmd + ntebprep', 'nstlim = ntcmd + nteb')
replace('启用 LiGaMD 模式', '启用 LiGaMD_Dual（配体非键能及体系剩余势能双提升）')
replace('对总势能进行加速', '阈值能量 E 的选择：1 为下界；iEP/iED 可分别覆盖')
replace('提升势标准差上限（势能/二面角）', '第一/第二提升势的标准差上限；LiGaMD_Dual 中对应配体非键能/体系剩余势能')
replace('蛋白质和配体的原子序号（结合 <code>dblig</code> 距离阈值自动判断哪个配体处于结合态）', '蛋白参考原子的序号，以及单个配体内部从 1 开始的原子序号；按最终拓扑核对，不能用全体系配体原子编号替代 atom_l')
replace('atom_l=3656,', 'atom_l=1,  ! 示例：配体内部第1个原子；必须选定与口袋参考点相配的原子')
replace('iE = 1 或 2（能量收集频率）', 'iE = 1 或 2（阈值能量选择；iEP/iED 可覆盖）')
replace('sigma0D = 6.0（二面角提升标准差上限）', 'sigma0D = 6.0（LiGaMD_Dual 第二提升势标准差上限）')
replace('骨架 RMSD &lt; 2-3 Å', '骨架 RMSD 及口袋结构随时间无异常漂移；阈值按体系确定')
replace('至少 3-5 次完整循环', '检查独立重复、有效事件数与不确定度，不能用固定次数保证收敛')
# Replace whole affected analysis subsections, retaining anchor IDs.
subsection('ligamd-events','ligamd-reweight', '''    <div class="subsection">
      <h3 class="subsection-title" id="ligamd-events">6. 结合/解离事件的定义与检测</h3>
      <p>先根据口袋结构、接触和距离定义结合核心态与游离核心态。下面用 d&lt;5 Å 和 d&gt;10 Å 演示滞后判据，中间区间保留最近的核心态；这些阈值需要敏感性分析，不能普遍套用。多个配体应逐配体追踪，不能把所有配体合成一个质心。启用 ibblig 时还需核对配体交换对身份跟踪的影响。</p>
      <p>可设置连续确认帧数抑制快速往返；最初未知态不计转换。末尾未完成的停留区间属于右删失，不应当作完整寿命。反应坐标中间区域也不自动等于动力学过渡态。</p>
      ''' + code('''from analysis.ligamd_analysis import detect_events
# distance 是经过PBC处理的单个配体-口袋距离，按保存帧排列。
states, events = detect_events(distance, d_bound=5, d_unbound=10,
                               min_confirm_frames=3)
print(f"确认的核心态转换: {len(events)}")''') + '\n    </div>')
subsection('ligamd-reweight','ligamd-kinetics', r'''    <div class="subsection">
      <h3 class="subsection-title" id="ligamd-reweight">7. 重加权分析（Reweighting）</h3>
      <p>仅分析偏置参数固定后的生产阶段。令 ΔV 为该帧所有提升势之和（kcal/mol），β=1/(kBT)，归一化指数重加权为：</p>
      <p>$$\langle O\rangle_0=\frac{\langle Oe^{\beta\Delta V}\rangle_b}{\langle e^{\beta\Delta V}\rangle_b}$$</p>
      <p>AMBER 默认日志为 gamd.log（可由 -gamdlog 改名）。列格式必须查阅当前版本及输出表头；不要假定 igamd.dat 的第三列就是总偏置。按 MD 步号将距离与两项偏置对齐，并导出 step,distance_A,boost_kcal_mol 三列 CSV。CPPTRAJ 帧号必须先按轨迹起始步与 ntwx 映射为 MD 步号。相同行数不等于数据已经对齐。</p>
      <h4>7.1 归一化指数估计（用于诊断）</h4>
      ''' + code('''from analysis.ligamd_analysis import KB, reweighted_mean
beta = 1 / (KB * 300)
average_distance = reweighted_mean(distance, total_boost, beta)
# 数值稳定不能消除少数高权重帧造成的统计不收敛。''') + r'''
      <h4>7.2 二阶累积量近似 PMF</h4>
      <p>每个反应坐标区间分别计算提升势均值和方差；当条件提升势分布接近高斯、采样充分时，采用：</p>
      <p>$$F_i\approx-\beta^{-1}\ln(n_i/\Delta\xi_i)-\langle\Delta V\rangle_i-\frac{\beta}{2}\mathrm{Var}(\Delta V)_i+C$$</p>
      <p>该式保留实际区间占比和偏置均值。零采样或低采样区间输出 NaN，不使用任意小概率制造有限能垒。需检查条件分布非高斯性、时间相关性、分块与独立重复收敛。</p>
      ''' + code('''from analysis.ligamd_analysis import calculate_pmf_ligamd
xi, pmf, counts = calculate_pmf_ligamd(distance, total_boost, beta,
                                      bins=50, min_count=10)
# counts阈值仅筛选稀疏区间，不能代替有效样本数或误差估计。''') + '''
      <p><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC7768792/">LiGaMD 原论文（附录 B）</a>；<a href="https://www.med.unc.edu/pharm/miaolab/wp-content/uploads/sites/1385/2023/09/GaMD_Amber-manual.pdf">AMBER 实现说明</a>。</p>
    </div>''')
subsection('ligamd-kinetics','ligamd-path', r'''    <div class="subsection">
      <h3 class="subsection-title" id="ligamd-kinetics">8. 动力学统计与 PMF 解读</h3>
      <h4>8.1 偏置轨迹中的表观事件速率</h4>
      <p>下面仅计算偏置模拟的事件数/状态总暴露时间，不能直接作为真实 k_off、k_on 或 K_d。帧间隔为 dt(ps)×ntwx/1000 ns；Job2 示例为 0.002×10000/1000=0.02 ns。结合速率还需要与事件定义匹配的游离配体浓度 [L]。</p>
      <p>$$k_{off}^{b}=N_{unbind}/T_{bound}^{b},\qquad k_{on}^{b}=N_{bind}/(T_{unbound}^{b}[L])$$</p>
      ''' + code('''from analysis.ligamd_analysis import estimate_biased_kinetics
stats = estimate_biased_kinetics(states, frame_dt_ns=0.02,
                               ligand_concentration_M=None)
print(stats)  # 单位s^-1；给定浓度时k_on单位M^-1 s^-1
# 两态马尔可夫/均匀帧间隔只是统计模型假设；末尾区间计入暴露时间。''') + r'''
      <p>真实动力学需要独立的方法验证和动力学重加权，例如原论文采用的 TST/Kramers 分析；不能简单用平均提升势的指数乘以停留时间。无事件只说明采样中未观察到事件，不证明真实速率为零。</p>
      <h4>8.2 PMF 水平差与标准结合自由能</h4>
      <p>PMF(unbound)−PMF(bound) 仅表示该坐标上的游离减结合水平差，接近解离方向，不能标为标准结合自由能。径向坐标还涉及 4πr² 的几何因子；标准 ΔG_bind 必须按状态定义积分并处理约束与标准态体积，不是简单反转符号就能得到。</p>
      ''' + code('''from analysis.ligamd_analysis import pmf_level_difference
level_difference = pmf_level_difference(xi, pmf, (0,5), (10,20))
print(f"PMF水平差（不是标准ΔG_bind）: {level_difference:.2f} kcal/mol")''') + '\n    </div>')
# Fix remaining old claims/standalone main script.
replace('np.arange(len(distance)) * 0.002  # 转换为 ns', 'np.arange(len(distance)) * frame_dt_ns  # 保存帧间隔（ns），不能用积分步长')
replace('np.array(bound_lifetimes)*0.002', 'np.array(bound_lifetimes)*frame_dt_ns')
replace('PMF(unbound) - PMF(bound)', '状态积分 + 几何/约束/标准态修正')
replace('提取 Vbias ──→ Maclaurin 展开', '按步号对齐总提升势 ──→ 二阶累积量与收敛检查')
replace('k_off ≈ N_unbind / τ_bound ──→ residence time', '表观事件速率 ──→ 单独动力学重加权/验证')
replace('<strong>Maclaurin 阶数</strong></td><td>通常 2-3 阶足够，高阶可能引入噪声', '<strong>二阶累积量适用性</strong></td><td>检查每区间提升势近高斯性、有效样本数与误差；不能保证所有体系适用')
replace('至少 3-5 次完整结合-解离循环', '检查完整循环数、独立重复与置信区间；固定循环数不保证收敛')
replace('sigma0L 过大', 'sigma0P / sigma0D 过大')
replace('k_on 需要标准态体积修正', 'k_on 需要与事件定义一致的游离配体浓度；标准结合自由能另需标准态修正')
block_after('13.2 Python 主分析脚本', '''# 从仓库根目录运行；输入CSV只包含固定偏置的生产阶段：
# step,distance_A,boost_kcal_mol
# 10000,4.2,7.1
# 20000,4.4,6.8
# 上例只是格式演示，不能用于统计结论。
# boost_kcal_mol 必须是按步号对齐的全部提升势之和。
python -m analysis.ligamd_analysis production_aligned.csv --dt-ps 0.002 \\
    --temperature 300 --bins 50 --confirm-frames 3 --output ligamd_pmf.csv
# 如提供浓度：增加 --concentration-M 实际游离配体浓度
# 脚本只报告偏置轨迹统计，不输出真实koff或标准ΔG_bind。''')
replace('Python — ligamd_reweight.py', 'Bash — 调用仓库内完整分析模块')
replace('Pang Y., Miao Y. LiGaMD: An Efficient and Easy-to-Use Ligand Gaussian Accelerated Molecular Dynamics for Flexible Protein-Ligand Docking. <em>J. Chem. Theory Comput.</em>, 2022, 18(3): 1499-1512.', 'Miao Y., Bhattarai A., Wang J. Ligand Gaussian Accelerated Molecular Dynamics (LiGaMD): Characterization of Ligand Binding Thermodynamics and Kinetics. <em>J. Chem. Theory Comput.</em>, 2020, 16(9): 5526–5547. <a href="https://doi.org/10.1021/acs.jctc.0c00395">DOI</a>.')
replace('Wang J., Miao Y. Improved Gaussian Accelerated Molecular Dynamics for Accurate Ligand Binding Free Energy Calculation. <em>J. Chem. Theory Comput.</em>, 2023, 19(5): 1681-1693.', 'GaMD/LiGaMD AMBER 实现、参数与日志格式：<a href="https://www.med.unc.edu/pharm/miaolab/wp-content/uploads/sites/1385/2023/09/GaMD_Amber-manual.pdf">开发者说明</a>（运行前与本地版本核对）。')
# SMD path and input consistency
replace('npath = 5, path=10,9,8,7,6', 'npath = 5, path=6,7,8,9,10')
replace('<code>harm=800.0</code>', '<code>harm=10.0</code>')
replace('<code>cv_min=2.0, cv_max=40.0</code> — 拉伸距离范围 (Å)', '<code>cv_min=2.0, cv_max=40.0</code> — CV 有效边界 (Å)；目标路径为 6→10 Å，实际起点需匹配平衡结构')
replace("cv_file = 'cv.in'", "cv_file = 'cv.in'")
replace('imin=0, irest=0, ntx=1,\n   ntt=3, gamma_ln=2.0, temp0=300,', 'imin=0, irest=1, ntx=5,\n   ntt=3, gamma_ln=2.0, temp0=300,')
replace('ntp=1, ntc=2, ntf=2, cut=10.0, iwrap=1,', 'ntb=2, ntp=1, ntc=2, ntf=2, cut=10.0, iwrap=0, ioutfm=1,')
replace('grep "SMD" smd.out &gt; smd_force.dat', '# AMBER 的本例由 &smd 输出 smd.txt。按当前版本表头解析实际CV、目标中心、力与功。\n# NAMD 的 SMD 日志格式不适用于本例；不要跨软件使用固定列号。')
replace('累计功是力对位移的积分：', '用于 Jarzynski 的功是对外部控制参数 λ 的功。本例 λ 是移动谐振中心，不是瞬时实际距离 ξ；先按日志和偏置势定义核对共轭力的符号：')
replace("$$W(x) = \\int_0^x F(x')\\, dx'$$", r'$$W=\int_0^t\frac{\partial U(\xi,\lambda)}{\partial\lambda}\dot\lambda\,dt,\quad U=\frac{k}{2}(\xi-\lambda)^2$$')
block_after('Python — 计算累计功', '''# 在解析本版本日志后提供同长度数组：lambda_center（Å）与
# force_on_control = ∂U/∂λ（kcal/mol/Å）。若日志给的是粒子受力，先核对符号。
# AMBER 的 harm 系数是否包含1/2也必须按实际偏置定义换算。
from scipy.integrate import cumulative_trapezoid
work = cumulative_trapezoid(force_on_control, lambda_center, initial=0)
# 用相同拉伸协议、独立平衡初态重复采样；不要将不同终态协议混合平均。''')
replace('3.2 二阶累积量展开（更稳定）', '3.2 二阶累积量近似（需检验功分布接近高斯）')
replace('结合自由能估算:', '同一协议端态的自由能差近似（尚非标准结合自由能）:')
replace('<tr><td>精确自由能</td><td>20-50 条 + 不同拉伸速率</td></tr>', '<tr><td>定量结果</td><td>逐步增加独立轨迹，检查低功尾部、分块/重复不确定度和速率敏感性；固定条数不保证精度</td></tr>')
subsection('smd-pmf','smd-interaction', '''    <div class="subsection">
      <h3 class="subsection-title" id="smd-pmf">6. 平均力势（PMF）分析</h3>
      <p>SMD 距离直方图属于时间依赖偏置下的非平衡分布，不能直接取 −kBT ln P 当作平衡 PMF。SMD 可提供路径和伞形采样窗口初态；各窗口需要单独平衡和充分采样，再以 WHAM/MBAR 去偏置并检查重叠与误差。</p>
      <p>若采用非平衡方法，需使用相同协议下的独立平衡初态和正确的外部参数功，采用 <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC31107/">Hummer–Szabo 重构</a>等适用方法。Jarzynski 端态自由能差、无偏坐标 PMF 与标准结合自由能是不同对象；后者需要状态积分及几何、约束和标准态修正。</p>
    </div>''')
replace('力曲线的峰值对应主要的能垒', '力峰可提示该拉伸协议下的机械阻力，不能直接等同平衡自由能垒或动力学过渡态')
replace('结合 PMF 的局部极大值定位过渡态', '无偏 PMF 极大值仅给出候选区域；动力学过渡态需进一步用 committor 等分析验证')
replace('Jarzynski 等式 → 结合自由能', '正确外部参数功 + 同一协议独立重复 → Jarzynski 端态自由能差')
replace('SMD 估算的自由能通常比实验值偏高，适合相对比较而非绝对值', '机械功含耗散；经充分收敛和适当修正才能与实验热力学量比较，不能默认系统性偏高或适合相对排序')
# Don't call candidate high-potential-energy frames kinetic transition states.
replace('9.2 过渡态结构提取', '9.2 中间区域候选结构提取')
replace('识别过渡态区域的高能构象', '选择中间距离区间的高势能候选构象；不是动力学过渡态判定')
replace('n_ts = min(10, len(ts_energy))\n    top_indices', 'n_ts = min(10, len(ts_energy))\n    if n_ts == 0:\n        return np.array([], dtype=int)\n    top_indices')
# Add common input title lines where a complete AMBER namelist previously lacked a title.
s = s.replace('<pre> &amp;cntrl', '<pre>MD example (adapt to the final topology)\n &amp;cntrl')
p.write_text(s, encoding='utf-8')
# Keep actual input files aligned with the rendered examples.
for filename, heading in [('smd/md_smd.in','md_smd.in — SMD 输入文件'),('smd/cv.in','cv.in — 质心距离限制文件'),('LiGaMD/job1.in','job1.in — conventional MD + GaMD Equilibration'),('LiGaMD/job2.in','job2.in — GaMD Production')]:
    pos=s.index(heading)
    match=re.search(r'<pre>(.*?)</pre>',s[pos:],re.S)
    text=html.unescape(match.group(1)).strip()+'\n'
    if filename.endswith('job2.in'):
        text=text.replace('irest=0,','irest=1,').replace('ntx=1,','ntx=5,')
        a=s.index('<pre>',pos)+5; b=s.index('</pre>',a)
        s=s[:a]+html.escape(text,quote=False)+s[b:]
    Path(filename).write_text(text,encoding='utf-8')
p.write_text(s,encoding='utf-8')
print('Core MD/LiGaMD/SMD corrections applied; paired input files updated.')
