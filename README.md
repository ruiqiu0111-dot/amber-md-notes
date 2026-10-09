# 分子动力学模拟笔记

AMBER / GROMACS 的模拟输入、分析示例与方法说明。网页入口为 https://ruiqiu0111-dot.github.io/amber-md-notes/ 。

## 验证状态

已进行内容修正、静态一致性检查和 LiGaMD 分析算法回归测试。
**未对真实分子体系运行 AMBER、GROMACS、Gaussian、PLUMED 或 QM/MM 模拟。**
本仓库包含方法示例，不能把命令执行成功、RMSD 平台或固定模拟时长当作科学收敛证明。

## 阅读与预览

从项目根目录执行 `python -m http.server 8000`，访问 http://localhost:8000 。
网页使用远程 MathJax，需要联网才能显示公式。

## 软件与依赖

- 本次本地分析验证：Python 3.11、NumPy 2.4.6。`requirements-analysis.txt` 只包含独立 LiGaMD 模块所需依赖。
- 主模拟示例：AMBER/AmberTools；LiGaMD_Dual 使用支持该算法的 `pmemd.cuda`。
  实际 AMBER 版本、构建、GPU 和输入关键词须由运行者核对并记录；本仓库没有模拟版本验证记录。
- GROMACS 示例需核对所用发行版的 MDP、WHAM、BAR、Colvars 与 PLUMED 接口；不要将不同版本命令混用。
- 网页的可选片段还可能需要 SciPy、Matplotlib、MDTraj、PyMBAR 4.x、VMD、Multiwfn 或 Gaussian。
  它们不是独立 LiGaMD 分析模块的必需依赖。各片段所需上游数组或文件须先准备，不能全部单独复制执行。
- Gaussian、AMBER 等模拟软件的许可证和安装请按供应商说明处理；仓库不附带软件或许可证。

## 运行前必须确认的体系信息

1. PDB/配体来源、链、缺失残基、结构水、辅因子、金属、二硫键、质子化态、互变异构体、净电荷。
2. 力场/水模型/离子模型、配体参数与所选电荷方法。RESP 和 AM1-BCC 是替代路线。
3. 最终拓扑的原子/残基编号、坐标对齐、总电荷与几何冲突。常规网页示例假设蛋白 :1-237、SAM :238、目标配体 :239；其他章节为不同体系示例，不得沿用这些编号。
4. 模拟步长、轨迹输出间隔、温压耦合、种子、平衡判断、重复数和生产阶段。记录实际输入与输出版本。
5. LiGaMD 的 atom_l 是单个配体内部从1开始的序号，不是完整体系的配体原子编号。

## 独立 LiGaMD 分析

```bash
python -m pip install -r requirements-analysis.txt
python -m unittest discover -s tests -v
python -m analysis.ligamd_analysis production_aligned.csv --dt-ps 0.002 --bins 50 --confirm-frames 3
```

`production_aligned.csv` 是运行者按本地日志表头整理的**固定偏置生产阶段**数据：

```csv
step,distance_A,boost_kcal_mol
10000,4.2,7.1
20000,4.4,6.8
```

两行仅展示格式，不是可用于自由能计算的演示数据。必须使用真实充分采样数据。

- step：MD 积分步号；不是 CPPTRAJ 输出帧号。跨续跑文件需拼接成递增步号。
- distance_A：经合适 PBC 处理后，单个配体与口袋的距离（Å）。多个配体分别追踪，不能取全部配体的共同质心。
- boost_kcal_mol：全部提升势之和（kcal/mol），按 MD 步号与距离严格对齐。不要假定原始日志的第三列或某个固定列是偏置。
- `--dt-ps` 为积分步长；脚本从步号差推导保存帧间隔。不允许非均匀间隔或长度错位。
- 输入已去除平衡阶段；不能把更新偏置参数的平衡帧混入固定偏置重加权。

输出 `ligamd_pmf.csv` 使用每区间二阶累积量近似；低样本区间为 NaN。
该坐标密度 PMF 未进行径向 Jacobian、约束或标准态修正。
脚本只报告**偏置轨迹表观事件速率**，不给出真实动力学或 Kd。
`--concentration-M` 可提供与事件定义相符的游离配体浓度，用于表观结合速率的浓度单位换算。
真实速率需要另行验证的动力学重加权，标准结合自由能需要状态积分及适当修正。

## 收敛与复现

检查区间覆盖、窗口重叠、条件提升势的近高斯性、时间相关性、有效样本数、分块和独立重复结果。
报告不确定度；固定帧数、固定循环次数和固定模拟时长均不保证收敛。
公开示例结构和轨迹前确认来源和再分发权限；大轨迹可使用 Git LFS 或外部数据仓库。

## 方法来源

- [LiGaMD 原论文](https://doi.org/10.1021/acs.jctc.0c00395)
- [GaMD / LiGaMD AMBER 开发者说明](https://www.med.unc.edu/pharm/miaolab/wp-content/uploads/sites/1385/2023/09/GaMD_Amber-manual.pdf)
- [Hummer–Szabo 非平衡 PMF 重构](https://doi.org/10.1073/pnas.071034098)
- [GROMACS 文档](https://manual.gromacs.org/)

本仓库暂未指定再分发许可证；发布前由作者选择适合自己内容与引用材料的许可证。
