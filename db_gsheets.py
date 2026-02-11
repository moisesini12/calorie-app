# db_gsheets.py
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


SHEET_ID = st.secrets["SPREADSHEET_ID"]
TAB_FOODS = "foods"
TAB_ENTRIES = "entries"
TAB_SETTINGS = "settings"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]



# ---------- Helpers ----------
@st.cache_resource
def _client() -> gspread.Client:
    sa_info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)





@st.cache_resource
def _sh():
    return _client().open_by_key(SHEET_ID)

@st.cache_resource
def _ws(tab_name: str):
    return _sh().worksheet(tab_name)



def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(str(x).replace(",", "."))
    except Exception:
        return default


def _to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or x == "":
            return default
        return int(float(str(x).replace(",", ".")))
    except Exception:
        return default


@st.cache_data(ttl=15)
def _get_all_records(tab_name: str):
    ws = _ws(tab_name)
    return ws.get_all_records()



def _next_id(tab_name: str) -> int:
    rows = _get_all_records(tab_name)
    if not rows:
        return 1
    mx = 0
    for r in rows:
        mx = max(mx, _to_int(r.get("id", 0), 0))
    return mx + 1


def _find_row_index_by_id(tab_name: str, id_value: int) -> Optional[int]:
    """
    Devuelve el índice REAL de la fila en Sheets (1-based),
    o None si no existe.
    Asume que la columna A es 'id'.
    """
    ws = _ws(tab_name)
    col = ws.col_values(1)  # columna A
    # col[0] es header
    target = str(id_value)
    for i, v in enumerate(col[1:], start=2):
        if str(v).strip() == target:
            return i
    return None

def _append_row_by_headers(ws, row_dict: dict):
    headers = ws.row_values(1)
    values = []
    for h in headers:
        values.append(row_dict.get(h, ""))  # si falta algo, vacío
    ws.append_row(values, value_input_option="RAW")


# ---------- Public API (mismo "contrato" que tu db.py) ----------
def init_db() -> None:
    try:
        sh = _sh()
        for name in [TAB_FOODS, TAB_ENTRIES, TAB_SETTINGS]:
            sh.worksheet(name)
    except Exception as e:
        raise RuntimeError(
            "No puedo abrir el Google Sheet o no encuentro las pestañas: foods, entries, settings."
        ) from e


def seed_foods_if_empty(foods):
    ws = _ws(TAB_FOODS)

    # ✅ check barato: si hay algo en la fila 2, ya está sembrado
    if ws.acell("A2").value or ws.acell("B2").value:
        return

    rows_to_add = []
    next_id = 1
    for f in foods:
        rows_to_add.append([
            next_id,
            f["name"],
            f["category"],
            _to_float(f.get("calories", 0)),
            _to_float(f.get("protein", 0)),
            _to_float(f.get("carbs", 0)),
            _to_float(f.get("fat", 0)),
        ])
        next_id += 1

    ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")
    st.cache_data.clear()


def list_categories() -> List[str]:
    foods = _get_all_records(TAB_FOODS)
    cats = sorted({str(f.get("category", "")).strip() for f in foods if f.get("category")})
    return cats


def list_foods_by_category(category: str) -> List[Dict[str, Any]]:
    foods = _get_all_records(TAB_FOODS)
    out = []
    for f in foods:
        if str(f.get("category", "")).strip() == category:
            out.append({
                "id": _to_int(f.get("id")),
                "name": str(f.get("name", "")).strip(),
                "category": str(f.get("category", "")).strip(),
                "calories": _to_float(f.get("calories")),
                "protein": _to_float(f.get("protein")),
                "carbs": _to_float(f.get("carbs")),
                "fat": _to_float(f.get("fat")),
            })
    return out


def list_all_foods() -> List[Dict[str, Any]]:
    foods = _get_all_records(TAB_FOODS)
    out = []
    for f in foods:
        out.append({
            "id": _to_int(f.get("id")),
            "name": str(f.get("name", "")).strip(),
            "category": str(f.get("category", "")).strip(),
            "calories": _to_float(f.get("calories")),
            "protein": _to_float(f.get("protein")),
            "carbs": _to_float(f.get("carbs")),
            "fat": _to_float(f.get("fat")),
        })
    # orden estable
    out.sort(key=lambda x: (x["category"], x["name"]))
    return out


def add_food(food: Dict[str, Any]) -> int:
    ws = _ws(TAB_FOODS)
    new_id = _next_id(TAB_FOODS)
    ws.append_row([
        new_id,
        food["name"],
        food["category"],
        _to_float(food.get("calories", 0)),
        _to_float(food.get("protein", 0)),
        _to_float(food.get("carbs", 0)),
        _to_float(food.get("fat", 0)),
    ], value_input_option="USER_ENTERED")
    st.cache_data.clear()
    return new_id


def update_food(food_id: int, updates: Dict[str, Any]) -> None:
    row_idx = _find_row_index_by_id(TAB_FOODS, food_id)
    if row_idx is None:
        raise ValueError(f"No existe food id={food_id}")

    ws = _ws(TAB_FOODS)
    # columnas: A id, B name, C category, D calories, E protein, F carbs, G fat
    values = [
        food_id,
        updates.get("name"),
        updates.get("category"),
        updates.get("calories"),
        updates.get("protein"),
        updates.get("carbs"),
        updates.get("fat"),
    ]

    # Si algún campo no viene, mantenemos lo que hay
    current = ws.row_values(row_idx)
    while len(current) < 7:
        current.append("")

    merged = [
        str(values[i]) if values[i] is not None else current[i]
        for i in range(7)
    ]
    st.cache_data.clear()
    ws.update(f"A{row_idx}:G{row_idx}", [merged], value_input_option="USER_ENTERED")


def delete_food_by_id(food_id: int) -> None:
    row_idx = _find_row_index_by_id(TAB_FOODS, food_id)
    if row_idx is None:
        return
    _ws(TAB_FOODS).delete_rows(row_idx)
    st.cache_data.clear()



def add_entry(user_id: str, entry: Dict[str, Any]) -> int:
    ws = _ws(TAB_ENTRIES)
    new_id = _next_id(TAB_ENTRIES)

    row_dict = {
        "id": new_id,
        "user_id": user_id,
        "entry_date": entry["entry_date"],
        "meal": entry["meal"],
        "name": entry["name"],
        "grams": _to_float(entry.get("grams", 0)),
        "calories": _to_float(entry.get("calories", 0)),
        "protein": _to_float(entry.get("protein", 0)),
        "carbs": _to_float(entry.get("carbs", 0)),
        "fat": _to_float(entry.get("fat", 0)),
    }

    _append_row_by_headers(ws, row_dict)
    st.cache_data.clear()
    return new_id




def list_entries_by_date(user_id: str, entry_date: str) -> List[Dict[str, Any]]:
    rows = _get_all_records(TAB_ENTRIES)
    out = []
    for r in rows:
        r_uid = str(r.get("user_id", "")).strip()
        r_date = str(r.get("entry_date", "")).strip()

        if r_uid == str(user_id).strip() and r_date == str(entry_date).strip():
            out.append({
                "id": _to_int(r.get("id")),
                "user_id": r_uid,
                "entry_date": r_date,
                "meal": str(r.get("meal", "")).strip(),
                "name": str(r.get("name", "")).strip(),
                "grams": _to_float(r.get("grams")),
                "calories": _to_float(r.get("calories")),
                "protein": _to_float(r.get("protein")),
                "carbs": _to_float(r.get("carbs")),
                "fat": _to_float(r.get("fat")),
            })
    return out




def update_entry(entry_id: int, **updates) -> None:
    row_idx = _find_row_index_by_id(TAB_ENTRIES, entry_id)
    if row_idx is None:
        raise ValueError(f"No existe entry id={entry_id}")

    ws = _ws(TAB_ENTRIES)
    # A id, B entry_date, C meal, D name, E grams, F calories, G protein, H carbs, I fat
    current = ws.row_values(row_idx)
    while len(current) < 9:
        current.append("")

    def pick(col_index_0based: int, key: str):
        v = updates.get(key, None)
        return str(v) if v is not None else current[col_index_0based]

    merged = [
        str(entry_id),                       # id siempre
        pick(1, "entry_date"),
        pick(2, "meal"),
        pick(3, "name"),
        pick(4, "grams"),
        pick(5, "calories"),
        pick(6, "protein"),
        pick(7, "carbs"),
        pick(8, "fat"),
    ]
    st.cache_data.clear()
    ws.update(f"A{row_idx}:I{row_idx}", [merged], value_input_option="USER_ENTERED")


def delete_entry_by_id(entry_id: int) -> None:
    row_idx = _find_row_index_by_id(TAB_ENTRIES, entry_id)
    if row_idx is None:
        return
    _ws(TAB_ENTRIES).delete_rows(row_idx)
    st.cache_data.clear()

def daily_totals_last_days(days: int = 30) -> List[Tuple[str, float, float, float, float]]:
    """
    Devuelve lista de tuplas:
    (date, calories, protein, carbs, fat)
    """
    rows = _get_all_records(TAB_ENTRIES)
    today = dt.date.today()
    start = today - dt.timedelta(days=days - 1)

    agg: Dict[str, Dict[str, float]] = {}
    for r in rows:
        d = str(r.get("entry_date", "")).strip()
        if not d:
            continue
        try:
            dd = dt.date.fromisoformat(d)
        except Exception:
            continue
        if dd < start or dd > today:
            continue

        if d not in agg:
            agg[d] = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        agg[d]["calories"] += _to_float(r.get("calories")) / 100
        agg[d]["protein"] += _to_float(r.get("protein")) / 100
        agg[d]["carbs"] += _to_float(r.get("carbs")) / 100
        agg[d]["fat"] += _to_float(r.get("fat")) / 100


    out = []
    for d in sorted(agg.keys()):
        a = agg[d]
        out.append((d, a["calories"], a["protein"], a["carbs"], a["fat"]))
    return out


def get_setting(key: str, default: Any = None) -> Any:
    rows = _get_all_records(TAB_SETTINGS)
    for r in rows:
        if str(r.get("key", "")).strip() == key:
            v = r.get("value", "")
            return v if v != "" else default
    return default


def set_setting(key: str, value: str) -> None:
    ws = _ws(TAB_SETTINGS)
    rows = ws.get_all_records()
    # buscamos fila
    for i, r in enumerate(rows, start=2):  # fila real en sheet
        if str(r.get("key", "")).strip() == key:
            ws.update(f"A{i}:B{i}", [[key, value]], value_input_option="USER_ENTERED")
            return
    ws.append_row([key, value], value_input_option="USER_ENTERED")
    st.cache_data.clear()






















