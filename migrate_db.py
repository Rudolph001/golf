
#!/usr/bin/env python3
"""
Database migration script to add the 'day' column to special_prize table
"""
import sqlite3
import os

def migrate_database():
    db_path = 'instance/golf_tournament.db'
    
    if not os.path.exists(db_path):
        print("Database not found. It will be created when the app runs.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the day column exists
        cursor.execute("PRAGMA table_info(special_prize)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'day' not in columns:
            print("Adding 'day' column to special_prize table...")
            cursor.execute("ALTER TABLE special_prize ADD COLUMN day INTEGER")
            print("✓ Added 'day' column")
        else:
            print("✓ 'day' column already exists")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
