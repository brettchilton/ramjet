#!/usr/bin/env python3
"""
Quick test to verify sample UUIDs exist as image files
"""

import os

# Sample UUIDs from the Excel data we saw
test_uuids = [
    'ca435366-46f9-42b3-b08e-425413d3b59b',
    '3dc4aba2-1dba-4ef1-a3af-7bead10b0ea4', 
    '3a719147-1f1e-485e-9cec-189067900c8f',
    'e068a97e-1d9a-43a4-bc7e-c5501b28de91'
]

photos_folder = "/Users/brettchilton/Downloads/OneDrive_1_01-08-2025/6efa8650-3a83-45d7-8356-d43d73418140/photos"

print("Testing sample UUIDs...")
print(f"Photos folder: {photos_folder}")

for uuid in test_uuids:
    file_path = f"{photos_folder}/{uuid}.jpg"
    exists = os.path.exists(file_path)
    print(f"{uuid}.jpg: {'EXISTS' if exists else 'NOT FOUND'}")
    
    if exists:
        # Get file size
        size = os.path.getsize(file_path)
        print(f"  Size: {size:,} bytes")
