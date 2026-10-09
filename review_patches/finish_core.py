from pathlib import Path
import re,html
p=Path('index.html'); s=p.read_text(encoding='utf-8')
def block_after(label,text):
    global s
    a=s.index('<pre>',s.index(label))+5; b=s.index('</pre>',a)
    s=s[:a]+html.escape(text,quote=False)+s[b:]
block_after('tleap — tleap_multi_T3Q.in', '''# 从项目根目录运行，使用真实对齐且已参数化的输入。
python LiGaMD/setup_multi_T3Q.py SeNMT.pdb SAM_ante.mol2 T3Q_ante.mol2 15.0,20.0,25.0 5
# 活性中心坐标和数量仅为格式示例，运行前按体系设置。
# 脚本复制参数化MOL2单元并translate，而非靠带猜测残基号的PDB恢复键级/电荷。
cat tleap_multi_T3Q.in
# 检查参数文件、坐标、力场、水模型、离子和分子数后：
tleap -f tleap_multi_T3Q.in
# 生成SeNMT_SAM_multiT3Q.parm7、.rst7和.pdb。按这些最终文件核对编号。''')
s=s.replace('tleap — tleap_multi_T3Q.in','Bash — 生成并核对 tleap_multi_T3Q.in')
block_after('cpptraj — check_distances.cpptraj', '''# 这是待填的检查模板，先从最终拓扑/PDB确认配体残基及参考原子。
parm SeNMT_SAM_multiT3Q.parm7
trajin SeNMT_SAM_multiT3Q.rst7
# 以下替换真实mask并取消注释：
# distance Ligand1Pocket :真实配体残基@真实原子 :真实口袋残基@真实原子 out distance.dat
# 检查所有配体的最近原子接触、PBC镜像和盒子边界，不能用单一COM距离证明无冲突。
run''')
s=s.replace('脚本还会生成 cpptraj 输入文件，用于检查配体放置是否合理：','脚本还会生成需要填写实际 mask 的 cpptraj 检查模板；原子对接触、配体身份和 PBC 镜像需在最终拓扑/坐标上核验：')
s=s.replace('运行距离检查：<code>cpptraj -i check_distances.cpptraj</code>','填写最终拓扑对应的 mask 并启用距离命令后运行：<code>cpptraj -i check_distances.cpptraj</code>')
s=s.replace('0</code> — 自动添加 Na⁺/Cl⁻ 使体系电中性','0</code> — 依据净电荷添加反离子中和；不等于指定盐浓度，若需生理盐浓度应另行计算并检查离子数')
s=s.replace('分配 GAFF 力场原子类型','分配所选 GAFF/GAFF2 力场原子类型（本例为 GAFF2）')
s=s.replace('Python — 过渡态识别','Python — 中间区域候选构象筛选')
s=s.replace('# 使用 cpptraj 提取过渡态结构','# 筛选索引转为cpptraj的1-based帧号后提取候选构象；真正过渡态需独立验证')
s=s.replace('      <h3 class="subsection-title" id="smd-pmf">6. 平均力势（PMF）分析</h3>','      <h3 class="subsection-title" id="smd-pmf">6. 平均力势（PMF）分析</h3>')
# Remove fixed-stage timeline segments that incorrectly add preparation lengths twice.
a=s.index('      <!-- 时间轴示意图 -->',s.index('id="ligamd-run"'))
b=s.index('      <div class="code-block">',a)
s=s[:a]+'''      <div class="tip-box"><div class="label">阶段定义</div>
        <p>0→ntcmd 为常规阶段，前 ntcmdprep 步用于准备；ntcmd→ntcmd+nteb 为加偏置平衡，前 ntebprep 步用于准备。准备阶段包含在 ntcmd/nteb 内部。Job2 读取保存的偏置参数与带速度的 restart，只采集固定偏置生产阶段；需保留原版本实际输出的 GaMD restart 文件名，不能重新拟合偏置后假装连续动力学。</p>
      </div>
''' + s[b:]
s=s.replace('<button class="back-top"', '</div><!-- main content -->\n<button class="back-top"')
p.write_text(s,encoding='utf-8')
