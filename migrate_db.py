#!/usr/bin/env python3
"""
Database migration script to add the 'prize_eligible' column to player table
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
        # Check if the prize_eligible column exists
        cursor.execute("PRAGMA table_info(player)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'prize_eligible' not in columns:
            print("Adding 'prize_eligible' column to player table...")
            cursor.execute("ALTER TABLE player ADD COLUMN prize_eligible BOOLEAN DEFAULT 1")
            print("✓ Added 'prize_eligible' column")
        else:
            print("✓ 'prize_eligible' column already exists")

        # Ensure all existing players have prize_eligible set to True
        cursor.execute("UPDATE player SET prize_eligible = 1 WHERE prize_eligible IS NULL")
        affected_rows = cursor.rowcount
        if affected_rows > 0:
            print(f"✓ Updated {affected_rows} players to be prize eligible")

        conn.commit()
        print("Database migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()