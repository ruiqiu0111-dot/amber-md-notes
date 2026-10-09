#!/usr/bin/env python3
"""验证替换后的 mol2 文件格式是否与原始文件一致"""

orig = open('SAM_ante.mol2', 'r').readlines()
new = open('SAM_ante_updated.mol2', 'r').readlines()

print(f"原始文件行数: {len(orig)}")
print(f"新文件行数: {len(new)}")

# 找到 ATOM 区块范围
orig_atom_start = None
orig_atom_end = None
for i, line in enumerate(orig):
    if line.strip() == '@<TRIPOS>ATOM':
        orig_atom_start = i
    if orig_atom_start is not None and line.strip().startswith('@<TRIPOS>') and i > orig_atom_start:
        orig_atom_end = i
        break

new_atom_start = None
new_atom_end = None
for i, line in enumerate(new):
    if line.strip() == '@<TRIPOS>ATOM':
        new_atom_start = i
    if new_atom_start is not None and line.strip().startswith('@<TRIPOS>') and i > new_atom_start:
        new_atom_end = i
        break

print(f"\n原始 ATOM 区块: 第 {orig_atom_start+1} 行到第 {orig_atom_end} 行")
print(f"新 ATOM 区块: 第 {new_atom_start+1} 行到第 {new_atom_end} 行")

# 逐行对比 ATOM 行
print("\n逐行对比 ATOM 行:")
all_ok = True
for i in range(orig_atom_start + 1, orig_atom_end):
    o_line = orig[i]
    n_line = new[i]
    
    # 检查行长度是否一致
    if len(o_line) != len(n_line):
        print(f"  行 {i+1}: 长度不一致! 原始={len(o_line)}, 新={len(n_line)}")
        all_ok = False
        continue
    
    # 找到电荷位置（最后一个token）
    # 比较最后一个token之前的部分是否完全一致
    o_stripped = o_line.rstrip('\n')
    n_stripped = n_line.rstrip('\n')
    
    # 找到最后一个token的起始位置
    def find_last_token_start(s):
        end = len(s)
        while end > 0 and s[end - 1].isspace():
            end -= 1
        start = end
        while start > 0 and not s[start - 1].isspace():
            start -= 1
        return start, end
    
    o_start, o_end = find_last_token_start(o_stripped)
    n_start, n_end = find_last_token_start(n_stripped)
    
    prefix_ok = o_stripped[:o_start] == n_stripped[:n_start]
    
    if not prefix_ok:
        print(f"  行 {i+1}: 前缀不一致!")
        print(f"    原始前缀: {repr(o_stripped[:o_start])}")
        print(f"    新前缀:   {repr(n_stripped[:n_start])}")
        all_ok = False
    else:
        print(f"  行 {i+1}: OK (前缀一致, 电荷 {o_stripped[o_start:o_end]} -> {n_stripped[n_start:n_end]})")

if all_ok:
    print("\n✓ 所有 ATOM 行格式一致!")
else:
    print("\n✗ 发现格式不一致的行")
