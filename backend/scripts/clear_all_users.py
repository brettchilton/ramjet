#!/usr/bin/env python3
"""
Script to clear all users from both the application database and Kratos
"""
import os
import sys
import psycopg2
import httpx
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
KRATOS_ADMIN_URL = os.getenv("KRATOS_ADMIN_URL", "http://localhost:4434")

# Build database URL from environment variables
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "eezy-peezy")
DB_USER = os.getenv("POSTGRES_USER", "brettchilton")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"


async def clear_kratos_identities():
    """Clear all identities from Kratos"""
    print("🔄 Fetching all Kratos identities...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get all identities
            response = await client.get(f"{KRATOS_ADMIN_URL}/admin/identities")
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch identities: {response.text}")
                return False
            
            identities = response.json()
            
            if not identities:
                print("ℹ️  No identities found in Kratos")
                return True
            
            print(f"📋 Found {len(identities)} identities to delete")
            
            # Delete each identity
            for identity in identities:
                identity_id = identity.get("id")
                email = identity.get("traits", {}).get("email", "Unknown")
                
                print(f"  🗑️  Deleting identity: {email} ({identity_id})")
                
                delete_response = await client.delete(
                    f"{KRATOS_ADMIN_URL}/admin/identities/{identity_id}"
                )
                
                if delete_response.status_code not in [200, 204]:
                    print(f"  ❌ Failed to delete {email}: {delete_response.text}")
                else:
                    print(f"  ✅ Deleted {email}")
            
            print("✅ All Kratos identities cleared")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing Kratos identities: {e}")
            return False


def clear_app_database():
    """Clear all users from the application database"""
    print("\n🔄 Clearing users from application database...")
    
    try:
        # Create engine and session
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Count existing users
        count_result = db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = count_result.scalar()
        
        if user_count == 0:
            print("ℹ️  No users found in application database")
            return True
        
        print(f"📋 Found {user_count} users to delete")
        
        # Delete all users
        db.execute(text("DELETE FROM users"))
        db.commit()
        
        print("✅ All users cleared from application database")
        
        # Verify deletion
        count_result = db.execute(text("SELECT COUNT(*) FROM users"))
        remaining = count_result.scalar()
        
        if remaining == 0:
            print("✅ Verified: Database is empty")
        else:
            print(f"⚠️  Warning: {remaining} users still remain")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing application database: {e}")
        return False


def clear_redis_passwords():
    """Clear any cached passwords from Redis (development only)"""
    print("\n🔄 Clearing Redis cache...")
    
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Find all user_password keys
        keys = r.keys("user_password:*")
        
        if not keys:
            print("ℹ️  No cached passwords found in Redis")
            return True
        
        print(f"📋 Found {len(keys)} cached passwords to delete")
        
        # Delete all matching keys
        for key in keys:
            r.delete(key)
            print(f"  🗑️  Deleted {key}")
        
        print("✅ Redis cache cleared")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not clear Redis (non-critical): {e}")
        return True  # Non-critical, so we return True


async def main():
    """Main function to orchestrate the cleanup"""
    print("🧹 Annie Defect Tracking - User Cleanup Script")
    print("=" * 50)
    print("⚠️  WARNING: This will delete ALL users from:")
    print("   - Application database (users table)")
    print("   - Kratos identity store")
    print("   - Redis cache")
    print("=" * 50)
    
    # Ask for confirmation
    confirm = input("\n❓ Are you sure you want to proceed? Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    print("\n🚀 Starting cleanup process...\n")
    
    # Clear application database first
    app_success = clear_app_database()
    
    # Clear Kratos identities
    kratos_success = await clear_kratos_identities()
    
    # Clear Redis cache
    redis_success = clear_redis_passwords()
    
    print("\n" + "=" * 50)
    print("📊 Cleanup Summary:")
    print(f"   Application Database: {'✅ Success' if app_success else '❌ Failed'}")
    print(f"   Kratos Identities: {'✅ Success' if kratos_success else '❌ Failed'}")
    print(f"   Redis Cache: {'✅ Success' if redis_success else '❌ Failed'}")
    print("=" * 50)
    
    if app_success and kratos_success:
        print("\n✅ All users have been successfully cleared!")
        print("\n📝 Next steps:")
        print("   1. Visit http://localhost:5179/auth/registration to create a new user")
        print("   2. Or use the existing registration page at http://localhost:5179/register")
    else:
        print("\n❌ Some operations failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())