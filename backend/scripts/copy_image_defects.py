import pandas as pd
import os
import shutil
from pathlib import Path

def copy_defect_images_from_excel(excel_file_path, source_folder, destination_folder):
    """
    Copy defect images from source folder to destination folder based on WHCC condition app Excel file.
    
    Parameters:
    excel_file_path (str): Path to the Excel file
    source_folder (str): Path to folder containing source images
    destination_folder (str): Path to destination folder
    """
    
    # Create destination folder if it doesn't exist
    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    
    # Read the defect sheet from Excel file
    try:
        df = pd.read_excel(excel_file_path, sheet_name='whcc_condition_app2_defect')
        print(f"Successfully loaded defect sheet with {len(df)} rows")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Get all image UUIDs from both photo columns
    image_uuids = []
    
    # Check defect_photos1 column
    if 'defect_photos1' in df.columns:
        photos1 = df['defect_photos1'].dropna().tolist()
        image_uuids.extend(photos1)
        print(f"Found {len(photos1)} images in defect_photos1 column")
    
    # Check defect_photos2 column  
    if 'defect_photos2' in df.columns:
        photos2 = df['defect_photos2'].dropna().tolist()
        image_uuids.extend(photos2)
        print(f"Found {len(photos2)} images in defect_photos2 column")
    
    # Remove duplicates
    image_uuids = list(set(image_uuids))
    print(f"Total unique image UUIDs to find: {len(image_uuids)}")
    
    # Common image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    copied_count = 0
    not_found_count = 0
    error_count = 0
    
    # Get list of all files in source folder for faster searching
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"Source folder does not exist: {source_folder}")
        return
    
    all_files = list(source_path.iterdir())
    print(f"Found {len(all_files)} files in source folder")
    
    for uuid in image_uuids:
        uuid = str(uuid).strip()  # Convert to string and remove whitespace
        found_file = None
        
        # Try to find file with UUID as filename (with any extension)
        for file_path in all_files:
            if file_path.is_file():
                # Check if filename (without extension) matches UUID
                if file_path.stem == uuid:
                    found_file = file_path
                    break
                # Also check if full filename matches (in case UUID includes extension)
                elif file_path.name == uuid:
                    found_file = file_path
                    break
        
        if found_file:
            try:
                destination_path = Path(destination_folder) / found_file.name
                shutil.copy2(found_file, destination_path)
                print(f"✓ Copied: {found_file.name}")
                copied_count += 1
            except Exception as e:
                print(f"✗ Error copying {uuid}: {e}")
                error_count += 1
        else:
            print(f"✗ Not found: {uuid}")
            not_found_count += 1
    
    # Summary
    print(f"\n--- Summary ---")
    print(f"Total UUIDs in Excel: {len(image_uuids)}")
    print(f"Successfully copied: {copied_count}")
    print(f"Not found: {not_found_count}")
    print(f"Errors: {error_count}")
    
    # Show some defect details for copied images
    if copied_count > 0:
        print(f"\n--- Defect Details for Reference ---")
        for _, row in df.iterrows():
            photos = []
            if pd.notna(row.get('defect_photos1')):
                photos.append(str(row['defect_photos1']))
            if pd.notna(row.get('defect_photos2')):
                photos.append(str(row['defect_photos2']))
            
            if photos:
                print(f"\nDefect: {row.get('_title', 'Unknown')}")
                print(f"  Type: {row.get('defect_type_', 'Unknown')}")
                print(f"  Location: {row.get('defect_location', 'Unknown')}")
                print(f"  Comment: {row.get('defect_comment', 'None')}")
                print(f"  Images: {', '.join(photos)}")

def copy_images_from_excel(excel_file_path, source_folder, destination_folder, 
                          filename_column='filename', sheet_name=0):
    """
    Generic function to copy images from source folder to destination folder based on filenames in Excel file.
    
    Parameters:
    excel_file_path (str): Path to the Excel file
    source_folder (str): Path to folder containing source images
    destination_folder (str): Path to destination folder
    filename_column (str): Name of column containing image filenames
    sheet_name (str/int): Sheet name or index to read from Excel
    """
    
    # Create destination folder if it doesn't exist
    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    
    # Read Excel file
    try:
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"Successfully loaded Excel file with {len(df)} rows")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Check if filename column exists
    if filename_column not in df.columns:
        print(f"Column '{filename_column}' not found in Excel file.")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Get list of image files to copy
    image_files = df[filename_column].dropna().tolist()
    print(f"Found {len(image_files)} image filenames in Excel")
    
    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    copied_count = 0
    not_found_count = 0
    error_count = 0
    
    for filename in image_files:
        filename = str(filename).strip()  # Convert to string and remove whitespace
        
        # Try to find the file (with or without extension)
        source_path = None
        
        # First, try exact filename
        potential_path = Path(source_folder) / filename
        if potential_path.exists():
            source_path = potential_path
        else:
            # If no extension provided, try common image extensions
            if not any(filename.lower().endswith(ext) for ext in image_extensions):
                for ext in image_extensions:
                    potential_path = Path(source_folder) / f"{filename}{ext}"
                    if potential_path.exists():
                        source_path = potential_path
                        break
        
        if source_path and source_path.exists():
            try:
                destination_path = Path(destination_folder) / source_path.name
                shutil.copy2(source_path, destination_path)
                print(f"✓ Copied: {source_path.name}")
                copied_count += 1
            except Exception as e:
                print(f"✗ Error copying {filename}: {e}")
                error_count += 1
        else:
            print(f"✗ Not found: {filename}")
            not_found_count += 1
    
    # Summary
    print(f"\n--- Summary ---")
    print(f"Total files in Excel: {len(image_files)}")
    print(f"Successfully copied: {copied_count}")
    print(f"Not found: {not_found_count}")
    print(f"Errors: {error_count}")

def list_available_sheets(excel_file_path):
    """Helper function to list all sheet names in Excel file"""
    try:
        xl_file = pd.ExcelFile(excel_file_path)
        return xl_file.sheet_names
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def preview_excel_columns(excel_file_path, sheet_name=0):
    """Helper function to preview column names and first few rows"""
    try:
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"Sheet: {sheet_name}")
        print(f"Columns: {list(df.columns)}")
        print(f"First 5 rows:")
        print(df.head())
        return df.columns.tolist()
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def list_available_sheets(excel_file_path):
    """Helper function to list all sheet names in Excel file"""
    try:
        xl_file = pd.ExcelFile(excel_file_path)
        return xl_file.sheet_names
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def preview_excel_columns(excel_file_path, sheet_name=0):
    """Helper function to preview column names and first few rows"""
    try:
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"Sheet: {sheet_name}")
        print(f"Columns: {list(df.columns)}")
        print(f"First 5 rows:")
        print(df.head())
        return df.columns.tolist()
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def list_images_in_folder(folder_path):
    """Helper function to list all image files in a folder"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Folder does not exist: {folder_path}")
        return []
    
    image_files = []
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path.name)
    
    return sorted(image_files)

# Example usage specifically for your WHCC data
if __name__ == "__main__":
    # Updated paths for local working directory
    excel_file = "whcc_condition_app2_test_dataset.xlsx"
    source_images_folder = "defect_images"  # Relative path to copied folder
    destination_folder = "selected_defect_images"  # Output folder
    
    # First, let's check what we have
    print("=== Checking Files ===")
    print(f"Excel file exists: {Path(excel_file).exists()}")
    print(f"Source folder exists: {Path(source_images_folder).exists()}")
    
    if Path(source_images_folder).exists():
        images = list_images_in_folder(source_images_folder)
        print(f"Found {len(images)} images in source folder")
        if len(images) > 0:
            print(f"Sample images: {images[:3]}")
    
    print("\n=== Available Excel Sheets ===")
    sheets = list_available_sheets(excel_file)
    for i, sheet in enumerate(sheets):
        print(f"  {i}: {sheet}")
    
    print("\n=== WHCC Defect Image Copy ===")
    copy_defect_images_from_excel(
        excel_file_path=excel_file,
        source_folder=source_images_folder,
        destination_folder=destination_folder
    )
    
    # Alternative: If you want to use the generic function for other columns
    # Uncomment below to use generic function:
    """
    print("\n=== Generic Image Copy (if needed) ===")
    copy_images_from_excel(
        excel_file_path=excel_file,
        source_folder=source_images_folder,
        destination_folder=destination_folder,
        filename_column='your_column_name',  # Change this to your column
        sheet_name='whcc_condition_app2_defect'
    )
    """