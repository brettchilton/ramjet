#!/usr/bin/env python3
"""
Product lookup utility for Ramjet automation
Demonstrates how to query product master data
"""

import sqlite3
import json

DB_FILE = '/home/claude/ramjet_products.db'

def get_product_full_specs(product_code, colour=None):
    """
    Get all specifications for a product
    If colour is None, returns all colour variants
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    # Base query
    query = '''
        SELECT 
            p.product_code,
            p.product_description,
            p.customer,
            p.mould_no,
            p.cycle_time_seconds,
            p.shot_weight_grams,
            p.num_cavities,
            p.product_weight_grams,
            p.estimated_running_time_hours,
            p.machine_min_requirements,
            pk.qty_per_bag,
            pk.bag_size,
            pk.qty_per_carton,
            pk.carton_size,
            pk.cartons_per_pallet,
            pk.cartons_per_layer,
            m.colour,
            m.material_grade,
            m.material_type,
            m.colour_no,
            m.colour_supplier,
            m.mb_add_rate,
            m.additive,
            m.additive_add_rate,
            m.additive_supplier,
            pr.unit_cost
        FROM products p
        JOIN packaging_specs pk ON p.product_code = pk.product_code
        JOIN material_specs m ON p.product_code = m.product_code
        JOIN pricing pr ON p.product_code = pr.product_code AND m.colour = pr.colour
        WHERE p.product_code = ?
    '''
    
    params = [product_code]
    
    if colour:
        query += ' AND m.colour = ?'
        params.append(colour)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    conn.close()
    
    if not rows:
        return None
    
    # Convert to dict
    results = []
    for row in rows:
        results.append({
            'product_code': row['product_code'],
            'product_description': row['product_description'],
            'customer': row['customer'],
            'mould_no': row['mould_no'],
            'cycle_time_seconds': row['cycle_time_seconds'],
            'shot_weight_grams': row['shot_weight_grams'],
            'num_cavities': row['num_cavities'],
            'product_weight_grams': row['product_weight_grams'],
            'estimated_running_time_hours': row['estimated_running_time_hours'],
            'machine_min_requirements': row['machine_min_requirements'],
            'packaging': {
                'qty_per_bag': row['qty_per_bag'],
                'bag_size': row['bag_size'],
                'qty_per_carton': row['qty_per_carton'],
                'carton_size': row['carton_size'],
                'cartons_per_pallet': row['cartons_per_pallet'],
                'cartons_per_layer': row['cartons_per_layer']
            },
            'material': {
                'colour': row['colour'],
                'material_grade': row['material_grade'],
                'material_type': row['material_type'],
                'colour_no': row['colour_no'],
                'colour_supplier': row['colour_supplier'],
                'mb_add_rate': row['mb_add_rate'],
                'additive': row['additive'],
                'additive_add_rate': row['additive_add_rate'],
                'additive_supplier': row['additive_supplier']
            },
            'unit_cost': row['unit_cost']
        })
    
    return results if len(results) > 1 else results[0]


def calculate_material_requirements(product_code, colour, quantity):
    """
    Calculate material requirements for a given quantity
    """
    specs = get_product_full_specs(product_code, colour)
    
    if not specs:
        return None
    
    # Calculate total product weight
    total_product_weight_kg = (specs['product_weight_grams'] * quantity) / 1000
    
    # Add waste factor (assume 5% waste)
    waste_factor = 1.05
    total_material_required_kg = total_product_weight_kg * waste_factor
    
    # Calculate masterbatch (colour) requirement
    mb_rate = specs['material']['mb_add_rate'] / 100  # Convert % to decimal
    mb_required_kg = total_material_required_kg * mb_rate
    
    # Calculate additive requirement
    add_rate = specs['material']['additive_add_rate'] / 100
    additive_required_kg = total_material_required_kg * add_rate
    
    # Calculate base material (total - mb - additive)
    base_material_kg = total_material_required_kg - mb_required_kg - additive_required_kg
    
    # Calculate packaging requirements
    cartons_needed = (quantity + specs['packaging']['qty_per_carton'] - 1) // specs['packaging']['qty_per_carton']
    bags_needed = (quantity + specs['packaging']['qty_per_bag'] - 1) // specs['packaging']['qty_per_bag']
    
    return {
        'product_code': product_code,
        'colour': colour,
        'quantity': quantity,
        'material_requirements': {
            'base_material_kg': round(base_material_kg, 2),
            'material_grade': specs['material']['material_grade'],
            'material_type': specs['material']['material_type'],
            'masterbatch_kg': round(mb_required_kg, 2),
            'colour_no': specs['material']['colour_no'],
            'colour_supplier': specs['material']['colour_supplier'],
            'additive_kg': round(additive_required_kg, 2),
            'additive': specs['material']['additive'],
            'additive_supplier': specs['material']['additive_supplier'],
            'total_material_kg': round(total_material_required_kg, 2)
        },
        'packaging_requirements': {
            'bags_needed': bags_needed,
            'bag_size': specs['packaging']['bag_size'],
            'cartons_needed': cartons_needed,
            'carton_size': specs['packaging']['carton_size']
        },
        'estimated_cost': round(specs['unit_cost'] * quantity, 2)
    }


def search_products(search_term):
    """
    Search products by code or description
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT product_code, product_description, customer
        FROM products
        WHERE product_code LIKE ? OR product_description LIKE ?
        ORDER BY product_code
    ''', (f'%{search_term}%', f'%{search_term}%'))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


# Demo usage
if __name__ == '__main__':
    print("="*70)
    print("RAMJET PRODUCT LOOKUP DEMO")
    print("="*70)
    
    # Example 1: Get full specs for a product
    print("\n1. LOOKUP: LOCAP2 (Black)")
    print("-"*70)
    specs = get_product_full_specs('LOCAP2', 'Black')
    print(json.dumps(specs, indent=2))
    
    # Example 2: Calculate material requirements
    print("\n\n2. CALCULATE MATERIALS: 1000 units of LOCAP2 (Black)")
    print("-"*70)
    materials = calculate_material_requirements('LOCAP2', 'Black', 1000)
    print(json.dumps(materials, indent=2))
    
    # Example 3: Search products
    print("\n\n3. SEARCH: Products containing 'CAP'")
    print("-"*70)
    results = search_products('CAP')
    for r in results[:10]:  # Show first 10
        print(f"  {r['product_code']}: {r['product_description']} ({r['customer']})")
    
    print(f"\n  ... and {len(results) - 10} more")
    
    # Example 4: Get product with multiple colours
    print("\n\n4. PRODUCT WITH MULTIPLE COLOURS:")
    print("-"*70)
    # Find a product with multiple colours
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT product_code, COUNT(*) as colour_count
        FROM material_specs
        GROUP BY product_code
        HAVING colour_count > 1
        LIMIT 1
    ''')
    multi_colour = cursor.fetchone()
    conn.close()
    
    if multi_colour:
        code = multi_colour[0]
        print(f"Product: {code}")
        variants = get_product_full_specs(code)
        for v in variants:
            print(f"  - {v['material']['colour']}: ${v['unit_cost']} each")
    
    print("\n" + "="*70)
    print("Database ready for automation demo!")
    print("="*70)
