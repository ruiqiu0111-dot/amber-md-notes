#!/usr/bin/env python3
"""检查 SAM.chg 中电荷值的格式"""

chg_lines = open('SAM.chg', 'r').readlines()
print(f"SAM.chg 共 {len(chg_lines)} 行")

charge_lengths = set()
for line in chg_lines:
    parts = line.strip().split()
    charge = parts[-1]
    charge_lengths.add(len(charge))
    
print(f"电荷值长度分布: {charge_lengths}")

# 也检查 mol2 中原电荷值长度
mol2 = open('SAM_ante.mol2', 'r').readlines()
in_atom = False
mol2_charges = []
for line in mol2:
    if '@<TRIPOS>ATOM' in line:
        in_atom = True
        continue
    if in_atom:
        if line.strip().startswith('@<TRIPOS>'):
            break
        if line.strip():
            parts = line.strip().split()
            mol2_charges.append(parts[-1])

mol2_charge_lengths = set(len(c) for c in mol2_charges)
print(f"mol2 电荷值长度分布: {mol2_charge_lengths}")

# 验证两个文件的电荷数量是否一致
print(f"mol2 原子数: {len(mol2_charges)}")
print(f"chg 行数: {len(chg_lines)}")
