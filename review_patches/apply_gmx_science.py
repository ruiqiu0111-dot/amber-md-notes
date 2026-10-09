from pathlib import Path
import json
p=Path('index.html'); s=p.read_text(encoding='utf-8')
changes=json.loads(Path('review_patches/gromacs_science.json').read_text(encoding='utf-8-sig'))
for i,x in enumerate(changes):
    old=x['old'].replace('\r\n','\n').replace('\r','')
    new=x['new'].replace('\r\r\n','\n').replace('\r\n','\n').replace('\r','')
    if s.count(old)!=1: raise ValueError(f'gromacs_science[{i}]: {s.count(old)} matches')
    s=s.replace(old,new)
# dim is a Y/N toggle for x,y,z, not a literal axis name.
s=s.replace('pull-coord1-dim = X N N','pull-coord1-dim = Y N N')
s=s.replace('pull-coord1-dim      = X N N','pull-coord1-dim      = Y N N')
s=s.replace('pull-coord1-dim      = Y N N           ; 只取 y 轴分量；若目标是三维 COM 距离，改为 Y Y Y','pull-coord1-dim      = Y N N           ; x,y,z维度开关：只取x分量；三维COM距离使用 Y Y Y')
s=s.replace('FORCE_FIELD" -water "$WATER_MODEL" -ignh','FORCE_FIELD" -water "$WATER_MODEL" -ignh -p protein.top')
# LIE must use all ligand-environment interactions in both ensembles.
s=s.replace('例如 bound.mdp: energygrps = Protein LIG；free.mdp: energygrps = LIG SOL','例如 bound.mdp: energygrps = LIG ENV；free.mdp: energygrps = LIG SOL')
s=s.replace('请用实际拓扑中的能量组名称，并确认当前 GROMACS 构建和运行设备确实写出了这些项。','ENV 需在 index.ndx 中包含结合态中除所研究配体之外的环境（蛋白、溶剂、离子/辅因子等），不能只取蛋白而漏掉结合态溶剂贡献。请核对两个系综能量定义、长程静电处理与所选 LIE 参数化一致，并确认运行设备支持所需能量分组输出；短程组间项不等于全部 PME 静电能。')
s=s.replace('Protein-LIG 组间','LIG-ENV 组间').replace('Protein-LIG, bound ensemble','LIG-ENV, bound ensemble')
s=s.replace('u_kn and temperature_K must be finite and valid','u_kn and temperature_K must be finite and valid')
s=s.replace('not np.all(np.isfinite(u_kn)) or temperature_K &lt;= 0','not np.all(np.isfinite(u_kn)) or not np.isfinite(temperature_K) or temperature_K &lt;= 0')
s=s.replace('比 FEP/TI 更快但精度略低。','通常成本较低，但其经验参数的适用性与误差需针对体系检验，不能给出普遍的精度排序。')
# Replace remaining cross-method star ranking with scientific applicability criteria.
a=s.index('      <table>',s.index('id="gmx-bfe"')); b=s.index('      </table>',a)+len('      </table>')
s=s[:a]+'''      <table>
        <tr><th>方法</th><th>主要适用条件与限制</th></tr>
        <tr><td>MM/PBSA、MM/GBSA</td><td>端点近似；检查采样、溶剂模型、熵与受体/配体分割，需针对目标任务验证</td></tr>
        <tr><td>LIE</td><td>结合态和游离态配体-环境能量差；参数需匹配体系与能量定义</td></tr>
        <tr><td>TI、FEP/BAR、MBAR</td><td>适当的热力学循环、状态定义、采样和态间重叠；绝对结合自由能还需约束及标准态修正</td></tr>
        <tr><td>伞形采样/WHAM</td><td>有效反应坐标、窗口平衡/重叠和去偏置；结合热力学需要状态积分及几何/标准态处理</td></tr>
      </table>''' + s[b:]
s=s.replace('对于大规模虚拟筛选，推荐 <strong>MM/PBSA</strong> 或 <strong>LIE</strong>。对于关键化合物的精确结合能，使用 <strong>FEP/BAR</strong> 或 <strong>TI</strong>。若需要了解解离路径和过渡态，选择 <strong>伞形采样</strong>。','方法选择应由目标可观测量、体系、计算预算、采样可行性及基准误差决定。计算形式严格不保证有限模拟精确；反应坐标 PMF 也不自动给出动力学过渡态。')
p.write_text(s,encoding='utf-8')
print('Applied 16 GROMACS scientific corrections; independently reviewed dimensions and LIE environment.')
