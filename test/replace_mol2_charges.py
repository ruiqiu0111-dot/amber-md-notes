#!/usr/bin/env python3
"""
Replace charges in a Tripos MOL2 file with charges from a .chg file.

Usage:
    python replace_mol2_charges.py <mol2_file> <chg_file> [output_file]

If output_file is not specified, writes to <mol2_file>.new.mol2
"""

import sys
import os


def extract_charges_from_chg(chg_path):
    """Read .chg file and return list of charge values (last column)."""
    with open(chg_path, 'r') as f:
        lines = f.readlines()
    
    charges = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            raise ValueError(f"CHG file line {i+1} has only {len(parts)} columns, expected at least 5.")
        charges.append(parts[-1])
    
    return charges


def replace_charges_in_mol2(mol2_path, charges):
    """Replace charges in MOL2 ATOM section and return new content lines."""
    with open(mol2_path, 'r') as f:
        lines = f.readlines()
    
    in_atom_section = False
    atom_line_indices = []  # indices of lines in the ATOM section
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '@<TRIPOS>ATOM':
            in_atom_section = True
            continue
        if in_atom_section and stripped.startswith('@<TRIPOS>'):
            in_atom_section = False
            continue
        if in_atom_section and stripped:
            atom_line_indices.append(i)
    
    if len(atom_line_indices) == 0:
        raise ValueError("No ATOM lines found in MOL2 file.")
    
    if len(atom_line_indices) != len(charges):
        raise ValueError(
            f"MOL2 ATOM count ({len(atom_line_indices)}) does not match "
            f"CHG charge count ({len(charges)})."
        )
    
    new_lines = list(lines)
    
    for idx, line_i in enumerate(atom_line_indices):
        line = new_lines[line_i]
        new_charge = charges[idx]
        
        # Find the last token (charge value) in the line
        # We search for the last contiguous non-space sequence
        stripped = line.rstrip('\n')
        
        # Find start of the last token by scanning from the end
        end_pos = len(stripped)
        while end_pos > 0 and stripped[end_pos - 1].isspace():
            end_pos -= 1
        start_pos = end_pos
        while start_pos > 0 and not stripped[start_pos - 1].isspace():
            start_pos -= 1
        
        old_charge = stripped[start_pos:end_pos]
        
        # Sanity check: new charge should have same length as old charge
        # to preserve exact spacing. If not, we still replace but log a warning.
        if len(new_charge) != len(old_charge):
            print(
                f"  Warning: atom line {idx+1} charge length mismatch: "
                f"old='{old_charge}' ({len(old_charge)} chars), "
                f"new='{new_charge}' ({len(new_charge)} chars)"
            )
            # Pad or trim to match old length (shouldn't normally happen)
            if len(new_charge) < len(old_charge):
                new_charge = new_charge.rjust(len(old_charge))
            else:
                new_charge = new_charge[:len(old_charge)]
        
        # Replace only the charge portion, keeping everything else identical
        new_line = stripped[:start_pos] + new_charge
        # Preserve any trailing newline style
        if line.endswith('\r\n'):
            new_line += '\r\n'
        elif line.endswith('\n'):
            new_line += '\n'
        
        new_lines[line_i] = new_line
    
    return new_lines


def main():
    if len(sys.argv) < 3:
        print("Usage: python replace_mol2_charges.py <mol2_file> <chg_file> [output_file]")
        sys.exit(1)
    
    mol2_path = sys.argv[1]
    chg_path = sys.argv[2]
    
    if len(sys.argv) >= 4:
        output_path = sys.argv[3]
    else:
        base, ext = os.path.splitext(mol2_path)
        output_path = f"{base}.new{ext}"
    
    if not os.path.exists(mol2_path):
        print(f"Error: MOL2 file not found: {mol2_path}")
        sys.exit(1)
    if not os.path.exists(chg_path):
        print(f"Error: CHG file not found: {chg_path}")
        sys.exit(1)
    
    print(f"Reading charges from: {chg_path}")
    charges = extract_charges_from_chg(chg_path)
    print(f"  Found {len(charges)} charge values")
    
    print(f"Reading MOL2 file: {mol2_path}")
    new_lines = replace_charges_in_mol2(mol2_path, charges)
    
    # Count ATOM lines for reporting
    with open(mol2_path, 'r') as f:
        raw = f.readlines()
    in_atom = False
    atom_count = 0
    for line in raw:
        if line.strip() == '@<TRIPOS>ATOM':
            in_atom = True
            continue
        if in_atom and line.strip().startswith('@<TRIPOS>'):
            break
        if in_atom and line.strip():
            atom_count += 1
    print(f"  Found {atom_count} ATOM lines")
    
    print(f"Writing output to: {output_path}")
    with open(output_path, 'w') as f:
        f.writelines(new_lines)
    
    print("Done.")


if __name__ == '__main__':
    main()
