
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
from app import app, db
from models import Player

def migrate_database():
    """Add prize_eligible field to existing players"""
    with app.app_context():
        # Check if column exists
        try:
            # Try to access the column
            players = Player.query.all()
            for player in players:
                _ = player.prize_eligible
            print("Column 'prize_eligible' already exists.")
        except Exception:
            # Column doesn't exist, add it
            print("Adding 'prize_eligible' column...")
            with db.engine.connect() as conn:
                conn.execute("ALTER TABLE player ADD COLUMN prize_eligible BOOLEAN DEFAULT 1")
                conn.commit()
            print("Column added successfully.")
        
        # Set default values for existing players
        players = Player.query.all()
        for player in players:
            if not hasattr(player, 'prize_eligible') or player.prize_eligible is None:
                player.prize_eligible = True
        
        db.session.commit()
        print("Migration completed successfully.")

if __name__ == '__main__':
    migrate_database()
