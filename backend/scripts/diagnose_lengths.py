#!/usr/bin/env python3
"""
Diagnostic version to find which field is causing the varchar(255) error.
"""

import sys
import os
import pandas as pd
from sqlalchemy.orm import Session

# Add the current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models import Base, DefectCategory, DefectType

def analyze_field_lengths(excel_file_path):
    """
    Analyze field lengths in the Excel file to find what's too long.
    """
    try:
        # Read the "Defect Costings Lookup" sheet
        df = pd.read_excel(excel_file_path, sheet_name='Defect Costings Lookup', header=3)
        
        print(f"📊 Analyzing field lengths in {len(df)} rows...")
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Check each text field for length
        text_fields = [
            'Defect Category',
            'Defect', 
            'Defect Type',
            'Rectification Works',
            'Rectification Type',
            'Priority',
            'Unit of Measure'
        ]
        
        for field in text_fields:
            if field in df.columns:
                # Get max length and show the longest entries
                df[field] = df[field].astype(str)
                max_length = df[field].str.len().max()
                longest_entries = df[df[field].str.len() == max_length][field].unique()
                
                print(f"\n🔍 {field}:")
                print(f"   Max length: {max_length} characters")
                if max_length > 255:
                    print(f"   ❌ TOO LONG for varchar(255)!")
                elif max_length > 200:
                    print(f"   ⚠️  Close to limit")
                else:
                    print(f"   ✅ OK")
                
                if max_length > 100:  # Show long entries
                    print(f"   Longest entry: '{longest_entries[0][:100]}{'...' if len(longest_entries[0]) > 100 else ''}'")
        
        return df
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None

def test_single_insert(db: Session, df: pd.DataFrame):
    """
    Try inserting one record at a time to find the problematic field.
    """
    print("\n🧪 Testing single record insertions...")
    
    # Get unique categories first
    categories = df['Defect Category'].dropna().unique()
    
    # Try inserting each category
    category_map = {}
    for i, category_name in enumerate(categories):
        print(f"\n🏷️  Testing category {i+1}: '{category_name[:50]}{'...' if len(category_name) > 50 else ''}'")
        print(f"   Length: {len(category_name)} characters")
        
        try:
            existing = db.query(DefectCategory).filter(DefectCategory.category == category_name).first()
            if existing:
                category_map[category_name] = existing.id
                print(f"   ✅ Already exists")
            else:
                new_category = DefectCategory(
                    category=category_name,
                    description=f"Test category: {category_name[:50]}"
                )
                db.add(new_category)
                db.flush()
                category_map[category_name] = new_category.id
                print(f"   ✅ Added successfully")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return
    
    db.commit()
    
    # Now try inserting defect types one by one
    print(f"\n🔧 Testing defect type insertions...")
    
    for index, row in df.head(5).iterrows():  # Test first 5 rows
        if pd.isna(row.get('Defect Category')) or pd.isna(row.get('Defect')):
            continue
            
        category_name = row['Defect Category']
        defect_name = row['Defect']
        
        print(f"\n🔧 Testing defect {index+1}: '{defect_name[:50]}{'...' if len(defect_name) > 50 else ''}'")
        
        # Check each field length
        fields_to_check = {
            'defect_type': defect_name,
            'defect_description': row.get('Defect Type', ''),
            'rectification_works': row.get('Rectification Works', ''),
            'rectification_type': row.get('Rectification Type', ''),
            'priority': row.get('Priority', ''),
            'unit_of_measure': row.get('Unit of Measure', '')
        }
        
        for field_name, field_value in fields_to_check.items():
            if field_value and len(str(field_value)) > 255:
                print(f"   ❌ {field_name} TOO LONG: {len(str(field_value))} chars")
                print(f"      Value: '{str(field_value)[:100]}...'")
        
        try:
            defect_type = DefectType(
                category_id=category_map.get(category_name),
                defect_type=defect_name,
                defect_description=row.get('Defect Type', ''),
                rectification_works=row.get('Rectification Works', ''),
                rectification_type=row.get('Rectification Type', ''),
                priority=row.get('Priority', ''),
                unit_of_measure=row.get('Unit of Measure', ''),
                base_cost=None,
                is_active=True
            )
            
            db.add(defect_type)
            db.flush()
            print(f"   ✅ Added successfully")
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            print(f"   Field lengths:")
            for field_name, field_value in fields_to_check.items():
                print(f"     {field_name}: {len(str(field_value))} chars")
            break
    
    db.commit()

def main():
    """Main diagnostic function."""
    
    excel_file = "Macutex Assessment Deliverable_Working Template.xlsx"
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return
    
    print("🔍 DIAGNOSTIC MODE - Finding varchar length issues...")
    print(f"📁 Using Excel file: {excel_file}")
    
    # Analyze field lengths
    df = analyze_field_lengths(excel_file)
    if df is None:
        return
    
    # Test database insertions
    db = SessionLocal()
    try:
        test_single_insert(db, df)
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
