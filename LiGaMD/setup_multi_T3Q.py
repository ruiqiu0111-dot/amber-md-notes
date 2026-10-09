#!/usr/bin/env python3
"""
setup_multi_T3Q.py
为 SeNMT + SAM + N×T3Q 体系随机放置多个T3Q配体

用法:
    python3 setup_multi_T3Q.py <SeNMT.pdb> <SAM_ante.mol2> <T3Q_ante.mol2> <pocket_center_x,y,z> [N_LIGANDS]

示例:
    python3 setup_multi_T3Q.py SeNMT.pdb SAM_ante.mol2 T3Q_ante.mol2 15.0,20.0,25.0 5

说明:
    - SAM 作为辅因子，固定在口袋中（坐标来自 SAM_ante.mol2，需已对齐到蛋白）
    - T3Q 作为被研究配体，随机放置 N 个到溶剂中
    - 自动生成 tleap.in 和 LiGaMD mdin 模板
"""

import numpy as np
import sys
import os

# ==================== 用户可调参数 ====================
BOX_BUFFER = 12.0               # 溶剂层厚度 (Å)，与 solvateoct 一致
MIN_LIG_LIG_DIST = 10.0         # 配体间最小原子-原子距离 (Å)
MIN_LIG_PRO_DIST = 5.0          # 配体-蛋白最小原子-原子距离 (Å)
MIN_LIG_SAM_DIST = 8.0          # T3Q 与 SAM 最小原子-原子距离 (Å)
POCKET_EXCLUDE_RADIUS = 18.0    # 口袋排除半径 (Å)，T3Q 初始不放这里
SEED = 42                       # 随机种子

# LiGaMD_Dual (igamd=11) 的示例阶段长度，单位为 MD steps。
# 这些是模板起点，不是对收敛或动力学精度的保证；应根据最终体系、
# GaMD 能量统计稳定性和独立重复模拟调整。ntcmd/nteb 应与 ntave 相容。
DT_PS = 0.002
NTCMD = 700_000
NTCMD_PREP = 280_000
NTEB = 27_300_000
NTEB_PREP = 280_000
NTAVE = 140_000
PRODUCTION_STEPS = 100_000_000  # 示例 200 ns；须按收敛情况调整
NSTLIM = NTCMD + NTEB + PRODUCTION_STEPS
# =====================================================

def leap_quote(path):
    """为 LEaP 输入中的文件路径加引号。"""
    return '"' + os.path.abspath(path).replace('\\', '/').replace('"', '\\"') + '"'

def verify_ligamd_template(mdin_file):
    """确认 AMBER namelist 和需人工核对的拓扑占位符都保留在模板中。"""
    with open(mdin_file, 'r') as f:
        text = f.read()

    required_markers = (
        "__FILL_T3Q_RESIDUE_MASK_FROM_FINAL_PRMTOP__",
        "__FILL_PROTEIN_ATOM_SERIAL_FROM_FINAL_PRMTOP__",
        "__FILL_T3Q_INTERNAL_ATOM_SERIAL_1_BASED__",
    )
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        raise RuntimeError(f"LiGaMD 模板缺少必填占位符: {', '.join(missing)}")
    if text.count('&cntrl') != 1 or '&pmd' in text:
        raise RuntimeError("LiGaMD 参数必须只写在一个 &cntrl namelist 中")
    if NTCMD % NTAVE != 0 or NTEB % NTAVE != 0:
        raise RuntimeError("ntcmd 和 nteb 必须按 GaMD 手册要求与 ntave 相容")
    if NTCMD_PREP > NTCMD or NTEB_PREP > NTEB:
        raise RuntimeError("ntcmdprep/ntebprep 不能大于对应阶段步数")
    if NSTLIM <= NTCMD + NTEB:
        raise RuntimeError("nstlim 必须大于 ntcmd + nteb，才能留出生产阶段")

def read_pdb_coords(pdb_file):
    """读取 PDB 中的 ATOM/HETATM 坐标"""
    coords = []
    atoms = []
    with open(pdb_file, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])
                atoms.append(line)
    return np.array(coords), atoms

def read_mol2(mol2_file):
    """读取 mol2 文件的 ATOM 段，返回坐标和原子信息"""
    coords = []
    atoms = []
    in_atom = False
    with open(mol2_file, 'r') as f:
        for line in f:
            if line.startswith('@<TRIPOS>ATOM'):
                in_atom = True
                continue
            if line.startswith('@<TRIPOS>BOND') or line.startswith('@<TRIPOS>SUBSTRUCTURE'):
                in_atom = False
                continue
            if in_atom and len(line.strip()) > 0:
                parts = line.strip().split()
                if len(parts) >= 6:
                    x = float(parts[2])
                    y = float(parts[3])
                    z = float(parts[4])
                    coords.append([x, y, z])
                    # 构造伪 PDB 格式的原子行，方便后续写入
                    atom_name = parts[1]
                    res_name = parts[7] if len(parts) > 7 else 'T3Q'
                    # 补齐到4字符的原子名
                    atom_name = atom_name[:4]
                    if len(atom_name) < 4:
                        atom_name = ' ' + atom_name if len(atom_name) == 3 else ' ' * (4 - len(atom_name)) + atom_name
                    # 构造 PDB 行
                    pdb_line = f"HETATM{len(atoms)+1:5d} {atom_name:4s} {res_name:3s}  {1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {parts[5]:2s}  \n"
                    atoms.append(pdb_line)
    return np.array(coords), atoms

def write_pdb(coords, atoms, outfile, resid=1):
    """写入 PDB，支持修改残基号"""
    with open(outfile, 'w') as f:
        for i, (coord, atom) in enumerate(zip(coords, atoms)):
            x, y, z = coord
            # 替换残基号（第22-26列）
            new_line = atom[:22] + f"{resid:4d}" + atom[26:30] + f"{x:8.3f}{y:8.3f}{z:8.3f}" + atom[54:]
            f.write(new_line)
        f.write("END\n")

def get_center_and_radius(coords):
    """获取几何中心和最大半径"""
    center = np.mean(coords, axis=0)
    dists = np.linalg.norm(coords - center, axis=1)
    return center, np.max(dists)

def minimum_atom_distance(coords_a, coords_b):
    """计算两组原子坐标间的最小距离，避免只用分子中心漏掉原子重叠。"""
    if len(coords_a) == 0 or len(coords_b) == 0:
        return float("inf")
    delta = coords_a[:, np.newaxis, :] - coords_b[np.newaxis, :, :]
    return float(np.sqrt(np.min(np.sum(delta * delta, axis=2))))

def generate_random_position(box_center, box_size, 
                             pocket_center, pocket_radius,
                             ligand_coords, ligand_center,
                             existing_ligands, prot_coords, sam_coords,
                             min_lig_lig, min_lig_pro, min_lig_sam,
                             max_attempts=20000):
    """
    在盒子内随机生成配体位置，满足多重约束
    """
    half_box = box_size / 2.0

    for attempt in range(max_attempts):
        pos = box_center + (np.random.rand(3) - 0.5) * box_size

        # 1. 不在口袋排除区内
        if pocket_center is not None:
            d_pocket = np.linalg.norm(pos - pocket_center)
            if d_pocket < pocket_radius:
                continue

        candidate_coords = ligand_coords - ligand_center + pos

        # 2. 不与蛋白原子太近
        if prot_coords is not None and len(prot_coords) > 0:
            d_pro = minimum_atom_distance(candidate_coords, prot_coords)
            if d_pro < min_lig_pro:
                continue

        # 3. 不与 SAM 原子太近
        if sam_coords is not None and len(sam_coords) > 0:
            d_sam = minimum_atom_distance(candidate_coords, sam_coords)
            if d_sam < min_lig_sam:
                continue

        # 4. 不与已有 T3Q 原子重叠
        if existing_ligands:
            d_ligs = [minimum_atom_distance(candidate_coords, placed_coords)
                      for placed_coords in existing_ligands]
            if min(d_ligs) < min_lig_lig:
                continue

        return pos

    raise RuntimeError(f"无法在 {max_attempts} 次尝试内找到合适位置。请尝试：\n"
                       f"  - 减小 N_LIGANDS\n"
                       f"  - 增大 BOX_BUFFER\n"
                       f"  - 减小 POCKET_EXCLUDE_RADIUS\n"
                       f"  - 减小 MIN_LIG_LIG_DIST")

def main():
    if len(sys.argv) < 5:
        print("用法: python3 setup_multi_T3Q.py <SeNMT.pdb> <SAM_ante.mol2> <T3Q_ante.mol2> <pocket_center_x,y,z> [N_LIGANDS]")
        print("示例: python3 setup_multi_T3Q.py SeNMT.pdb SAM_ante.mol2 T3Q_ante.mol2 15.0,20.0,25.0 5")
        print()
        print("说明:")
        print("  - SAM_ante.mol2 的坐标必须已与 SeNMT.pdb 对齐（辅因子在口袋中）")
        print("  - T3Q_ante.mol2 会被复制 N 份，随机散布在溶剂中")
        print("  - pocket_center 用于排除初始放置区域，让 T3Q 从远处扩散进入")
        sys.exit(1)

    prot_file = sys.argv[1]
    sam_file = sys.argv[2]
    lig_file = sys.argv[3]
    pocket_center = np.array([float(x) for x in sys.argv[4].split(',')])
    N_LIGANDS = int(sys.argv[5]) if len(sys.argv) > 5 else 5

    if pocket_center.shape != (3,):
        raise ValueError("pocket_center 必须是三个逗号分隔的坐标，例如 15.0,20.0,25.0")
    if N_LIGANDS < 1:
        raise ValueError("N_LIGANDS 必须至少为 1")

    np.random.seed(SEED)

    print("=" * 60)
    print("SeNMT + SAM + N×T3Q 多配体体系构建")
    print("=" * 60)
    print()

    # 读取结构
    print(f"[1/5] 读取蛋白: {prot_file}")
    prot_coords, _ = read_pdb_coords(prot_file)

    print(f"[2/5] 读取 SAM (辅因子): {sam_file}")
    sam_coords, sam_atoms = read_mol2(sam_file)

    print(f"[3/5] 读取 T3Q (被研究配体): {lig_file}")
    lig_coords, lig_atoms = read_mol2(lig_file)

    if len(prot_coords) == 0 or len(sam_coords) == 0 or len(lig_coords) == 0:
        raise ValueError("蛋白 PDB、SAM MOL2 和 T3Q MOL2 都必须至少含有一个原子")

    # 计算盒子参数
    prot_center, prot_radius = get_center_and_radius(prot_coords)
    box_size = 2 * (prot_radius + BOX_BUFFER)
    box_center = prot_center

    print()
    print("体系信息:")
    print(f"  蛋白原子数:     {len(prot_coords)}")
    print(f"  SAM 原子数:     {len(sam_coords)}")
    print(f"  T3Q 原子数:     {len(lig_coords)}")
    print(f"  蛋白中心:       [{prot_center[0]:.2f}, {prot_center[1]:.2f}, {prot_center[2]:.2f}]")
    print(f"  蛋白半径:       {prot_radius:.2f} Å")
    print(f"  溶剂盒子大小:   {box_size:.2f} Å (buffer={BOX_BUFFER} Å)")
    print(f"  口袋中心:       [{pocket_center[0]:.2f}, {pocket_center[1]:.2f}, {pocket_center[2]:.2f}]")
    print(f"  口袋排除半径:   {POCKET_EXCLUDE_RADIUS} Å")
    print(f"  T3Q 数量:       {N_LIGANDS}")
    print()

    # 随机放置 T3Q
    print(f"[4/5] 随机放置 {N_LIGANDS} 个 T3Q...")
    ligand_positions = []
    placed_ligand_coords = []
    lig_com = np.mean(lig_coords, axis=0)

    for i in range(N_LIGANDS):
        pos = generate_random_position(
            box_center=box_center,
            box_size=box_size,
            pocket_center=pocket_center,
            pocket_radius=POCKET_EXCLUDE_RADIUS,
            ligand_coords=lig_coords,
            ligand_center=lig_com,
            existing_ligands=placed_ligand_coords,
            prot_coords=prot_coords,
            sam_coords=sam_coords,
            min_lig_lig=MIN_LIG_LIG_DIST,
            min_lig_pro=MIN_LIG_PRO_DIST,
            min_lig_sam=MIN_LIG_SAM_DIST
        )

        # 平移配体到目标位置
        new_coords = lig_coords - lig_com + pos
        ligand_positions.append(pos)
        placed_ligand_coords.append(new_coords)

        # 该 PDB 仅用于单个配体构象的目视检查；最终 residue 编号由 LEaP
        # 根据完整体系生成，必须在最终 prmtop/PDB 中核对，不能在此猜测。
        outfile = f"T3Q_pos{i+1}.pdb"
        write_pdb(new_coords, lig_atoms, outfile, resid=1)

        d_to_pocket = np.linalg.norm(pos - pocket_center)
        d_to_sam = minimum_atom_distance(new_coords, sam_coords)
        print(f"  T3Q {i+1:2d} (单体检查 PDB 使用残基号 1): 到口袋 {d_to_pocket:5.1f} Å | 到 SAM {d_to_sam:5.1f} Å | 位置 [{pos[0]:7.2f}, {pos[1]:7.2f}, {pos[2]:7.2f}]")

    print()

    # 生成 tleap.in
    print("[5/5] 生成 tleap 输入文件...")
    tleap_file = "tleap_multi_T3Q.in"

    with open(tleap_file, 'w') as f:
        f.write("# ============================================================\n")
        f.write("# tleap_multi_T3Q.in\n")
        f.write("# SeNMT + SAM (辅因子) + N×T3Q (随机溶剂配体)\n")
        f.write("# ============================================================\n\n")

        f.write("# --- 力场 ---\n")
        f.write("source leaprc.protein.ff19SB\n")
        f.write("source leaprc.gaff2\n")
        f.write("source leaprc.water.tip3p\n\n")

        f.write("# --- 配体参数 ---\n")
        f.write("loadamberparams SAM.frcmod\n")
        f.write("loadamberparams T3Q_ante.frcmod\n\n")

        f.write("# --- 加载分子 ---\n")
        f.write("# 蛋白\n")
        f.write(f"rec = loadpdb {leap_quote(prot_file)}\n\n")

        f.write("# SAM 辅因子（已对齐到口袋）\n")
        f.write(f"SAM = loadmol2 {leap_quote(sam_file)}\n\n")

        f.write("# T3Q 配体模板\n")
        f.write(f"T3Q = loadmol2 {leap_quote(lig_file)}\n\n")

        f.write("# --- 合并体系 ---\n")
        for i, pos in enumerate(ligand_positions):
            shift = pos - lig_com
            f.write(f"T3Q_pos{i+1} = copy T3Q\n")
            f.write(f"translate T3Q_pos{i+1} {{ {shift[0]:.3f} {shift[1]:.3f} {shift[2]:.3f} }}\n")
        f.write("\ncomplex = combine {rec SAM")
        for i in range(N_LIGANDS):
            f.write(f" T3Q_pos{i+1}")
        f.write("}\n\n")

        f.write("# --- 溶剂化 (八面体盒子) ---\n")
        f.write(f"solvateoct complex TIP3PBOX {BOX_BUFFER}\n\n")

        f.write("# --- 中和 ---\n")
        f.write("addions complex Na+ 0\n")
        f.write("addions complex Cl- 0\n\n")

        f.write("# --- 保存 ---\n")
        f.write("saveamberparm complex SeNMT_SAM_multiT3Q.parm7 SeNMT_SAM_multiT3Q.rst7\n")
        f.write("savepdb complex SeNMT_SAM_multiT3Q.pdb\n\n")

        f.write("quit\n")

    print(f"  生成: {tleap_file}")

    # 生成 LiGaMD mdin 模板
    mdin_file = "ligamd_multi_T3Q.in"
    with open(mdin_file, 'w') as f:
        f.write("LiGaMD_Dual (igamd=11) multi-T3Q input template; fill and verify markers before use.\n")
        f.write("&cntrl\n")
        f.write("  ! LiGaMD_Dual boosts ligand nonbonded and remaining-system potential energies.\n")
        f.write("  ! Verify the T3Q residue mask and atom indices against the final parm7/PDB.\n")
        f.write("  ! nlig is the T3Q molecule count; ibblig=1 enables selective bound-ligand boosting.\n")
        f.write("  ! atom_p is a protein atom serial, not the protein atom count.\n")
        f.write("  ! atom_l is a 1-based atom serial within one T3Q, not its atom count.\n")
        f.write("  ! dblig=3.7 A is an example contact cutoff; check it for the selected anchors.\n")
        f.write("  ! Replace every __FILL_...__ marker before running this input.\n")
        f.write("  ! LiGaMD accelerates sampling; this template does not directly yield physical kon/koff.\n")
        f.write("  ! Kinetics require independent replicas, convergence assessment, and validated kinetic reweighting.\n")
        f.write("  ! GaMD manual: https://www.med.unc.edu/pharm/miaolab/wp-content/uploads/sites/1385/2023/09/GaMD_Amber-manual.pdf\n")
        f.write("  imin=0, irest=1, ntx=5,          ! 从带速度的平衡 restart 继续\n")
        f.write(f"  nstlim={NSTLIM}, dt={DT_PS:.3f},\n")
        f.write("  ntt=3, temp0=300.0, gamma_ln=2.0,\n")
        f.write("  ntb=2, ntp=1, taup=2.0,\n")
        f.write("  pres0=1.0,\n")
        f.write("  ntc=2, ntf=1,                    ! LiGaMD soft-core/TI 示例设置；ntf=1 本身不启用软核\n")
        f.write("  cut=10.0,\n")
        f.write("  igamd=11, irest_gamd=0,\n")
        f.write(f"  ntcmd={NTCMD}, ntcmdprep={NTCMD_PREP},\n")
        f.write(f"  nteb={NTEB}, ntebprep={NTEB_PREP}, ntave={NTAVE},\n")
        f.write("  sigma0P=4.0, sigma0D=6.0, iEP=2, iED=1,\n")
        f.write("  icfe=1, ifsc=1,\n")
        f.write("  gti_cpu_output=0, gti_add_sc=1,\n")
        f.write("  timask1=':__FILL_T3Q_RESIDUE_MASK_FROM_FINAL_PRMTOP__',\n")
        f.write("  scmask1=':__FILL_T3Q_RESIDUE_MASK_FROM_FINAL_PRMTOP__',\n")
        f.write("  timask2='', scmask2='',\n")
        f.write("  ioutfm=1,\n")
        f.write("  ntwr=50000, ntwx=50000, ntpr=5000,\n")
        f.write("  ntxo=2,                         ! restart 文件使用 NetCDF\n")
        f.write("  ! --- 多配体参数 ---\n")
        f.write("  ibblig=1,                        ! 启用动态配体检测\n")
        f.write(f"  nlig={N_LIGANDS},                ! T3Q 总数\n")
        f.write("  atom_p=__FILL_PROTEIN_ATOM_SERIAL_FROM_FINAL_PRMTOP__,\n")
        f.write("  atom_l=__FILL_T3Q_INTERNAL_ATOM_SERIAL_1_BASED__,\n")
        f.write("  dblig=3.7,                       ! 结合判定距离 (Å)\n")
        f.write(f"  ! nstlim = ntcmd + nteb + {PRODUCTION_STEPS} production steps ({PRODUCTION_STEPS * DT_PS / 1000:.1f} ns).\n")
        f.write("  ! LiGaMD manual example values below are starting points, not convergence criteria.\n")
        f.write("  ! ntave should be reviewed after inspecting final total atom count; manual suggests ~4 x natom.\n")
        f.write("  ! Ensure ntcmd and nteb satisfy the ntave requirements in the manual.\n")
        f.write("/\n")

    verify_ligamd_template(mdin_file)

    print(f"  生成: {mdin_file}")
    print("  模板检查通过：&cntrl 与必填占位符齐全；填入并核对最终 prmtop 编号前不要运行。")

    # 生成 cpptraj 检查脚本
    check_file = "check_distances.cpptraj"
    with open(check_file, 'w') as f:
        f.write("parm SeNMT_SAM_multiT3Q.parm7\n")
        f.write("trajin SeNMT_SAM_multiT3Q.rst7\n\n")
        f.write("# 仅为待填检查模板：先从最终 parm7/PDB 确认 residue mask 和实际原子名。\n")
        f.write("# 不要使用生成脚本臆测的 residue/atom 编号。\n")
        f.write("# distance T3Q1_to_pocket :<T3Q_RESIDUE>@<T3Q_ATOM> :<PROTEIN_RESIDUE>@<PROTEIN_ATOM> out check_dist.dat\n")
        f.write("# distance T3Q1_T3Q2 :<T3Q1_RESIDUE>@<T3Q_ATOM> :<T3Q2_RESIDUE>@<T3Q_ATOM> out check_liglig.dat\n")
        f.write("# 填好并取消注释所需命令后再添加 run。\n")

    print(f"  生成: {check_file}")

    print()
    print("=" * 60)
    print("完成！下一步操作:")
    print("=" * 60)
    print()
    print("1. 检查 SAM 坐标是否已对齐到蛋白:")
    print(f"   vmd {prot_file} {sam_file}")
    print("   # 确认 SAM 在口袋中，没有明显冲突")
    print()
    print("2. 运行 tleap 构建拓扑:")
    print("   tleap -f tleap_multi_T3Q.in")
    print()
    print("3. 检查初始结构:")
    print("   vmd SeNMT_SAM_multiT3Q.pdb")
    print("   # 确认所有 T3Q 分散在溶剂中，没有重叠")
    print()
    print("4. 能量最小化 + 升温 + 平衡 (标准流程)")
    print("   tleap 输出后先检查最终 parm7/PDB，并填写 ligamd_multi_T3Q.in 中所有 __FILL_...__ 占位符。")
    print("   atom_p/atom_l 不是原子总数；须按最终拓扑的原子顺序及所选锚点确认。")
    print()
    print("5. LiGaMD 生产模拟:")
    print("   pmemd.cuda -O -i ligamd_multi_T3Q.in -o ligamd.mdout \\")
    print("         -p SeNMT_SAM_multiT3Q.parm7 -c equil.rst7 \\")
    print("         -r ligamd.rst7 -x ligamd.nc")
    print()
    print("=" * 60)

if __name__ == '__main__':
    main()
