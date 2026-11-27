import os
import sqlite3
from urllib.request import pathname2url


class PaathDatabase:
    """Read-only access to assets/paath.db (built by build_paath.py)."""

    def __init__(self, readonly=True):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "assets", "paath.db")
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if readonly:
            uri = "file:" + pathname2url(path) + "?mode=ro"
            self.conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        else:
            self.conn = sqlite3.connect(path, check_same_thread=False)

    def list_sections(self):
        """Rows: group_id, group_gur, group_en, id, gur, en, source_key, start, end"""
        return self.conn.execute("""
            SELECT g.id, g.title_gur, g.title_en,
                   s.id, s.title_gur, s.title_en, s.source_key, s.start_page, s.end_page
            FROM sections s JOIN groups g ON g.id = s.grp
            ORDER BY g.sort, s.sort
        """).fetchall()

    def get_section(self, section_id):
        """Returns (info, parts).
        info  = (title_gur, title_en, source_key)
        parts = [(page, part, text), ...] in reading order
        """
        info = self.conn.execute(
            "SELECT title_gur, title_en, source_key, start_page, end_page "
            "FROM sections WHERE id = ?", (section_id,)).fetchone()
        if info is None:
            return None, []
        gur, eng, key, a, b = info
        parts = self.conn.execute(
            "SELECT page, part, text FROM pages "
            "WHERE source_key = ? AND page BETWEEN ? AND ? ORDER BY page, part",
            (key, a, b)).fetchall()
        return (gur, eng, key), parts

    def close(self):
        self.conn.close()
