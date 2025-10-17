#!/usr/bin/env python3
"""
Script to set up Kratos database
"""
import os
import sys
import psycopg2
from psycopg2 import sql

def create_kratos_database():
    """Create the Kratos database if it doesn't exist."""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'db'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('POSTGRES_USER', 'brettchilton'),
        'password': os.getenv('POSTGRES_PASSWORD', 'mypassword'),
        'database': os.getenv('POSTGRES_DB', 'eezy-peezy')
    }
    
    try:
        # Connect to the default database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if kratos database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'kratos'"
        )
        exists = cursor.fetchone()
        
        if not exists:
            # Create the kratos database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier('kratos')
            ))
            print("✅ Kratos database created successfully!")
        else:
            print("ℹ️  Kratos database already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating Kratos database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_kratos_database()