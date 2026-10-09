#!/usr/bin/env python3
"""分析 SAM_ante.mol2 的列宽格式"""

mol2 = open('SAM_ante.mol2', 'r').readlines()

# 找到 @<TRIPOS>ATOM 后面的原子数据行
in_atom = False
atom_lines = []
for line in mol2:
    if '@<TRIPOS>ATOM' in line:
        in_atom = True
        continue
    if in_atom:
        if line.strip().startswith('@<TRIPOS>'):
            break
        if line.strip():
            atom_lines.append(line.rstrip('\n'))

print(f"找到 {len(atom_lines)} 个原子行")
print()

# 分析最后一列（电荷）的位置
# 找到每行最后一个token的位置
import re

charges = []
for line in atom_lines:
    # 找到所有非空白token
    tokens = re.findall(r'\S+', line)
    charge_token = tokens[-1]
    # 找到它在行中的起始位置
    idx = line.rfind(charge_token)
    charges.append((line, charge_token, idx, len(line)))
    
print("前5行原子数据：")
for line, charge, idx, length in charges[:5]:
    print(f"  长度={length}, 电荷起始={idx}, 电荷='{charge}'")
    print(f"  行: {repr(line)}")
    
print()
print("所有行的长度分布:", set(length for _, _, _, length in charges))
print("电荷起始位置分布:", set(idx for _, _, idx, _ in charges))
print("电荷值长度分布:", set(len(charge) for _, charge, _, _ in charges))

# 找出电荷字段的精确列范围
print()
for line, charge, idx, length in charges[:3]:
    prefix = line[:idx]
    print(f"前缀长度: {len(prefix)}, 前缀: {repr(prefix)}")
