# db.py
import sqlite3

DB_PATH = "calorie_app.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        # Alimentos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL NOT NULL,
                fat REAL NOT NULL
            )
        """)

        # Entradas por día
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                meal TEXT NOT NULL,
                name TEXT NOT NULL,
                grams REAL NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL NOT NULL,
                fat REAL NOT NULL
            )
        """)

        # Ajustes/objetivos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()

        # Migración por si venías de tabla vieja sin entry_date
        try:
            cur.execute("ALTER TABLE entries ADD COLUMN entry_date TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

def seed_foods_if_empty(default_foods: list[dict]):
    """Rellena foods solo si está vacío (primera ejecución)."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM foods")
        count = cur.fetchone()[0]
        if count == 0:
            cur.executemany("""
                INSERT INTO foods (name, category, calories, protein, carbs, fat)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [
                (f["name"], f["category"], f["calories"], f["protein"], f["carbs"], f["fat"])
                for f in default_foods
            ])
            conn.commit()

def list_categories():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category FROM foods ORDER BY category")
        return [r[0] for r in cur.fetchall()]

def list_foods_by_category(category: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, category, calories, protein, carbs, fat
            FROM foods
            WHERE category = ?
            ORDER BY name
        """, (category,))
        rows = cur.fetchall()
    return [
        {"name": r[0], "category": r[1], "calories": r[2], "protein": r[3], "carbs": r[4], "fat": r[5]}
        for r in rows
    ]

def add_food(food: dict):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO foods (name, category, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (food["name"], food["category"], food["calories"], food["protein"], food["carbs"], food["fat"]))
        conn.commit()

def delete_food_by_name(name: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM foods WHERE name = ?", (name,))
        conn.commit()

def add_entry(entry: dict):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO entries (entry_date, meal, name, grams, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["entry_date"], entry["meal"], entry["name"], entry["grams"],
            entry["calories"], entry["protein"], entry["carbs"], entry["fat"]
        ))
        conn.commit()

def list_entries_by_date(entry_date: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, meal, name, grams, calories, protein, carbs, fat
            FROM entries
            WHERE entry_date = ?
            ORDER BY id
        """, (entry_date,))
        return cur.fetchall()

def daily_totals_last_days(days: int = 30):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT entry_date,
                   SUM(calories) as calories,
                   SUM(protein)  as protein,
                   SUM(carbs)    as carbs,
                   SUM(fat)      as fat
            FROM entries
            WHERE entry_date >= date('now', '-{int(days)} day')
            GROUP BY entry_date
            ORDER BY entry_date
        """)
        return cur.fetchall()

def set_setting(key: str, value: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        conn.commit()

def get_setting(key: str, default: str | None = None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
    return row[0] if row else default
def list_all_foods():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, category, calories, protein, carbs, fat
            FROM foods
            ORDER BY category, name
        """)
        rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "category": r[2], "calories": r[3], "protein": r[4], "carbs": r[5], "fat": r[6]}
        for r in rows
    ]

def update_food(food_id: int, updated: dict):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE foods
            SET name = ?, category = ?, calories = ?, protein = ?, carbs = ?, fat = ?
            WHERE id = ?
        """, (
            updated["name"], updated["category"], updated["calories"],
            updated["protein"], updated["carbs"], updated["fat"],
            food_id
        ))
        conn.commit()

def delete_food_by_id(food_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM foods WHERE id = ?", (food_id,))
        conn.commit()

def update_entry(entry_id: int, grams: float, calories: float, protein: float, carbs: float, fat: float, meal: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE entries
            SET grams = ?, calories = ?, protein = ?, carbs = ?, fat = ?, meal = ?
            WHERE id = ?
        """, (grams, calories, protein, carbs, fat, meal, entry_id))
        conn.commit()

def delete_entry_by_id(entry_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()

