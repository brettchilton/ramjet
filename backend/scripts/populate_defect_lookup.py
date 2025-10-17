#!/usr/bin/env python3
"""
Populate defect_types and defect_categories tables from Excel lookup data.

Fixed version with correct column mapping based on Excel structure analysis.
"""

import sys
import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

# Add the backend directory to path so we can import our modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.core.database import SessionLocal, engine
from app.core.models import Base, DefectCategory, DefectType

def load_defect_data_from_excel(excel_file_path):
    """
    Load defect categories and types from the Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file
    
    Returns:
        DataFrame: Cleaned defect data
    """
    try:
        # Read the "Defect Costings Lookup" sheet with correct header row
        df = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=3)
        
        print(f"📊 Loaded {len(df)} rows from Excel")
        
        # Clean up column names (remove any extra spaces)
        df.columns = df.columns.str.strip()
        
        print(f"📋 Columns found: {list(df.columns)}")
        
        # Show first few rows for verification
        print("\n🔍 First 3 rows of key fields:")
        key_cols = ['Defect Category', 'Defect', 'Defect Type', 'Rectification Works', 'Priority', 'Rectification Type']
        available_cols = [col for col in key_cols if col in df.columns]
        print(df[available_cols].head(3).to_string())
        
        # Remove rows where essential fields are NaN
        initial_rows = len(df)
        df = df.dropna(subset=['Defect Category', 'Defect'])
        final_rows = len(df)
        print(f"\n🧹 Cleaned data: {initial_rows} -> {final_rows} rows (removed {initial_rows - final_rows} incomplete rows)")
        
        return df
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None

def populate_defect_categories(db: Session, df: pd.DataFrame):
    """
    Populate the defect_categories table.
    
    Args:
        db: Database session
        df: DataFrame with defect data
    """
    # Get unique categories (excluding NaN values)
    categories = df['Defect Category'].dropna().unique()
    categories = [cat for cat in categories if str(cat).lower() != 'nan']
    
    print(f"\n📝 Found {len(categories)} unique defect categories:")
    for cat in categories[:10]:  # Show first 10
        print(f"  - {cat[:80]}{'...' if len(str(cat)) > 80 else ''}")
    if len(categories) > 10:
        print(f"  ... and {len(categories) - 10} more")
    
    # Insert categories
    category_map = {}
    for category_name in categories:
        # Check if category already exists
        existing = db.query(DefectCategory).filter(DefectCategory.category == str(category_name)).first()
        
        if existing:
            print(f"⏭️  Category already exists: {str(category_name)[:50]}{'...' if len(str(category_name)) > 50 else ''}")
            category_map[category_name] = existing.id
        else:
            new_category = DefectCategory(
                category=str(category_name),
                description=f"Standard defect category"
            )
            db.add(new_category)
            db.flush()  # Get the ID without committing
            category_map[category_name] = new_category.id
            print(f"✅ Added category: {str(category_name)[:50]}{'...' if len(str(category_name)) > 50 else ''}")
    
    db.commit()
    return category_map

def populate_defect_types(db: Session, df: pd.DataFrame, category_map: dict):
    """
    Populate the defect_types table with correct field mapping.
    
    Args:
        db: Database session
        df: DataFrame with defect data
        category_map: Mapping of category names to IDs
    """
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        try:
            # Skip rows with missing essential data
            if pd.isna(row.get('Defect Category')) or pd.isna(row.get('Defect')):
                continue
                
            category_name = row['Defect Category']
            defect_name = row['Defect']
            
            # Check if this defect type already exists
            existing = db.query(DefectType).filter(
                DefectType.defect_type == str(defect_name),
                DefectType.category_id == category_map.get(category_name)
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Map Excel columns to database fields correctly
            # Based on the debug output, here's the correct mapping:
            defect_description = str(row.get('Defect Type', '')) if pd.notna(row.get('Defect Type')) else ''
            rectification_works = str(row.get('Rectification Works', '')) if pd.notna(row.get('Rectification Works')) else ''
            rectification_type = str(row.get('Rectification Type', '')) if pd.notna(row.get('Rectification Type')) else ''
            priority = str(row.get('Priority', '')) if pd.notna(row.get('Priority')) else ''
            unit_of_measure = str(row.get('Unit of Measure', '')) if pd.notna(row.get('Unit of Measure')) else ''
            
            # Create new defect type (NO PRICING DATA - AI will handle that)
            defect_type = DefectType(
                category_id=category_map.get(category_name),
                defect_type=str(defect_name),
                defect_description=defect_description,
                rectification_works=rectification_works,
                rectification_type=rectification_type,
                priority=priority,
                unit_of_measure=unit_of_measure,
                base_cost=None,  # No pricing - AI will handle this
                is_active=True
            )
            
            db.add(defect_type)
            added_count += 1
            
            if added_count <= 5:  # Show first 5 for verification
                print(f"✅ Added: {str(category_name)[:30]} -> {str(defect_name)[:30]}")
                print(f"   📝 Type: {defect_description[:50]}{'...' if len(defect_description) > 50 else ''}")
                print(f"   🔧 Rectification: {rectification_type}")
                print(f"   ⚡ Priority: {priority}")
            elif added_count == 6:
                print("   ... (showing first 5, continuing silently)")
        
        except Exception as e:
            error_count += 1
            print(f"❌ Error processing row {index}: {e}")
            if error_count >= 5:
                print("❌ Too many errors, stopping...")
                break
            continue
    
    if error_count == 0:
        db.commit()
        print(f"\n📊 Summary:")
        print(f"  ✅ Added: {added_count} defect types")
        print(f"  ⏭️  Skipped: {skipped_count} existing defect types")
        print(f"  💰 Pricing: Will be handled by AI (no traditional costs stored)")
    else:
        db.rollback()
        print(f"\n❌ Errors encountered: {error_count}. Transaction rolled back.")

def main():
    """Main function to run the import."""
    
    # Default Excel file path (adjust as needed)
    excel_file = "Macutex Assessment Deliverable_Working Template.xlsx"
    
    # Check if file exists
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        print("Please place the Excel file in the backend directory or provide the path as an argument.")
        print("Usage: python populate_defect_lookup.py [path_to_excel_file]")
        return
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    
    print("🚀 Starting defect lookup table population...")
    print("💡 Note: Only importing categories, types, and rectification info - AI will handle pricing")
    print(f"📁 Using Excel file: {excel_file}")
    
    # Load data from Excel
    df = load_defect_data_from_excel(excel_file)
    if df is None:
        return
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Populate categories first
        print("\n🏷️  Populating defect categories...")
        category_map = populate_defect_categories(db, df)
        
        # Then populate defect types
        print("\n🔧 Populating defect types...")
        populate_defect_types(db, df, category_map)
        
        print("\n🎉 Successfully populated defect lookup tables!")
        print("🤖 AI will generate dynamic pricing based on photos, location, and defect details")
        
        # Show summary
        total_categories = db.query(DefectCategory).count()
        total_types = db.query(DefectType).count()
        print(f"\n📊 Database now contains:")
        print(f"  📋 {total_categories} defect categories")
        print(f"  🔧 {total_types} defect types")
        print(f"  💰 0 traditional pricing entries (AI-driven pricing)")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
