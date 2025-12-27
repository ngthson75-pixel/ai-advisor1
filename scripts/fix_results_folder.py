#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUICK FIX - Add RESULTS_FOLDER to backtest script
"""

import os
import sys

script_name = "backtest_4strategies_2025.py"

if not os.path.exists(script_name):
    print(f"❌ File not found: {script_name}")
    print("Make sure you're in the scripts folder!")
    sys.exit(1)

# Read file
with open(script_name, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check if RESULTS_FOLDER already exists
has_results_folder = any('RESULTS_FOLDER' in line for line in lines)

if has_results_folder:
    print("✅ RESULTS_FOLDER already exists in the file!")
    print("The error might be from a different issue.")
    print("\nChecking configuration section...")
    
    for i, line in enumerate(lines[:50], 1):
        if 'RESULTS_FOLDER' in line:
            print(f"Line {i}: {line.strip()}")
else:
    print("⚠️ RESULTS_FOLDER not found! Adding it now...")
    
    # Find where to insert
    insert_index = None
    for i, line in enumerate(lines):
        if 'END_DATE' in line and '=' in line:
            insert_index = i + 1
            break
    
    if insert_index:
        # Insert RESULTS_FOLDER definition
        new_lines = [
            "\n",
            "# Results folder\n",
            "RESULTS_FOLDER = os.path.join(SCRIPT_DIR, \"backtest_results_2025\")\n",
            "os.makedirs(RESULTS_FOLDER, exist_ok=True)\n"
        ]
        
        for j, new_line in enumerate(new_lines):
            lines.insert(insert_index + j, new_line)
        
        # Write back
        with open(script_name, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ Added RESULTS_FOLDER at line {insert_index}!")
        print("\nAdded lines:")
        for line in new_lines:
            print(f"  {line.rstrip()}")
    else:
        print("❌ Could not find insertion point!")
        print("Please add manually after END_DATE line:")
        print("\nRESULTS_FOLDER = os.path.join(SCRIPT_DIR, \"backtest_results_2025\")")
        print("os.makedirs(RESULTS_FOLDER, exist_ok=True)")

print("\n" + "="*70)
print("Now try running again:")
print("python backtest_4strategies_2025.py")
print("="*70)
