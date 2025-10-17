#!/usr/bin/env python3
"""
Debug the Excel column mapping to see why text is going into float fields.
"""

import sys
import os
import pandas as pd

def debug_excel_structure(excel_file_path):
    """
    Debug the Excel file structure to understand column mapping.
    """
    try:
        print("🔍 DEBUGGING EXCEL STRUCTURE...")
        
        # Read the sheet with different header options
        print("\n📊 Reading with header=3 (current approach):")
        df3 = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=3)
        print(f"Columns: {list(df3.columns)}")
        print(f"First row data types:")
        for col in df3.columns:
            first_val = df3[col].iloc[0] if len(df3) > 0 else None
            print(f"  {col}: {type(first_val)} = {first_val}")
        
        print(f"\nFirst few rows:")
        print(df3.head(3).to_string())
        
        print("\n📊 Reading with header=2:")
        df2 = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=2)
        print(f"Columns: {list(df2.columns)}")
        
        print("\n📊 Reading with header=1:")
        df1 = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=1)
        print(f"Columns: {list(df1.columns)}")
        
        print("\n📊 Reading with header=0:")
        df0 = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=0)
        print(f"Columns: {list(df0.columns)}")
        
        # Show raw data structure
        print("\n📊 Raw data (no header):")
        df_raw = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=None)
        print("First 6 rows:")
        print(df_raw.head(6).to_string())
        
        return df3
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None

def main():
    excel_file = "Macutex Assessment Deliverable_Working Template.xlsx"
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return
    
    debug_excel_structure(excel_file)

if __name__ == "__main__":
    main()
