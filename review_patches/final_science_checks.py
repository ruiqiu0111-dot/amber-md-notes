from pathlib import Path
import html
p=Path('index.html'); s=p.read_text(encoding='utf-8')
def block_after(label,text):
    global s
    a=s.index('<pre>',s.index(label))+5; b=s.index('</pre>',a)
    s=s[:a]+html.escape(text,quote=False)+s[b:]
block_after('Python — 酶催化效应', '''import numpy as np
# 仅为数值示例；两者必须是相同温度、可比较参考态/标准态下的活化自由能。
# 不能把溶液相单点势能垒直接与酶中QM/MM自由能垒比较。
enzyme_barrier = 18.5    # kcal/mol, illustrative activation free energy
solution_barrier = 25.3  # kcal/mol, illustrative activation free energy
T = 300.0
R = 0.00198720425864083  # kcal mol^-1 K^-1
barrier_reduction = solution_barrier - enzyme_barrier
# Eyring比较假定相同前因子/传输系数；真实速率还需检验这些假设。
rate_ratio = np.exp(barrier_reduction / (R * T))
print(f"活化自由能降低: {barrier_reduction:.1f} kcal/mol")
print(f"相同前因子假设下的速率比: {rate_ratio:.2e}")
# 在300K，1.37 kcal/mol约对应10倍速率，不是exp(ΔΔG/1.36)。''')
block_after('Python — 分块收敛分析', '''PMF 分块检查流程（方法步骤，不是可直接执行的 Python）：
1. 剔除各窗口平衡段，并估算目标可观测量的自相关时间。
2. 每个时间块都包含全部窗口的对应生产片段。
3. 对每个完整块重新运行 WHAM/MBAR，重建整条 PMF，统一自由能零点。
4. 在相同反应物盆地与候选势垒定义下计算每块的自由能差，比较块长与独立重复结果。
5. 检查区间覆盖、窗口重叠和稀疏区间；不足时延长采样，不能用有限伪概率补齐。
反应坐标均值的标准差不是 PMF 的统计误差。块数很少或块长不足时不能作可靠误差判断。''')
s=s.replace('Python — 分块收敛分析','text — PMF 分块收敛分析')
s=s.replace('METAD ARG=d SIGMA=0.05 HEIGHT=1.2 BIASFACTOR=10 PACE=500 FILE=HILLS','metad: METAD ARG=d SIGMA=0.05 HEIGHT=1.2 BIASFACTOR=10 TEMP=300 PACE=500 FILE=HILLS')
block_after('bash — PLUMED 安装与集成', '''# 复用已验证且支持PLUMED的GROMACS构建；集成/编译方式随版本变化。
# 本仓库不提供跨版本通用patch命令。
gmx mdrun -h  # 确认包含 -plumed 选项
plumed info --version
# 保存GROMACS/PLUMED具体版本、构建方式与运行参数。
# 支持接口的构建通常以命令行启用：
gmx mdrun -deffnm metad -plumed plumed.dat
# 官方示例：https://www.plumed.org/doc-v2.9/user-doc/html/cambridge.html''')
block_after('metad.mdp — MetaDynamics 参数', '''; 参数片段：补入与既有平衡模拟一致的完整非键/约束/输出设置。
; PLUMED通过支持该接口的mdrun -plumed plumed.dat启动，而不是plumedfile MDP字段。
integrator = md
nsteps = 5000000
dt = 0.001
continuation = yes
gen_vel = no
tcoupl = V-rescale
tc-grps = System
tau_t = 0.1
ref_t = 300
; 示例使用NVT生产；先用匹配体系的NPT平衡密度，并通过checkpoint延续速度。
pcoupl = no
; 300K须与PLUMED METAD TEMP一致；上述5ns不能保证FES收敛。''')
s=s.replace('distance d_CS :1201 :1205','distance d_CS @1201 @1205').replace('distance d_CO :1201 :1302','distance d_CO @1201 @1302').replace('angle a_OCS :1302 :1201 :1205','angle a_OCS @1302 @1201 @1205')
s=s.replace('hbond out ts_hbond.dat :1-300 :SAM,PHB dist 3.0 angle 120 series','hbond ReactiveHB (:1-300|:SAM,PHB) out ts_hbond.dat dist 3.0 angle 120 series')
s=s.replace('solvent :WAT out watershell.dat :1201,1302 4.0 6.0','watershell :SAM,PHB out watershell.dat lower 4.0 upper 6.0\n# mask与距离阈值仅为示例，核对所用cpptraj版本。')
p.write_text(s,encoding='utf-8')
print('Corrected Eyring scaling, PMF uncertainty interpretation and PLUMED configuration.')
