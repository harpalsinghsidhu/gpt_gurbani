import os
import sqlite3
from pathlib import Path

class PaathDatabase:
    """Local scripture store. Import only verified, correctly attributed text."""
    def __init__(self, path=None, readonly=False):
        if path is None:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "paath.db")
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        if readonly:
            self.conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        else:
            self.conn = sqlite3.connect(path)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS angs (
                    ang INTEGER PRIMARY KEY CHECK(ang BETWEEN 1 AND 1430),
                    text TEXT NOT NULL
                )
            """)
            self.conn.commit()
        
    def get_ang(self, ang):
        row = self.conn.execute("SELECT text FROM angs WHERE ang=?", (ang,)).fetchone()
        if row:
            return row[0]
        return (
            "ਇੱਥੇ ਅੰਗ ਦਾ ਪ੍ਰਮਾਣਿਤ ਗੁਰਬਾਣੀ ਪਾਠ ਦਿਖਾਇਆ ਜਾਵੇਗਾ।\n\n"
            "This is a placeholder, not Gurbani.\n"
            "Import a verified Gurmukhi scripture dataset before public use.\n\n"
        ) * 12
        
    def import_text(self, ang, text):
        if not 1 <= int(ang) <= 1430:
            raise ValueError("Ang must be between 1 and 1430")
        self.conn.execute(
            "INSERT OR REPLACE INTO angs(ang, text) VALUES(?, ?)",
            (int(ang), text)
        )
        self.conn.commit()
        
    def close(self):
        self.conn.close()
