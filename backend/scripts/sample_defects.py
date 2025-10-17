#!/usr/bin/env python3
"""
Script to sample 10 defects and related data/images for testing.
Generates:
- backend/data/sample_defects.xlsx
- backend/data/sample_defect_images/...
"""
import os
import shutil
import pandas as pd

# Paths - update these if your source files are in a different location
EXCEL_FILE = '/Users/brettchilton/Downloads/OneDrive_1_01-08-2025/6efa8650-3a83-45d7-8356-d43d73418140 2/whcc_condition_app2.xlsx'
IMAGES_DIR = '/Users/brettchilton/Downloads/OneDrive_1_01-08-2025/6efa8650-3a83-45d7-8356-d43d73418140 2/defect_images'

# Determine output directories
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
data_dir = os.path.join(backend_dir, 'data')
output_excel = os.path.join(data_dir, 'sample_defects.xlsx')
output_images_dir = os.path.join(data_dir, 'sample_defect_images')

# Create output directories
os.makedirs(data_dir, exist_ok=True)
os.makedirs(output_images_dir, exist_ok=True)

# Load all sheets
excel = pd.ExcelFile(EXCEL_FILE)
data = {sheet: excel.parse(sheet) for sheet in excel.sheet_names}

# Explicit hierarchical filtering
# Identify sheet names by suffix
sheet_names = excel.sheet_names
sheet_defect = next(s for s in sheet_names if s.lower().endswith('_defect'))
sheet_condition = next(s for s in sheet_names if s.lower().endswith('_condition'))
sheet_room = next(s for s in sheet_names if s.lower().endswith('_room_detail') or s.lower().endswith('_room'))
sheet_main = next(s for s in sheet_names if s not in [sheet_defect, sheet_condition, sheet_room])

# Load DataFrames
df_main = data[sheet_main]
df_room = data[sheet_room]
df_condition = data[sheet_condition]
df_defect = data[sheet_defect]

# Sample 10 defects
sample_defect_df = df_defect.sample(n=10, random_state=42)

# Filter downstream tables
sample_condition_df = df_condition[df_condition['_record_id'].isin(sample_defect_df['_parent_id'])]
sample_room_df = df_room[df_room['_record_id'].isin(sample_condition_df['_parent_id'])]
sample_main_df = df_main[df_main['_record_id'].isin(sample_room_df['_parent_id'])]

# Prepare filtered dictionary
filtered = {
    sheet_main: sample_main_df,
    sheet_room: sample_room_df,
    sheet_condition: sample_condition_df,
    sheet_defect: sample_defect_df
}

# Write sampled data to new workbook
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    for sheet, df in filtered.items():
        df.to_excel(writer, sheet_name=sheet, index=False)

# Collect image IDs from sampled condition and defect sheets
image_ids = set()
# Condition sheet photos
for col in [
    'condition_photo_1',
    'condition_photo_2'
]:
    if col in sample_condition_df.columns:
        image_ids.update(sample_condition_df[col].dropna().astype(str))
# Defect sheet photos
for col in [
    'defect_photos1',
    'defect_photos2'
]:
    if col in sample_defect_df.columns:
        image_ids.update(sample_defect_df[col].dropna().astype(str))

# Copy image files matching GUIDs
for fname in os.listdir(IMAGES_DIR):
    name, ext = os.path.splitext(fname)
    if name in image_ids:
        shutil.copy2(
            os.path.join(IMAGES_DIR, fname),
            os.path.join(output_images_dir, fname)
        )

print(f"Sample Excel written to {output_excel}")
print(f"Sample images copied to {output_images_dir}")
