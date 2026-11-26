"""
build_paath.py  -  builds assets/paath.db from source.sqlite

  python build_paath.py --inspect     (step 1: shows what is inside source.sqlite)
  python build_paath.py               (step 2: builds assets/paath.db)

Run both from the folder that contains source.sqlite.
"""
import os
import sqlite3
import sys
from itertools import groupby

SRC = "source.sqlite"
OUT = os.path.join("assets", "paath.db")

# source_id numbers inside source.sqlite.  These are best guesses.
# Run  python build_paath.py --inspect  and fix them here if they are wrong.
SOURCE_IDS = {
    "sggs": 1,       # Sri Guru Granth Sahib Ji
    "dasam": 2,      # Sri Dasam Granth Sahib Ji
    "gurdas": 3,     # Bhai Gurdas Ji (Vaaran)
    "nandlal": 4,    # Bhai Nand Lal Ji
}

# One text block = at most this many lines (keeps each label texture small,
# which avoids the black box on older phones)
PART_LINES = 14

# Nitnem items that live inside Dasam Granth. Fill (start_page, end_page)
# after looking at the --inspect output, e.g. "chaupai": (123, 125)
NITNEM_DASAM = {
    "tav_prasad": None,
    "chaupai": None,
}

# (id, gurmukhi title, english title)
GROUPS = [
    ("nitnem", "ਨਿਤਨੇਮ", "Nitnem"),
    ("sggs", "ਸ੍ਰੀ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ", "Sri Guru Granth Sahib Ji - Full and Banis"),
    ("raag", "ਰਾਗ ਅਨੁਸਾਰ ਬਾਣੀ", "Sri Guru Granth Sahib Ji - Raags"),
    ("after", "ਰਾਗਾਂ ਤੋਂ ਬਾਅਦ", "Sri Guru Granth Sahib Ji - After the Raags"),
    ("dasam", "ਸ੍ਰੀ ਦਸਮ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ", "Sri Dasam Granth Sahib Ji"),
    ("gurdas", "ਭਾਈ ਗੁਰਦਾਸ ਜੀ", "Bhai Gurdas Ji"),
    ("nandlal", "ਭਾਈ ਨੰਦ ਲਾਲ ਜੀ", "Bhai Nand Lal Ji"),
]

# (id, group, source, gurmukhi, english, start_ang, end_ang)
FIXED = [
    ("nit_japji", "nitnem", "sggs", "ਜਪੁ ਜੀ ਸਾਹਿਬ", "Japji Sahib", 1, 8),
    ("nit_anand", "nitnem", "sggs", "ਅਨੰਦੁ ਸਾਹਿਬ", "Anand Sahib", 917, 922),
    ("nit_rehras", "nitnem", "sggs", "ਸੋ ਦਰੁ / ਸੋ ਪੁਰਖੁ (ਰਹਰਾਸਿ)", "Rehras - So Dar and So Purakh", 8, 12),
    ("nit_sohila", "nitnem", "sggs", "ਸੋਹਿਲਾ ਸਾਹਿਬ", "Sohila Sahib", 12, 13),

    ("sggs_full", "sggs", "sggs", "ਸ੍ਰੀ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ", "Full SGGS", 1, 1430),
    ("b_japji", "sggs", "sggs", "ਜਪੁ ਜੀ ਸਾਹਿਬ", "Japji Sahib", 1, 8),
    ("b_sodar", "sggs", "sggs", "ਸੋ ਦਰੁ", "So Dar", 8, 10),
    ("b_sopurakh", "sggs", "sggs", "ਸੋ ਪੁਰਖੁ", "So Purakh", 10, 12),
    ("b_sohila", "sggs", "sggs", "ਸੋਹਿਲਾ", "Sohila", 12, 13),
    ("b_sukhmani", "sggs", "sggs", "ਸੁਖਮਨੀ ਸਾਹਿਬ", "Sukhmani Sahib", 262, 296),
    ("b_anand", "sggs", "sggs", "ਅਨੰਦੁ ਸਾਹਿਬ", "Anand Sahib", 917, 922),
    ("b_asadivaar", "sggs", "sggs", "ਆਸਾ ਦੀ ਵਾਰ", "Asa di Vaar", 462, 475),
    ("b_barahmajh", "sggs", "sggs", "ਬਾਰਹ ਮਾਹਾ ਮਾਝ", "Barah Maha (Majh)", 133, 136),
    ("b_barahtukhari", "sggs", "sggs", "ਬਾਰਹ ਮਾਹਾ ਤੁਖਾਰੀ", "Barah Maha (Tukhari)", 1107, 1110),
    ("b_bavan", "sggs", "sggs", "ਬਾਵਨ ਅਖਰੀ", "Bavan Akhri", 250, 262),
    ("b_sidhgosht", "sggs", "sggs", "ਸਿਧ ਗੋਸਟਿ", "Sidh Gosht", 938, 946),
    ("b_dakhni", "sggs", "sggs", "ਦਖਣੀ ਓਅੰਕਾਰੁ", "Dakhni Oankar", 929, 938),
    ("b_sad", "sggs", "sggs", "ਸਦੁ", "Sad", 923, 924),
    ("b_lavan", "sggs", "sggs", "ਲਾਵਾਂ (ਸੂਹੀ)", "Lavan", 773, 774),

    ("r_siri", "raag", "sggs", "ਸਿਰੀਰਾਗੁ", "Siri Raag", 14, 93),
    ("r_majh", "raag", "sggs", "ਮਾਝ", "Majh", 94, 150),
    ("r_gauri", "raag", "sggs", "ਗਉੜੀ", "Gauri", 151, 346),
    ("r_asa", "raag", "sggs", "ਆਸਾ", "Aasa", 347, 488),
    ("r_gujri", "raag", "sggs", "ਗੂਜਰੀ", "Gujri", 489, 526),
    ("r_devgandhari", "raag", "sggs", "ਦੇਵਗੰਧਾਰੀ", "Devgandhari", 527, 536),
    ("r_bihagra", "raag", "sggs", "ਬਿਹਾਗੜਾ", "Bihagra", 537, 556),
    ("r_vadhans", "raag", "sggs", "ਵਡਹੰਸੁ", "Vadhans", 557, 594),
    ("r_sorath", "raag", "sggs", "ਸੋਰਠਿ", "Sorath", 595, 659),
    ("r_dhanasri", "raag", "sggs", "ਧਨਾਸਰੀ", "Dhanasri", 660, 695),
    ("r_jaitsri", "raag", "sggs", "ਜੈਤਸਰੀ", "Jaitsri", 696, 710),
    ("r_todi", "raag", "sggs", "ਟੋਡੀ", "Todi", 711, 718),
    ("r_bairari", "raag", "sggs", "ਬੈਰਾੜੀ", "Bairari", 719, 720),
    ("r_tilang", "raag", "sggs", "ਤਿਲੰਗ", "Tilang", 721, 727),
    ("r_suhi", "raag", "sggs", "ਸੂਹੀ", "Suhi", 728, 794),
    ("r_bilaval", "raag", "sggs", "ਬਿਲਾਵਲੁ", "Bilaval", 795, 858),
    ("r_gond", "raag", "sggs", "ਗੋਂਡ", "Gond", 859, 875),
    ("r_ramkali", "raag", "sggs", "ਰਾਮਕਲੀ", "Ramkali", 876, 974),
    ("r_natnarayan", "raag", "sggs", "ਨਟ ਨਾਰਾਇਨ", "Nat Narayan", 975, 983),
    ("r_maligaura", "raag", "sggs", "ਮਾਲੀ ਗਉੜਾ", "Mali Gaura", 984, 988),
    ("r_maru", "raag", "sggs", "ਮਾਰੂ", "Maru", 989, 1106),
    ("r_tukhari", "raag", "sggs", "ਤੁਖਾਰੀ", "Tukhari", 1107, 1117),
    ("r_kedara", "raag", "sggs", "ਕੇਦਾਰਾ", "Kedara", 1118, 1124),
    ("r_bhairo", "raag", "sggs", "ਭੈਰਉ", "Bhairo", 1125, 1167),
    ("r_basant", "raag", "sggs", "ਬਸੰਤੁ", "Basant", 1168, 1196),
    ("r_sarang", "raag", "sggs", "ਸਾਰੰਗ", "Sarang", 1197, 1253),
    ("r_malar", "raag", "sggs", "ਮਲਾਰ", "Malar", 1254, 1293),
    ("r_kanra", "raag", "sggs", "ਕਾਨੜਾ", "Kanra", 1294, 1318),
    ("r_kalyan", "raag", "sggs", "ਕਲਿਆਨ", "Kalyan", 1319, 1326),
    ("r_prabhati", "raag", "sggs", "ਪ੍ਰਭਾਤੀ", "Prabhati", 1327, 1351),
    ("r_jaijavanti", "raag", "sggs", "ਜੈਜਾਵੰਤੀ", "Jaijavanti", 1352, 1353),

    ("a_sahaskriti", "after", "sggs", "ਸਲੋਕ ਸਹਸਕ੍ਰਿਤੀ", "Salok Sahaskriti", 1353, 1360),
    ("a_gatha", "after", "sggs", "ਗਾਥਾ", "Gatha", 1360, 1361),
    ("a_phunhe", "after", "sggs", "ਫੁਨਹੇ", "Phunhe", 1361, 1363),
    ("a_chaubole", "after", "sggs", "ਚਉਬੋਲੇ", "Chaubole", 1363, 1364),
    ("a_kabir", "after", "sggs", "ਸਲੋਕ ਕਬੀਰ ਜੀ", "Salok Kabir Ji", 1364, 1377),
    ("a_farid", "after", "sggs", "ਸਲੋਕ ਫਰੀਦ ਜੀ", "Salok Farid Ji", 1377, 1384),
    ("a_savaiye", "after", "sggs", "ਸਵਈਏ", "Savaiye", 1385, 1409),
    ("a_vaaran", "after", "sggs", "ਸਲੋਕ ਵਾਰਾਂ ਤੇ ਵਧੀਕ", "Salok Vaaran te Vadhik", 1410, 1429),
    ("a_m9", "after", "sggs", "ਸਲੋਕ ਮਹਲਾ ੯", "Salok Mahalla 9", 1426, 1429),
    ("a_mundavani", "after", "sggs", "ਮੁੰਦਾਵਣੀ", "Mundavani", 1429, 1429),
    ("a_raagmala", "after", "sggs", "ਰਾਗਮਾਲਾ", "Raagmala", 1429, 1430),
]

# Gurmukhi titles for sections that are read from the database
GURMUKHI_NAMES = [
    ("jaap", "ਜਾਪੁ ਸਾਹਿਬ"),
    ("akal ustat", "ਅਕਾਲ ਉਸਤਤਿ"),
    ("bachittar", "ਬਚਿਤ੍ਰ ਨਾਟਕ"),
    ("bichitra", "ਬਚਿਤ੍ਰ ਨਾਟਕ"),
    ("chandi di", "ਚੰਡੀ ਦੀ ਵਾਰ"),
    ("chandi", "ਚੰਡੀ ਚਰਿਤ੍ਰ"),
    ("gyan", "ਗਿਆਨ ਪ੍ਰਬੋਧ"),
    ("gian", "ਗਿਆਨ ਪ੍ਰਬੋਧ"),
    ("chaubis", "ਚਉਬੀਸ ਅਵਤਾਰ"),
    ("brahma", "ਬ੍ਰਹਮਾ ਅਵਤਾਰ"),
    ("rudra", "ਰੁਦ੍ਰ ਅਵਤਾਰ"),
    ("shabad hazare", "ਸ਼ਬਦ ਹਜ਼ਾਰੇ"),
    ("savaiye", "ਸਵਯੇ"),
    ("swaiye", "ਸਵਯੇ"),
    ("khalsa", "ਖਾਲਸਾ ਮਹਿਮਾ"),
    ("shastar", "ਸ਼ਸਤ੍ਰ ਨਾਮ ਮਾਲਾ"),
    ("pakhyan", "ਪਖਯਾਨ ਚਰਿਤ੍ਰ"),
    ("charitr", "ਪਖਯਾਨ ਚਰਿਤ੍ਰ"),
    ("zafar", "ਜ਼ਫ਼ਰਨਾਮਾ"),
    ("hikayat", "ਹਿਕਾਇਤਾਂ"),
]

SCHEMA = """
CREATE TABLE groups(
    id TEXT PRIMARY KEY, title_gur TEXT, title_en TEXT, sort INTEGER
);
CREATE TABLE sections(
    id TEXT PRIMARY KEY, grp TEXT, source_key TEXT,
    title_gur TEXT, title_en TEXT,
    start_page INTEGER, end_page INTEGER, sort INTEGER
);
CREATE TABLE pages(
    source_key TEXT, page INTEGER, part INTEGER, text TEXT NOT NULL,
    PRIMARY KEY(source_key, page, part)
);
"""


def inspect(src):
    print("==== sources table ====")
    try:
        cur = src.execute("SELECT * FROM sources")
        print([d[0] for d in cur.description])
        for r in cur.fetchall():
            print(r)
    except sqlite3.Error as e:
        print("could not read sources table:", e)
    print()
    print("==== lines per source_id (page range) ====")
    for sid, n, a, b in src.execute("""
            SELECT s.source_id, COUNT(*), MIN(l.source_page), MAX(l.source_page)
            FROM lines l JOIN shabads s ON s.id = l.shabad_id
            GROUP BY s.source_id ORDER BY s.source_id"""):
        print(f"source_id={sid}  lines={n}  pages {a} to {b}")
    print()
    print("==== sections found inside each wanted source ====")
    names = load_section_names(src)
    for key, sid in SOURCE_IDS.items():
        print(f"--- {key} (source_id {sid}) ---")
        for sec_id, a, b in section_ranges(src, sid):
            print(f"  section_id={sec_id}  name={names.get(sec_id)}  pages {a}-{b}")


def load_section_names(src):
    names = {}
    try:
        cols = [r[1] for r in src.execute("PRAGMA table_info(sections)")]
        eng = "name_english" if "name_english" in cols else None
        if eng:
            for sid, name in src.execute(f"SELECT id, {eng} FROM sections"):
                names[sid] = name
    except sqlite3.Error:
        pass
    return names


def section_ranges(src, source_id):
    try:
        return src.execute("""
            SELECT s.section_id, MIN(l.source_page), MAX(l.source_page)
            FROM lines l JOIN shabads s ON s.id = l.shabad_id
            WHERE s.source_id = ? AND l.source_page IS NOT NULL
            GROUP BY s.section_id
            ORDER BY MIN(l.source_page), MIN(s.order_id)""", (source_id,)).fetchall()
    except sqlite3.Error as e:
        print("  could not read sections:", e)
        return []


def gurmukhi_for(english):
    low = (english or "").lower()
    for key, gur in GURMUKHI_NAMES:
        if key in low:
            return gur
    return ""


def load_pages(src, out, key, source_id):
    rows = src.execute("""
        SELECT l.source_page, l.source_line, l.gurmukhi
        FROM lines l JOIN shabads s ON s.id = l.shabad_id
        WHERE s.source_id = ?
        ORDER BY l.source_page, l.source_line, s.order_id, l.order_id
    """, (source_id,)).fetchall()
    bad = sum(1 for r in rows if r[0] is None or r[1] is None or r[2] is None)
    rows = [r for r in rows if r[0] is not None and r[1] is not None and r[2] is not None]
    if not rows:
        print(f"[{key}] source_id {source_id}: NO lines found - skipped")
        return False

    pages = {}
    for page, page_rows in groupby(rows, key=lambda r: r[0]):
        printed = []
        for _, parts in groupby(page_rows, key=lambda r: r[1]):
            printed.append(" ".join(p[2] for p in parts))
        pages[page] = printed

    data = []
    for page, printed in pages.items():
        for i in range(0, len(printed), PART_LINES):
            data.append((key, page, i // PART_LINES, "\n".join(printed[i:i + PART_LINES])))
    out.executemany("INSERT INTO pages(source_key, page, part, text) VALUES(?,?,?,?)", data)
    print(f"[{key}] lines={len(rows)} pages={len(pages)} "
          f"range={min(pages)}-{max(pages)} skipped_rows={bad}")
    return True


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"{SRC} not found. Run this from the folder that contains it.")
    src = sqlite3.connect(SRC)
    if "--inspect" in sys.argv:
        inspect(src)
        return

    os.makedirs("assets", exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    out = sqlite3.connect(OUT)
    out.executescript(SCHEMA)

    loaded = {}
    for key, sid in SOURCE_IDS.items():
        loaded[key] = load_pages(src, out, key, sid)
    if not loaded["sggs"]:
        raise SystemExit("SGGS was not found - check SOURCE_IDS (run --inspect).")

    sort_no = {}
    sections = []

    def add(sec_id, grp, key, gur, eng, a, b):
        sort_no[grp] = sort_no.get(grp, 0) + 1
        sections.append((sec_id, grp, key, gur, eng, a, b, sort_no[grp]))

    names = load_section_names(src)
    dasam_jaap = None
    auto = []
    for key in ("dasam", "gurdas", "nandlal"):
        if not loaded[key]:
            continue
        for sec_id, a, b in section_ranges(src, SOURCE_IDS[key]):
            eng = names.get(sec_id) or f"Section {sec_id}"
            auto.append((f"{key}_{sec_id}", key, key, gurmukhi_for(eng), eng, a, b))
            if key == "dasam" and dasam_jaap is None and "jaap" in eng.lower():
                dasam_jaap = (gurmukhi_for(eng), eng, a, b)

    # Nitnem group: order is Japji, Jaap, Tav-Prasad, Chaupai, Anand, Rehras, Sohila
    fixed = {f[0]: f for f in FIXED}
    add(*fixed["nit_japji"])
    if dasam_jaap:
        add("nit_jaap", "nitnem", "dasam", "ਜਾਪੁ ਸਾਹਿਬ", "Jaap Sahib", dasam_jaap[2], dasam_jaap[3])
    else:
        print("NOTE: Jaap Sahib not found in Dasam sections - not added to Nitnem")
    for name, gur, eng in (("tav_prasad", "ਤ੍ਵਪ੍ਰਸਾਦਿ ਸਵਯੇ", "Tav-Prasad Savaiye"),
                           ("chaupai", "ਚੌਪਈ ਸਾਹਿਬ", "Chaupai Sahib")):
        rng = NITNEM_DASAM.get(name)
        if rng and loaded["dasam"]:
            add(f"nit_{name}", "nitnem", "dasam", gur, eng, rng[0], rng[1])
        else:
            print(f"NOTE: {eng} not added - set NITNEM_DASAM['{name}'] = (start_page, end_page)")
    for k in ("nit_anand", "nit_rehras", "nit_sohila"):
        add(*fixed[k])

    for f in FIXED:
        if not f[0].startswith("nit_"):
            add(*f)
    for a in auto:
        add(*a)

    used = {s[1] for s in sections}
    gdata = [(g[0], g[1], g[2], i) for i, g in enumerate(GROUPS) if g[0] in used]
    out.executemany("INSERT INTO groups VALUES(?,?,?,?)", gdata)
    out.executemany("INSERT INTO sections VALUES(?,?,?,?,?,?,?,?)", sections)
    out.commit()

    n_sggs = out.execute("SELECT COUNT(DISTINCT page) FROM pages WHERE source_key='sggs'").fetchone()[0]
    missing = [a for a in range(1, 1431) if not out.execute(
        "SELECT 1 FROM pages WHERE source_key='sggs' AND page=? LIMIT 1", (a,)).fetchone()]
    print("---------------------------------------------")
    print("SGGS Angs written:", n_sggs, "(expected 1430)")
    print("Missing SGGS Angs:", missing)
    print("Sections written:", len(sections))
    for g in gdata:
        n = sum(1 for s in sections if s[1] == g[0])
        print(f"  {g[2]}: {n}")
    out.close()
    src.close()


if __name__ == "__main__":
    main()
