#!/usr/bin/env python3
"""检查mol2和chg电荷值长度分布是否一致"""

mol2 = open('SAM_ante.mol2', 'r').readlines()
chg_lines = open('SAM.chg', 'r').readlines()

# 提取mol2电荷值
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

# 提取chg电荷值
chg_charges = []
for line in chg_lines:
    parts = line.strip().split()
    chg_charges.append(parts[-1])

print("逐行对比电荷值长度:")
for i, (m, c) in enumerate(zip(mol2_charges, chg_charges)):
    same_len = len(m) == len(c)
    if not same_len:
        print(f"  行{i+1}: mol2={m} (len={len(m)}), chg={c} (len={len(c)}) -- 长度不同!")
    
print(f"\n总长度不同的行数: {sum(1 for m,c in zip(mol2_charges, chg_charges) if len(m)!=len(c))}")
